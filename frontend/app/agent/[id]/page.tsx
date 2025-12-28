"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import {
    Save, Copy, Check, Database,
    Bot, FileText, Share2, ArrowLeft, Upload, Trash2, Play,
    Settings, MessageSquare, Sun, Moon, ChevronRight, Loader2,
    MoreHorizontal, Search, Plus, X
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import Dialog from "@/components/ui/Dialog";
import { useToast } from "@/components/ui/Toast";
import { useTheme } from "@/contexts/ThemeContext";

export default function AgentConfiguration({ params: paramsPromise }: { params: Promise<{ id: string }> }) {
    const params = use(paramsPromise);
    const router = useRouter();
    const { toast } = useToast();
    const [activeTab, setActiveTab] = useState("agent");
    const [agent, setAgent] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const { theme, toggleTheme } = useTheme();
    const isDark = theme === "dark";

    // Form State
    const [systemPrompt, setSystemPrompt] = useState("");
    const [firstMessage, setFirstMessage] = useState("");
    const [selectedLlmId, setSelectedLlmId] = useState("");
    const [selectedKBs, setSelectedKBs] = useState<string[]>([]);
    const [selectedDBs, setSelectedDBs] = useState<string[]>([]);

    // Resources State
    const [llmConfigs, setLlmConfigs] = useState<any[]>([]);
    const [availableKBs, setAvailableKBs] = useState<any[]>([]);
    const [availableDBs, setAvailableDBs] = useState<any[]>([]);

    // Dialog State
    const [dialogOpen, setDialogOpen] = useState(false);
    const [dialogConfig, setDialogConfig] = useState({
        title: "",
        description: "",
        buttons: [] as any[],
        children: null as React.ReactNode | null
    });

    const showDialog = (title: string, description: string, buttons: any[] = [], children: React.ReactNode = null) => {
        setDialogConfig({ title, description, buttons, children });
        setDialogOpen(true);
    };

    const closeDialog = () => setDialogOpen(false);

    // Share State
    const [copied, setCopied] = useState(false);

    // Add Resource State
    const [resourceToAdd, setResourceToAdd] = useState("");
    const [isUploading, setIsUploading] = useState(false);

    useEffect(() => {
        fetchAgentData();
    }, []);

    const fetchAgentData = async () => {
        try {
            const [agentRes, llmRes, kbRes, dbRes] = await Promise.all([
                api.get(`/agents/${params.id}`),
                api.get("/llm"),
                api.get("/kb"),
                api.get("/resources/databases")
            ]);

            setAgent(agentRes.data);
            setLlmConfigs(llmRes.data);
            setAvailableKBs(kbRes.data);
            setAvailableDBs(dbRes.data);

            // Set initial form state
            setSystemPrompt(agentRes.data.system_prompt || "You are a helpful AI assistant.");
            setFirstMessage(agentRes.data.first_message || "Hello! How can I help you today?");
            setSelectedLlmId(agentRes.data.llm_config_id || "");
            setSelectedKBs(agentRes.data.knowledge_bases?.map((kb: any) => kb.id) || []);
            setSelectedDBs(agentRes.data.database_connections?.map((db: any) => db.id) || []);

        } catch (error) {
            console.error("Failed to load agent", error);
            toast("Failed to load agent configuration", "error");
        } finally {
            setLoading(false);
        }
    };

    const saveChanges = async (updates: any = {}, showToast = true) => {
        if (!selectedLlmId && !updates.llm_config_id) {
            showDialog("Configuration Error", "You must select a Global LLM Configuration before saving the agent.", [{ label: "OK", onClick: closeDialog, variant: "primary" }]);
            return;
        }

        setSaving(true);
        try {
            // Merge current state with updates
            const payload = {
                system_prompt: systemPrompt,
                first_message: firstMessage,
                llm_config_id: selectedLlmId,
                kb_ids: selectedKBs,
                db_connection_ids: selectedDBs,
                ...updates
            };

            await api.put(`/agents/${params.id}`, payload);

            // Update local state if needed (for auto-saves that pass updates)
            if (updates.kb_ids) setSelectedKBs(updates.kb_ids);
            if (updates.db_connection_ids) setSelectedDBs(updates.db_connection_ids);

            if (showToast) toast("Changes saved successfully", "success");
        } catch (error) {
            console.error("Save failed", error);
            toast("Failed to save changes", "error");
        } finally {
            setSaving(false);
        }
    };

    const handleSaveAgent = () => saveChanges();

    const copyToClipboard = () => {
        const url = `${window.location.origin}/chat/${agent.share_token}`;
        navigator.clipboard.writeText(url);
        setCopied(true);
        toast("Link copied to clipboard", "success");
        setTimeout(() => setCopied(false), 2000);
    };

    const handleAddKB = () => {
        const unselectedKBs = availableKBs.filter(kb => !selectedKBs.includes(kb.id));
        setResourceToAdd(unselectedKBs.length > 0 ? unselectedKBs[0].id : "");
        setAddKBDialogOpen(true);
    };

    const [addKBDialogOpen, setAddKBDialogOpen] = useState(false);
    const [addDBDialogOpen, setAddDBDialogOpen] = useState(false);

    const confirmAddKB = async () => {
        if (resourceToAdd) {
            const newKBs = [...selectedKBs, resourceToAdd];
            // Auto-save
            await saveChanges({ kb_ids: newKBs });
            setAddKBDialogOpen(false);
            setResourceToAdd("");
        }
    };

    const removeKB = async (id: string) => {
        const newKBs = selectedKBs.filter(kbId => kbId !== id);
        await saveChanges({ kb_ids: newKBs });
    };

    const handleAddDB = () => {
        const unselectedDBs = availableDBs.filter(db => !selectedDBs.includes(db.id));
        setResourceToAdd(unselectedDBs.length > 0 ? unselectedDBs[0].id : "");
        setAddDBDialogOpen(true);
    };

    const confirmAddDB = async () => {
        if (resourceToAdd) {
            const newDBs = [...selectedDBs, resourceToAdd];
            await saveChanges({ db_connection_ids: newDBs });
            setAddDBDialogOpen(false);
            setResourceToAdd("");
        }
    };

    const removeDB = async (id: string) => {
        const newDBs = selectedDBs.filter(dbId => dbId !== id);
        await saveChanges({ db_connection_ids: newDBs });
    };


    const handleDeleteAgent = async () => {
        showDialog(
            "Delete Agent",
            "Are you sure you want to delete this agent? This action cannot be undone.",
            [
                { label: "Cancel", onClick: closeDialog, variant: "outline" },
                {
                    label: "Delete",
                    onClick: async () => {
                        try {
                            await api.delete(`/agents/${params.id}`);
                            toast("Agent deleted successfully", "success");
                            router.push("/dashboard/agents");
                        } catch (error) {
                            console.error("Delete failed", error);
                            toast("Failed to delete agent", "error");
                        } finally {
                            closeDialog();
                        }
                    },
                    variant: "danger"
                }
            ]
        );
    };

    const tabs = [
        { id: "agent", label: "Agent" },
        { id: "knowledge", label: "Knowledge Base" },
        { id: "advanced", label: "Advanced" },
    ];

    if (loading || !agent) return (
        <div className="flex h-screen items-center justify-center bg-white dark:bg-black text-[#76B900]">
            <Loader2 className="w-8 h-8 animate-spin" />
        </div>
    );

    return (
        <div className={cn(
            "flex flex-col h-screen font-sans transition-colors duration-300",
            isDark ? "bg-black text-white" : "bg-white text-gray-900"
        )}>
            {/* Header */}
            <header className={cn(
                "flex flex-col md:flex-row items-start md:items-center justify-between px-4 md:px-8 py-4 border-b sticky top-0 z-10 gap-4 transition-colors duration-300",
                isDark ? "bg-black/50 border-white/10 backdrop-blur-md" : "bg-white/80 border-gray-200 backdrop-blur-md"
            )}>
                <div className="flex items-center justify-between w-full md:w-auto">
                    <div className="flex items-center space-x-4">
                        <Link href="/dashboard/agents" className={cn("transition-colors", isDark ? "text-gray-400 hover:text-white" : "text-gray-600 hover:text-gray-900")}>
                            <ArrowLeft className="w-5 h-5" />
                        </Link>
                        <div>
                            <div className="flex items-center space-x-2">
                                <h1 className={cn("text-xl font-bold truncate max-w-[150px] md:max-w-none", isDark ? "text-white" : "text-gray-900")}>{agent.name}</h1>
                                <span className={cn("px-2 py-0.5 text-[10px] font-medium rounded-full shrink-0", isDark ? "bg-gray-800 text-gray-400" : "bg-gray-100 text-gray-500")}>
                                    {agent.is_public ? "Public" : "Private"}
                                </span>
                            </div>
                            <p className="text-[10px] text-gray-500 font-mono mt-0.5">agent_{agent.id}</p>
                        </div>
                    </div>

                    {/* Mobile Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        className={cn("md:hidden p-2 rounded-lg transition-colors", isDark ? "text-gray-400 hover:text-white hover:bg-white/5" : "text-gray-600 hover:text-gray-900 hover:bg-gray-100")}
                    >
                        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                    </button>
                </div>

                <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
                    <button
                        onClick={handleSaveAgent}
                        disabled={saving}
                        className="flex-1 md:flex-none justify-center px-4 py-2 bg-[#76B900] text-black text-sm font-bold rounded-lg hover:bg-[#6aa600] transition-all flex items-center shadow-[0_0_15px_rgba(118,185,0,0.3)] disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                        {saving ? "Saving..." : "Save Changes"}
                    </button>

                    <div className={cn("hidden md:block h-6 w-px mx-2", isDark ? "bg-white/10" : "bg-gray-200")}></div>

                    <button
                        onClick={copyToClipboard}
                        className={cn("flex-1 md:flex-none justify-center px-3 py-2 text-sm font-medium rounded-lg transition-colors flex items-center whitespace-nowrap", isDark ? "text-gray-300 hover:bg-white/5" : "text-gray-600 hover:bg-gray-100")}
                    >
                        <Copy className="w-4 h-4 mr-2" />
                        {copied ? "Copied" : "Copy link"}
                    </button>

                    <button
                        onClick={() => {
                            if (!selectedLlmId) {
                                toast("Configuration Error", "error");
                                showDialog("Configuration Error", "You must select a Global LLM Configuration before previewing the agent.", [{ label: "OK", onClick: closeDialog, variant: "primary" }]);
                                return;
                            }
                            window.open(`/chat/${agent.share_token}?new=true`, '_blank');
                        }}
                        disabled={!selectedLlmId}
                        className={cn("flex-1 md:flex-none justify-center px-4 py-2 text-sm font-bold rounded-lg transition-all flex items-center disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap", isDark ? "bg-white/10 text-white hover:bg-white/20" : "bg-gray-200 text-gray-900 hover:bg-gray-300")}
                    >
                        Preview
                    </button>

                    {/* Desktop Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        className={cn("hidden md:flex p-2 rounded-lg transition-colors ml-2", isDark ? "text-gray-400 hover:text-white hover:bg-white/5" : "text-gray-600 hover:text-gray-900 hover:bg-gray-100")}
                    >
                        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                    </button>
                </div>
            </header>

            {/* Tabs */}
            <div className={cn("px-4 md:px-8 border-b overflow-x-auto", isDark ? "border-white/10" : "border-gray-200")}>
                <div className="flex space-x-6 min-w-max">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "py-3 text-sm font-medium border-b-2 transition-colors relative whitespace-nowrap",
                                activeTab === tab.id
                                    ? "border-[#76B900] text-[#76B900]"
                                    : cn("border-transparent", isDark ? "text-gray-500 hover:text-gray-300" : "text-gray-500 hover:text-gray-700")
                            )}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className={cn("flex-1 overflow-y-auto p-4 md:p-8", isDark ? "bg-[#0A0A0A]" : "bg-gray-50")}>
                <div className="max-w-6xl mx-auto">
                    {activeTab === "agent" && (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Left Column */}
                            <div className="lg:col-span-2 space-y-6">
                                {/* System Prompt */}
                                <div className={cn("rounded-xl border p-1 shadow-sm", isDark ? "bg-[#111] border-white/10" : "bg-white border-gray-200")}>
                                    <div className={cn("flex items-center justify-between px-4 py-3 border-b", isDark ? "border-white/10" : "border-gray-100")}>
                                        <div className="flex items-center space-x-2">
                                            <span className={cn("text-sm font-medium", isDark ? "text-white" : "text-gray-900")}>System Prompt</span>
                                        </div>
                                    </div>
                                    <div className="p-4">
                                        <textarea
                                            value={systemPrompt}
                                            onChange={(e) => setSystemPrompt(e.target.value)}
                                            placeholder="Enter the system prompt for your agent..."
                                            className={cn("w-full h-64 bg-transparent border-none focus:ring-0 text-sm resize-none placeholder-gray-400", isDark ? "text-gray-200" : "text-gray-800")}
                                        />
                                    </div>
                                    <div className={cn("px-4 py-3 border-t flex items-center justify-between rounded-b-xl", isDark ? "border-white/10 bg-black/20" : "border-gray-100 bg-gray-50/50")}>
                                        <div className="flex items-center space-x-2">
                                            <span className="text-xs text-gray-500">Type {"{{"} to add variables</span>
                                        </div>
                                    </div>
                                </div>

                                {/* First Message */}
                                <div className="space-y-2">
                                    <h3 className={cn("text-sm font-medium", isDark ? "text-white" : "text-gray-900")}>First message</h3>
                                    <p className="text-xs text-gray-500">The first message the agent will say. If empty, the agent will wait for the user to start the conversation.</p>
                                    <div className={cn("rounded-xl border p-1 shadow-sm", isDark ? "bg-[#111] border-white/10" : "bg-white border-gray-200")}>
                                        <div className="p-4">
                                            <textarea
                                                value={firstMessage}
                                                onChange={(e) => setFirstMessage(e.target.value)}
                                                placeholder="e.g. Hello, how can I help you today?"
                                                className={cn("w-full h-24 bg-transparent border-none focus:ring-0 text-sm resize-none placeholder-gray-400", isDark ? "text-gray-200" : "text-gray-800")}
                                            />
                                        </div>
                                        <div className={cn("px-4 py-3 border-t flex items-center justify-between rounded-b-xl", isDark ? "border-white/10 bg-black/20" : "border-gray-100 bg-gray-50/50")}>
                                            <span className="text-xs text-gray-500">Type {"{{"} to add variables</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Right Column */}
                            <div className="space-y-6">
                                {/* LLM Selection */}
                                <div className="space-y-2">
                                    <h3 className={cn("text-sm font-medium", isDark ? "text-white" : "text-gray-900")}>LLM</h3>
                                    <p className="text-xs text-gray-500">Select which provider and model to use for the LLM.</p>
                                    <div className={cn("rounded-xl border overflow-hidden", isDark ? "bg-[#111] border-white/10" : "bg-white border-gray-200")}>
                                        <select
                                            value={selectedLlmId}
                                            onChange={(e) => setSelectedLlmId(e.target.value)}
                                            className={cn("w-full p-4 bg-transparent border-none focus:ring-0 text-sm appearance-none cursor-pointer transition-colors", isDark ? "text-white hover:bg-gray-900" : "text-gray-900 hover:bg-gray-50")}
                                        >
                                            <option value="" disabled>Select LLM Configuration</option>
                                            {llmConfigs.map((config) => (
                                                <option key={config.id} value={config.id}>
                                                    {config.name} ({config.model})
                                                </option>
                                            ))}
                                        </select>
                                        <div className={cn("px-4 py-3 border-t", isDark ? "bg-black/20 border-white/10" : "bg-gray-50/50 border-gray-100")}>
                                            <Link href="/dashboard/llm" className="text-xs text-gray-500 hover:text-[#76B900] flex items-center">
                                                <Plus className="w-3 h-3 mr-1" /> Add new LLM
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === "knowledge" && (
                        <div className="space-y-8">
                            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                                <h2 className={cn("text-lg font-bold", isDark ? "text-white" : "text-gray-900")}>Agent Knowledge Base</h2>
                                <button
                                    onClick={handleAddKB}
                                    className="w-full sm:w-auto px-4 py-2 bg-[#76B900] text-black text-sm font-bold rounded-lg hover:bg-[#6aa600] transition-colors flex items-center justify-center shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                                >
                                    <Plus className="w-4 h-4 mr-2" /> Add Knowledge Base
                                </button>
                            </div>

                            <div className={cn("rounded-xl border overflow-hidden", isDark ? "bg-[#111] border-white/10" : "bg-white border-gray-200")}>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-sm">
                                        <thead>
                                            <tr className={cn("border-b", isDark ? "border-white/10 bg-black/20" : "border-gray-200 bg-gray-50/50")}>
                                                <th className="px-6 py-3 font-medium text-gray-500">Name</th>
                                                <th className="px-6 py-3 font-medium text-gray-500">Type</th>
                                                <th className="px-6 py-3 font-medium text-gray-500">Status</th>
                                                <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className={cn("divide-y", isDark ? "divide-white/10" : "divide-gray-200")}>
                                            {availableKBs.filter(kb => selectedKBs.includes(kb.id)).map((kb) => (
                                                <tr key={kb.id} className={cn("transition-colors", isDark ? "hover:bg-gray-900/50" : "hover:bg-gray-50")}>
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center">
                                                            <FileText className="w-4 h-4 text-gray-400 mr-3" />
                                                            <span className={cn("font-medium", isDark ? "text-white" : "text-gray-900")}>{kb.name || kb.filename}</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 text-gray-500">{kb.file_type || "Document"}</td>
                                                    <td className="px-6 py-4">
                                                        <span className={cn(
                                                            "px-2 py-1 rounded-full text-xs font-medium",
                                                            kb.status === "indexed" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                                                        )}>
                                                            {kb.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <button
                                                            onClick={() => removeKB(kb.id)}
                                                            className="text-gray-400 hover:text-red-500 transition-colors"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                            {selectedKBs.length === 0 && (
                                                <tr>
                                                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                                                        No knowledge bases linked. Click "Add Knowledge Base" to link one.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Database Connections Section */}
                            <div className="mt-8">
                                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
                                    <h3 className={cn("text-lg font-bold", isDark ? "text-white" : "text-gray-900")}>Database Connections</h3>
                                    <button
                                        onClick={handleAddDB}
                                        className="w-full sm:w-auto px-4 py-2 bg-[#76B900] text-black text-sm font-bold rounded-lg hover:bg-[#6aa600] transition-colors flex items-center justify-center shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                                    >
                                        <Plus className="w-4 h-4 mr-2" /> Add Database
                                    </button>
                                </div>
                                <div className={cn("rounded-xl border overflow-hidden", isDark ? "bg-[#111] border-white/10" : "bg-white border-gray-200")}>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left text-sm">
                                            <thead>
                                                <tr className={cn("border-b", isDark ? "border-white/10 bg-black/20" : "border-gray-200 bg-gray-50/50")}>
                                                    <th className="px-6 py-3 font-medium text-gray-500">Name</th>
                                                    <th className="px-6 py-3 font-medium text-gray-500">Type</th>
                                                    <th className="px-6 py-3 font-medium text-gray-500">Host</th>
                                                    <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody className={cn("divide-y", isDark ? "divide-white/10" : "divide-gray-200")}>
                                                {availableDBs.filter(db => selectedDBs.includes(db.id)).map((db) => (
                                                    <tr key={db.id} className={cn("transition-colors", isDark ? "hover:bg-gray-900/50" : "hover:bg-gray-50")}>
                                                        <td className="px-6 py-4">
                                                            <div className="flex items-center">
                                                                <Database className="w-4 h-4 text-gray-400 mr-3" />
                                                                <span className={cn("font-medium", isDark ? "text-white" : "text-gray-900")}>{db.name}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 text-gray-500 uppercase">{db.type}</td>
                                                        <td className="px-6 py-4 text-gray-500">{db.host}</td>
                                                        <td className="px-6 py-4 text-right">
                                                            <button
                                                                onClick={() => removeDB(db.id)}
                                                                className="text-gray-400 hover:text-red-500 transition-colors"
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                                {selectedDBs.length === 0 && (
                                                    <tr>
                                                        <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                                                            No database connections linked. Click "Add Database" to link one.
                                                        </td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === "advanced" && (
                        <div className="max-w-2xl mx-auto space-y-8">
                            <div className={cn("border rounded-xl p-6", isDark ? "bg-red-900/10 border-red-900" : "bg-red-50 border-red-200")}>
                                <h3 className={cn("text-lg font-bold mb-2", isDark ? "text-red-400" : "text-red-700")}>Danger Zone</h3>
                                <p className={cn("text-sm mb-4", isDark ? "text-red-300" : "text-red-600")}>
                                    Deleting this agent will permanently remove it and all associated chat history. This action cannot be undone.
                                </p>
                                <button
                                    onClick={handleDeleteAgent}
                                    className="px-4 py-2 bg-red-600 text-white font-bold rounded-lg hover:bg-red-700 transition-colors"
                                >
                                    Delete Agent
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Generic Alert Dialog */}
            <Dialog
                isOpen={dialogOpen}
                onClose={closeDialog}
                title={dialogConfig.title}
                description={dialogConfig.description}
                buttons={dialogConfig.buttons}
                theme={theme}
            >
                {dialogConfig.children}
            </Dialog>

            {/* Add KB Dialog */}
            <Dialog
                isOpen={addKBDialogOpen}
                onClose={() => setAddKBDialogOpen(false)}
                title="Add Knowledge Base"
                description="Link an existing Knowledge Base."
                theme={theme}
                buttons={[
                    { label: "Add Selected", onClick: confirmAddKB, variant: "primary" },
                    { label: "Cancel", onClick: () => setAddKBDialogOpen(false), variant: "outline" }
                ]}
            >
                <div className="space-y-6">
                    {/* Select Existing */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Select Existing KB</label>
                        <select
                            value={resourceToAdd}
                            onChange={(e) => setResourceToAdd(e.target.value)}
                            className="w-full p-3 bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-gray-800 rounded-xl text-sm focus:ring-2 focus:ring-[#76B900] outline-none"
                        >
                            <option value="">Select a Knowledge Base...</option>
                            {availableKBs.filter(kb => !selectedKBs.includes(kb.id)).map(kb => (
                                <option key={kb.id} value={kb.id}>{kb.name || kb.filename}</option>
                            ))}
                        </select>
                        {availableKBs.filter(kb => !selectedKBs.includes(kb.id)).length === 0 && (
                            <p className="text-xs text-gray-500">No unlinked knowledge bases available.</p>
                        )}
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl">
                        <p className="text-sm text-blue-600 dark:text-blue-400">
                            To upload new documents, please visit the <Link href="/dashboard/kb" className="underline font-bold">Knowledge Base</Link> section.
                        </p>
                    </div>
                </div>
            </Dialog>

            {/* Add DB Dialog */}
            <Dialog
                isOpen={addDBDialogOpen}
                onClose={() => setAddDBDialogOpen(false)}
                title="Add Database Connection"
                description="Link an existing Database Connection."
                theme={theme}
                buttons={[
                    { label: "Add Selected", onClick: confirmAddDB, variant: "primary" },
                    { label: "Cancel", onClick: () => setAddDBDialogOpen(false), variant: "outline" }
                ]}
            >
                <div className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Select Existing Connection</label>
                        <select
                            value={resourceToAdd}
                            onChange={(e) => setResourceToAdd(e.target.value)}
                            className="w-full p-3 bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-gray-800 rounded-xl text-sm focus:ring-2 focus:ring-[#76B900] outline-none"
                        >
                            <option value="">Select a Database...</option>
                            {availableDBs.filter(db => !selectedDBs.includes(db.id)).map(db => (
                                <option key={db.id} value={db.id}>{db.name} ({db.type})</option>
                            ))}
                        </select>
                        {availableDBs.filter(db => !selectedDBs.includes(db.id)).length === 0 && (
                            <p className="text-xs text-gray-500">No unlinked database connections available.</p>
                        )}
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl">
                        <p className="text-sm text-blue-600 dark:text-blue-400">
                            To create a new database connection, please visit the <Link href="/dashboard/kb" className="underline font-bold">Knowledge Base</Link> section.
                        </p>
                    </div>
                </div>
            </Dialog>
        </div>
    );
}
