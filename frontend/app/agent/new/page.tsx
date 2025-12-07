"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Bot, Loader2 } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@/lib/utils";

export default function NewAgentPage() {
    const router = useRouter();
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
        <div className="min-h-screen bg-black text-white flex flex-col">
            <nav className="border-b border-white/10 bg-nvidia-dark/50 backdrop-blur-md">
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

            <main className="flex-1 flex items-center justify-center p-4">
                <div className="w-full max-w-md space-y-8">
                    <div className="text-center">
                        <div className="mx-auto h-12 w-12 bg-nvidia-green/10 rounded-xl flex items-center justify-center mb-4">
                            <Bot className="h-6 w-6 text-nvidia-green" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white">Create New Agent</h2>
                        <p className="mt-2 text-sm text-gray-400">
                            Give your agent a name and description to get started.
                        </p>
                    </div>

                    <div className="bg-nvidia-dark/50 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-xl">
                        {error && (
                            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/50 text-red-200 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        <form className="space-y-6" onSubmit={handleSubmit}>
                            <div>
                                <label htmlFor="name" className="block text-sm font-medium text-gray-300">
                                    Agent Name
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="text"
                                        name="name"
                                        id="name"
                                        required
                                        className="block w-full px-4 py-3 bg-black/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-nvidia-green focus:border-transparent text-white placeholder-gray-500 transition-all"
                                        placeholder="e.g., Customer Support Bot"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label htmlFor="description" className="block text-sm font-medium text-gray-300">
                                    Description
                                </label>
                                <div className="mt-1">
                                    <textarea
                                        id="description"
                                        name="description"
                                        rows={3}
                                        className="block w-full px-4 py-3 bg-black/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-nvidia-green focus:border-transparent text-white placeholder-gray-500 transition-all"
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
