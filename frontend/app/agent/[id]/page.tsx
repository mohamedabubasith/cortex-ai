"use client";

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

export default function AgentConfiguration({ params: paramsPromise }: { params: Promise<{ id: string }> }) {
    const params = use(paramsPromise);
    const router = useRouter();
    const { toast } = useToast();
    const [activeTab, setActiveTab] = useState("agent");
    const [agent, setAgent] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [theme, setTheme] = useState<"dark" | "light">("dark");

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
                api.get("/llm/"),
                api.get("/kb/"),
                api.get("/resources/databases/")
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


    if (loading) return (
        <div className="flex h-screen items-center justify-center bg-white dark:bg-black text-[#76B900]">
            <Loader2 className="w-8 h-8 animate-spin" />
        </div>
    );

    const tabs = [
        { id: "agent", label: "Agent" },
        { id: "knowledge", label: "Knowledge Base" },
        { id: "advanced", label: "Advanced" },
    ];

    return (
        <div className={cn(
            "flex flex-col h-screen font-sans transition-colors duration-300",
            theme === 'dark' ? "bg-black text-white" : "bg-white text-gray-900"
        )}>
            {/* Header */}
            <header className="flex items-center justify-between px-8 py-4 border-b border-gray-200 dark:border-gray-800 bg-black/50 backdrop-blur-sm sticky top-0 z-10">
                <div className="flex items-center space-x-4">
                    <Link href="/dashboard/agents" className="text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <div className="flex items-center space-x-2">
                            <h1 className="text-xl font-bold">{agent.name}</h1>
                            <span className="px-2 py-0.5 text-[10px] font-medium bg-gray-100 dark:bg-gray-800 text-gray-500 rounded-full">
                                {agent.is_public ? "Public" : "Private"}
                            </span>
                        </div>
                        <p className="text-xs text-gray-500 font-mono mt-0.5">agent_{agent.id}</p>
                    </div>
                </div>
                <div className="flex items-center space-x-3">
                    <button
                        onClick={handleSaveAgent}
                        disabled={saving}
                        className="px-4 py-2 bg-[#76B900] text-black text-sm font-bold rounded-lg hover:bg-[#6aa600] transition-all flex items-center shadow-[0_0_15px_rgba(118,185,0,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                        {saving ? "Saving..." : "Save Changes"}
                    </button>
                    <div className="h-6 w-px bg-gray-800 mx-2"></div>
                    <button
                        onClick={copyToClipboard}
                        className="px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors flex items-center"
                    >
                        <Copy className="w-4 h-4 mr-2" />
                        {copied ? "Copied" : "Copy link"}
                    </button>
                    <button
                        onClick={() => window.open(`/chat/${agent.share_token}`, '_blank')}
                        className="px-4 py-1.5 bg-white/10 text-white text-sm font-bold rounded-lg hover:bg-white/20 transition-all flex items-center"
                    >
                        Preview Agent
                    </button>
                </div>
            </header>

            {/* Tabs */}
            <div className="px-8 border-b border-gray-200 dark:border-gray-800">
                <div className="flex space-x-6">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "py-3 text-sm font-medium border-b-2 transition-colors relative",
                                activeTab === tab.id
                                    ? "border-[#76B900] text-[#76B900]"
                                    : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                            )}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8 bg-gray-50 dark:bg-[#0A0A0A]">
                <div className="max-w-6xl mx-auto">
                    {activeTab === "agent" && (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Left Column */}
                            <div className="lg:col-span-2 space-y-6">
                                {/* System Prompt */}
                                <div className="bg-white dark:bg-[#111] rounded-xl border border-gray-200 dark:border-gray-800 p-1 shadow-sm">
                                    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-sm font-medium text-gray-900 dark:text-white">System Prompt</span>
                                        </div>
                                    </div>
                                    <div className="p-4">
                                        <textarea
                                            value={systemPrompt}
                                            onChange={(e) => setSystemPrompt(e.target.value)}
                                            placeholder="Enter the system prompt for your agent..."
                                            className="w-full h-64 bg-transparent border-none focus:ring-0 text-sm resize-none text-gray-800 dark:text-gray-200 placeholder-gray-400"
                                        />
                                    </div>
                                    <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between bg-gray-50/50 dark:bg-black/20 rounded-b-xl">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-xs text-gray-500">Type {"{{"} to add variables</span>
                                        </div>
                                    </div>
                                </div>

                                {/* First Message */}
                                <div className="space-y-2">
                                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">First message</h3>
                                    <p className="text-xs text-gray-500">The first message the agent will say. If empty, the agent will wait for the user to start the conversation.</p>
                                    <div className="bg-white dark:bg-[#111] rounded-xl border border-gray-200 dark:border-gray-800 p-1 shadow-sm">
                                        <div className="p-4">
                                            <textarea
                                                value={firstMessage}
                                                onChange={(e) => setFirstMessage(e.target.value)}
                                                placeholder="e.g. Hello, how can I help you today?"
                                                className="w-full h-24 bg-transparent border-none focus:ring-0 text-sm resize-none text-gray-800 dark:text-gray-200 placeholder-gray-400"
                                            />
                                        </div>
                                        <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between bg-gray-50/50 dark:bg-black/20 rounded-b-xl">
                                            <span className="text-xs text-gray-500">Type {"{{"} to add variables</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Right Column */}
                            <div className="space-y-6">
                                {/* LLM Selection */}
                                <div className="space-y-2">
                                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">LLM</h3>
                                    <p className="text-xs text-gray-500">Select which provider and model to use for the LLM.</p>
                                    <div className="bg-white dark:bg-[#111] rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
                                        <select
                                            value={selectedLlmId}
                                            onChange={(e) => setSelectedLlmId(e.target.value)}
                                            className="w-full p-4 bg-transparent border-none focus:ring-0 text-sm text-gray-900 dark:text-white appearance-none cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                                        >
                                            <option value="" disabled>Select LLM Configuration</option>
                                            {llmConfigs.map((config) => (
                                                <option key={config.id} value={config.id}>
                                                    {config.name} ({config.model})
                                                </option>
                                            ))}
                                        </select>
                                        <div className="px-4 py-3 bg-gray-50/50 dark:bg-black/20 border-t border-gray-100 dark:border-gray-800">
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
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Agent Knowledge Base</h2>
                                <button
                                    onClick={handleAddKB}
                                    className="px-4 py-2 bg-[#76B900] text-black text-sm font-bold rounded-lg hover:bg-[#6aa600] transition-colors flex items-center shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                                >
                                    <Plus className="w-4 h-4 mr-2" /> Add Knowledge Base
                                </button>
                            </div>

                            <div className="bg-white dark:bg-[#111] rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-sm">
                                        <thead>
                                            <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-black/20">
                                                <th className="px-6 py-3 font-medium text-gray-500">Name</th>
                                                <th className="px-6 py-3 font-medium text-gray-500">Type</th>
                                                <th className="px-6 py-3 font-medium text-gray-500">Status</th>
                                                <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                                            {availableKBs.filter(kb => selectedKBs.includes(kb.id)).map((kb) => (
                                                <tr key={kb.id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center">
                                                            <FileText className="w-4 h-4 text-gray-400 mr-3" />
                                                            <span className="font-medium text-gray-900 dark:text-white">{kb.name || kb.filename}</span>
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
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">Database Connections</h3>
                                    <button
                                        onClick={handleAddDB}
                                        className="px-4 py-2 bg-[#76B900] text-black text-sm font-bold rounded-lg hover:bg-[#6aa600] transition-colors flex items-center shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                                    >
                                        <Plus className="w-4 h-4 mr-2" /> Add Database
                                    </button>
                                </div>
                                <div className="bg-white dark:bg-[#111] rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left text-sm">
                                            <thead>
                                                <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-black/20">
                                                    <th className="px-6 py-3 font-medium text-gray-500">Name</th>
                                                    <th className="px-6 py-3 font-medium text-gray-500">Type</th>
                                                    <th className="px-6 py-3 font-medium text-gray-500">Host</th>
                                                    <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                                                {availableDBs.filter(db => selectedDBs.includes(db.id)).map((db) => (
                                                    <tr key={db.id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                                                        <td className="px-6 py-4">
                                                            <div className="flex items-center">
                                                                <Database className="w-4 h-4 text-gray-400 mr-3" />
                                                                <span className="font-medium text-gray-900 dark:text-white">{db.name}</span>
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
                            <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900 rounded-xl p-6">
                                <h3 className="text-lg font-bold text-red-700 dark:text-red-400 mb-2">Danger Zone</h3>
                                <p className="text-sm text-red-600 dark:text-red-300 mb-4">
                                    Deleting this agent will permanently remove it and all associated chat history. This action cannot be undone.
                                </p>
                                <button className="px-4 py-2 bg-red-600 text-white font-bold rounded-lg hover:bg-red-700 transition-colors">
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
