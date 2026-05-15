"use client";

import { useEffect, useState } from "react";
import { Plus, Server, Trash2, RefreshCw, Plug, Shield, Edit, Check, X, AlertTriangle, Loader2, Key, ChevronDown, ChevronUp } from "lucide-react";
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
    auth_headers?: string;
}

export default function MCPHubPage() {
    const { toast } = useToast();
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [connections, setConnections] = useState<MCPConnection[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [connecting, setConnecting] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ status: string; message: string; tool_count?: number } | null>(null);
    const [showAdvanced, setShowAdvanced] = useState(false);

    // Form state
    const [formData, setFormData] = useState({
        name: "",
        server_url: "",
        protocol: "sse",
        bearer_token: "",
        auth_headers: [] as { key: string; value: string }[]
    });

    useEffect(() => { fetchConnections(); }, []);

    const fetchConnections = async () => {
        setLoading(true);
        try {
            const res = await api.get("/resources/mcp");
            setConnections(res.data);
        } catch {
            toast("Failed to load MCP servers", "error");
        } finally {
            setLoading(false);
        }
    };

    const openModal = (conn: MCPConnection | null = null) => {
        setTestResult(null);
        setShowAdvanced(false);
        if (conn) {
            setEditingId(conn.id);
            setFormData({ name: conn.name, server_url: conn.server_url, protocol: conn.protocol || "sse", bearer_token: "", auth_headers: [] });
        } else {
            setEditingId(null);
            setFormData({ name: "", server_url: "", protocol: "sse", bearer_token: "", auth_headers: [] });
        }
        setIsModalOpen(true);
    };

    // Build final headers object from bearer token + custom headers
    const buildHeaders = () => {
        const headers: Record<string, string> = {};
        if (formData.bearer_token.trim()) {
            headers["Authorization"] = `Bearer ${formData.bearer_token.trim()}`;
        }
        formData.auth_headers.forEach(h => {
            if (h.key.trim()) headers[h.key.trim()] = h.value;
        });
        return headers;
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            const res = await api.post("/resources/mcp/test", {
                name: formData.name,
                server_url: formData.server_url,
                protocol: formData.protocol,
                auth_headers: buildHeaders()
            });
            setTestResult(res.data);
            if (res.data.status === "success") {
                toast(`Connected — ${res.data.tool_count} tools found`, "success");
            } else {
                toast("Connection failed", "error");
            }
        } catch (error: any) {
            const msg = error.response?.data?.message || "Connection failed";
            setTestResult({ status: "failed", message: msg });
        } finally {
            setTesting(false);
        }
    };

    const handleSave = async () => {
        if (!formData.name.trim() || !formData.server_url.trim()) {
            toast("Name and URL are required", "error");
            return;
        }
        setConnecting(true);
        try {
            const headers = buildHeaders();
            const payload: any = {
                name: formData.name,
                server_url: formData.server_url,
                protocol: formData.protocol
            };
            if (Object.keys(headers).length > 0) payload.auth_headers = headers;

            if (editingId) {
                await api.put(`/resources/mcp/${editingId}`, payload);
                toast("Server updated", "success");
            } else {
                const res = await api.post("/resources/mcp", payload);
                toast("MCP server connected", "success");
                try {
                    await api.post(`/resources/mcp/${res.data.id}/sync`);
                    toast("Tools synced", "success");
                } catch { /* sync failure is non-fatal */ }
            }

            setIsModalOpen(false);
            fetchConnections();
        } catch (error: any) {
            toast(error.response?.data?.detail || "Failed to save", "error");
        } finally {
            setConnecting(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Remove this MCP server?")) return;
        try {
            await api.delete(`/resources/mcp/${id}`);
            toast("Server removed", "success");
            fetchConnections();
        } catch {
            toast("Failed to remove server", "error");
        }
    };

    const handleSync = async (id: string) => {
        toast("Syncing tools…", "info");
        try {
            await api.post(`/resources/mcp/${id}/sync`);
            toast("Tools synced", "success");
            fetchConnections();
        } catch {
            toast("Sync failed", "error");
        }
    };

    return (
        <div className="space-y-8 relative pb-20">
            {/* Header */}
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
                    onClick={() => openModal()}
                    className="flex items-center justify-center px-4 py-2 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    Add Custom Server
                </button>
            </div>

            {/* Installed Servers */}
            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-12 h-12 text-nvidia-green animate-spin" />
                </div>
            ) : connections.length === 0 ? (
                <div className={cn("flex flex-col items-center justify-center py-24 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                    <Plug className="w-16 h-16 text-gray-500 mb-4" />
                    <h3 className={cn("text-xl font-bold mb-2", isDark ? "text-white" : "text-gray-900")}>No servers connected</h3>
                    <p className={cn("mb-6 text-sm", isDark ? "text-gray-400" : "text-gray-600")}>
                        Add a custom MCP server to give your agents new tools.
                    </p>
                    <button
                        onClick={() => openModal()}
                        className="flex items-center px-4 py-2 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all text-sm"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Custom Server
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {connections.map((conn) => (
                        <div
                            key={conn.id}
                            className={cn(
                                "backdrop-blur-sm border rounded-xl p-6 transition-all group relative overflow-hidden",
                                isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm"
                            )}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className={cn("p-3 rounded-lg", isDark ? "bg-white/5" : "bg-gray-100")}>
                                    <Server className={cn("w-6 h-6", isDark ? "text-nvidia-green" : "text-gray-700")} />
                                </div>
                                <div className="flex space-x-1">
                                    <button
                                        onClick={() => handleSync(conn.id)}
                                        className={cn("p-2 rounded-lg transition-colors", isDark ? "text-gray-400 hover:text-white hover:bg-white/10" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100")}
                                        title="Sync tools"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => openModal(conn)}
                                        className={cn("p-2 rounded-lg transition-colors", isDark ? "text-gray-400 hover:text-white hover:bg-white/10" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100")}
                                        title="Edit"
                                    >
                                        <Edit className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(conn.id)}
                                        className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-500/10 transition-colors"
                                        title="Remove"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            <h3 className={cn("text-lg font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>{conn.name}</h3>
                            <div className="flex items-center text-xs text-gray-500 mb-4 font-mono truncate">
                                <Shield className="w-3 h-3 mr-1 shrink-0" />
                                {conn.server_url}
                            </div>

                            {conn.summary && (
                                <p className={cn("text-sm line-clamp-3 mb-4", isDark ? "text-gray-400" : "text-gray-600")}>
                                    {conn.summary}
                                </p>
                            )}

                            <div className={cn("mt-auto pt-4 border-t flex justify-between items-center", isDark ? "border-white/5" : "border-gray-100")}>
                                <span className={cn("text-xs uppercase font-bold px-2 py-1 rounded", isDark ? "bg-white/10 text-gray-300" : "bg-gray-100 text-gray-700")}>
                                    {conn.tools_metadata?.length || 0} Tools
                                </span>
                                <span className={cn("text-xs font-mono uppercase", isDark ? "text-gray-500" : "text-gray-400")}>
                                    {conn.protocol}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Add / Edit Modal */}
            <Dialog
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingId ? "Edit MCP Server" : "Add MCP Server"}
                buttons={[
                    { label: "Cancel", onClick: () => setIsModalOpen(false), variant: "outline" },
                    { label: connecting ? "Saving…" : "Save Connection", onClick: handleSave, variant: "primary", isLoading: connecting }
                ]}
            >
                <div className="space-y-5">
                    {/* Name */}
                    <Input
                        label="Server Name"
                        placeholder="My Custom Server"
                        value={formData.name}
                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                    />

                    {/* Protocol + URL */}
                    <div className="grid grid-cols-5 gap-4">
                        <div className="col-span-2">
                            <Select
                                label="Protocol"
                                value={formData.protocol}
                                onChange={e => setFormData({ ...formData, protocol: e.target.value })}
                                options={[
                                    { label: "SSE", value: "sse" },
                                    { label: "HTTP (Streamable)", value: "http" }
                                ]}
                            />
                        </div>
                        <div className="col-span-3">
                            <Input
                                label="Server URL"
                                placeholder="https://example.com/mcp"
                                value={formData.server_url}
                                onChange={e => setFormData({ ...formData, server_url: e.target.value })}
                            />
                        </div>
                    </div>

                    {/* Bearer Token — shown for HTTP streamable, optional for SSE */}
                    <div>
                        <Label>
                            Bearer Token
                            <span className={cn("ml-2 text-xs font-normal", isDark ? "text-gray-500" : "text-gray-400")}>
                                optional
                                {formData.protocol === "http" && (
                                    <span className="ml-1 text-nvidia-green">— recommended for Streamable HTTP</span>
                                )}
                            </span>
                        </Label>
                        <div className="relative mt-1">
                            <Key className={cn("absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4", isDark ? "text-gray-500" : "text-gray-400")} />
                            <input
                                type="password"
                                placeholder="eyJ… or your API token"
                                value={formData.bearer_token}
                                onChange={e => setFormData({ ...formData, bearer_token: e.target.value })}
                                className={cn(
                                    "w-full pl-9 pr-4 py-2 rounded-lg border text-sm outline-none transition-colors",
                                    isDark
                                        ? "bg-white/5 border-white/10 text-white placeholder-gray-600 focus:border-nvidia-green/50"
                                        : "bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-nvidia-green"
                                )}
                            />
                        </div>
                        {formData.bearer_token && (
                            <p className={cn("mt-1 text-xs", isDark ? "text-gray-500" : "text-gray-400")}>
                                Will be sent as <code className="font-mono">Authorization: Bearer …</code>
                            </p>
                        )}
                    </div>

                    {/* Advanced: custom headers */}
                    <div>
                        <button
                            type="button"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className={cn("flex items-center gap-1 text-xs font-medium transition-colors", isDark ? "text-gray-500 hover:text-gray-300" : "text-gray-400 hover:text-gray-700")}
                        >
                            {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            Advanced: custom headers
                        </button>

                        {showAdvanced && (
                            <div className="mt-3 space-y-2">
                                <div className="flex justify-between items-center">
                                    <p className={cn("text-xs", isDark ? "text-gray-500" : "text-gray-400")}>
                                        Extra request headers (e.g. <code className="font-mono">X-Tenant-Id</code>)
                                    </p>
                                    <button
                                        onClick={() => setFormData({ ...formData, auth_headers: [...formData.auth_headers, { key: "", value: "" }] })}
                                        className="text-xs text-nvidia-green hover:underline"
                                    >
                                        + Add Header
                                    </button>
                                </div>
                                <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
                                    {formData.auth_headers.map((h, idx) => (
                                        <div key={idx} className="flex gap-2 items-center">
                                            <input
                                                className={cn("flex-1 bg-transparent border rounded px-2 py-1 text-sm", isDark ? "border-white/20 text-white" : "border-gray-300 text-black")}
                                                placeholder="Header name"
                                                value={h.key}
                                                onChange={e => {
                                                    const updated = [...formData.auth_headers];
                                                    updated[idx].key = e.target.value;
                                                    setFormData({ ...formData, auth_headers: updated });
                                                }}
                                            />
                                            <input
                                                className={cn("flex-1 bg-transparent border rounded px-2 py-1 text-sm", isDark ? "border-white/20 text-white" : "border-gray-300 text-black")}
                                                placeholder="Value"
                                                type="password"
                                                value={h.value}
                                                onChange={e => {
                                                    const updated = [...formData.auth_headers];
                                                    updated[idx].value = e.target.value;
                                                    setFormData({ ...formData, auth_headers: updated });
                                                }}
                                            />
                                            <button
                                                onClick={() => setFormData({ ...formData, auth_headers: formData.auth_headers.filter((_, i) => i !== idx) })}
                                                className="text-red-500 hover:text-red-400 shrink-0"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    ))}
                                    {formData.auth_headers.length === 0 && (
                                        <p className={cn("text-xs italic", isDark ? "text-gray-600" : "text-gray-400")}>No custom headers.</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Test Connection */}
                    <div className={cn("pt-4 border-t", isDark ? "border-white/10" : "border-gray-100")}>
                        <button
                            onClick={handleTestConnection}
                            disabled={testing || !formData.server_url.trim()}
                            className={cn(
                                "w-full font-medium px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center border",
                                isDark
                                    ? "bg-white/10 text-white hover:bg-white/20 border-white/5"
                                    : "bg-gray-100 text-gray-900 hover:bg-gray-200 border-gray-200"
                            )}
                        >
                            {testing ? (
                                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Testing…</>
                            ) : "Test Connection"}
                        </button>

                        {testResult && (
                            <div className={cn(
                                "mt-3 p-3 rounded-lg text-sm flex items-start border",
                                testResult.status === "success"
                                    ? "bg-nvidia-green/10 text-nvidia-green border-nvidia-green/30"
                                    : "bg-red-500/10 text-red-400 border-red-500/30"
                            )}>
                                {testResult.status === "success"
                                    ? <Check className="w-4 h-4 mr-2 mt-0.5 shrink-0" />
                                    : <AlertTriangle className="w-4 h-4 mr-2 mt-0.5 shrink-0" />
                                }
                                <span>{testResult.message}</span>
                            </div>
                        )}
                    </div>
                </div>
            </Dialog>
        </div>
    );
}
