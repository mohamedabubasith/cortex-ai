"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState, memo } from "react";
import { Users, Database, Cpu, Activity, ArrowUpRight, TrendingUp, MessageSquare, AlertCircle } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Area, AreaChart, Cell } from "recharts";
import api from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [stats, setStats] = useState({
        agents: 0,
        kbs: 0,
        llms: 0,
        apiCalls: 0
    });
    const [analyticsData, setAnalyticsData] = useState<any>(null);
    const [usageData, setUsageData] = useState<any[]>([]);
    const [tokenData, setTokenData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                // Use allSettled to prevent one failure from breaking everything
                const results = await Promise.allSettled([
                    api.get("/agents"),
                    api.get("/llm"),
                    api.get("/analytics/stats/overview?hours=24"),
                    api.get("/analytics/stats/usage?hours=12"), // Fetch usage history directly
                    api.get("/kb"),
                    api.get("/analytics/stats/agents?limit=5")
                ]);

                // Helper to get data or default
                const getData = (result: PromiseSettledResult<any>, defaultVal: any) =>
                    result.status === 'fulfilled' ? result.value.data : defaultVal;

                const agentsData = getData(results[0], []);
                const llmData = getData(results[1], []);
                const analyticsOverview = getData(results[2], {});
                const usageHistory = getData(results[3], []);
                const kbData = getData(results[4], []);
                const topAgentsData = getData(results[5], []);

                setStats({
                    agents: agentsData.length,
                    llms: llmData.length,
                    kbs: kbData.length,
                    apiCalls: analyticsOverview.api_hits?.total_hits || 0
                });

                setAnalyticsData(analyticsOverview);

                // Set aggregated usage data directly
                setUsageData(usageHistory);

                // Process Token Data from Backend
                setTokenData(topAgentsData);

            } catch (error) {
                console.error("Failed to fetch stats", error);
                setError("Failed to load dashboard data.");
            } finally {
                setLoading(false);
            }
        };

        fetchStats();

        // Refresh every 30 seconds
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    const StatCard = memo(({ title, value, icon: Icon, trend, isDark }: any) => (
        <div className={`backdrop-blur-xl border rounded-2xl p-6 transition-all duration-300 group relative overflow-hidden ${isDark ? "bg-nvidia-dark/50 border-white/10 hover:border-nvidia-green/30" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm"}`}>
            {/* Hover Glow Effect */}
            <div className="absolute -inset-2 bg-nvidia-green/20 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-full" />

            <div className="relative z-10">
                <div className="flex justify-between items-start mb-4">
                    <div className={`p-3 rounded-xl transition-all duration-300 ${isDark ? "bg-white/5 group-hover:bg-nvidia-green text-gray-400 group-hover:text-black" : "bg-gray-100 group-hover:bg-nvidia-green text-gray-600 group-hover:text-black"}`}>
                        <Icon className="w-6 h-6" />
                    </div>
                    {trend && (
                        <div className="flex items-center text-nvidia-green text-sm font-medium bg-nvidia-green/10 px-2 py-1 rounded-lg border border-nvidia-green/20">
                            <ArrowUpRight className="w-3 h-3 mr-1" />
                            {trend}
                        </div>
                    )}
                </div>
                <h3 className={`text-sm font-medium mb-1 ${isDark ? "text-gray-400" : "text-gray-600"}`}>{title}</h3>
                <p className={`text-3xl font-bold tracking-tight ${isDark ? "text-white" : "text-gray-900"}`}>{value}</p>
            </div>
        </div>
    ));
    StatCard.displayName = "StatCard";

    const CustomTooltip = memo(({ active, payload, label, isDark }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className={`border rounded-xl p-4 backdrop-blur-md shadow-xl ${isDark ? "bg-black/80 border-white/10" : "bg-white/90 border-gray-200"}`}>
                    <p className={`text-sm font-semibold mb-2 ${isDark ? "text-gray-300" : "text-gray-700"}`}>{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 text-sm mb-1">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                            <span className={isDark ? "text-gray-400" : "text-gray-600"}>{entry.name}:</span>
                            <span className={`font-mono font-medium ${isDark ? "text-white" : "text-gray-900"}`}>{entry.value}</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    });
    CustomTooltip.displayName = "CustomTooltip";

    if (loading) {
        return (
            <div className="space-y-8 animate-in fade-in duration-500">
                <div>
                    <Skeleton className="h-10 w-48 mb-2" />
                    <Skeleton className="h-5 w-64" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[...Array(4)].map((_, i) => (
                        <Skeleton key={i} className="h-40 rounded-2xl" />
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Skeleton className="h-[350px] rounded-2xl" />
                    <Skeleton className="h-[350px] rounded-2xl" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-[50vh] flex flex-col items-center justify-center text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
                <h2 className={`text-xl font-bold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>Something went wrong</h2>
                <p className={`text-sm max-w-md ${isDark ? "text-gray-400" : "text-gray-600"}`}>{error}</p>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-6 px-4 py-2 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-colors"
                >
                    Retry
                </button>
            </div>
        )
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div>
                <h1 className={`text-2xl md:text-3xl font-bold tracking-tight mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>Dashboard Overview</h1>
                <p className={isDark ? "text-gray-400" : "text-gray-600"}>Real-time analytics and system status.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Active Agents" value={stats.agents} icon={Users} isDark={isDark} />
                <StatCard title="Knowledge Bases" value={stats.kbs} icon={Database} isDark={isDark} />
                <StatCard title="LLM Models" value={stats.llms} icon={Cpu} isDark={isDark} />
                <StatCard title="API Calls (24h)" value={stats.apiCalls.toLocaleString()} icon={Activity} isDark={isDark} />
            </div>

            {/* Token Usage Stats - Mini Cards */}
            {analyticsData && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className={`border rounded-2xl p-6 relative overflow-hidden group ${isDark ? "bg-nvidia-dark/30 border-white/5 hover:border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <MessageSquare className="w-24 h-24 text-nvidia-green" />
                        </div>
                        <div className="flex items-center gap-3 mb-2 relative z-10">
                            <MessageSquare className="w-5 h-5 text-nvidia-green" />
                            <h3 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Total Chats</h3>
                        </div>
                        <p className={`text-3xl font-bold relative z-10 ${isDark ? "text-white" : "text-gray-900"}`}>{analyticsData.token_usage?.total_requests || 0}</p>
                        <p className={`text-sm mt-1 relative z-10 ${isDark ? "text-gray-400" : "text-gray-600"}`}>Last 24 hours</p>
                    </div>

                    <div className={`border rounded-2xl p-6 relative overflow-hidden group ${isDark ? "bg-nvidia-dark/30 border-white/5 hover:border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <TrendingUp className="w-24 h-24 text-blue-400" />
                        </div>
                        <div className="flex items-center gap-3 mb-2 relative z-10">
                            <TrendingUp className="w-5 h-5 text-blue-400" />
                            <h3 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Tokens Used</h3>
                        </div>
                        <p className={`text-3xl font-bold relative z-10 ${isDark ? "text-white" : "text-gray-900"}`}>{(analyticsData.token_usage?.total_tokens || 0).toLocaleString()}</p>
                        <p className={`text-sm mt-1 relative z-10 ${isDark ? "text-gray-400" : "text-gray-600"}`}>Avg: {Math.round(analyticsData.token_usage?.avg_tokens_per_request || 0)}/chat</p>
                    </div>

                    <div className={`border rounded-2xl p-6 relative overflow-hidden group ${isDark ? "bg-nvidia-dark/30 border-white/5 hover:border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <Activity className="w-24 h-24 text-purple-400" />
                        </div>
                        <div className="flex items-center gap-3 mb-2 relative z-10">
                            <Activity className="w-5 h-5 text-purple-400" />
                            <h3 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Unique Users</h3>
                        </div>
                        <p className={`text-3xl font-bold relative z-10 ${isDark ? "text-white" : "text-gray-900"}`}>{analyticsData.api_hits?.unique_users || 0}</p>
                        <p className={`text-sm mt-1 relative z-10 ${isDark ? "text-gray-400" : "text-gray-600"}`}>Active in 24h</p>
                    </div>
                </div>
            )}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Usage Analytics Chart */}
                <div className={`border rounded-2xl p-6 ${isDark ? "bg-nvidia-dark/30 border-white/5" : "bg-white border-gray-200 shadow-sm"}`}>
                    <h3 className={`text-base font-bold mb-6 flex items-center gap-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                        <Activity className="w-5 h-5 text-nvidia-green" />
                        Usage Activity (12h)
                    </h3>
                    <div className="h-[300px] w-full">
                        {usageData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={usageData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorChats" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#76b900" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#76b900" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="colorHits" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#333" : "#e5e7eb"} vertical={false} />
                                    <XAxis
                                        dataKey="time"
                                        stroke={isDark ? "#666" : "#9ca3af"}
                                        tick={{ fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                        dy={10}
                                        tickFormatter={(str) => {
                                            if (!str) return "";
                                            try {
                                                if (str.includes(":00") && str.length === 5) return str;
                                                const date = new Date(str);
                                                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                                            } catch (e) {
                                                return str;
                                            }
                                        }}
                                    />
                                    <YAxis
                                        stroke={isDark ? "#666" : "#9ca3af"}
                                        tick={{ fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                        dx={-10}
                                    />
                                    <Tooltip content={<CustomTooltip isDark={isDark} />} cursor={{ stroke: isDark ? '#ffffff20' : '#00000010', strokeWidth: 2 }} />
                                    <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                                    <Area
                                        type="monotone"
                                        dataKey="chats"
                                        stroke="#76b900"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#colorChats)"
                                        name="Chats"
                                        activeDot={{ r: 6, strokeWidth: 0, fill: '#76b900' }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="hits"
                                        stroke="#3b82f6"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#colorHits)"
                                        name="API Hits"
                                        activeDot={{ r: 6, strokeWidth: 0, fill: '#3b82f6' }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className={`h-full flex items-center justify-center ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                                No usage data available
                            </div>
                        )}
                    </div>
                </div>

                {/* Agent Performance Chart */}
                <div className={`border rounded-2xl p-6 ${isDark ? "bg-nvidia-dark/30 border-white/5" : "bg-white border-gray-200 shadow-sm"}`}>
                    <h3 className={`text-base font-bold mb-6 flex items-center gap-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                        Top Agents (By Tokens)
                    </h3>
                    <div className="h-[300px] w-full">
                        {tokenData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={tokenData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#333" : "#e5e7eb"} vertical={false} />
                                    <XAxis
                                        dataKey="name"
                                        stroke={isDark ? "#666" : "#9ca3af"}
                                        tick={{ fontSize: 12 }}
                                        axisLine={false}
                                        tickLine={false}
                                        dy={10}
                                    />
                                    <YAxis
                                        stroke={isDark ? "#666" : "#9ca3af"}
                                        tick={{ fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                        dx={-10}
                                    />
                                    <Tooltip cursor={{ fill: isDark ? '#ffffff05' : '#00000005' }} content={<CustomTooltip isDark={isDark} />} />
                                    <Bar
                                        dataKey="tokens"
                                        fill="#76b900"
                                        name="Tokens"
                                        radius={[6, 6, 0, 0]}
                                        barSize={40}
                                    >
                                        {tokenData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={index === 0 ? '#76b900' : '#76b90080'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className={`h-full flex items-center justify-center ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                                No agent data available
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

