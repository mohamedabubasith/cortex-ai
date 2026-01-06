"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Cpu, Trash2, Loader2, Plus, Save, X, Edit2, AlertCircle, Server, RefreshCw, Key, Plug } from "lucide-react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import Dialog from "@/components/ui/Dialog";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import CustomDropdown from "@/components/ui/CustomDropdown";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
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

interface MCPConnection {
    id: string;
    name: string;
    server_url: string;
    summary: string;
    status?: string;
    auth_headers?: string;
    protocol?: 'sse' | 'http';
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

    const [activeTab, setActiveTab] = useState<'models' | 'mcp'>('models');
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

    // --- MCP State ---
    const [mcpConnections, setMcpConnections] = useState<MCPConnection[]>([]);
    const [isMcpModalOpen, setIsMcpModalOpen] = useState(false);
    const [savingMcp, setSavingMcp] = useState(false);
    const [syncingMcp, setSyncingMcp] = useState<string | null>(null);
    const [currentMcp, setCurrentMcp] = useState<any>({
        name: "",
        server_url: "",
        auth_headers: "",
        protocol: "sse"
    });
    const [deleteMcpDialogOpen, setDeleteMcpDialogOpen] = useState(false);
    const [mcpToDelete, setMcpToDelete] = useState<string | null>(null);
    const [testingMcp, setTestingMcp] = useState(false);


    useEffect(() => {
        fetchResources();
    }, []);

