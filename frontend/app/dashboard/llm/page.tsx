"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Cpu, Trash2, Loader2, Plus, Save, X, Edit2 } from "lucide-react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import Dialog from "@/components/ui/Dialog";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import CustomDropdown from "@/components/ui/CustomDropdown";

interface LLMConfig {
    id: string;
    name: string;
    provider: string;
    model: string;
    api_key?: string;
    base_url?: string;
}

export default function LLMPage() {
    const { toast } = useToast();
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [llmConfigs, setLlmConfigs] = useState<LLMConfig[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [creating, setCreating] = useState(false);
    const [testing, setTesting] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);

    // Delete State
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [configToDelete, setConfigToDelete] = useState<string | null>(null);

    // New Config Form State
    const [newConfig, setNewConfig] = useState<Partial<LLMConfig>>({
        name: "",
        provider: "openai",
        model: "gpt-4o",
        api_key: "",
        base_url: ""
    });

    useEffect(() => {
        fetchLLMs();
    }, []);

    const fetchLLMs = async () => {
        setLoading(true);
        try {
            const response = await api.get("/llm");
            setLlmConfigs(response.data);
        } catch (error) {
            console.error("Failed to fetch LLM configs", error);
            toast("Failed to fetch LLM configurations", "error");
        } finally {
            setLoading(false);
        }
    };

    const handleCreateOrUpdateLLM = async () => {
        setCreating(true);
        try {
            if (editingId) {
                await api.put(`/llm/${editingId}`, newConfig);
                toast("Configuration updated successfully", "success");
            } else {
                await api.post("/llm", newConfig);
                toast("Configuration created successfully", "success");
            }
            setIsModalOpen(false);
            resetForm();
            fetchLLMs();
        } catch (error) {
            console.error("Failed to save LLM config", error);
            toast("Failed to save configuration. Please check your inputs.", "error");
        } finally {
            setCreating(false);
        }
    };

    const resetForm = () => {
        setNewConfig({ name: "", provider: "openai", model: "gpt-4o", api_key: "", base_url: "" });
        setEditingId(null);
    };

    const handleEditLLM = (config: LLMConfig) => {
        setNewConfig({
            name: config.name,
            provider: config.provider,
            model: config.model,
            api_key: config.api_key || "",
            base_url: config.base_url || ""
        });
        setEditingId(config.id);
        setIsModalOpen(true);
    };

    const handleTestConnection = async () => {
        if (!newConfig.api_key) {
            toast("Please enter an API Key to test.", "warning");
            return;
        }
        setTesting(true);
        try {
            await api.post("/llm/test", {
                provider: newConfig.provider,
                model: newConfig.model,
                api_key: newConfig.api_key,
                base_url: newConfig.base_url
            });
            toast("Connection successful!", "success");
        } catch (error: any) {
            console.error("Test connection failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Connection failed. Please check your credentials.";
            toast(errorMessage, "error");
        } finally {
            setTesting(false);
        }
    };

    const confirmDeleteLLM = (id: string) => {
        setConfigToDelete(id);
        setDeleteDialogOpen(true);
    };

    const handleDeleteLLM = async () => {
        if (!configToDelete) return;
        try {
            await api.delete(`/llm/${configToDelete}`);
            toast("Configuration deleted successfully", "success");
            fetchLLMs();
        } catch (error) {
            console.error("Failed to delete LLM config", error);
            toast("Failed to delete configuration", "error");
        } finally {
            setDeleteDialogOpen(false);
            setConfigToDelete(null);
        }
    };

    return (
        <div className="space-y-8 relative">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-2xl md:text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>LLM Configurations</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>Manage your Large Language Model connections.</p>
                </div>
                <button
                    onClick={() => { resetForm(); setIsModalOpen(true); }}
                    className="flex items-center justify-center w-full md:w-auto px-6 py-3 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(118,185,0,0.3)]"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    New Configuration
                </button>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-12 h-12 text-nvidia-green animate-spin" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {llmConfigs.map((config) => (
                        <div key={config.id} className={cn("backdrop-blur-sm border rounded-xl p-6 transition-all group flex flex-col justify-between h-full min-h-[180px]", isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm")}>
                            <div>
                                <div className="flex justify-between items-start mb-4">
                                    <div className={cn("p-3 rounded-lg transition-colors", isDark ? "bg-white/5 group-hover:bg-nvidia-green/10" : "bg-gray-100 group-hover:bg-nvidia-green/10")}>
                                        <Cpu className={cn("w-6 h-6 transition-colors", isDark ? "text-gray-400 group-hover:text-nvidia-green" : "text-gray-600 group-hover:text-nvidia-green")} />
                                    </div>
                                    <div className="flex space-x-2">
                                        <button
                                            onClick={() => handleEditLLM(config)}
                                            className="text-gray-500 hover:text-white transition-colors p-1 rounded-md hover:bg-white/10"
                                            title="Edit"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => confirmDeleteLLM(config.id)}
                                            className="text-gray-500 hover:text-red-500 transition-colors p-1 rounded-md hover:bg-red-500/10"
                                            title="Delete"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                                <h3 className={cn("text-base md:text-lg font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>{config.name}</h3>
                                <div className="flex flex-wrap gap-2">
                                    <span className={cn("text-xs px-2 py-1 rounded font-mono border", isDark ? "text-gray-300 bg-white/10 border-white/5" : "text-gray-600 bg-gray-100 border-gray-200")}>
                                        {config.model}
                                    </span>
                                </div>
                            </div>
                            {config.base_url && (
                                <div className={cn("mt-4 pt-4 border-t", isDark ? "border-white/5" : "border-gray-100")}>
                                    <p className="text-xs text-gray-500 truncate" title={config.base_url}>
                                        {config.base_url}
                                    </p>
                                </div>
                            )}
                        </div>
                    ))}
                    {llmConfigs.length === 0 && (
                        <div className={cn("col-span-full flex flex-col items-center justify-center py-20 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                            <Cpu className="w-16 h-16 text-gray-600 mb-4" />
                            <h3 className={cn("text-xl font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>No LLM Configs</h3>
                            <p className={isDark ? "text-gray-400" : "text-gray-600"}>Add your first LLM provider configuration.</p>
                        </div>
                    )}
                </div>
            )}

            {/* Create/Edit Dialog */}
            <Dialog
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingId ? "Edit Configuration" : "Add LLM Configuration"}
                buttons={[
                    { label: "Cancel", onClick: () => setIsModalOpen(false), variant: "outline" },
                    { label: "Test Connection", onClick: handleTestConnection, variant: "secondary", isLoading: testing },
                    { label: creating ? "Saving..." : "Save Configuration", onClick: handleCreateOrUpdateLLM, variant: "primary", isLoading: creating }
                ]}
            >
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                        <input
                            type="text"
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                            placeholder="My GPT-4 Config"
                            value={newConfig.name}
                            onChange={e => setNewConfig({ ...newConfig, name: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Provider</label>
                        <CustomDropdown
                            options={[
                                { id: "openai", name: "OpenAI" },
                                { id: "anthropic", name: "Anthropic" },
                                { id: "azure", name: "Azure OpenAI" },
                                { id: "ollama", name: "Ollama (Local)" }
                            ]}
                            value={{ id: newConfig.provider || "openai", name: "" }} // Name is not used for value matching in this simple case, but needed for type
                            onChange={(option) => setNewConfig({ ...newConfig, provider: option.id })}
                            getLabel={(option) => option.name}
                            getKey={(option) => option.id}
                            placeholder="Select Provider"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Model Name</label>
                        <input
                            type="text"
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                            placeholder="gpt-4o"
                            value={newConfig.model}
                            onChange={e => setNewConfig({ ...newConfig, model: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">API Key</label>
                        <input
                            type="password"
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                            placeholder="sk-..."
                            value={newConfig.api_key}
                            onChange={e => setNewConfig({ ...newConfig, api_key: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">API Base URL (Optional)</label>
                        <input
                            type="text"
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                            placeholder="https://api.openai.com/v1"
                            value={newConfig.base_url}
                            onChange={e => setNewConfig({ ...newConfig, base_url: e.target.value })}
                        />
                    </div>
                </div>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog
                isOpen={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
                title="Delete Configuration"
                description="Are you sure you want to delete this LLM configuration? This action cannot be undone."
                buttons={[
                    { label: "Cancel", onClick: () => setDeleteDialogOpen(false), variant: "outline" },
                    { label: "Delete", onClick: handleDeleteLLM, variant: "danger" }
                ]}
            />
        </div>
    );
}
