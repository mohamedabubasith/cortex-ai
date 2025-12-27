"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, Settings, Trash2, Loader2, Bot } from "lucide-react";
import api from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

import Dialog from "@/components/ui/Dialog";

interface Agent {
    id: string;
    name: string;
    description: string;
    updated_at: string;
    is_public: boolean;
}

export default function AgentsPage() {
    const router = useRouter();
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [agentToDelete, setAgentToDelete] = useState<string | null>(null);

    useEffect(() => {
        fetchAgents();
    }, []);

    const fetchAgents = async () => {
        setLoading(true);
        try {
            const response = await api.get("/agents/");
            setAgents(response.data);
        } catch (error) {
            console.error("Failed to fetch agents", error);
        } finally {
            setLoading(false);
        }
    };

    const confirmDeleteAgent = (id: string) => {
        setAgentToDelete(id);
        setDeleteDialogOpen(true);
    };

    const handleDeleteAgent = async () => {
        if (!agentToDelete) return;
        try {
            await api.delete(`/agents/${agentToDelete}`);
            fetchAgents();
        } catch (error) {
            console.error("Failed to delete agent", error);
        } finally {
            setDeleteDialogOpen(false);
            setAgentToDelete(null);
        }
    };

    return (
        <div className="space-y-8 relative">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>Agents</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>Create and manage your AI agents.</p>
                </div>
                <Link
                    href="/agent/new"
                    className="flex items-center justify-center w-full md:w-auto px-6 py-3 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(118,185,0,0.3)]"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    New Agent
                </Link>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-12 h-12 text-nvidia-green animate-spin" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {agents.map((agent) => (
                        <div
                            key={agent.id}
                            onClick={() => router.push(`/agent/${agent.id}`)}
                            className={cn("group backdrop-blur-sm rounded-xl p-6 border transition-all duration-300 hover:shadow-[0_0_30px_rgba(118,185,0,0.1)] hover:-translate-y-1 cursor-pointer", isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm")}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <h3 className={cn("text-xl font-bold group-hover:text-nvidia-green transition-colors", isDark ? "text-white" : "text-gray-900")}>
                                    {agent.name}
                                </h3>
                                <span className="px-3 py-1 text-xs font-bold rounded-full border bg-nvidia-green/10 text-nvidia-green border-nvidia-green/20">
                                    AGENT
                                </span>
                            </div>
                            <p className={cn("mb-8 h-12 line-clamp-2 text-sm leading-relaxed", isDark ? "text-gray-400" : "text-gray-600")}>
                                {agent.description}
                            </p>
                            <div className="flex space-x-3">
                                <Link
                                    href={`/agent/${agent.id}`}
                                    onClick={(e) => e.stopPropagation()}
                                    className={cn("flex-1 flex items-center justify-center px-4 py-2 border rounded-lg text-sm font-medium transition-colors", isDark ? "border-gray-700 text-gray-300 hover:bg-white/5 hover:text-white" : "border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900")}
                                >
                                    <Settings className="w-4 h-4 mr-2" />
                                    Configure
                                </Link>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        confirmDeleteAgent(agent.id);
                                    }}
                                    className={cn("px-3 py-2 border rounded-lg transition-colors", isDark ? "border-gray-700 text-gray-400 hover:bg-red-900/20 hover:text-red-400 hover:border-red-900/30" : "border-gray-200 text-gray-400 hover:bg-red-50 hover:text-red-600 hover:border-red-100")}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                    {agents.length === 0 && (
                        <div className={cn("col-span-full flex flex-col items-center justify-center py-20 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                            <Bot className="w-16 h-16 text-gray-600 mb-4" />
                            <h3 className={cn("text-xl font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>No Agents Found</h3>
                            <p className={isDark ? "text-gray-400 mb-6" : "text-gray-600 mb-6"}>Get started by creating your first AI agent.</p>
                            <Link
                                href="/agent/new"
                                className="flex items-center px-6 py-3 bg-white/10 text-white font-bold rounded-lg hover:bg-white/20 transition-all"
                            >
                                <Plus className="w-5 h-5 mr-2" />
                                Create Agent
                            </Link>
                        </div>
                    )}
                </div>
            )}

            <Dialog
                isOpen={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
                title="Delete Agent"
                description="Are you sure you want to delete this agent? This action cannot be undone."
                buttons={[
                    { label: "Cancel", onClick: () => setDeleteDialogOpen(false), variant: "outline" },
                    { label: "Delete", onClick: handleDeleteAgent, variant: "danger" }
                ]}
            />
        </div>
    );
}
