"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import api from "@/lib/api";
import { Loader2, Clock, Zap, Trash2, ChevronLeft, ChevronRight, Bot, MessageSquare, TrendingUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import Dialog from "@/components/ui/Dialog";

const PAGE_SIZE = 20;

export default function AgentLogsPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [selectedLog, setSelectedLog] = useState<any>(null);
    const [user, setUser] = useState<any>(null);
    const [currentPage, setCurrentPage] = useState(1);

    useEffect(() => {
        api.get("/auth/me").then(res => setUser(res.data)).catch(console.error);
    }, []);

    const fetchLogs = async (page: number = 1) => {
        try {
            setLoading(true);
            const offset = (page - 1) * PAGE_SIZE;
            const response = await api.get(`/analytics/agent-audit/logs?limit=${PAGE_SIZE}&offset=${offset}`);
            setLogs(response.data);
        } catch (err: any) {
            console.error(err);
            setError("Failed to load agent logs.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchLogs(currentPage);
        }
    }, [user, currentPage]);

    const handleClearLogs = async () => {
        if (!confirm("Are you sure you want to clear all agent logs? This action cannot be undone.")) return;
        try {
            await api.delete("/analytics/agent-audit/logs");
            setLogs([]);
            setCurrentPage(1);
            toast.success("Agent logs cleared");
        } catch (err) {
            console.error(err);
            toast.error("Failed to clear logs");
        }
    };

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
                    <h1 className="text-2xl md:text-3xl font-bold tracking-tight mb-2">Agent Logs</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                        {user?.is_superuser ? "Complete history of all LLM interactions." : "Your LLM interaction history."}
                    </p>
                </div>
                <button
                    onClick={handleClearLogs}
                    className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isDark ? "bg-red-900/20 text-red-400 hover:bg-red-900/40" : "bg-red-50 text-red-600 hover:bg-red-100"}`}
                >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Clear Logs
                </button>
            </div>

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
                            {logs.map((log) => (
                                <tr
                                    key={log.id}
                                    onClick={() => setSelectedLog(log)}
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
                            {logs.length === 0 && (
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
                {logs.length > 0 && (
                    <div className={`px-6 py-4 border-t flex items-center justify-between ${isDark ? "border-white/10" : "border-gray-200"}`}>
                        <div className="text-sm text-gray-500">
                            Page {currentPage}
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${currentPage === 1
                                        ? "opacity-50 cursor-not-allowed"
                                        : isDark
                                            ? "bg-white/10 hover:bg-white/20"
                                            : "bg-gray-100 hover:bg-gray-200"
                                    }`}
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => setCurrentPage(p => p + 1)}
                                disabled={logs.length < PAGE_SIZE}
                                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${logs.length < PAGE_SIZE
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

            {/* Agent Log Details Modal */}
            <Dialog
                isOpen={!!selectedLog}
                onClose={() => setSelectedLog(null)}
                title="Agent Interaction Details"
            >
                {selectedLog && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                            {/* Token Usage */}
                            <div className="col-span-2 p-4 rounded-lg bg-nvidia-green/10 border border-nvidia-green/20">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Token Usage</label>
                                <div className="grid grid-cols-3 gap-4 mt-2">
                                    <div>
                                        <div className="text-xs text-gray-500">Prompt</div>
                                        <div className="text-lg font-bold text-nvidia-green">{selectedLog.prompt_tokens || 0}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500">Completion</div>
                                        <div className="text-lg font-bold text-nvidia-green">{selectedLog.completion_tokens || 0}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500">Total</div>
                                        <div className="text-lg font-bold text-nvidia-green">{selectedLog.total_tokens || 0}</div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Model</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.model_name || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Latency</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.latency_ms || 0}ms</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Agent ID</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.agent_id || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Session ID</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.session_id?.substring(0, 16) || "N/A"}</div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">User Message</label>
                                <div className="text-sm bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                    {selectedLog.user_message || "N/A"}
                                </div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">LLM Response</label>
                                <div className="text-sm bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-60 overflow-y-auto whitespace-pre-wrap">
                                    {selectedLog.llm_response || "N/A"}
                                </div>
                            </div>

                            {selectedLog.tool_calls && selectedLog.tool_calls.length > 0 && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Tool Calls</label>
                                    <div className="text-sm font-mono bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {JSON.stringify(selectedLog.tool_calls, null, 2)}
                                    </div>
                                </div>
                            )}

                            {selectedLog.rag_context && Object.keys(selectedLog.rag_context).length > 0 && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">RAG Context</label>
                                    <div className="text-sm font-mono bg-gray-50 dark:bg-black p-3 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {JSON.stringify(selectedLog.rag_context, null, 2)}
                                    </div>
                                </div>
                            )}

                            {selectedLog.error_message && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-red-500 uppercase tracking-wider">Error</label>
                                    <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/10 p-3 rounded border border-red-200 dark:border-red-500/20 mt-1">
                                        {selectedLog.error_message}
                                    </div>
                                </div>
                            )}

                            <div className="col-span-2 text-xs text-gray-500 pt-2 border-t border-gray-200 dark:border-white/10">
                                <div>IP: {selectedLog.ip_address || "N/A"}</div>
                                <div>Timestamp: {new Date(selectedLog.created_at).toLocaleString()}</div>
                            </div>
                        </div>
                    </div>
                )}
            </Dialog>
        </div>
    );
}