    const fetchResources = async () => {
        setLoading(true);
        try {
            const [llmRes, mcpRes] = await Promise.allSettled([
                api.get("/llm"),
                api.get("/resources/mcp")
            ]);

            if (llmRes.status === 'fulfilled') setLlmConfigs(llmRes.value.data);
            if (mcpRes.status === 'fulfilled') setMcpConnections(mcpRes.value.data);

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

    // --- MCP Handlers ---

    const handleOpenMcpDialog = (mcp: any = null) => {
        if (mcp) {
            setCurrentMcp({ ...mcp, auth_headers: "", protocol: mcp.protocol || "sse" }); // Don't show auth headers back
        } else {
            setCurrentMcp({
                name: "",
                server_url: "http://localhost:8000/sse",
                auth_headers: "",
                protocol: "sse"
            });
        }
        setIsMcpModalOpen(true);
    };

    const handleTestMcp = async () => {
        if (!currentMcp.server_url) {
            toast("Please enter a Server URL.", "warning");
            return;
        }

        setTestingMcp(true);
        try {
            let authHeadersObj = null;
            if (currentMcp.auth_headers && currentMcp.auth_headers.trim()) {
                try {
                    authHeadersObj = JSON.parse(currentMcp.auth_headers);
                } catch (e) {
                    toast("Invalid JSON in Auth Headers", "error");
                    setTestingMcp(false);
                    return;
                }
            }

            const payload = {
                name: currentMcp.name || "Test Connection",
                server_url: currentMcp.server_url,
                auth_headers: authHeadersObj,
                protocol: currentMcp.protocol
            };

            const res = await api.post("/resources/mcp/test", payload);

            if (res.data.status === "success") {
                toast(res.data.message, "success");
            } else {
                toast(res.data.message, "error");
            }

        } catch (error: any) {
            console.error("Test connection failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Connection failed.";
            toast(errorMessage, "error");
        } finally {
            setTestingMcp(false);
        }
    };

    const handleSaveMcp = async () => {
        setSavingMcp(true);
        try {
            // Parse headers if present
            let authHeadersObj = null;
            if (currentMcp.auth_headers && currentMcp.auth_headers.trim()) {
                try {
                    authHeadersObj = JSON.parse(currentMcp.auth_headers);
                } catch (e) {
                    toast("Invalid JSON in Auth Headers", "error");
                    setSavingMcp(false);
                    return;
                }
            }

            const payload = {
                name: currentMcp.name,
                server_url: currentMcp.server_url,
                auth_headers: authHeadersObj,
                protocol: currentMcp.protocol
            };

            if (currentMcp.id) {
                // Update
                await api.put(`/resources/mcp/${currentMcp.id}`, payload);
                toast("MCP Connection updated", "success");
            } else {
                // Create
                await api.post("/resources/mcp", payload);
                toast("MCP Connection saved", "success");
            }

            setIsMcpModalOpen(false);
            fetchResources();
        } catch (error: any) {
            console.error("Failed to save MCP", error);
            const errorMessage = error.response?.data?.detail || error.message || "Failed to save MCP";
            toast(errorMessage, "error");
        } finally {
            setSavingMcp(false);
        }
    };

    const handleSyncMcp = async (mcpId: string) => {
        setSyncingMcp(mcpId);
        try {
            await api.post(`/resources/mcp/${mcpId}/sync`);
            toast("Tools synced and summarized successfully", "success");
            fetchResources();
        } catch (error: any) {
            console.error("Sync failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Sync failed";
            toast(errorMessage, "error");
        } finally {
            setSyncingMcp(null);
        }
    };

    const confirmDeleteMcp = (id: string) => {
        setMcpToDelete(id);
        setDeleteMcpDialogOpen(true);
    }

    const handleDeleteMcp = async () => {
        if (!mcpToDelete) return;
        try {
            await api.delete(`/resources/mcp/${mcpToDelete}`);
            toast("MCP connection deleted successfully", "success");
            fetchResources();
        } catch (error) {
            console.error("Delete failed", error);
            toast("Failed to delete item", "error");
        } finally {
            setDeleteMcpDialogOpen(false);
            setMcpToDelete(null);
        }
    }


    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-2xl md:text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>Providers</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>Manage your AI capabilities and connections.</p>
                </div>
                <button
                    onClick={() => {
                        if (activeTab === 'models') {
                            resetLlmForm();
                            setIsLlmModalOpen(true);
                        } else {
                            handleOpenMcpDialog();
                        }
                    }}
                    className="flex items-center justify-center w-full md:w-auto px-6 py-3 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(118,185,0,0.3)]"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    {activeTab === 'models' ? "Add Model" : "Add Connection"}
                </button>
            </div>

            {/* Tabs */}
            <div className={cn("flex space-x-6 border-b overflow-x-auto whitespace-nowrap pb-1", isDark ? "border-white/10" : "border-gray-200")}>
                <button
                    onClick={() => setActiveTab('models')}
                    className={`pb-4 text-base md:text-sm font-bold transition-colors relative ${activeTab === 'models' ? 'text-nvidia-green' : isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
                >
                    <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        Model Providers
                    </div>
                    {activeTab === 'models' && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-nvidia-green rounded-t-full" />
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('mcp')}
                    className={`pb-4 text-base md:text-sm font-bold transition-colors relative ${activeTab === 'mcp' ? 'text-nvidia-green' : isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
                >
                    <div className="flex items-center gap-2">
                        <Plug className="w-4 h-4" />
                        MCP Servers
                    </div>
                    {activeTab === 'mcp' && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-nvidia-green rounded-t-full" />
                    )}
                </button>
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[...Array(3)].map((_, i) => (
                            <Skeleton key={i} className="h-48 rounded-xl" />
                        ))}
                    </div>
                ) : activeTab === 'models' ? (
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
                                <h3 className={cn("text-xl font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>No Model Providers</h3>
                                <p className={isDark ? "text-gray-400" : "text-gray-600"}>Add your first LLM provider configuration.</p>
                            </div>
                        )}
                    </div>
                ) : (
                    // MCP Tab Content
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {mcpConnections.map((conn) => (
                            <div
                                key={conn.id}
                                onClick={() => handleOpenMcpDialog(conn)}
                                className={cn(
                                    "backdrop-blur-sm border rounded-xl p-6 transition-all group flex flex-col justify-between h-full min-h-[180px] cursor-pointer",
                                    isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50 hover:bg-white/5" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm hover:shadow-md"
                                )}
                            >
                                <div>
                                    <div className="flex justify-between items-start mb-4">
                                        <div className={cn("p-3 rounded-lg transition-colors", isDark ? "bg-white/5 group-hover:bg-nvidia-green/10" : "bg-gray-100 group-hover:bg-nvidia-green/10")}>
                                            <Server className={cn("w-6 h-6 transition-colors", isDark ? "text-gray-400 group-hover:text-nvidia-green" : "text-gray-600 group-hover:text-nvidia-green")} />
                                        </div>
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleSyncMcp(conn.id);
                                                }}
                                                disabled={syncingMcp === conn.id}
                                                className={cn("text-gray-500 hover:text-white transition-colors p-1 rounded-md hover:bg-white/10", syncingMcp === conn.id && "animate-spin text-nvidia-green")}
                                                title="Sync Tools"
                                            >
                                                <RefreshCw className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    confirmDeleteMcp(conn.id);
                                                }}
                                                className="text-gray-500 hover:text-red-500 transition-colors p-1 rounded-md hover:bg-red-500/10"
                                                title="Delete"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                    <h3 className={cn("text-base md:text-lg font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>{conn.name}</h3>
                                    <p className={cn("text-sm mb-4 line-clamp-3", isDark ? "text-gray-400" : "text-gray-600")}>
                                        {conn.summary || "No summary available. Sync to fetch tools."}
                                    </p>
                                </div>
                                <div className={cn("mt-4 pt-4 border-t flex justify-between items-center", isDark ? "border-white/5" : "border-gray-100")}>
                                    <p className="text-xs text-gray-500 truncate max-w-[70%]" title={conn.server_url}>
                                        {conn.server_url}
                                    </p>
                                    <span className={cn("text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider",
                                        conn.status !== 'error' ? "bg-nvidia-green/20 text-nvidia-green" : "bg-red-500/20 text-red-400"
                                    )}>
                                        {conn.status || 'Active'}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {mcpConnections.length === 0 && (
                            <div className={cn("col-span-full flex flex-col items-center justify-center py-20 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                                <Server className="w-16 h-16 text-gray-600 mb-4" />
                                <h3 className={cn("text-xl font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>No MCP Connections</h3>
                                <p className={isDark ? "text-gray-400" : "text-gray-600"}>Connect to an MCP server to add tools.</p>
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

            {/* MCP Dialog */}
            <Dialog
                isOpen={isMcpModalOpen}
                onClose={() => setIsMcpModalOpen(false)}
                title={currentMcp.id ? "Edit MCP Connection" : "Add MCP Connection"}
                buttons={[
                    { label: "Cancel", onClick: () => setIsMcpModalOpen(false), variant: "outline" },
                    { label: "Test Connection", onClick: handleTestMcp, variant: "secondary", isLoading: testingMcp },
                    { label: savingMcp ? "Saving..." : "Save Connection", onClick: handleSaveMcp, variant: "primary", isLoading: savingMcp }
                ]}
            >
                <div className="space-y-4">
                    <div>
                        <label className={cn("block text-sm font-medium mb-1", isDark ? "text-gray-300" : "text-gray-700")}>Name</label>
                        <input
                            type="text"
                            className={cn(
                                "w-full border rounded-lg px-4 py-2 focus:ring-nvidia-green focus:border-nvidia-green",
                                isDark ? "bg-black/50 border-gray-700 text-white" : "bg-white border-gray-300 text-gray-900"
                            )}
                            placeholder="My Local Tools"
                            value={currentMcp.name}
                            onChange={e => setCurrentMcp({ ...currentMcp, name: e.target.value })}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={cn("block text-sm font-medium mb-1", isDark ? "text-gray-300" : "text-gray-700")}>Protocol</label>
                            <select
                                className={cn(
                                    "w-full border rounded-lg px-4 py-2 focus:ring-nvidia-green focus:border-nvidia-green",
                                    isDark ? "bg-black/50 border-gray-700 text-white" : "bg-white border-gray-300 text-gray-900"
                                )}
                                value={currentMcp.protocol || "sse"}
                                onChange={e => setCurrentMcp({ ...currentMcp, protocol: e.target.value })}
                            >
                                <option value="sse">SSE (Server-Sent Events)</option>
                                <option value="http">HTTP (Streamable)</option>
                            </select>
                        </div>
                        <div>
                            <label className={cn("block text-sm font-medium mb-1", isDark ? "text-gray-300" : "text-gray-700")}>Server URL</label>
                            <input
                                type="text"
                                className={cn(
                                    "w-full border rounded-lg px-4 py-2 focus:ring-nvidia-green focus:border-nvidia-green",
                                    isDark ? "bg-black/50 border-gray-700 text-white" : "bg-white border-gray-300 text-gray-900"
                                )}
                                placeholder={currentMcp.protocol === 'http' ? "http://localhost:8000/mcp" : "http://localhost:8000/sse"}
                                value={currentMcp.server_url}
                                onChange={e => setCurrentMcp({ ...currentMcp, server_url: e.target.value })}
                            />
                        </div>
                    </div>
                    <div>
                        <label className={cn("block text-sm font-medium mb-1", isDark ? "text-gray-300" : "text-gray-700")}>Auth Headers (JSON, Optional)</label>
                        <textarea
                            className={cn(
                                "w-full border rounded-lg px-4 py-2 focus:ring-nvidia-green focus:border-nvidia-green h-24 font-mono text-xs",
                                isDark ? "bg-black/50 border-gray-700 text-white" : "bg-white border-gray-300 text-gray-900"
                            )}
                            placeholder={'{"Authorization": "Bearer token"}'}
                            value={currentMcp.auth_headers}
                            onChange={e => setCurrentMcp({ ...currentMcp, auth_headers: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">Optional JSON object for authentication headers.</p>
                    </div>
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

            {/* Delete MCP Dialog */}
            <Dialog
                isOpen={deleteMcpDialogOpen}
                onClose={() => setDeleteMcpDialogOpen(false)}
                title="Delete Connection"
                description="Are you sure you want to delete this MCP connection? This action cannot be undone."
                buttons={[
                    { label: "Cancel", onClick: () => setDeleteMcpDialogOpen(false), variant: "outline" },
                    { label: "Delete", onClick: handleDeleteMcp, variant: "danger" }
                ]}
            />

        </div>
    );
}
