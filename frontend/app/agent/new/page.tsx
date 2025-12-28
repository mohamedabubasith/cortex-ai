"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Bot, Loader2 } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

export default function NewAgentPage() {
    const router = useRouter();
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [formData, setFormData] = useState({
        name: "",
        description: "",
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const response = await api.post("/agents/", {
                name: formData.name,
                description: formData.description,
                is_public: true
            });

            // Redirect to Agent Configuration
            router.push(`/agent/${response.data.id}`);
        } catch (err) {
            console.error(err);
            setError("Failed to create agent. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={cn("h-[100dvh] flex flex-col transition-colors duration-300 overflow-hidden", isDark ? "bg-black text-white" : "bg-gray-50 text-gray-900")}>
            <nav className={cn("border-b backdrop-blur-md shrink-0", isDark ? "border-white/10 bg-nvidia-dark/50" : "border-gray-200 bg-white/80")}>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <Link
                                href="/dashboard/agents"
                                className="flex items-center text-gray-400 hover:text-white transition-colors"
                            >
                                <ArrowLeft className="h-5 w-5 mr-2" />
                                Back to Agents
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="flex-1 flex items-center justify-center p-4 overflow-y-auto">
                <div className="w-full max-w-md space-y-8">
                    <div className="text-center">
                        <div className={cn("mx-auto h-12 w-12 rounded-xl flex items-center justify-center mb-4", isDark ? "bg-nvidia-green/10" : "bg-nvidia-green/10")}>
                            <Bot className="h-6 w-6 text-nvidia-green" />
                        </div>
                        <h2 className={cn("text-3xl font-bold tracking-tight", isDark ? "text-white" : "text-gray-900")}>Create New Agent</h2>
                        <p className="mt-2 text-sm text-gray-400">
                            Give your agent a name and description to get started.
                        </p>
                    </div>

                    <div className={cn("backdrop-blur-md border rounded-2xl p-8 shadow-xl", isDark ? "bg-nvidia-dark/50 border-white/10" : "bg-white border-gray-200")}>
                        {error && (
                            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/50 text-red-200 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        <form className="space-y-6" onSubmit={handleSubmit}>
                            <div>
                                <label htmlFor="name" className={cn("block text-sm font-medium", isDark ? "text-gray-300" : "text-gray-700")}>
                                    Agent Name
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="text"
                                        name="name"
                                        id="name"
                                        required
                                        className={cn("block w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-nvidia-green focus:border-transparent transition-all text-base md:text-sm", isDark ? "bg-black/50 border-gray-700 text-white placeholder-gray-500" : "bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400")}
                                        placeholder="e.g., Customer Support Bot"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label htmlFor="description" className={cn("block text-sm font-medium", isDark ? "text-gray-300" : "text-gray-700")}>
                                    Description
                                </label>
                                <div className="mt-1">
                                    <textarea
                                        id="description"
                                        name="description"
                                        rows={3}
                                        className={cn("block w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-nvidia-green focus:border-transparent transition-all text-base md:text-sm", isDark ? "bg-black/50 border-gray-700 text-white placeholder-gray-500" : "bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400")}
                                        placeholder="What does this agent do?"
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-black bg-nvidia-green hover:bg-[#8CD600] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-nvidia-green disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02]"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    "Create Agent"
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    );
}
