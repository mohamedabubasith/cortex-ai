"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Database, FileText, Trash2, Loader2, Plus, Upload, Search, X, Edit, Check, AlertTriangle, Server, RefreshCw, Link, Sparkles } from "lucide-react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import Dialog from "@/components/ui/Dialog";
import SidePanel from "@/components/ui/SidePanel";
import ShareResourceModal from "@/components/ShareResourceModal";
import ResourceMenu from "@/components/ResourceMenu";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import CustomDropdown from "@/components/ui/CustomDropdown";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import { Label } from "@/components/ui/Label";

interface KnowledgeBase {
    id: string;
    name: string;
    file_type: string;
    status: string;
    created_at: string;
    tenant_id?: string;
}

interface DatabaseConnection {
    id: string;
    name: string;
    type: string;
    host: string;
    port: number;
    username: string;
    database_name: string;
    status: string;
    ssl_mode?: string;
    tenant_id?: string;
}

interface MCPConnection {
    id: string;
    name: string;
    server_url: string;
    summary: string;
    status?: string;
}

export default function KnowledgeBasePage() {
    const { toast } = useToast();
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [activeTab, setActiveTab] = useState<'documents' | 'databases'>('documents');
    const [kbFiles, setKbFiles] = useState<KnowledgeBase[]>([]);
    const [dbConnections, setDbConnections] = useState<DatabaseConnection[]>([]);
    const [loading, setLoading] = useState(true);

    // Upload State
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    // DB Connection State
    const [isDbOpen, setIsDbOpen] = useState(false);
    const [connecting, setConnecting] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null);
    const [currentDb, setCurrentDb] = useState<any>({
        name: "",
        type: "postgres",
        host: "localhost",
        port: 5432,
        username: "",
        password: "",
        database_name: "",
        ssl_mode: "disable"
    });

    // Delete State
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [itemToDelete, setItemToDelete] = useState<{ id: string, type: 'kb' | 'db' } | null>(null);

    // Query State
    const [queryDialogOpen, setQueryDialogOpen] = useState(false);
    const [queryDocId, setQueryDocId] = useState<string | null>(null);
    const [queryText, setQueryText] = useState("");
    const [queryResults, setQueryResults] = useState<any[] | null>(null);
    const [queryMeta, setQueryMeta] = useState<any>(null);
    const [querying, setQuerying] = useState(false);
    const [llmConfigs, setLlmConfigs] = useState<any[]>([]);
    const [selectedLlmId, setSelectedLlmId] = useState<string>("");

    // Share State
    const [shareModalOpen, setShareModalOpen] = useState(false);
    const [resourceToShare, setResourceToShare] = useState<{ id: string; name: string; type: "knowledge_base" | "database_connection"; tenant_id?: string } | null>(null);


    useEffect(() => {
        fetchResources();
        fetchLLMs();
    }, []);

    const [processingFiles, setProcessingFiles] = useState<Set<string>>(new Set());

    // Polling for status updates with exponential backoff
    useEffect(() => {
        const filesToPoll = kbFiles.filter(f =>
            ['pending', 'processing', 'indexing', 'initiated', 'unknown'].includes(f.status || '') || !f.status
        );

        if (filesToPoll.length === 0) return;

        let timeoutId: NodeJS.Timeout;

        const poll = async () => {
            let updated = false;
            const newFiles = [...kbFiles];

            await Promise.all(filesToPoll.map(async (file) => {
                try {
                    const res = await api.get(`/kb/${file.id}/status`);
                    const newStatus = res.data?.status || 'processing';

                    if (newStatus !== file.status) {
                        const index = newFiles.findIndex(f => f.id === file.id);
                        if (index !== -1) {
                            newFiles[index] = { ...newFiles[index], status: newStatus };
                            updated = true;
                        }
                    }
                } catch (error) {
                    console.error(`Failed to poll status for ${file.id}`, error);
                }
            }));

            if (updated) {
                setKbFiles(newFiles);
            }

            // Continue polling only if there are still processing files
            const stillProcessing = newFiles.some(f =>
                ['pending', 'processing', 'indexing', 'initiated', 'unknown'].includes(f.status || '') || !f.status
            );

            if (stillProcessing) {
                timeoutId = setTimeout(poll, 3000); // Poll every 3 seconds
            }
        };

        poll();

        return () => clearTimeout(timeoutId);
    }, [kbFiles.length]); // Only reset polling when file count changes (e.g. new upload)

    const fetchLLMs = async () => {
        try {
            const res = await api.get("/llm");
            setLlmConfigs(res.data);
            if (res.data.length > 0) setSelectedLlmId(res.data[0].id);
        } catch (error) {
            console.error("Failed to fetch LLMs", error);
            toast("Failed to fetch LLM configurations", "error");
        }
    };

    const fetchResources = async () => {
        setLoading(true);
        try {
            const [kbRes, dbRes] = await Promise.all([
                api.get("/kb"),
                api.get("/resources/databases")
            ]);
            setKbFiles(kbRes.data);
            setDbConnections(dbRes.data);
        } catch (error) {
            console.error("Failed to fetch resources", error);
            toast("Failed to fetch resources", "error");
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedFile) return;

        setUploading(true);
        const formData = new FormData();
        formData.append("file", selectedFile);
        if (selectedLlmId) {
            formData.append("llm_config_id", selectedLlmId);
        }

        try {
            await api.post("/kb/upload", formData);
            toast("File uploaded successfully. Processing started.", "success");
            setIsUploadOpen(false);
            setSelectedFile(null);
            fetchResources(); // This triggers the polling effect
        } catch (error: any) {
            console.error("Upload failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Upload failed. Please try again.";
            toast(errorMessage, "error");
        } finally {
            setUploading(false);
        }
    };

    const handleOpenDbDialog = (db: any = null) => {
        if (db) {
            // Edit mode: populate with existing data, password empty
            setCurrentDb({ ...db, password: "" });
        } else {
            // Create mode: reset to default
            setCurrentDb({
                name: "",
                type: "postgres",
                host: "localhost",
                port: 5432,
                username: "",
                password: "",
                database_name: "",
                ssl_mode: "disable"
            });
        }
        setTestResult(null);
        setIsDbOpen(true);
    };

    const handleTestDb = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            // Testing the form values (Create or Edit)
            const res = await api.post("/resources/databases/test", currentDb);
            setTestResult(res.data);
            if (res.data.status === "success") {
                toast("Connection test successful!", "success");
            } else {
                toast("Connection test failed", "error");
            }
        } catch (error: any) {
            console.error("Test failed", error);
            const errorMessage = error.response?.data?.message || error.message || "Test failed. Please check your credentials.";
            setTestResult({ status: "failed", message: errorMessage });
            toast(errorMessage, "error");
        } finally {
            setTesting(false);
        }
    };

    const handleSaveDb = async () => {
        setConnecting(true);
        try {
            if (currentDb.id) {
                // Update
                const updateData: any = {};
                // Send all fields for simplicity, backend handles update logic
                updateData.name = currentDb.name;
                updateData.type = currentDb.type;
                updateData.host = currentDb.host;
                updateData.port = currentDb.port;
                updateData.username = currentDb.username;
                updateData.database_name = currentDb.database_name;
                updateData.ssl_mode = currentDb.ssl_mode;
                if (currentDb.password && currentDb.password.trim() !== "") {
                    updateData.password = currentDb.password;
                }

                await api.put(`/resources/databases/${currentDb.id}`, updateData);
                toast("Database connection updated successfully", "success");
            } else {
                // Create
                await api.post("/resources/databases", currentDb);
                toast("Database connected successfully", "success");
            }

            setIsDbOpen(false);
            setTestResult(null);
            fetchResources();
        } catch (error: any) {
            console.error("DB Save failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Connection failed.";
            toast(errorMessage, "error");
        } finally {
            setConnecting(false);
        }
    };



    const confirmDelete = (id: string, type: 'kb' | 'db') => {
        setItemToDelete({ id, type });
        setDeleteDialogOpen(true);
    };

    const handleDelete = async () => {
        if (!itemToDelete) return;
        try {
            if (itemToDelete.type === 'kb') {
                await api.delete(`/kb/${itemToDelete.id}`);
                toast("Document deleted successfully", "success");
            } else {
                await api.delete(`/resources/databases/${itemToDelete.id}`);
                toast("Database connection deleted successfully", "success");
            }
            fetchResources();
        } catch (error) {
            console.error("Delete failed", error);
            toast("Delete failed. Please try again.", "error");
        } finally {
            setDeleteDialogOpen(false);
            setItemToDelete(null);
        }
    };

    const openQueryDialog = (docId: string) => {
        setQueryDocId(docId);
        setQueryText("");
        setQueryResults(null);
        setQueryDialogOpen(true);
    };

    const handleQuery = async () => {
        if (!queryText || !selectedLlmId) return;
        setQuerying(true);
        try {
            const res = await api.post(`/kb/${queryDocId}/query`, {
                query: queryText,
                llm_config_id: selectedLlmId
            });

            setQueryMeta(res.data.meta || null);

            if (res.data.success && Array.isArray(res.data.results)) {
                // Standard LangChain Service Response
                setQueryResults(res.data.results);
            } else if (res.data.success && Array.isArray(res.data.data)) {
                // Handle Cognee structure where results are nested in search_result
                const results = res.data.data.flatMap((item: any) => {
                    if (item.search_result && Array.isArray(item.search_result)) {
                        return item.search_result;
                    }
                    return item;
                });
                setQueryResults(results);
            } else if (res.data.answer) {
                // Fallback
                setQueryResults([{ text: res.data.answer }]);
            } else {
                setQueryResults([{ text: JSON.stringify(res.data, null, 2) }]);
            }
        } catch (error) {
            console.error("Query failed", error);
            setQueryResults([{ text: "Error querying document." }]);
        } finally {
            setQuerying(false);
        }
    };

    return (
        <div className="space-y-8 relative">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-2xl md:text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>Knowledge Base</h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>Manage documents and database connections.</p>
                </div>
                <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3 w-full md:w-auto">
                    <button
                        onClick={() => setIsUploadOpen(true)}
                        className="flex items-center justify-center px-4 py-2 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all"
                    >
                        <Upload className="w-5 h-5 mr-2" />
                        Upload Document
                    </button>
                    <button
                        onClick={() => setIsDbOpen(true)}
                        className={cn("flex items-center justify-center px-4 py-2 font-bold rounded-lg transition-all", isDark ? "bg-white/10 text-white hover:bg-white/20" : "bg-gray-200 text-gray-900 hover:bg-gray-300")}
                    >
                        <Database className="w-5 h-5 mr-2" />
                        Add Database
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className={cn("flex space-x-6 border-b overflow-x-auto whitespace-nowrap pb-1", isDark ? "border-white/10" : "border-gray-200")}>
                <button
                    onClick={() => setActiveTab('documents')}
                    className={`pb-4 text-base md:text-sm font-bold transition-colors relative ${activeTab === 'documents' ? 'text-nvidia-green' : 'text-gray-400 hover:text-white'}`}
                >
                    Documents
                    {activeTab === 'documents' && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-nvidia-green rounded-t-full" />
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('databases')}
                    className={`pb-4 text-base md:text-sm font-bold transition-colors relative ${activeTab === 'databases' ? 'text-nvidia-green' : isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
                >
                    Databases
                    {activeTab === 'databases' && (
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
                    {activeTab === 'documents' ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {kbFiles.map((file) => (
                                <div key={file.id} className={cn("backdrop-blur-sm border rounded-xl p-6 transition-all group", isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm")}>
                                    <div className="flex justify-between items-start mb-4">
                                        <div className={cn("p-3 rounded-lg transition-colors", isDark ? "bg-white/5 group-hover:bg-nvidia-green/10" : "bg-gray-100 group-hover:bg-nvidia-green/10")}>
                                            <FileText className={cn("w-6 h-6 transition-colors", isDark ? "text-gray-400 group-hover:text-nvidia-green" : "text-gray-600 group-hover:text-nvidia-green")} />
                                        </div>
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={() => openQueryDialog(file.id)}
                                                disabled={file.status !== 'ready' && file.status !== 'indexed'}
                                                className={cn(
                                                    "transition-colors p-1 rounded-md",
                                                    (file.status === 'ready' || file.status === 'indexed')
                                                        ? "text-gray-500 hover:text-white hover:bg-white/10"
                                                        : "text-gray-600 opacity-40 cursor-not-allowed"
                                                )}
                                                title={(file.status === 'ready' || file.status === 'indexed') ? "Query Document" : "Processing in progress..."}
                                            >
                                                <Search className="w-4 h-4" />
                                            </button>
                                            <ResourceMenu
                                                isDark={isDark}
                                                resourceType="Document"
                                                onShare={() => {
                                                    setResourceToShare({ id: file.id, name: file.name, type: "knowledge_base", tenant_id: file.tenant_id });
                                                    setShareModalOpen(true);
                                                }}
                                                onDelete={() => confirmDelete(file.id, 'kb')}
                                            />
                                        </div>
                                    </div>
                                    <h3 className={cn("text-base md:text-lg font-bold mb-1 truncate", isDark ? "text-white" : "text-gray-900")} title={file.name}>{file.name}</h3>
                                    <div className="flex justify-between items-center mt-4">
                                        <span className="text-xs text-gray-400 uppercase">{file.file_type}</span>
                                        <span className={`text-xs font-bold px-2 py-1 rounded uppercase ${file.status === 'ready' || file.status === 'indexed' ? 'text-nvidia-green bg-nvidia-green/10' :
                                            file.status === 'indexing' ? 'text-blue-500 bg-blue-500/10' :
                                                file.status === 'processing' ? 'text-yellow-500 bg-yellow-500/10' :
                                                    file.status === 'failed' ? 'text-red-500 bg-red-500/10' :
                                                        'text-yellow-500 bg-yellow-500/10'
                                            }`}>
                                            {file.status === 'indexed' ? 'ready' : file.status || 'processing'}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {kbFiles.length === 0 && (
                                <div className={cn("col-span-full flex flex-col items-center justify-center py-20 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                                    <FileText className="w-16 h-16 text-gray-600 mb-4" />
                                    <h3 className="text-xl font-bold text-white mb-2">No Documents</h3>
                                    <p className="text-gray-400">Upload documents to build your knowledge base.</p>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {dbConnections.map((db) => (
                                <div
                                    key={db.id}
                                    onClick={() => handleOpenDbDialog(db)}
                                    className={cn("backdrop-blur-sm border rounded-xl p-6 transition-all group cursor-pointer relative overflow-hidden", isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50 hover:bg-white/5" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm")}
                                >
                                    <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Edit className={cn("w-4 h-4", isDark ? "text-nvidia-green" : "text-gray-600")} />
                                    </div>
                                    <div className="flex justify-between items-start mb-4">
                                        <div className={cn("p-3 rounded-lg transition-colors", isDark ? "bg-white/5 group-hover:bg-nvidia-green/10" : "bg-gray-100 group-hover:bg-nvidia-green/10")}>
                                            <Database className={cn("w-6 h-6 transition-colors", isDark ? "text-gray-400 group-hover:text-nvidia-green" : "text-gray-600 group-hover:text-nvidia-green")} />
                                        </div>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                confirmDelete(db.id, 'db');
                                            }}
                                            className="text-gray-500 hover:text-red-500 transition-colors p-2 hover:bg-red-500/10 rounded-lg z-10"
                                            title="Delete Connection"
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                    <h3 className={cn("text-base md:text-lg font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>{db.name}</h3>
                                    <div className="flex items-center text-sm text-gray-400 mb-4">
                                        <Server className="w-3 h-3 mr-1" />
                                        <span className="truncate max-w-[200px]">{db.host}:{db.port}</span>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        <span className={cn("text-xs font-bold px-2 py-1 rounded uppercase", isDark ? "bg-white/10 text-gray-300" : "bg-gray-100 text-gray-600")}>
                                            {db.type}
                                        </span>
                                        <span className={cn("text-xs font-medium px-2 py-1 rounded uppercase", isDark ? "bg-white/5 text-gray-500" : "bg-gray-50 text-gray-400")}>
                                            {db.database_name}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {dbConnections.length === 0 && (
                                <div className={cn("col-span-full flex flex-col items-center justify-center py-20 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                                    <Database className="w-16 h-16 text-gray-600 mb-4" />
                                    <h3 className="text-xl font-bold text-white mb-2">No Database Connections</h3>
                                    <p className="text-gray-400">Connect to external databases like PostgreSQL or MySQL.</p>
                                    <button
                                        onClick={() => handleOpenDbDialog()}
                                        className="mt-4 text-nvidia-green hover:underline font-bold"
                                    >
                                        Connect Database
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}



            {/* Upload Dialog */}
            <Dialog
                isOpen={isUploadOpen}
                onClose={() => setIsUploadOpen(false)}
                title="Upload Document"
                buttons={[
                    { label: "Cancel", onClick: () => setIsUploadOpen(false), variant: "outline" },
                    { label: uploading ? "Uploading..." : "Upload", onClick: () => document.getElementById('upload-form')?.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true })), variant: "primary", isLoading: uploading }
                ]}
            >
                <form id="upload-form" onSubmit={handleUpload} className="space-y-4">
                    {/* ... upload form (unchanged) ... */}
                    <div className="border-2 border-dashed border-gray-700 rounded-xl p-8 text-center hover:border-nvidia-green/50 transition-colors">
                        <input
                            type="file"
                            id="file-upload"
                            className="hidden"
                            accept=".pdf,application/pdf"
                            onChange={(e) => {
                                const file = e.target.files?.[0] || null;
                                if (file && file.type !== 'application/pdf') {
                                    toast("Only PDF files are allowed", "error");
                                    e.target.value = ''; // Reset input
                                    setSelectedFile(null);
                                    return;
                                }
                                setSelectedFile(file);
                            }}
                        />
                        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                            <Upload className="w-12 h-12 text-gray-500 mb-4" />
                            <span className="text-white font-bold mb-1">
                                {selectedFile ? selectedFile.name : "Click to select file"}
                            </span>
                            <span className="text-gray-500 text-sm">PDF supported (Max 100MB)</span>
                        </label>
                    </div>
                </form>
            </Dialog>

            {/* Unified Database Dialog (Create & Edit) */}
            <Dialog
                isOpen={isDbOpen}
                onClose={() => setIsDbOpen(false)}
                title={currentDb.id ? "Edit Database Connection" : "Add Database Connection"}
                buttons={[
                    { label: "Cancel", onClick: () => setIsDbOpen(false), variant: "outline" },
                    { label: connecting ? "Saving..." : (currentDb.id ? "Save Changes" : "Connect"), onClick: handleSaveDb, variant: "primary", isLoading: connecting }
                ]}
            >
                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <Input
                            label="Connection Name"
                            placeholder="My Production DB"
                            value={currentDb.name}
                            onChange={e => setCurrentDb({ ...currentDb, name: e.target.value })}
                        />
                        <Select
                            label="Type"
                            value={currentDb.type}
                            onChange={e => setCurrentDb({ ...currentDb, type: e.target.value })}
                            options={[
                                { label: "PostgreSQL", value: "postgres" },
                                { label: "MySQL", value: "mysql" },
                                { label: "SQL Server", value: "sqlserver" }
                            ]}
                        />
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <div className="col-span-2">
                            <Input
                                label="Host"
                                placeholder="localhost"
                                value={currentDb.host}
                                onChange={e => setCurrentDb({ ...currentDb, host: e.target.value })}
                            />
                        </div>
                        <div>
                            <Input
                                label="Port"
                                type="number"
                                value={currentDb.port}
                                onChange={e => setCurrentDb({ ...currentDb, port: parseInt(e.target.value) })}
                            />
                        </div>
                    </div>

                    <Input
                        label="Database Name"
                        placeholder="postgres"
                        value={currentDb.database_name}
                        onChange={e => setCurrentDb({ ...currentDb, database_name: e.target.value })}
                    />

                    <div className="grid grid-cols-2 gap-4">
                        <Input
                            label="Username"
                            placeholder="postgres"
                            value={currentDb.username}
                            onChange={e => setCurrentDb({ ...currentDb, username: e.target.value })}
                        />
                        <div>
                            <Label>
                                Password {currentDb.id && <span className="text-xs text-gray-500 font-normal">(leave blank to keep)</span>}
                            </Label>
                            <Input
                                type="password"
                                placeholder="••••••••"
                                value={currentDb.password}
                                onChange={e => setCurrentDb({ ...currentDb, password: e.target.value })}
                            />
                        </div>
                    </div>

                    <Select
                        label="SSL Mode"
                        value={currentDb.ssl_mode || "disable"}
                        onChange={e => setCurrentDb({ ...currentDb, ssl_mode: e.target.value })}
                        options={[
                            { label: "Disable", value: "disable" },
                            { label: "Require", value: "require" },
                            { label: "Prefer", value: "prefer" }
                        ]}
                    />

                    {/* Test Connection Button and Result */}
                    <div className="pt-4 border-t border-white/10">
                        <button
                            onClick={handleTestDb}
                            disabled={testing || !currentDb.host || !currentDb.database_name}
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

            {/* Delete Confirmation Dialog */}
            <Dialog
                isOpen={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
                title={itemToDelete?.type === 'kb' ? "Delete Document" : "Delete Database"}
                description={`Are you sure you want to delete this ${itemToDelete?.type === 'kb' ? "document" : "database connection"}? This action cannot be undone.`}
                buttons={[
                    { label: "Cancel", onClick: () => setDeleteDialogOpen(false), variant: "outline" },
                    { label: "Delete", onClick: handleDelete, variant: "danger" }
                ]}
            />

            {/* Share Modal */}
            {resourceToShare && (
                <ShareResourceModal
                    isOpen={shareModalOpen}
                    onClose={() => {
                        setShareModalOpen(false);
                        setResourceToShare(null);
                    }}
                    resourceId={resourceToShare.id}
                    resourceType={resourceToShare.type}
                    resourceName={resourceToShare.name}
                    tenantId={resourceToShare.tenant_id}
                />
            )}

            {/* Query Side Panel */}
            <SidePanel
                isOpen={queryDialogOpen}
                onClose={() => setQueryDialogOpen(false)}
                title="Test Query"
                width="50%"
            >
                <div className="space-y-6">
                    {/* LLM Selection */}
                    <div>
                        <Label className="mb-2">Select Model</Label>
                        <select
                            className={cn(
                                "w-full border rounded-lg px-4 py-3 focus:ring-2 focus:ring-nvidia-green focus:border-transparent transition-all outline-none",
                                isDark ? "bg-white/5 border-white/10 text-white" : "bg-white border-gray-300 text-gray-900"
                            )}
                            value={selectedLlmId}
                            onChange={e => setSelectedLlmId(e.target.value)}
                        >
                            {llmConfigs.map(llm => (
                                <option key={llm.id} value={llm.id} className={isDark ? "bg-gray-900" : "bg-white"}>{llm.name} ({llm.model})</option>
                            ))}
                        </select>
                    </div>

                    {/* Query Input */}
                    <div>
                        <Label className="mb-2">Your Query</Label>
                        <div className="relative">
                            <textarea
                                className={cn(
                                    "w-full border rounded-lg px-4 py-3 focus:ring-2 focus:ring-nvidia-green focus:border-transparent transition-all outline-none min-h-[120px] resize-none",
                                    isDark ? "bg-white/5 border-white/10 text-white" : "bg-white border-gray-300 text-gray-900"
                                )}
                                placeholder="Enter your question here..."
                                value={queryText}
                                onChange={e => setQueryText(e.target.value)}
                                onKeyDown={e => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleQuery();
                                    }
                                }}
                            />
                            <div className="absolute bottom-3 right-3">
                                <button
                                    onClick={handleQuery}
                                    disabled={querying || !queryText.trim()}
                                    className="bg-nvidia-green text-black font-bold px-4 py-2 rounded-md hover:bg-[#8CD600] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                                >
                                    {querying ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Processing...
                                        </>
                                    ) : (
                                        <>
                                            <Search className="w-4 h-4 mr-2" />
                                            Run Query
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                        <p className={cn("text-xs mt-2", isDark ? "text-gray-500" : "text-gray-400")}>Press Enter to search</p>
                    </div>

                    {/* Results */}
                    {queryResults && (
                        <div className="pt-6 border-t border-white/10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            {queryMeta?.reformulated && (
                                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 mb-4 text-xs md:text-sm text-blue-400 flex items-start gap-2">
                                    <Sparkles className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                    <div>
                                        <span className="font-semibold">Query Optimized:</span> We searched for <span className="font-mono bg-blue-500/20 px-1 rounded">"{queryMeta.actual_query}"</span> to improve results.
                                    </div>
                                </div>
                            )}

                            <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                                <span className="w-1 h-6 bg-nvidia-green rounded-full mr-3"></span>
                                Results
                                <span className="ml-3 text-xs font-normal text-gray-500 bg-white/5 px-2 py-1 rounded-full">
                                    {queryResults.length} matches
                                </span>
                            </h3>

                            <div className="space-y-4">
                                {queryResults.length === 0 ? (
                                    <div className="text-center py-10 bg-white/5 rounded-xl border border-white/5 border-dashed">
                                        <p className="text-gray-400">No relevant results found in this document.</p>
                                    </div>
                                ) : (
                                    queryResults.map((chunk, i) => {
                                        // Calculate match percentage (1 - distance)
                                        const score = chunk.score || 0;
                                        const matchPercentage = Math.round(Math.max(0, Math.min(100, (1 - score) * 100)));

                                        // Determine color based on quality
                                        let scoreColor = "text-red-400 bg-red-500/10 border-red-500/20"; // < 40
                                        if (matchPercentage >= 80) scoreColor = "text-nvidia-green bg-nvidia-green/10 border-nvidia-green/20"; // 80-100
                                        else if (matchPercentage >= 60) scoreColor = "text-blue-400 bg-blue-500/10 border-blue-500/20"; // 60-80
                                        else if (matchPercentage >= 40) scoreColor = "text-orange-400 bg-orange-500/10 border-orange-500/20"; // 40-60

                                        return (
                                            <div key={i} className="bg-white/5 rounded-xl border border-white/10 overflow-hidden group hover:border-nvidia-green/30 transition-all">
                                                {/* Header with Score */}
                                                <div className="px-4 py-2 border-b border-white/5 bg-black/20 flex justify-between items-center">
                                                    <span className="text-xs text-gray-400 font-mono">#{i + 1}</span>
                                                    <div className={cn("text-xs font-bold px-2 py-0.5 rounded border flex items-center gap-1", scoreColor)}>
                                                        <span>{matchPercentage}% Match</span>
                                                    </div>
                                                </div>

                                                <div className="p-4">
                                                    <div className="prose prose-invert prose-sm max-w-none">
                                                        {/* Render markdown content properly if possible, or just text */}
                                                        <div className="text-sm md:text-base text-gray-300 leading-relaxed whitespace-pre-wrap font-sans">
                                                            {chunk.content || chunk.text}
                                                        </div>
                                                    </div>
                                                </div>

                                                {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                                                    <div className="bg-black/20 px-4 py-3 border-t border-white/5 flex flex-wrap gap-2">
                                                        {Object.entries(chunk.metadata).map(([k, v]) => {
                                                            if (k === 'source' || k === 'file_type' || k === 'page') {
                                                                return (
                                                                    <div key={k} className="flex items-center text-xs text-gray-500 bg-white/5 px-2 py-1 rounded border border-white/5">
                                                                        <span className="font-medium text-gray-400 mr-1 capitalize">{k.replace('_', ' ')}:</span>
                                                                        <span className="truncate max-w-[200px] text-gray-300">{String(v)}</span>
                                                                    </div>
                                                                );
                                                            }
                                                            return null;
                                                        })}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </SidePanel>
        </div>
    );
}
