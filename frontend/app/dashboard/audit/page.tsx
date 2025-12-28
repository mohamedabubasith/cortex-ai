"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import api from "@/lib/api";
import { Loader2, Clock, User, Activity, Globe, FileText, Trash2, ChevronLeft, ChevronRight, Bot, MessageSquare, TrendingUp, Zap } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import Dialog from "@/components/ui/Dialog";

const PAGE_SIZE = 20;

type TabType = "api" | "agent";

export default function AuditLogsPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [activeTab, setActiveTab] = useState<TabType>("api");

    // API Logs State
    const [apiLogs, setApiLogs] = useState<any[]>([]);
    const [apiLoading, setApiLoading] = useState(true);
    const [apiError, setApiError] = useState("");
    const [selectedApiLog, setSelectedApiLog] = useState<any>(null);
    const [apiCurrentPage, setApiCurrentPage] = useState(1);

    // Agent Logs State
    const [agentLogs, setAgentLogs] = useState<any[]>([]);
    const [agentLoading, setAgentLoading] = useState(true);
    const [agentError, setAgentError] = useState("");
    const [selectedAgentLog, setSelectedAgentLog] = useState<any>(null);
    const [agentCurrentPage, setAgentCurrentPage] = useState(1);

    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        api.get("/auth/me").then(res => setUser(res.data)).catch(console.error);
    }, []);

    const fetchApiLogs = async (page: number = 1) => {
        try {
            setApiLoading(true);
            const offset = (page - 1) * PAGE_SIZE;
            const response = await api.get(`/analytics/audit/logs?limit=${PAGE_SIZE}&offset=${offset}`);
            setApiLogs(response.data);
        } catch (err: any) {
            console.error(err);
            setApiError("Failed to load API logs.");
        } finally {
            setApiLoading(false);
        }
    };

    const fetchAgentLogs = async (page: number = 1) => {
        try {
            setAgentLoading(true);
            const offset = (page - 1) * PAGE_SIZE;
            const response = await api.get(`/analytics/agent-audit/logs?limit=${PAGE_SIZE}&offset=${offset}`);
            setAgentLogs(response.data);
        } catch (err: any) {
            console.error(err);
            setAgentError("Failed to load agent logs.");
        } finally {
            setAgentLoading(false);
        }
    };

    useEffect(() => {
        if (user && activeTab === "api") {
            fetchApiLogs(apiCurrentPage);
        }
    }, [user, apiCurrentPage, activeTab]);

    useEffect(() => {
        if (user && activeTab === "agent") {
            fetchAgentLogs(agentCurrentPage);
        }
    }, [user, agentCurrentPage, activeTab]);

    const handleClearApiLogs = async () => {
        if (!confirm("Are you sure you want to clear all API audit logs? This action cannot be undone.")) return;
        try {
            await api.delete("/analytics/audit/logs");
            setApiLogs([]);
            setApiCurrentPage(1);
            toast.success("API audit logs cleared");
        } catch (err) {
            console.error(err);
            toast.error("Failed to clear logs");
        }
    };

    const handleClearAgentLogs = async () => {
        if (!confirm("Are you sure you want to clear all agent logs? This action cannot be undone.")) return;
        try {
            await api.delete("/analytics/agent-audit/logs");
            setAgentLogs([]);
            setAgentCurrentPage(1);
            toast.success("Agent logs cleared");
        } catch (err) {
            console.error(err);
            toast.error("Failed to clear logs");
        }
    };

    const getActionColor = (action: string) => {
        const colors: any = {
            "create": "text-green-500",
            "update": "text-blue-500",
            "delete": "text-red-500",
            "access": "text-gray-500"
        };
        return colors[action] || "text-gray-500";
    };

    const getActionBadge = (action: string) => {
        const badges: any = {
            "create": "bg-green-500/10 text-green-500 border-green-500/20",
            "update": "bg-blue-500/10 text-blue-500 border-blue-500/20",
            "delete": "bg-red-500/10 text-red-500 border-red-500/20",
            "access": "bg-gray-500/10 text-gray-500 border-gray-500/20"
        };
        return badges[action] || "bg-gray-500/10 text-gray-500 border-gray-500/20";
    };

    const loading = activeTab === "api" ? apiLoading : agentLoading;
    const error = activeTab === "api" ? apiError : agentError;
    const currentPage = activeTab === "api" ? apiCurrentPage : agentCurrentPage;
    const setCurrentPage = activeTab === "api" ? setApiCurrentPage : setAgentCurrentPage;
    const logs = activeTab === "api" ? apiLogs : agentLogs;

    if (loading && currentPage === 1) {
        return (
            <div className={`flex h-full items-center justify-center ${isDark ? "bg-black text-[#76B900]" : "bg-white text-[#76B900]"}`}>
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        );
    }

    if (error) {
        return (
            <div className={`p-8 text-center ${isDark ? "text-red-400" : "text-red-600"}`}>
                {error}
            </div>
        );
    }

    return (
        <div className={`min-h-full ${isDark ? "text-white" : "text-gray-900"}`}>
            <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold tracking-tight mb-2">Audit Logs</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                        {activeTab === "api"
                            ? (user?.is_superuser ? "Complete history of all API requests." : "Your API activity history.")
                            : (user?.is_superuser ? "Complete history of all LLM interactions." : "Your LLM interaction history.")}
                    </p>
                </div>
                <button
                    onClick={activeTab === "api" ? handleClearApiLogs : handleClearAgentLogs}
                    className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isDark ? "bg-red-900/20 text-red-400 hover:bg-red-900/40" : "bg-red-50 text-red-600 hover:bg-red-100"}`}
                >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Clear Logs
                </button>
            </div>

            {/* Tabs */}
            <div className="mb-6 flex gap-2 border-b border-gray-200 dark:border-white/10">
                <button
                    onClick={() => setActiveTab("api")}
                    className={`px-4 py-2 font-medium text-sm transition-colors border-b-2 ${activeTab === "api"
                            ? "border-nvidia-green text-nvidia-green"
                            : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        API Logs
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab("agent")}
                    className={`px-4 py-2 font-medium text-sm transition-colors border-b-2 ${activeTab === "agent"
                            ? "border-nvidia-green text-nvidia-green"
                            : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        Agent Logs
                    </div>
                </button>
            </div>

            {/* API Logs Table */}
            {activeTab === "api" && (
                <div className={`rounded-2xl border overflow-hidden ${isDark ? "bg-nvidia-dark/50 border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className={`border-b ${isDark ? "border-white/10 bg-white/5" : "border-gray-200 bg-gray-50"}`}>
                                <tr>
                                    <th className="px-6 py-4 font-medium">Time</th>
                                    <th className="px-6 py-4 font-medium">User</th>
                                    <th className="px-6 py-4 font-medium">Action</th>
                                    <th className="px-6 py-4 font-medium">Resource</th>
                                    <th className="px-6 py-4 font-medium">IP Address</th>
                                    <th className="px-6 py-4 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody className={`divide-y ${isDark ? "divide-white/5" : "divide-gray-100"}`}>
                                {apiLogs.map((log) => (
                                    <tr
                                        key={log.id}
                                        onClick={() => setSelectedApiLog(log)}
                                        className={`transition-colors cursor-pointer ${isDark ? "hover:bg-white/5" : "hover:bg-gray-50"}`}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                                            <div className="flex items-center gap-2">
                                                <Clock className="w-4 h-4" />
                                                {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <User className="w-4 h-4 text-blue-400" />
                                                {log.details?.user_email || "Anonymous"}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getActionBadge(log.action)}`}>
                                                {log.action.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <Activity className="w-4 h-4 text-nvidia-green" />
                                                <span className="font-mono text-xs">{log.resource_type}</span>
                                                {log.resource_id && (
                                                    <span className="text-gray-500 text-xs">#{log.resource_id.substring(0, 8)}</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-xs">
                                            {log.ip_address || "N/A"}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-md text-xs font-medium ${log.details?.status_code >= 200 && log.details?.status_code < 300
                                                ? "bg-green-500/10 text-green-500"
                                                : log.details?.status_code >= 400
                                                    ? "bg-red-500/10 text-red-500"
                                                    : "bg-gray-500/10 text-gray-500"
                                                }`}>
                                                {log.details?.status_code || "N/A"}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                                {apiLogs.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                                            No API audit logs recorded yet.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {apiLogs.length > 0 && (
                        <div className={`px-6 py-4 border-t flex items-center justify-between ${isDark ? "border-white/10" : "border-gray-200"}`}>
                            <div className="text-sm text-gray-500">
                                Page {apiCurrentPage}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setApiCurrentPage(p => Math.max(1, p - 1))}
                                    disabled={apiCurrentPage === 1}
                                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${apiCurrentPage === 1
                                            ? "opacity-50 cursor-not-allowed"
                                            : isDark
                                                ? "bg-white/10 hover:bg-white/20"
                                                : "bg-gray-100 hover:bg-gray-200"
                                        }`}
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => setApiCurrentPage(p => p + 1)}
                                    disabled={apiLogs.length < PAGE_SIZE}
                                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${apiLogs.length < PAGE_SIZE
                                            ? "opacity-50 cursor-not-allowed"
                                            : isDark
                                                ? "bg-white/10 hover:bg-white/20"
                                                : "bg-gray-100 hover:bg-gray-200"
                                        }`}
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Agent Logs Table */}
            {activeTab === "agent" && (
                <div className={`rounded-2xl border overflow-hidden ${isDark ? "bg-nvidia-dark/50 border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className={`border-b ${isDark ? "border-white/10 bg-white/5" : "border-gray-200 bg-gray-50"}`}>
                                <tr>
                                    <th className="px-6 py-4 font-medium">Time</th>
                                    <th className="px-6 py-4 font-medium">Agent</th>
                                    <th className="px-6 py-4 font-medium">Model</th>
                                    <th className="px-6 py-4 font-medium">Tokens</th>
                                    <th className="px-6 py-4 font-medium">Latency</th>
                                    <th className="px-6 py-4 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody className={`divide-y ${isDark ? "divide-white/5" : "divide-gray-100"}`}>
                                {agentLogs.map((log) => (
                                    <tr
                                        key={log.id}
                                        onClick={() => setSelectedAgentLog(log)}
                                        className={`transition-colors cursor-pointer ${isDark ? "hover:bg-white/5" : "hover:bg-gray-50"}`}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                                            <div className="flex items-center gap-2">
                                                <Clock className="w-4 h-4" />
                                                {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <Bot className="w-4 h-4 text-nvidia-green" />
                                                <span className="font-mono text-xs">{log.agent_id?.substring(0, 8) || "N/A"}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-xs">
                                            {log.model_name || "N/A"}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <TrendingUp className="w-4 h-4 text-blue-400" />
                                                <span className="font-mono text-xs">{log.total_tokens || 0}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-xs text-gray-500">
                                            {log.latency_ms || 0}ms
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-md text-xs font-medium ${log.status === "success"
                                                    ? "bg-green-500/10 text-green-500"
                                                    : "bg-red-500/10 text-red-500"
                                                }`}>
                                                {log.status?.toUpperCase() || "UNKNOWN"}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                                {agentLogs.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                                            No agent logs recorded yet.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {agentLogs.length > 0 && (
                        <div className={`px-6 py-4 border-t flex items-center justify-between ${isDark ? "border-white/10" : "border-gray-200"}`}>
                            <div className="text-sm text-gray-500">
                                Page {agentCurrentPage}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setAgentCurrentPage(p => Math.max(1, p - 1))}
                                    disabled={agentCurrentPage === 1}
                                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${agentCurrentPage === 1
                                            ? "opacity-50 cursor-not-allowed"
                                            : isDark
                                                ? "bg-white/10 hover:bg-white/20"
                                                : "bg-gray-100 hover:bg-gray-200"
                                        }`}
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => setAgentCurrentPage(p => p + 1)}
                                    disabled={agentLogs.length < PAGE_SIZE}
                                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${agentLogs.length < PAGE_SIZE
                                            ? "opacity-50 cursor-not-allowed"
                                            : isDark
                                                ? "bg-white/10 hover:bg-white/20"
                                                : "bg-gray-100 hover:bg-gray-200"
                                        }`}
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* API Log Details Modal */}
            <Dialog
                isOpen={!!selectedApiLog}
                onClose={() => setSelectedApiLog(null)}
                title="API Log Details"
            >
                {selectedApiLog && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Action</label>
                                <div className="mt-1">
                                    <span className={`px-3 py-1 rounded-md text-sm font-medium border ${getActionBadge(selectedApiLog.action)}`}>
                                        {selectedApiLog.action.toUpperCase()}
                                    </span>
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">User</label>
                                <div className="font-medium mt-1">{selectedApiLog.details?.user_email || "Anonymous"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</label>
                                <div className="text-sm mt-1">{new Date(selectedApiLog.created_at).toLocaleString()}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Resource Type</label>
                                <div className="font-mono text-sm mt-1">{selectedApiLog.resource_type}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Resource ID</label>
                                <div className="font-mono text-sm mt-1">{selectedApiLog.resource_id || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</label>
                                <div className="font-mono text-sm mt-1">{selectedApiLog.ip_address || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Status Code</label>
                                <div className="font-mono text-sm mt-1">{selectedApiLog.details?.status_code || "N/A"}</div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Request Path</label>
                                <div className="font-mono text-sm bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1">
                                    {selectedApiLog.details?.method} {selectedApiLog.details?.path}
                                </div>
                            </div>

                            {selectedApiLog.details?.request_body && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Request Body</label>
                                    <div className="text-sm font-mono break-all bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {selectedApiLog.details.request_body}
                                    </div>
                                </div>
                            )}

                            {selectedApiLog.details?.query_params && Object.keys(selectedApiLog.details.query_params).length > 0 && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Query Parameters</label>
                                    <div className="text-sm font-mono bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1">
                                        {JSON.stringify(selectedApiLog.details.query_params, null, 2)}
                                    </div>
                                </div>
                            )}

                            {selectedApiLog.details?.response_body && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Response Body</label>
                                    <div className="text-sm font-mono break-all bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {selectedApiLog.details.response_body}
                                    </div>
                                </div>
                            )}

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">User Agent</label>
                                <div className="text-sm font-mono break-all bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1">
                                    {selectedApiLog.user_agent || "N/A"}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </Dialog>

            {/* Agent Log Details Modal */}
            <Dialog
                isOpen={!!selectedAgentLog}
                onClose={() => setSelectedAgentLog(null)}
                title="Agent Interaction Details"
            >
                {selectedAgentLog && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                            {/* Token Usage */}
                            <div className="col-span-2 p-4 rounded-lg bg-nvidia-green/10 border border-nvidia-green/20">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Token Usage</label>
                                <div className="grid grid-cols-3 gap-4 mt-2">
                                    <div>
                                        <div className="text-xs text-gray-500">Prompt</div>
                                        <div className="text-lg font-bold text-nvidia-green">{selectedAgentLog.prompt_tokens || 0}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500">Completion</div>
                                        <div className="text-lg font-bold text-nvidia-green">{selectedAgentLog.completion_tokens || 0}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500">Total</div>
                                        <div className="text-lg font-bold text-nvidia-green">{selectedAgentLog.total_tokens || 0}</div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Model</label>
                                <div className="font-mono text-sm mt-1">{selectedAgentLog.model_name || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Latency</label>
                                <div className="font-mono text-sm mt-1">{selectedAgentLog.latency_ms || 0}ms</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Agent ID</label>
                                <div className="font-mono text-sm mt-1">{selectedAgentLog.agent_id || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Session ID</label>
                                <div className="font-mono text-sm mt-1">{selectedAgentLog.session_id?.substring(0, 16) || "N/A"}</div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">User Message</label>
                                <div className="text-sm bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                    {selectedAgentLog.user_message || "N/A"}
                                </div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">LLM Response</label>
                                <div className="text-sm bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-60 overflow-y-auto whitespace-pre-wrap">
                                    {selectedAgentLog.llm_response || "N/A"}
                                </div>
                            </div>

                            {selectedAgentLog.tool_calls && selectedAgentLog.tool_calls.length > 0 && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Tool Calls</label>
                                    <div className="text-sm font-mono bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {JSON.stringify(selectedAgentLog.tool_calls, null, 2)}
                                    </div>
                                </div>
                            )}

                            {selectedAgentLog.rag_context && Object.keys(selectedAgentLog.rag_context).length > 0 && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">RAG Context</label>
                                    <div className="text-sm font-mono bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {JSON.stringify(selectedAgentLog.rag_context, null, 2)}
                                    </div>
                                </div>
                            )}

                            {selectedAgentLog.error_message && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-red-500 uppercase tracking-wider">Error</label>
                                    <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/10 p-3 rounded border border-red-200 dark:border-red-500/20 mt-1">
                                        {selectedAgentLog.error_message}
                                    </div>
                                </div>
                            )}

                            <div className="col-span-2 text-xs text-gray-500 pt-2 border-t border-gray-200 dark:border-white/10">
                                <div>IP: {selectedAgentLog.ip_address || "N/A"}</div>
                                <div>Timestamp: {new Date(selectedAgentLog.created_at).toLocaleString()}</div>
                            </div>
                        </div>
                    </div>
                )}
            </Dialog>
        </div>
    );
}
