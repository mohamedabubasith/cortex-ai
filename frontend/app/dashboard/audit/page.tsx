"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import api from "@/lib/api";
import { Loader2, Clock, User, Activity, Globe, FileText } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import Dialog from "@/components/ui/Dialog";

export default function AuditLogsPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [selectedLog, setSelectedLog] = useState<any>(null);
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        // Fetch current user
        api.get("/auth/me").then(res => setUser(res.data)).catch(console.error);
    }, []);

    const fetchLogs = async () => {
        try {
            // Admin users see all logs, regular users see only their own
            const response = await api.get("/analytics/audit/logs?limit=100");
            setLogs(response.data);
        } catch (err: any) {
            console.error(err);
            setError("Failed to load audit logs. You might not be authorized.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchLogs();
            const interval = setInterval(fetchLogs, 30000);
            return () => clearInterval(interval);
        }
    }, [user]);

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

    if (loading) {
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
            <div className="mb-8">
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight mb-2">Audit Logs</h1>
                <p className={isDark ? "text-gray-400" : "text-gray-600"}>Complete history of all user actions and API requests.</p>
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
