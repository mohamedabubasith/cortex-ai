"use client";

export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Cpu, Trash2, Loader2, Plus, Edit2, CheckCircle2 } from "lucide-react";
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
    context_window?: number | null;
}

interface ModelOption {
    id: string;
    name: string;
}

const PROVIDER_OPTIONS = [
    { id: "openai",    name: "OpenAI" },
    { id: "anthropic", name: "Anthropic" },
    { id: "azure",     name: "Azure OpenAI" },
    { id: "ollama",    name: "Ollama (Local)" },
];

const BASE_URL_HINTS: Record<string, string> = {
    openai:    "https://api.openai.com/v1",
    anthropic: "",
    azure:     "https://<resource>.openai.azure.com",
    ollama:    "http://localhost:11434/v1",
};

export default function ProvidersPage() {
    const { toast } = useToast();
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [loading, setLoading] = useState(true);
    const [llmConfigs, setLlmConfigs] = useState<LLMConfig[]>([]);

    const [isLlmModalOpen, setIsLlmModalOpen] = useState(false);
    const [creatingLlm, setCreatingLlm] = useState(false);
    const [editingLlmId, setEditingLlmId] = useState<string | null>(null);
    const [newLlmConfig, setNewLlmConfig] = useState<Partial<LLMConfig>>({
        name: "", provider: "openai", model: "", api_key: "", base_url: "", context_window: null
    });

    const [fetchingModels, setFetchingModels] = useState(false);
    const [fetchedModels, setFetchedModels] = useState<ModelOption[]>([]);
    const [connected, setConnected] = useState(false);

    const [deleteLlmDialogOpen, setDeleteLlmDialogOpen] = useState(false);
    const [llmToDelete, setLlmToDelete] = useState<string | null>(null);

    useEffect(() => { fetchResources(); }, []);

    const fetchResources = async () => {
        setLoading(true);
        try {
            const res = await api.get("/llm");
            setLlmConfigs(res.data);
        } catch {
            toast("Failed to load providers", "error");
        } finally {
            setLoading(false);
        }
    };

    const resetForm = () => {
        setNewLlmConfig({ name: "", provider: "openai", model: "", api_key: "", base_url: "", context_window: null });
        setEditingLlmId(null);
        setFetchedModels([]);
        setConnected(false);
    };

    const handleProviderChange = (providerId: string) => {
        setNewLlmConfig(prev => ({ ...prev, provider: providerId, model: "" }));
        setFetchedModels([]);
        setConnected(false);
    };

    const handleFetchModels = async () => {
        if (!newLlmConfig.api_key && newLlmConfig.provider !== "ollama") {
            toast("Enter an API key first", "warning");
            return;
        }
        setFetchingModels(true);
        setConnected(false);
        try {
            const res = await api.post("/llm/models", {
                provider: newLlmConfig.provider,
                api_key: newLlmConfig.api_key || "ollama",
                base_url: newLlmConfig.base_url || undefined,
            });
            const models: ModelOption[] = res.data.models;
            setFetchedModels(models);
            setConnected(true);
            if (!newLlmConfig.model && models.length > 0) {
                setNewLlmConfig(prev => ({ ...prev, model: models[0].id }));
            }
            toast(`${models.length} model${models.length !== 1 ? "s" : ""} found`, "success");
        } catch (err: any) {
            const msg = err.response?.data?.detail || "Could not connect to provider";
            toast(msg, "error");
        } finally {
            setFetchingModels(false);
        }
    };

    const handleCreateOrUpdate = async () => {
        if (!newLlmConfig.model) { toast("Select a model", "warning"); return; }
        if (!newLlmConfig.name)  { toast("Enter a config name", "warning"); return; }
        setCreatingLlm(true);
        try {
            if (editingLlmId) {
                const { api_key, ...rest } = newLlmConfig;
                const payload = api_key ? { ...rest, api_key } : rest;
                await api.put(`/llm/${editingLlmId}`, payload);
                toast("Configuration updated", "success");
            } else {
                await api.post("/llm", newLlmConfig);
                toast("Configuration created", "success");
            }
            setIsLlmModalOpen(false);
            resetForm();
            fetchResources();
        } catch {
            toast("Failed to save configuration", "error");
        } finally {
            setCreatingLlm(false);
        }
    };

    const handleEditLLM = (config: LLMConfig) => {
        setNewLlmConfig({ name: config.name, provider: config.provider, model: config.model, api_key: "", base_url: config.base_url || "", context_window: config.context_window ?? null });
        setEditingLlmId(config.id);
        setFetchedModels([]);
        setConnected(false);
        setIsLlmModalOpen(true);
    };

    const confirmDeleteLLM = (id: string) => { setLlmToDelete(id); setDeleteLlmDialogOpen(true); };

    const handleDeleteLLM = async () => {
        if (!llmToDelete) return;
        try {
            await api.delete(`/llm/${llmToDelete}`);
            toast("Configuration deleted", "success");
            fetchResources();
        } catch {
            toast("Failed to delete configuration", "error");
        } finally {
            setDeleteLlmDialogOpen(false);
            setLlmToDelete(null);
        }
    };

    const selectedModel = fetchedModels.find(m => m.id === newLlmConfig.model);

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-2xl md:text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>Model Providers</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>Manage your AI capability providers (LLMs).</p>
                </div>
                <Can permission="llm.manage">
                    <button
                        onClick={() => { resetForm(); setIsLlmModalOpen(true); }}
                        className="flex items-center justify-center w-full md:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(118,185,0,0.3)]"
                    >
                        <Plus className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                        Add Model
                    </button>
                </Can>
            </div>

            <div className="min-h-[400px]">
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-48 rounded-xl" />)}
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
                                                <button onClick={() => handleEditLLM(config)} className="text-gray-500 hover:text-white transition-colors p-1 rounded-md hover:bg-white/10" title="Edit"><Edit2 className="w-4 h-4" /></button>
                                                <button onClick={() => confirmDeleteLLM(config.id)} className="text-gray-500 hover:text-red-500 transition-colors p-1 rounded-md hover:bg-red-500/10" title="Delete"><Trash2 className="w-4 h-4" /></button>
                                            </Can>
                                        </div>
                                    </div>
                                    <h3 className={cn("text-base md:text-lg font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>{config.name}</h3>
                                    <div className="flex flex-wrap gap-2">
                                        <span className={cn("text-xs px-2 py-1 rounded-full font-medium border", isDark ? "text-[#76B900] bg-[#76B900]/10 border-[#76B900]/20" : "text-[#76B900] bg-[#76B900]/5 border-[#76B900]/20")}>
                                            {PROVIDER_OPTIONS.find(p => p.id === config.provider)?.name ?? config.provider}
                                        </span>
                                        <span className={cn("text-xs px-2 py-1 rounded font-mono border", isDark ? "text-gray-300 bg-white/10 border-white/5" : "text-gray-600 bg-gray-100 border-gray-200")}>
                                            {config.model}
                                        </span>
                                    </div>
                                </div>
                                {config.base_url && (
                                    <div className={cn("mt-4 pt-4 border-t", isDark ? "border-white/5" : "border-gray-100")}>
                                        <p className="text-xs text-gray-500 truncate" title={config.base_url}>{config.base_url}</p>
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

            <Dialog
                isOpen={isLlmModalOpen}
                onClose={() => { setIsLlmModalOpen(false); resetForm(); }}
                title={editingLlmId ? "Edit Configuration" : "Add LLM Configuration"}
                buttons={[
                    { label: "Cancel", onClick: () => { setIsLlmModalOpen(false); resetForm(); }, variant: "outline" },
                    { label: creatingLlm ? "Saving..." : "Save", onClick: handleCreateOrUpdate, variant: "primary", isLoading: creatingLlm }
                ]}
            >
                <div className="space-y-4">
                    <Input
                        label="Config Name"
                        placeholder="My GPT-4o Config"
                        value={newLlmConfig.name}
                        onChange={e => setNewLlmConfig(p => ({ ...p, name: e.target.value }))}
                    />

                    <div>
                        <Label>Provider</Label>
                        <CustomDropdown
                            options={PROVIDER_OPTIONS}
                            value={PROVIDER_OPTIONS.find(o => o.id === newLlmConfig.provider) ?? PROVIDER_OPTIONS[0]}
                            onChange={(o) => handleProviderChange(o.id)}
                            getLabel={(o) => o.name}
                            getKey={(o) => o.id}
                            placeholder="Select Provider"
                        />
                    </div>

                    <Input
                        label={newLlmConfig.provider === "azure" ? "Azure Endpoint (required)" : "Base URL (optional)"}
                        placeholder={BASE_URL_HINTS[newLlmConfig.provider ?? "openai"] ?? ""}
                        value={newLlmConfig.base_url}
                        onChange={e => { setNewLlmConfig(p => ({ ...p, base_url: e.target.value })); setConnected(false); }}
                    />

                    <Input
                        label="API Key"
                        type="password"
                        placeholder={editingLlmId ? "Leave blank to keep existing key" : (newLlmConfig.provider === "ollama" ? "Not required for local Ollama" : "sk-...")}
                        value={newLlmConfig.api_key}
                        onChange={e => { setNewLlmConfig(p => ({ ...p, api_key: e.target.value })); setConnected(false); }}
                    />

                    <button
                        type="button"
                        onClick={handleFetchModels}
                        disabled={fetchingModels}
                        className={cn(
                            "w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg border font-semibold text-sm transition-all",
                            connected
                                ? "border-[#76B900]/40 text-[#76B900] bg-[#76B900]/[0.08]"
                                : isDark
                                    ? "border-white/15 text-gray-200 hover:border-[#76B900]/50 hover:text-[#76B900]"
                                    : "border-gray-300 text-gray-700 hover:border-[#76B900]/50 hover:text-[#76B900]"
                        )}
                    >
                        {fetchingModels ? (
                            <><Loader2 className="w-4 h-4 animate-spin" /> Connecting...</>
                        ) : connected ? (
                            <><CheckCircle2 className="w-4 h-4" /> Connected — {fetchedModels.length} model{fetchedModels.length !== 1 ? "s" : ""} available</>
                        ) : (
                            "Connect & Fetch Models"
                        )}
                    </button>

                    {fetchedModels.length > 0 ? (
                        <div>
                            <Label>Model</Label>
                            <CustomDropdown
                                options={fetchedModels}
                                value={selectedModel ?? fetchedModels[0]}
                                onChange={(m) => setNewLlmConfig(p => ({ ...p, model: m.id }))}
                                getLabel={(m) => m.name}
                                getKey={(m) => m.id}
                                placeholder="Select a model"
                            />
                        </div>
                    ) : (
                        <Input
                            label="Model ID"
                            placeholder={newLlmConfig.provider === "azure" ? "your-deployment-name" : "gpt-4o"}
                            value={newLlmConfig.model}
                            onChange={e => setNewLlmConfig(p => ({ ...p, model: e.target.value }))}
                        />
                    )}

                    <Input
                        label="Context Window (tokens) — optional"
                        placeholder="Auto-detected from model name if left blank"
                        type="number"
                        value={newLlmConfig.context_window ?? ""}
                        onChange={e => setNewLlmConfig(p => ({ ...p, context_window: e.target.value ? parseInt(e.target.value) : null }))}
                    />
                </div>
            </Dialog>

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
