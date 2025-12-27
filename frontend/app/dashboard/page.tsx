"use client";

import { useEffect, useState } from "react";
import { Users, Database, Cpu, Activity, ArrowUpRight, TrendingUp, MessageSquare } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Area, AreaChart } from "recharts";
import api from "@/lib/api";

export default function DashboardPage() {
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

    const StatCard = ({ title, value, icon: Icon, trend }: any) => (
        <div className="bg-nvidia-dark/50 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:border-nvidia-green/30 transition-all duration-300 group">
            <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-white/5 rounded-xl group-hover:bg-nvidia-green/10 transition-colors">
                    <Icon className="w-6 h-6 text-gray-400 group-hover:text-nvidia-green transition-colors" />
                </div>
                {trend && (
                    <div className="flex items-center text-nvidia-green text-sm font-medium bg-nvidia-green/10 px-2 py-1 rounded-lg">
                        <ArrowUpRight className="w-3 h-3 mr-1" />
                        {trend}
                    </div>
                )}
            </div>
            <h3 className="text-gray-400 text-sm font-medium mb-1">{title}</h3>
            <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
        </div>
    );

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-nvidia-dark/95 border border-nvidia-green/30 rounded-lg p-3 backdrop-blur-sm">
                    <p className="text-gray-400 text-sm mb-2">{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} className="text-sm" style={{ color: entry.color }}>
                            {entry.name}: {entry.value}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-white tracking-tight mb-2">Dashboard Overview</h1>
                <p className="text-gray-400">Real-time analytics and system status.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Active Agents" value={stats.agents} icon={Users} />
                <StatCard title="Knowledge Bases" value={stats.kbs} icon={Database} />
                <StatCard title="LLM Models" value={stats.llms} icon={Cpu} />
                <StatCard title="API Calls (24h)" value={stats.apiCalls.toLocaleString()} icon={Activity} />
            </div>

            {/* Token Usage Stats */}
            {analyticsData && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-nvidia-dark/30 border border-white/10 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <MessageSquare className="w-5 h-5 text-nvidia-green" />
                            <h3 className="text-white font-semibold">Total Chats</h3>
                        </div>
                        <p className="text-3xl font-bold text-white">{analyticsData.token_usage?.total_requests || 0}</p>
                        <p className="text-gray-400 text-sm mt-1">Last 24 hours</p>
                    </div>
                    <div className="bg-nvidia-dark/30 border border-white/10 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <TrendingUp className="w-5 h-5 text-blue-400" />
                            <h3 className="text-white font-semibold">Tokens Used</h3>
                        </div>
                        <p className="text-3xl font-bold text-white">{(analyticsData.token_usage?.total_tokens || 0).toLocaleString()}</p>
                        <p className="text-gray-400 text-sm mt-1">Avg: {analyticsData.token_usage?.avg_tokens_per_request || 0}/chat</p>
                    </div>
                    <div className="bg-nvidia-dark/30 border border-white/10 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <Activity className="w-5 h-5 text-purple-400" />
                            <h3 className="text-white font-semibold">Unique Users</h3>
                        </div>
                        <p className="text-3xl font-bold text-white">{analyticsData.api_hits?.unique_users || 0}</p>
                        <p className="text-gray-400 text-sm mt-1">Active in 24h</p>
                    </div>
                </div>
            )}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Usage Analytics Chart */}
                <div className="bg-nvidia-dark/30 border border-white/10 rounded-2xl p-6">
                    <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
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
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis dataKey="time" stroke="#888" />
                                <YAxis stroke="#888" />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Area type="monotone" dataKey="chats" stroke="#76b900" fillOpacity={1} fill="url(#colorChats)" name="Chats" />
                                <Area type="monotone" dataKey="hits" stroke="#60a5fa" fillOpacity={1} fill="url(#colorHits)" name="API Hits" />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[280px] flex items-center justify-center text-gray-500">
                            No data available
                        </div>
                    )}
                </div>

                {/* Agent Performance Chart */}
                <div className="bg-nvidia-dark/30 border border-white/10 rounded-2xl p-6">
                    <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                        Agent Token Usage (Top 5)
                    </h3>
                    {tokenData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={tokenData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis dataKey="name" stroke="#888" />
                                <YAxis stroke="#888" />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="tokens" fill="#76b900" name="Tokens" radius={[8, 8, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[280px] flex items-center justify-center text-gray-500">
                            No agent data available
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
