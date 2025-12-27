"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState, memo } from "react";
import { Users, Database, Cpu, Activity, ArrowUpRight, TrendingUp, MessageSquare } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Area, AreaChart } from "recharts";
import api from "@/lib/api";

export default function DashboardPage() {
    // Dashboard always uses dark theme
    const isDark = true;

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

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [agentsRes, llmRes, analyticsRes, liveEvents, kbRes] = await Promise.all([
                    api.get("/agents"),
                    api.get("/llm"),
                    api.get("/analytics/stats/overview?hours=24"),
                    api.get("/analytics/live?limit=50"),
                    api.get("/kb")
                ]);

                setStats({
                    agents: agentsRes.data.length,
                    llms: llmRes.data.length,
                    kbs: kbRes.data.length,
                    apiCalls: analyticsRes.data.api_hits?.total_hits || 0
                });

                setAnalyticsData(analyticsRes.data);

                // Process events for charts
                const events = liveEvents.data || [];

                // Group by hour for usage chart
                const hourlyData: any = {};
                events.forEach((event: any) => {
                    const hour = new Date(event.created_at).getHours();
                    const key = `${hour}:00`;

                    if (!hourlyData[key]) {
                        hourlyData[key] = { time: key, chats: 0, hits: 0 };
                    }

                    if (event.event_type === 'chat') hourlyData[key].chats++;
                    if (event.event_type === 'api_hit') hourlyData[key].hits++;
                });

                setUsageData(Object.values(hourlyData).slice(-12));


                // Get token usage by agent
                const agentTokens: any = {};
                const existingAgentIds = new Set(agentsRes.data.map((a: any) => a.id));

                events.forEach((event: any) => {
                    if (event.event_type === 'chat' && event.event_data?.tokens) {
                        const agentId = event.agent_id;

                        // Only include token data for agents that actually exist
                        if (agentId && existingAgentIds.has(agentId)) {
                            if (!agentTokens[agentId]) {
                                // Find the actual agent name
                                const agent = agentsRes.data.find((a: any) => a.id === agentId);
                                agentTokens[agentId] = {
                                    name: agent?.name || `Agent ${agentId.slice(0, 6)}`,
                                    tokens: 0
                                };
                            }
                            agentTokens[agentId].tokens += event.event_data.tokens.total_tokens || 0;
                        }
                    }
                });

                setTokenData(Object.values(agentTokens).slice(0, 5));

            } catch (error) {
                console.error("Failed to fetch stats", error);
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
        <div className={`backdrop-blur-sm border rounded-2xl p-6 transition-all duration-200 group ${isDark ? "bg-nvidia-dark/50 border-white/10 hover:border-nvidia-green/30" : "bg-white border-gray-200 hover:border-nvidia-green shadow-sm"}`}>
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl transition-colors ${isDark ? "bg-white/5 group-hover:bg-nvidia-green/10" : "bg-gray-100 group-hover:bg-nvidia-green/10"}`}>
                    <Icon className={`w-6 h-6 transition-colors ${isDark ? "text-gray-400 group-hover:text-nvidia-green" : "text-gray-600 group-hover:text-nvidia-green"}`} />
                </div>
                {trend && (
                    <div className="flex items-center text-nvidia-green text-sm font-medium bg-nvidia-green/10 px-2 py-1 rounded-lg">
                        <ArrowUpRight className="w-3 h-3 mr-1" />
                        {trend}
                    </div>
                )}
            </div>
            <h3 className={`text-sm font-medium mb-1 ${isDark ? "text-gray-400" : "text-gray-600"}`}>{title}</h3>
            <p className={`text-3xl font-bold tracking-tight ${isDark ? "text-white" : "text-gray-900"}`}>{value}</p>
        </div>
    ));
    StatCard.displayName = "StatCard";

    const CustomTooltip = memo(({ active, payload, label, isDark }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className={`border rounded-lg p-3 backdrop-blur-sm ${isDark ? "bg-nvidia-dark/95 border-nvidia-green/30" : "bg-white border-gray-200 shadow-lg"}`}>
                    <p className={`text-sm mb-2 ${isDark ? "text-gray-400" : "text-gray-600"}`}>{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} className="text-sm" style={{ color: entry.color }}>
                            {entry.name}: {entry.value}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    });
    CustomTooltip.displayName = "CustomTooltip";

    return (
        <div className="space-y-8">
            <div>
                <h1 className={`text-3xl font-bold tracking-tight mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>Dashboard Overview</h1>
                <p className={isDark ? "text-gray-400" : "text-gray-600"}>Real-time analytics and system status.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Active Agents" value={stats.agents} icon={Users} isDark={isDark} />
                <StatCard title="Knowledge Bases" value={stats.kbs} icon={Database} isDark={isDark} />
                <StatCard title="LLM Models" value={stats.llms} icon={Cpu} isDark={isDark} />
                <StatCard title="API Calls (24h)" value={stats.apiCalls.toLocaleString()} icon={Activity} isDark={isDark} />
            </div>

            {/* Token Usage Stats */}
            {analyticsData && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className={`border rounded-2xl p-6 ${isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                        <div className="flex items-center gap-3 mb-2">
                            <MessageSquare className="w-5 h-5 text-nvidia-green" />
                            <h3 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Total Chats</h3>
                        </div>
                        <p className={`text-3xl font-bold ${isDark ? "text-white" : "text-gray-900"}`}>{analyticsData.token_usage?.total_requests || 0}</p>
                        <p className={`text-sm mt-1 ${isDark ? "text-gray-400" : "text-gray-600"}`}>Last 24 hours</p>
                    </div>
                    <div className={`border rounded-2xl p-6 ${isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                        <div className="flex items-center gap-3 mb-2">
                            <TrendingUp className="w-5 h-5 text-blue-400" />
                            <h3 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Tokens Used</h3>
                        </div>
                        <p className={`text-3xl font-bold ${isDark ? "text-white" : "text-gray-900"}`}>{(analyticsData.token_usage?.total_tokens || 0).toLocaleString()}</p>
                        <p className={`text-sm mt-1 ${isDark ? "text-gray-400" : "text-gray-600"}`}>Avg: {analyticsData.token_usage?.avg_tokens_per_request || 0}/chat</p>
                    </div>
                    <div className={`border rounded-2xl p-6 ${isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                        <div className="flex items-center gap-3 mb-2">
                            <Activity className="w-5 h-5 text-purple-400" />
                            <h3 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Unique Users</h3>
                        </div>
                        <p className={`text-3xl font-bold ${isDark ? "text-white" : "text-gray-900"}`}>{analyticsData.api_hits?.unique_users || 0}</p>
                        <p className={`text-sm mt-1 ${isDark ? "text-gray-400" : "text-gray-600"}`}>Active in 24h</p>
                    </div>
                </div>
            )}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Usage Analytics Chart */}
                <div className={`border rounded-2xl p-6 ${isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                    <h3 className={`font-semibold mb-4 flex items-center gap-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                        <Activity className="w-5 h-5 text-nvidia-green" />
                        Usage Analytics (Last 12 Hours)
                    </h3>
                    {usageData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <AreaChart data={usageData}>
                                <defs>
                                    <linearGradient id="colorChats" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#76b900" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#76b900" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorHits" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#333" : "#e5e7eb"} />
                                <XAxis dataKey="time" stroke={isDark ? "#888" : "#6b7280"} />
                                <YAxis stroke={isDark ? "#888" : "#6b7280"} />
                                <Tooltip content={<CustomTooltip isDark={isDark} />} />
                                <Legend />
                                <Area type="monotone" dataKey="chats" stroke="#76b900" fillOpacity={1} fill="url(#colorChats)" name="Chats" />
                                <Area type="monotone" dataKey="hits" stroke="#60a5fa" fillOpacity={1} fill="url(#colorHits)" name="API Hits" />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className={`h-[280px] flex items-center justify-center ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                            No data available
                        </div>
                    )}
                </div>

                {/* Agent Performance Chart */}
                <div className={`border rounded-2xl p-6 ${isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-white border-gray-200 shadow-sm"}`}>
                    <h3 className={`font-semibold mb-4 flex items-center gap-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                        Agent Token Usage (Top 5)
                    </h3>
                    {tokenData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={tokenData}>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#333" : "#e5e7eb"} />
                                <XAxis dataKey="name" stroke={isDark ? "#888" : "#6b7280"} />
                                <YAxis stroke={isDark ? "#888" : "#6b7280"} />
                                <Tooltip content={<CustomTooltip isDark={isDark} />} />
                                <Bar dataKey="tokens" fill="#76b900" name="Tokens" radius={[8, 8, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className={`h-[280px] flex items-center justify-center ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                            No agent data available
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
