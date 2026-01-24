"use client";

import { useEffect, useState } from "react";
import { Plus, Search, Server, Trash2, RefreshCw, Plug, Shield, Edit, ShoppingBag, Globe, Database, FolderOpen, Github, Mail, MessageSquare, Check, X, AlertTriangle, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import Dialog from "@/components/ui/Dialog";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Select } from "@/components/ui/Select";

interface MCPConnection {
    id: string;
    name: string;
    server_url: string;
    protocol: string;
    status?: string;
    tools_metadata?: any[];
    summary?: string;
    auth_headers?: string; // Encrypted string from backend, usually hidden
}

interface MCPRegistryItem {
    id: string;
    name: string;
    description: string;
    icon: string;
    server_url?: string;
    protocol?: string;
    documentation?: string;
    env_vars?: any[];
}

export default function MCPHubPage() {
    const { toast } = useToast();
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [activeTab, setActiveTab] = useState<'installed' | 'hub'>('installed');
    const [connections, setConnections] = useState<MCPConnection[]>([]);
    const [registry, setRegistry] = useState<MCPRegistryItem[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [connecting, setConnecting] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ status: string; message: string; tool_count?: number } | null>(null);

    // Form State
    const [formData, setFormData] = useState({
        name: "",
        server_url: "",
        protocol: "sse",
        auth_headers: [] as { key: string; value: string }[]
    });

    useEffect(() => {
        fetchResources();
    }, []);

    const fetchResources = async () => {
        setLoading(true);
        try {
            const [connRes, hubRes] = await Promise.all([
                api.get("/resources/mcp"),
                api.get("/resources/mcp/hub")
            ]);
            setConnections(connRes.data);
            setRegistry(hubRes.data);
        } catch (error) {
            console.error("Failed to fetch MCP resources", error);
            toast("Failed to load resources", "error");
        } finally {
            setLoading(false);
        }
    };

    const handleOpenModal = (conn: MCPConnection | null = null, registryItem: MCPRegistryItem | null = null) => {
        setTestResult(null);
        if (conn) {
            // Edit Mode
            setEditingId(conn.id);
            setFormData({
                name: conn.name,
                server_url: conn.server_url,
                protocol: conn.protocol || "sse",
                auth_headers: [] // We can't see existing headers for security, user must re-enter if changing
            });
        } else if (registryItem) {
            // Install from Registry Mode
            setEditingId(null);
            setFormData({
                name: registryItem.name,
                server_url: registryItem.server_url || "",
                protocol: registryItem.protocol || "sse",
                auth_headers: registryItem.env_vars?.map(v => ({ key: v.name, value: "" })) || []
            });
        } else {
            // Create Custom Mode
            setEditingId(null);
            setFormData({
                name: "",
                server_url: "",
                protocol: "sse",
                auth_headers: []
            });
        }
        setIsModalOpen(true);
    };

    const handleAddHeader = () => {
        setFormData({
            ...formData,
            auth_headers: [...formData.auth_headers, { key: "", value: "" }]
        });
    };

    const handleRemoveHeader = (index: number) => {
        const newHeaders = [...formData.auth_headers];
        newHeaders.splice(index, 1);
        setFormData({ ...formData, auth_headers: newHeaders });
    };

    const handleHeaderChange = (index: number, field: 'key' | 'value', value: string) => {
        const newHeaders = [...formData.auth_headers];
        newHeaders[index][field] = value;
        setFormData({ ...formData, auth_headers: newHeaders });
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            // Transform headers array to object
            const headersObj = formData.auth_headers.reduce((acc, curr) => {
                if (curr.key.trim()) acc[curr.key.trim()] = curr.value;
                return acc;
            }, {} as Record<string, string>);

            const payload = {
                name: formData.name,
                server_url: formData.server_url,
                protocol: formData.protocol,
                auth_headers: headersObj
            };

            const res = await api.post("/resources/mcp/test", payload);
            setTestResult(res.data);
            if (res.data.status === "success") {
                toast(`Success! Found ${res.data.tool_count} tools.`, "success");
            } else {
                toast("Connection failed", "error");
            }
        } catch (error: any) {
            console.error("Test failed", error);
            const msg = error.response?.data?.message || "Connection failed";
            setTestResult({ status: "failed", message: msg });
        } finally {
            setTesting(false);
        }
    };

    const handleSave = async () => {
        setConnecting(true);
        try {
            const headersObj = formData.auth_headers.reduce((acc, curr) => {
                if (curr.key.trim()) acc[curr.key.trim()] = curr.value;
                return acc;
            }, {} as Record<string, string>);

            const payload: any = {
                name: formData.name,
                server_url: formData.server_url,
                protocol: formData.protocol
            };

            if (Object.keys(headersObj).length > 0) {
                payload.auth_headers = headersObj;
            }

            if (editingId) {
                await api.put(`/resources/mcp/${editingId}`, payload);
                toast("Connection updated successfully", "success");
            } else {
                await api.post("/resources/mcp", payload);
                toast("MCP Server connected successfully", "success");
            }

            setIsModalOpen(false);
            fetchResources();
            setActiveTab("installed");
        } catch (error: any) {
            console.error("Save failed", error);
            toast(error.response?.data?.detail || "Failed to save connection", "error");
        } finally {
            setConnecting(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to remove this server?")) return;
        try {
            await api.delete(`/resources/mcp/${id}`);
            toast("Server removed", "success");
            fetchResources();
        } catch (error) {
            toast("Failed to remove server", "error");
        }
    };

    const handleSync = async (id: string) => {
        const toastId = toast("Syncing tools...", "loading"); // Need loading toast support or just standard
        try {
            await api.post(`/resources/mcp/${id}/sync`);
            toast("Tools synced successfully", "success");
            fetchResources();
        } catch (error) {
            toast("Sync failed", "error");
        }
    };

    const getIconComponent = (iconName: string) => {
        const icons: any = { FolderOpen, Github, Database, Globe, Mail, MessageSquare, ShoppingBag, Plug };
        return icons[iconName] || Plug;
    };

    return (
        <div className="space-y-8 relative pb-20">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-2xl md:text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>
                        MCP Hub
                    </h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                        Connect and manage Model Context Protocol servers.
                    </p>
                </div>
                <button
                    onClick={() => handleOpenModal()}
                    className="flex items-center justify-center px-4 py-2 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    Add Custom Server
                </button>
            </div>

            {/* Tabs */}
            <div className={cn("flex space-x-6 border-b overflow-x-auto whitespace-nowrap pb-1", isDark ? "border-white/10" : "border-gray-200")}>
                <button
                    onClick={() => setActiveTab('installed')}
                    className={`pb-4 text-base md:text-sm font-bold transition-colors relative ${activeTab === 'installed' ? 'text-nvidia-green' : isDark ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
                >
                    Installed Servers
                    {activeTab === 'installed' && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-nvidia-green rounded-t-full" />
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('hub')}
                    className={`pb-4 text-base md:text-sm font-bold transition-colors relative ${activeTab === 'hub' ? 'text-nvidia-green' : isDark ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
                >
                    Hub Registry
                    {activeTab === 'hub' && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-nvidia-green rounded-t-full" />
                    )}
                </button>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-12 h-12 text-nvidia-green animate-spin" />
                </div>
            ) : (
                <div className="min-h-[400px]">
                    {activeTab === 'installed' ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {connections.map((conn) => (
                                <div key={conn.id} className={cn("backdrop-blur-sm border rounded-xl p-6 transition-all group relative overflow-hidden", isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm")}>
                                    <div className="flex justify-between items-start mb-4">
                                        <div className={cn("p-3 rounded-lg", isDark ? "bg-white/5" : "bg-gray-100")}>
                                            <Server className={cn("w-6 h-6", isDark ? "text-nvidia-green" : "text-gray-700")} />
                                        </div>
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={() => handleSync(conn.id)}
                                                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                                                title="Sync Tools"
                                            >
                                                <RefreshCw className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleOpenModal(conn)}
                                                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                                                title="Edit"
                                            >
                                                <Edit className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(conn.id)}
                                                className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-500/10 transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                    <h3 className={cn("text-lg font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>{conn.name}</h3>
                                    <div className="flex items-center text-xs text-gray-500 mb-4 font-mono truncate">
                                        <Shield className="w-3 h-3 mr-1" />
                                        {conn.server_url}
                                    </div>

                                    {conn.summary && (
                                        <p className={cn("text-sm line-clamp-3 mb-4", isDark ? "text-gray-400" : "text-gray-600")}>
                                            {conn.summary}
                                        </p>
                                    )}

                                    <div className="mt-auto pt-4 border-t border-white/5 flex justify-between items-center">
                                        <span className={cn("text-xs uppercase font-bold px-2 py-1 rounded", isDark ? "bg-white/10 text-gray-300" : "bg-gray-100 text-gray-700")}>
                                            {conn.tools_metadata?.length || 0} Tools
                                        </span>
                                        <span className={cn("text-xs font-mono", isDark ? "text-gray-500" : "text-gray-400")}>{conn.protocol}</span>
                                    </div>
                                </div>
                            ))}

                            {connections.length === 0 && (
                                <div className={cn("col-span-full flex flex-col items-center justify-center py-20 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                                    <ShoppingBag className="w-16 h-16 text-gray-600 mb-4" />
                                    <h3 className="text-xl font-bold text-white mb-2">No Installed Servers</h3>
                                    <p className="text-gray-400 mb-6">Install servers from the Registry or add a custom one.</p>
                                    <button
                                        onClick={() => setActiveTab('hub')}
                                        className="text-nvidia-green hover:underline font-bold"
                                    >
                                        Browse Registry
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {registry.map((item) => {
                                const Icon = getIconComponent(item.icon);
                                const isInstalled = connections.some(c => c.name === item.name || c.server_url === item.server_url);

                                return (
                                    <div key={item.id} className={cn("backdrop-blur-sm border rounded-xl p-6 transition-all group flex flex-col", isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm")}>
                                        <div className="flex justify-between items-start mb-4">
                                            <div className={cn("p-3 rounded-lg", isDark ? "bg-white/5" : "bg-gray-100")}>
                                                <Icon className={cn("w-6 h-6", isDark ? "text-nvidia-green" : "text-gray-700")} />
                                            </div>
                                            {isInstalled ? (
                                                <span className="flex items-center text-xs font-bold text-nvidia-green bg-nvidia-green/10 px-2 py-1 rounded">
                                                    <Check className="w-3 h-3 mr-1" /> Installed
                                                </span>
                                            ) : (
                                                <span className="text-xs font-bold text-gray-500 bg-gray-500/10 px-2 py-1 rounded uppercase">Available</span>
                                            )}
                                        </div>
                                        <h3 className={cn("text-lg font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>{item.name}</h3>
                                        <p className={cn("text-sm mb-4 flex-grow", isDark ? "text-gray-400" : "text-gray-600")}>
                                            {item.description}
                                        </p>

                                        <div className="pt-4 border-t border-white/5 space-y-3">
                                            {item.documentation && (
                                                <div className="text-xs font-mono p-2 rounded bg-black/30 text-gray-400 truncate" title={item.documentation}>
                                                    {item.documentation}
                                                </div>
                                            )}
                                            <button
                                                onClick={() => handleOpenModal(null, item)}
                                                disabled={isInstalled}
                                                className={cn(
                                                    "w-full py-2 rounded-lg font-bold text-sm transition-all flex items-center justify-center",
                                                    isInstalled
                                                        ? "bg-white/5 text-gray-500 cursor-not-allowed"
                                                        : "bg-white/10 text-white hover:bg-white/20 hover:text-nvidia-green border border-white/5"
                                                )}
                                            >
                                                {isInstalled ? "Already Installed" : "Configure & Install"}
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* Main Modal */}
            <Dialog
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingId ? "Edit MCP Server" : "Add MCP Server"}
                buttons={[
                    { label: "Cancel", onClick: () => setIsModalOpen(false), variant: "outline" },
                    { label: connecting ? "Saving..." : "Save Connection", onClick: handleSave, variant: "primary", isLoading: connecting }
                ]}
            >
                <div className="space-y-4">
                    <div className="bg-blue-500/10 border border-blue-500/20 text-blue-200 p-3 rounded-lg text-xs mb-4">
                        <p className="font-bold flex items-center mb-1"><AlertTriangle className="w-3 h-3 mr-1" /> Configuration Note</p>
                        <p>For generic servers, enter the server URL (SSE). If referencing a registry item, ensure any required environment variables/headers are added below.</p>
                    </div>

                    <Input
                        label="Server Name"
                        placeholder="My Custom Server"
                        value={formData.name}
                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                    />

                    <Input
                        label="Server URL (SSE Endpoint)"
                        placeholder="http://localhost:8000/sse"
                        value={formData.server_url}
                        onChange={e => setFormData({ ...formData, server_url: e.target.value })}
                    />

                    <div>
                        <div className="flex justify-between items-center mb-2">
                            <Label>Configuration & Headers</Label>
                            <button onClick={handleAddHeader} className="text-xs text-nvidia-green hover:underline">+ Add Variable</button>
                        </div>

                        <div className="space-y-2 max-h-[150px] overflow-y-auto pr-1">
                            {formData.auth_headers.map((header, idx) => (
                                <div key={idx} className="flex gap-2 items-center">
                                    <input
                                        className={cn("flex-1 bg-transparent border rounded px-2 py-1 text-sm", isDark ? "border-white/20 text-white" : "border-gray-300 text-black")}
                                        placeholder="KEY / Header Name"
                                        value={header.key}
                                        onChange={e => handleHeaderChange(idx, 'key', e.target.value)}
                                    />
                                    <input
                                        className={cn("flex-1 bg-transparent border rounded px-2 py-1 text-sm", isDark ? "border-white/20 text-white" : "border-gray-300 text-black")}
                                        placeholder="VALUE"
                                        type="password"
                                        value={header.value}
                                        onChange={e => handleHeaderChange(idx, 'value', e.target.value)}
                                    />
                                    <button onClick={() => handleRemoveHeader(idx)} className="text-red-500 hover:text-red-400">
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                            {formData.auth_headers.length === 0 && (
                                <p className="text-xs text-gray-500 italic">No custom headers or environment variables configured.</p>
                            )}
                        </div>
                    </div>

                    {/* Test Button */}
                    <div className="pt-4 border-t border-white/10">
                        <button
                            onClick={handleTestConnection}
                            disabled={testing || !formData.server_url}
                            className="w-full bg-white/10 text-white font-medium px-4 py-2 rounded-lg hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center border border-white/5"
                        >
                            {testing ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Testing Connection...
                                </>
                            ) : (
                                "Test Connection"
                            )}
                        </button>

                        {testResult && (
                            <div className={`mt-3 p-3 rounded-lg text-sm flex items-start ${testResult.status === 'success' ? 'bg-nvidia-green/10 text-nvidia-green border border-nvidia-green/30' : 'bg-red-500/10 text-red-400 border border-red-500/30'}`}>
                                {testResult.status === 'success' ? (
                                    <Check className="w-4 h-4 mr-2 mt-0.5 shrink-0" />
                                ) : (
                                    <AlertTriangle className="w-4 h-4 mr-2 mt-0.5 shrink-0" />
                                )}
                                <span>{testResult.message}</span>
                            </div>
                        )}
                    </div>
                </div>
            </Dialog>
        </div>
    );
}
