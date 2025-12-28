"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import api from "@/lib/api";
import { Loader2, Clock, User, Activity, Globe, FileText, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import Dialog from "@/components/ui/Dialog";

const PAGE_SIZE = 20;

export default function AuditLogsPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [selectedLog, setSelectedLog] = useState<any>(null);
    const [user, setUser] = useState<any>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalLogs, setTotalLogs] = useState(0);

    useEffect(() => {
        // Fetch current user
        api.get("/auth/me").then(res => setUser(res.data)).catch(console.error);
    }, []);

    const fetchLogs = async (page: number = 1) => {
        try {
            setLoading(true);
            const offset = (page - 1) * PAGE_SIZE;
            const response = await api.get(`/analytics/audit/logs?limit=${PAGE_SIZE}&offset=${offset}`);
            setLogs(response.data);
            // Note: Backend doesn't return total count, so we estimate
            setTotalLogs(response.data.length === PAGE_SIZE ? page * PAGE_SIZE + 1 : (page - 1) * PAGE_SIZE + response.data.length);
        } catch (err: any) {
            console.error(err);
            setError("Failed to load audit logs. You might not be authorized.");
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
        if (!confirm("Are you sure you want to clear all your audit logs? This action cannot be undone.")) return;
        try {
            await api.delete("/analytics/audit/logs");
            setLogs([]);
            setCurrentPage(1);
            toast.success("Audit logs cleared");
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

    const totalPages = Math.ceil(totalLogs / PAGE_SIZE);

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
                        {user?.is_superuser ? "Complete history of all user actions and API requests." : "Your activity history and API requests."}
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
                                <th className="px-6 py-4 font-medium">User</th>
                                <th className="px-6 py-4 font-medium">Action</th>
                                <th className="px-6 py-4 font-medium">Resource</th>
                                <th className="px-6 py-4 font-medium">IP Address</th>
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
                            {logs.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                                        No audit logs recorded yet.
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
                            Page {currentPage} of {totalPages || 1}
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

            {/* Audit Log Details Modal */}
            <Dialog
                isOpen={!!selectedLog}
                onClose={() => setSelectedLog(null)}
                title="Audit Log Details"
            >
                {selectedLog && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Action</label>
                                <div className="mt-1">
                                    <span className={`px-3 py-1 rounded-md text-sm font-medium border ${getActionBadge(selectedLog.action)}`}>
                                        {selectedLog.action.toUpperCase()}
                                    </span>
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">User</label>
                                <div className="font-medium mt-1">{selectedLog.details?.user_email || "Anonymous"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</label>
                                <div className="text-sm mt-1">{new Date(selectedLog.created_at).toLocaleString()}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Resource Type</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.resource_type}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Resource ID</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.resource_id || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.ip_address || "N/A"}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Status Code</label>
                                <div className="font-mono text-sm mt-1">{selectedLog.details?.status_code || "N/A"}</div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Request Path</label>
                                <div className="font-mono text-sm bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1">
                                    {selectedLog.details?.method} {selectedLog.details?.path}
                                </div>
                            </div>

                            {selectedLog.details?.request_body && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Request Body</label>
                                    <div className="text-sm font-mono break-all bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {selectedLog.details.request_body}
                                    </div>
                                </div>
                            )}

                            {selectedLog.details?.query_params && Object.keys(selectedLog.details.query_params).length > 0 && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Query Parameters</label>
                                    <div className="text-sm font-mono bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1">
                                        {JSON.stringify(selectedLog.details.query_params, null, 2)}
                                    </div>
                                </div>
                            )}

                            {selectedLog.details?.response_body && (
                                <div className="col-span-2">
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Response Body</label>
                                    <div className="text-sm font-mono break-all bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1 max-h-40 overflow-y-auto">
                                        {selectedLog.details.response_body}
                                    </div>
                                </div>
                            )}

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">User Agent</label>
                                <div className="text-sm font-mono break-all bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1">
                                    {selectedLog.user_agent || "N/A"}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </Dialog>
        </div>
    );
}
