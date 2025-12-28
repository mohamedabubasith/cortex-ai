"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import api from "@/lib/api";
import { Loader2, Globe, Clock, MapPin, Monitor, Trash2, Info, ChevronLeft, ChevronRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import Dialog from "@/components/ui/Dialog";

const PAGE_SIZE = 20;

export default function VisitorsPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [visitors, setVisitors] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [selectedVisitor, setSelectedVisitor] = useState<any>(null);
    const [currentPage, setCurrentPage] = useState(1);

    const fetchVisitors = async (page: number = 1) => {
        try {
            setLoading(true);
            const offset = (page - 1) * PAGE_SIZE;
            const response = await api.get(`/admin/visitors/list?limit=${PAGE_SIZE}&offset=${offset}`);
            setVisitors(response.data);
        } catch (err: any) {
            console.error(err);
            setError("Failed to load visitors. You might not be authorized.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVisitors(currentPage);
    }, [currentPage]);

    const handleClearLogs = async () => {
        if (!confirm("Are you sure you want to clear all visitor logs?")) return;
        try {
            await api.delete("/admin/visitors/list");
            setVisitors([]);
            setCurrentPage(1);
            toast.success("Visitor logs cleared");
        } catch (err) {
            console.error(err);
            toast.error("Failed to clear logs");
        }
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
            <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold tracking-tight mb-2">Visitor Traffic</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>Real-time monitoring of API traffic and visitor locations.</p>
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
                                <th className="px-6 py-4 font-medium">IP Address</th>
                                <th className="px-6 py-4 font-medium">Location</th>
                                <th className="px-6 py-4 font-medium">Path</th>
                                <th className="px-6 py-4 font-medium">User Agent</th>
                            </tr>
                        </thead>
                        <tbody className={`divide-y ${isDark ? "divide-white/5" : "divide-gray-100"}`}>
                            {visitors.map((visitor) => (
                                <tr
                                    key={visitor.id}
                                    onClick={() => setSelectedVisitor(visitor)}
                                    className={`transition-colors cursor-pointer ${isDark ? "hover:bg-white/5" : "hover:bg-gray-50"}`}
                                >
                                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                                        <div className="flex items-center gap-2">
                                            <Clock className="w-4 h-4" />
                                            {formatDistanceToNow(new Date(visitor.created_at), { addSuffix: true })}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-mono text-xs">
                                        {visitor.meta_data?.ip || "Unknown"}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <Globe className="w-4 h-4 text-blue-400" />
                                            {visitor.meta_data?.country || "Unknown"}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-mono text-xs text-nvidia-green">
                                        {visitor.event_data?.method} {visitor.event_data?.path}
                                    </td>
                                    <td className="px-6 py-4 max-w-xs truncate text-gray-500" title={visitor.meta_data?.user_agent}>
                                        <div className="flex items-center gap-2">
                                            <Monitor className="w-4 h-4" />
                                            {visitor.meta_data?.user_agent?.split(')')[0] + ')' || "Unknown"}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {visitors.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                                        No visitors recorded yet.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {visitors.length > 0 && (
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
                                disabled={visitors.length < PAGE_SIZE}
                                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${visitors.length < PAGE_SIZE
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

            {/* Visitor Details Modal */}
            <Dialog
                isOpen={!!selectedVisitor}
                onClose={() => setSelectedVisitor(null)}
                title="Visitor Details"
            >
                {selectedVisitor && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2 p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/10">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</label>
                                <div className="font-mono text-lg">{selectedVisitor.meta_data?.ip}</div>
                                {selectedVisitor.meta_data?.isp && (
                                    <div className="text-sm text-gray-400 mt-1">{selectedVisitor.meta_data.isp}</div>
                                )}
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Location</label>
                                <div className="font-medium">{selectedVisitor.meta_data?.city || "Unknown"}, {selectedVisitor.meta_data?.regionName || ""}</div>
                                <div className="text-sm text-gray-400">{selectedVisitor.meta_data?.country}</div>
                            </div>

                            <div>
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Coordinates</label>
                                <div className="font-mono text-sm">
                                    {selectedVisitor.meta_data?.lat ? `${selectedVisitor.meta_data.lat}, ${selectedVisitor.meta_data.lon}` : "N/A"}
                                </div>
                                <div className="text-sm text-gray-400">{selectedVisitor.meta_data?.timezone}</div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">User Agent</label>
                                <div className="text-sm font-mono break-all bg-gray-50 dark:bg-black p-2 rounded border border-gray-100 dark:border-white/10 mt-1">
                                    {selectedVisitor.meta_data?.user_agent}
                                </div>
                            </div>

                            <div className="col-span-2">
                                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Request</label>
                                <div className="text-sm font-mono text-nvidia-green mt-1">
                                    {selectedVisitor.event_data?.method} {selectedVisitor.event_data?.path}
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                    {new Date(selectedVisitor.created_at).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </Dialog>
        </div>
    );
}
