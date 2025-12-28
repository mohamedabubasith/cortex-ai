"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import api from "@/lib/api";
import { Loader2, Globe, Clock, MapPin, Monitor } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function VisitorsPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [visitors, setVisitors] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchVisitors = async () => {
            try {
                const response = await api.get("/admin/visitors/list?limit=100");
                setVisitors(response.data);
            } catch (err: any) {
                console.error(err);
                setError("Failed to load visitors. You might not be authorized.");
            } finally {
                setLoading(false);
            }
        };

        fetchVisitors();

        // Refresh every 30s
        const interval = setInterval(fetchVisitors, 30000);
        return () => clearInterval(interval);
    }, []);

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
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight mb-2">Visitor Traffic</h1>
                <p className={isDark ? "text-gray-400" : "text-gray-600"}>Real-time monitoring of API traffic and visitor locations.</p>
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
                                <tr key={visitor.id} className={`transition-colors ${isDark ? "hover:bg-white/5" : "hover:bg-gray-50"}`}>
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
            </div>
        </div>
    );
}
