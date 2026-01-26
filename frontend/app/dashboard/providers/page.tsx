"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Cpu, Trash2, Loader2, Plus, Edit2, AlertCircle } from "lucide-react";
import api from "@/lib/api";
import { Can } from "@/contexts/AuthContext";
import { useToast } from "@/components/ui/Toast";
import Dialog from "@/components/ui/Dialog";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import CustomDropdown from "@/components/ui/CustomDropdown";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Skeleton } from "@/components/ui/skeleton";

interface LLMConfig {
    id: string;
    name: string;
    provider: string;
    model: string;
    api_key?: string;
    base_url?: string;
}

const PROVIDER_OPTIONS = [
    { id: "openai", name: "OpenAI" },
    { id: "anthropic", name: "Anthropic" },
    { id: "azure", name: "Azure OpenAI" },
    { id: "ollama", name: "Ollama (Local)" }
];

export default function ProvidersPage() {
    const { toast } = useToast();
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [loading, setLoading] = useState(true);

    // --- LLM State ---
    const [llmConfigs, setLlmConfigs] = useState<LLMConfig[]>([]);
    const [isLlmModalOpen, setIsLlmModalOpen] = useState(false);
    const [creatingLlm, setCreatingLlm] = useState(false);
    const [testingLlm, setTestingLlm] = useState(false);
    const [editingLlmId, setEditingLlmId] = useState<string | null>(null);
    const [deleteLlmDialogOpen, setDeleteLlmDialogOpen] = useState(false);
    const [llmToDelete, setLlmToDelete] = useState<string | null>(null);
    const [newLlmConfig, setNewLlmConfig] = useState<Partial<LLMConfig>>({
        name: "",
        provider: "openai",
        model: "gpt-4o",
        api_key: "",
        base_url: ""
    });

    useEffect(() => {
        fetchResources();
    }, []);

    const fetchResources = async () => {
        setLoading(true);
        try {
            const llmRes = await api.get("/llm");
            setLlmConfigs(llmRes.data);
        } catch (error) {
            console.error("Failed to fetch resources", error);
            toast("Failed to load providers", "error");
        } finally {
            setLoading(false);
        }
    };

    // --- LLM Handlers ---

    const handleCreateOrUpdateLLM = async () => {
        setCreatingLlm(true);
        try {
            if (editingLlmId) {
                await api.put(`/llm/${editingLlmId}`, newLlmConfig);
                toast("Configuration updated successfully", "success");
            } else {
                await api.post("/llm", newLlmConfig);
                toast("Configuration created successfully", "success");
            }
            setIsLlmModalOpen(false);
            resetLlmForm();
            fetchResources();
        } catch (error) {
            console.error("Failed to save LLM config", error);
            toast("Failed to save configuration.", "error");
        } finally {
            setCreatingLlm(false);
        }
    };

    const resetLlmForm = () => {
        setNewLlmConfig({ name: "", provider: "openai", model: "gpt-4o", api_key: "", base_url: "" });
        setEditingLlmId(null);
    };

    const handleEditLLM = (config: LLMConfig) => {
        setNewLlmConfig({
            name: config.name,
            provider: config.provider,
            model: config.model,
            api_key: config.api_key || "",
            base_url: config.base_url || ""
        });
        setEditingLlmId(config.id);
        setIsLlmModalOpen(true);
    };

    const handleTestLlmConnection = async () => {
        if (!newLlmConfig.api_key) {
            toast("Please enter an API Key to test.", "warning");
            return;
        }
        setTestingLlm(true);
        try {
            await api.post("/llm/test", {
                provider: newLlmConfig.provider,
                model: newLlmConfig.model,
                api_key: newLlmConfig.api_key,
                base_url: newLlmConfig.base_url
            });
            toast("Connection successful!", "success");
        } catch (error: any) {
            console.error("Test connection failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Connection failed.";
            toast(errorMessage, "error");
        } finally {
            setTestingLlm(false);
        }
    };

    const confirmDeleteLLM = (id: string) => {
        setLlmToDelete(id);
        setDeleteLlmDialogOpen(true);
    };

    const handleDeleteLLM = async () => {
        if (!llmToDelete) return;
        try {
            await api.delete(`/llm/${llmToDelete}`);
            toast("Configuration deleted successfully", "success");
            fetchResources();
        } catch (error) {
            toast("Failed to delete configuration", "error");
        } finally {
            setDeleteLlmDialogOpen(false);
            setLlmToDelete(null);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-2xl md:text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>Model Providers</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>Manage your AI capability providers (LLMs).</p>
                </div>
                <Can permission="llm.manage">
                    <button
                        onClick={() => {
                            resetLlmForm();
                            setIsLlmModalOpen(true);
                        }}
                        className="flex items-center justify-center w-full md:w-auto px-6 py-3 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(118,185,0,0.3)]"
                    >
                        <Plus className="w-5 h-5 mr-2" />
                        Add Model
                    </button>
                </Can>
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[...Array(3)].map((_, i) => (
                            <Skeleton key={i} className="h-48 rounded-xl" />
                        ))}
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
                                            <Can permission="llm.manage">
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
                                            </Can>
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
                                <h3 className={cn("text-xl font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>No Model Providers</h3>
                                <p className={isDark ? "text-gray-400" : "text-gray-600"}>Add your first LLM provider configuration.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* LLM Dialog */}
            <Dialog
                isOpen={isLlmModalOpen}
                onClose={() => setIsLlmModalOpen(false)}
                title={editingLlmId ? "Edit Configuration" : "Add LLM Configuration"}
                buttons={[
                    { label: "Cancel", onClick: () => setIsLlmModalOpen(false), variant: "outline" },
                    { label: "Test Connection", onClick: handleTestLlmConnection, variant: "secondary", isLoading: testingLlm },
                    { label: creatingLlm ? "Saving..." : "Save Configuration", onClick: handleCreateOrUpdateLLM, variant: "primary", isLoading: creatingLlm }
                ]}
            >
                <div className="space-y-4">
                    <Input
                        label="Name"
                        placeholder="My GPT-4 Config"
                        value={newLlmConfig.name}
                        onChange={e => setNewLlmConfig({ ...newLlmConfig, name: e.target.value })}
                    />

                    <div>
                        <Label>Provider</Label>
                        <CustomDropdown
                            options={PROVIDER_OPTIONS}
                            value={PROVIDER_OPTIONS.find(opt => opt.id === newLlmConfig.provider) || PROVIDER_OPTIONS[0]}
                            onChange={(option) => setNewLlmConfig({ ...newLlmConfig, provider: option.id })}
                            getLabel={(option) => option.name}
                            getKey={(option) => option.id}
                            placeholder="Select Provider"
                        />
                    </div>

                    <Input
                        label="Model Name"
                        placeholder="gpt-4o"
                        value={newLlmConfig.model}
                        onChange={e => setNewLlmConfig({ ...newLlmConfig, model: e.target.value })}
                    />

                    <Input
                        label="API Key"
                        type="password"
                        placeholder="sk-..."
                        value={newLlmConfig.api_key}
                        onChange={e => setNewLlmConfig({ ...newLlmConfig, api_key: e.target.value })}
                    />

                    <Input
                        label="API Base URL (Optional)"
                        placeholder="https://api.openai.com/v1"
                        value={newLlmConfig.base_url}
                        onChange={e => setNewLlmConfig({ ...newLlmConfig, base_url: e.target.value })}
                    />
                </div>
            </Dialog>

            {/* Delete LLM Dialog */}
            <Dialog
                isOpen={deleteLlmDialogOpen}
                onClose={() => setDeleteLlmDialogOpen(false)}
                title="Delete Configuration"
                description="Are you sure you want to delete this configuration? This action cannot be undone."
                buttons={[
                    { label: "Cancel", onClick: () => setDeleteLlmDialogOpen(false), variant: "outline" },
                    { label: "Delete", onClick: handleDeleteLLM, variant: "danger" }
                ]}
            />
        </div>
    );
}
