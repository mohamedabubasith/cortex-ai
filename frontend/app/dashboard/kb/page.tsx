"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Database, FileText, Trash2, Loader2, Plus, Upload, Search, X } from "lucide-react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import Dialog from "@/components/ui/Dialog";
import SidePanel from "@/components/ui/SidePanel";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import CustomDropdown from "@/components/ui/CustomDropdown";

interface KnowledgeBase {
    id: string;
    name: string;
    file_type: string;
    status: string;
    created_at: string;
}

interface DatabaseConnection {
    id: string;
    name: string;
    type: string;
    host: string;
    database_name: string;
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
    const [selectedDb, setSelectedDb] = useState<any>(null);
    const [isDbDetailsOpen, setIsDbDetailsOpen] = useState(false);
    const [isEditingDb, setIsEditingDb] = useState(false);
    const [editedDb, setEditedDb] = useState<any>(null);
    const [newDb, setNewDb] = useState({
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
    const [querying, setQuerying] = useState(false);
    const [llmConfigs, setLlmConfigs] = useState<any[]>([]);
    const [selectedLlmId, setSelectedLlmId] = useState<string>("");


    useEffect(() => {
        fetchResources();
        fetchLLMs();
    }, []);

    // Polling for status updates
    useEffect(() => {
        const processingFiles = kbFiles.filter(f =>
            ['pending', 'processing', 'initiated', 'unknown'].includes(f.status) || !f.status
        );

        if (processingFiles.length === 0) return;

        const interval = setInterval(async () => {
            let updated = false;
            const newFiles = [...kbFiles];

            for (const file of processingFiles) {
                try {
                    const res = await api.get(`/kb/${file.id}/status`);
                    // Backend now returns mapped status: indexed, processing, failed, initiated
                    // Handle empty or undefined status by defaulting to 'processing'
                    let newStatus = res.data?.status;

                    // If status is empty/undefined/null, default to 'processing'
                    if (!newStatus || newStatus === 'unknown') {
                        newStatus = 'processing';
                    }

                    if (newStatus !== file.status) {
                        const index = newFiles.findIndex(f => f.id === file.id);
                        if (index !== -1) {
                            newFiles[index] = { ...newFiles[index], status: newStatus };
                            updated = true;
                        }
                    }
                } catch (error) {
                    console.error(`Failed to poll status for ${file.id}`, error);
                    // On error, set to 'processing' if it's not already failed
                    const index = newFiles.findIndex(f => f.id === file.id);
                    if (index !== -1 && !['indexed', 'failed'].includes(newFiles[index].status)) {
                        newFiles[index] = { ...newFiles[index], status: 'processing' };
                        updated = true;
                    }
                }
            }

            if (updated) {
                setKbFiles(newFiles);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [kbFiles]);

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
        e.preventDefault(); // Keep for form submission if triggered by enter
        if (!selectedFile) return;

        setUploading(true);
        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            await api.post("/kb/upload", formData);
            toast("File uploaded successfully. Processing started.", "success");
            setIsUploadOpen(false);
            setSelectedFile(null);
            fetchResources();
        } catch (error: any) {
            console.error("Upload failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Upload failed. Please try again.";
            toast(errorMessage, "error");
        } finally {
            setUploading(false);
        }
    };

    const handleTestDb = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            if (selectedDb) {
                // Testing an existing saved connection - use the ID-based endpoint
                const res = await api.post(`/resources/databases/${selectedDb.id}/test`);
                setTestResult(res.data);
                if (res.data.status === "success") {
                    toast("Connection test successful!", "success");
                } else {
                    toast("Connection test failed", "error");
                }
            } else {
                // Testing a new connection - send the full connection data
                const res = await api.post("/resources/databases/test", newDb);
                setTestResult(res.data);
                if (res.data.status === "success") {
                    toast("Connection test successful!", "success");
                } else {
                    toast("Connection test failed", "error");
                }
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

    const handleViewDbDetails = (db: any) => {
        setSelectedDb(db);
        setEditedDb({ ...db, password: "" }); // Password is empty for security, user can update if needed
        setIsEditingDb(false);
        setIsDbDetailsOpen(true);
        setTestResult(null);
    };

    const handleUpdateDb = async () => {
        if (!selectedDb) return;
        setConnecting(true);
        try {
            // Only send fields that have changed
            const updateData: any = {};
            if (editedDb.name !== selectedDb.name) updateData.name = editedDb.name;
            if (editedDb.type !== selectedDb.type) updateData.type = editedDb.type;
            if (editedDb.host !== selectedDb.host) updateData.host = editedDb.host;
            if (editedDb.port !== selectedDb.port) updateData.port = editedDb.port;
            if (editedDb.username !== selectedDb.username) updateData.username = editedDb.username;
            if (editedDb.database_name !== selectedDb.database_name) updateData.database_name = editedDb.database_name;
            if (editedDb.ssl_mode !== selectedDb.ssl_mode) updateData.ssl_mode = editedDb.ssl_mode;
            if (editedDb.password && editedDb.password.trim() !== "") updateData.password = editedDb.password;

            await api.put(`/resources/databases/${selectedDb.id}`, updateData);
            toast("Database connection updated successfully", "success");
            setIsDbDetailsOpen(false);
            setIsEditingDb(false);
            setTestResult(null);
            fetchResources();
        } catch (error: any) {
            console.error("DB Update failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Update failed. Please try again.";
            toast(errorMessage, "error");
        } finally {
            setConnecting(false);
        }
    };

    const handleCreateDb = async () => {
        setConnecting(true);
        try {
            await api.post("/resources/databases", newDb);
            toast("Database connected successfully", "success");
            setIsDbOpen(false);
            setTestResult(null);
            setNewDb({
                name: "",
                type: "postgres",
                host: "localhost",
                port: 5432,
                username: "",
                password: "",
                database_name: "",
                ssl_mode: "disable"
            });
            fetchResources();
        } catch (error: any) {
            console.error("DB Connection failed", error);
            const errorMessage = error.response?.data?.detail || error.message || "Connection failed. Please check your credentials.";
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

            if (res.data.success && Array.isArray(res.data.data)) {
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
                                                className="text-gray-500 hover:text-white transition-colors p-1 rounded-md hover:bg-white/10"
                                                title="Query Document"
                                            >
                                                <Search className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => confirmDelete(file.id, 'kb')}
                                                className="text-gray-500 hover:text-red-500 transition-colors p-1 rounded-md hover:bg-red-500/10"
                                                title="Delete"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                    <h3 className={cn("text-base md:text-lg font-bold mb-1 truncate", isDark ? "text-white" : "text-gray-900")} title={file.name}>{file.name}</h3>
                                    <div className="flex justify-between items-center mt-4">
                                        <span className="text-xs text-gray-400 uppercase">{file.file_type}</span>
                                        <span className={`text-xs font-bold px-2 py-1 rounded uppercase ${file.status === 'indexed' ? 'text-nvidia-green bg-nvidia-green/10' :
                                            file.status === 'failed' ? 'text-red-500 bg-red-500/10' :
                                                'text-yellow-500 bg-yellow-500/10'
                                            }`}>
                                            {file.status}
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
                                    onClick={() => handleViewDbDetails(db)}
                                    className={cn("backdrop-blur-sm border rounded-xl p-6 transition-all group cursor-pointer", isDark ? "bg-nvidia-dark/80 border-white/10 hover:border-nvidia-green/50" : "bg-white border-gray-200 hover:border-nvidia-green/50 shadow-sm")}
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <div className={cn("p-3 rounded-lg transition-colors", isDark ? "bg-white/5 group-hover:bg-nvidia-green/10" : "bg-gray-100 group-hover:bg-nvidia-green/10")}>
                                            <Database className={cn("w-6 h-6 transition-colors", isDark ? "text-gray-400 group-hover:text-nvidia-green" : "text-gray-600 group-hover:text-nvidia-green")} />
                                        </div>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                confirmDelete(db.id, 'db');
                                            }}
                                            className="text-gray-500 hover:text-red-500 transition-colors"
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                    <h3 className={cn("text-base md:text-lg font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>{db.name}</h3>
                                    <p className="text-sm text-gray-400 mb-4">{db.database_name} @ {db.host}</p>
                                    <div className="flex flex-wrap gap-2">
                                        <span className="text-xs font-bold text-black bg-nvidia-green px-2 py-1 rounded uppercase">
                                            {db.type}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {dbConnections.length === 0 && (
                                <div className={cn("col-span-full flex flex-col items-center justify-center py-20 border rounded-2xl border-dashed", isDark ? "bg-nvidia-dark/30 border-white/10" : "bg-gray-50 border-gray-300")}>
                                    <Database className="w-16 h-16 text-gray-600 mb-4" />
                                    <h3 className="text-xl font-bold text-white mb-2">No Database Connections</h3>
                                    <p className="text-gray-400">Connect to external databases.</p>
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
                    <div className="border-2 border-dashed border-gray-700 rounded-xl p-8 text-center hover:border-nvidia-green/50 transition-colors">
                        <input
                            type="file"
                            id="file-upload"
                            className="hidden"
                            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        />
                        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                            <Upload className="w-12 h-12 text-gray-500 mb-4" />
                            <span className="text-white font-bold mb-1">
                                {selectedFile ? selectedFile.name : "Click to select file"}
                            </span>
                            <span className="text-gray-500 text-sm">PDF, TXT, MD, JSON, Word, Excel supported</span>
                        </label>
                    </div>
                </form>
            </Dialog>

            {/* Database Dialog */}
            <Dialog
                isOpen={isDbOpen}
                onClose={() => setIsDbOpen(false)}
                title="Add Database Connection"
                buttons={[
                    { label: "Cancel", onClick: () => setIsDbOpen(false), variant: "outline" },
                    { label: connecting ? "Connecting..." : "Connect", onClick: handleCreateDb, variant: "primary", isLoading: connecting }
                ]}
            >
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Connection Name</label>
                        <input
                            type="text"
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                            placeholder="My Production DB"
                            value={newDb.name}
                            onChange={e => setNewDb({ ...newDb, name: e.target.value })}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Type</label>
                            <CustomDropdown
                                options={[
                                    { id: "postgres", name: "PostgreSQL" },
                                    { id: "mysql", name: "MySQL" },
                                    { id: "sqlserver", name: "SQL Server" }
                                ]}
                                value={{ id: newDb.type || "postgres", name: "" }}
                                onChange={(option) => setNewDb({ ...newDb, type: option.id })}
                                getLabel={(option) => option.name}
                                getKey={(option) => option.id}
                                placeholder="Select Database Type"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Port</label>
                            <input
                                type="number"
                                className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                value={newDb.port}
                                onChange={e => setNewDb({ ...newDb, port: parseInt(e.target.value) })}
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Host</label>
                        <input
                            type="text"
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                            placeholder="localhost"
                            value={newDb.host}
                            onChange={e => setNewDb({ ...newDb, host: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Database Name</label>
                        <input
                            type="text"
                            className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                            placeholder="postgres"
                            value={newDb.database_name}
                            onChange={e => setNewDb({ ...newDb, database_name: e.target.value })}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Username</label>
                            <input
                                type="text"
                                className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                placeholder="postgres"
                                value={newDb.username}
                                onChange={e => setNewDb({ ...newDb, username: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
                            <input
                                type="password"
                                className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                placeholder="••••••••"
                                value={newDb.password}
                                onChange={e => setNewDb({ ...newDb, password: e.target.value })}
                            />
                        </div>
                    </div>

                    {/* Test Connection Button and Result */}
                    <div className="pt-4 border-t border-white/10">
                        <button
                            onClick={handleTestDb}
                            disabled={testing || !newDb.host || !newDb.database_name}
                            className="w-full bg-white/10 text-white font-medium px-4 py-2 rounded-lg hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
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
                            <div className={`mt-3 p-3 rounded-lg text-sm ${testResult.status === 'success' ? 'bg-nvidia-green/10 text-nvidia-green border border-nvidia-green/30' : 'bg-red-500/10 text-red-400 border border-red-500/30'}`}>
                                {testResult.message}
                            </div>
                        )}
                    </div>
                </div>
            </Dialog>

            {/* Database Details Dialog */}
            {selectedDb && editedDb && (
                <Dialog
                    isOpen={isDbDetailsOpen}
                    onClose={() => {
                        setIsDbDetailsOpen(false);
                        setIsEditingDb(false);
                        setTestResult(null);
                    }}
                    title="Database Connection Details"
                    buttons={[
                        { label: "Close", onClick: () => setIsDbDetailsOpen(false), variant: "outline" as const },
                        ...(isEditingDb ? [
                            { label: connecting ? "Saving..." : "Save Changes", onClick: handleUpdateDb, variant: "primary" as const, isLoading: connecting }
                        ] : [
                            { label: "Edit", onClick: () => setIsEditingDb(true), variant: "primary" as const }
                        ])
                    ]}
                >
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Connection Name</label>
                                {isEditingDb ? (
                                    <input
                                        type="text"
                                        className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                        value={editedDb.name}
                                        onChange={e => setEditedDb({ ...editedDb, name: e.target.value })}
                                    />
                                ) : (
                                    <div className="bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white">
                                        {selectedDb.name}
                                    </div>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Type</label>
                                {isEditingDb ? (
                                    <select
                                        className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                        value={editedDb.type}
                                        onChange={e => setEditedDb({ ...editedDb, type: e.target.value })}
                                    >
                                        <option value="postgres">PostgreSQL</option>
                                        <option value="mysql">MySQL</option>
                                    </select>
                                ) : (
                                    <div className="bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white uppercase">
                                        {selectedDb.type}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Host</label>
                                {isEditingDb ? (
                                    <input
                                        type="text"
                                        className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                        value={editedDb.host}
                                        onChange={e => setEditedDb({ ...editedDb, host: e.target.value })}
                                    />
                                ) : (
                                    <div className="bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white">
                                        {selectedDb.host}
                                    </div>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Port</label>
                                {isEditingDb ? (
                                    <input
                                        type="number"
                                        className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                        value={editedDb.port}
                                        onChange={e => setEditedDb({ ...editedDb, port: parseInt(e.target.value) })}
                                    />
                                ) : (
                                    <div className="bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white">
                                        {selectedDb.port}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Database Name</label>
                            {isEditingDb ? (
                                <input
                                    type="text"
                                    className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                    value={editedDb.database_name}
                                    onChange={e => setEditedDb({ ...editedDb, database_name: e.target.value })}
                                />
                            ) : (
                                <div className="bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white">
                                    {selectedDb.database_name}
                                </div>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Username</label>
                            {isEditingDb ? (
                                <input
                                    type="text"
                                    className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                    value={editedDb.username}
                                    onChange={e => setEditedDb({ ...editedDb, username: e.target.value })}
                                />
                            ) : (
                                <div className="bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white">
                                    {selectedDb.username}
                                </div>
                            )}
                        </div>

                        {isEditingDb && (
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">
                                    Password <span className="text-xs text-gray-500">(leave empty to keep current)</span>
                                </label>
                                <input
                                    type="password"
                                    className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                    placeholder="••••••••"
                                    value={editedDb.password}
                                    onChange={e => setEditedDb({ ...editedDb, password: e.target.value })}
                                />
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">SSL Mode</label>
                            {isEditingDb ? (
                                <select
                                    className="w-full bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-nvidia-green focus:border-nvidia-green"
                                    value={editedDb.ssl_mode || "disable"}
                                    onChange={e => setEditedDb({ ...editedDb, ssl_mode: e.target.value })}
                                >
                                    <option value="disable">Disable</option>
                                    <option value="require">Require</option>
                                    <option value="prefer">Prefer</option>
                                </select>
                            ) : (
                                <div className="bg-black/30 border border-gray-700 rounded-lg px-4 py-2 text-white">
                                    {selectedDb.ssl_mode || 'disable'}
                                </div>
                            )}
                        </div>

                        {/* Test Connection Button */}
                        <div className="pt-4 border-t border-white/10">
                            <button
                                onClick={handleTestDb}
                                disabled={testing}
                                className="w-full bg-nvidia-green text-black font-bold px-4 py-2 rounded-lg hover:bg-nvidia-green/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
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
                                <div className={`mt-3 p-3 rounded-lg text-sm ${testResult.status === 'success' ? 'bg-nvidia-green/10 text-nvidia-green border border-nvidia-green/30' : 'bg-red-500/10 text-red-400 border border-red-500/30'}`}>
                                    {testResult.message}
                                </div>
                            )}
                        </div>
                    </div>
                </Dialog>
            )}

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
                        <label className="block text-sm font-medium text-gray-400 mb-2">Select Model</label>
                        <select
                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-nvidia-green focus:border-transparent transition-all outline-none"
                            value={selectedLlmId}
                            onChange={e => setSelectedLlmId(e.target.value)}
                        >
                            {llmConfigs.map(llm => (
                                <option key={llm.id} value={llm.id} className="bg-gray-900">{llm.name} ({llm.model})</option>
                            ))}
                        </select>
                    </div>

                    {/* Query Input */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Your Query</label>
                        <div className="relative">
                            <textarea
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-nvidia-green focus:border-transparent transition-all outline-none min-h-[120px] resize-none"
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
                        <p className="text-xs text-gray-500 mt-2">Press Enter to search</p>
                    </div>

                    {/* Results */}
                    {queryResults && (
                        <div className="pt-6 border-t border-white/10 animate-in fade-in slide-in-from-bottom-4 duration-500">
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
                                    queryResults.map((chunk, i) => (
                                        <div key={i} className="bg-white/5 rounded-xl border border-white/10 overflow-hidden group hover:border-nvidia-green/30 transition-all">
                                            <div className="p-4">
                                                <p className="text-sm md:text-base text-gray-300 leading-relaxed whitespace-pre-wrap">{chunk.text}</p>
                                            </div>
                                            {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                                                <div className="bg-black/20 px-4 py-3 border-t border-white/5 flex flex-wrap gap-2">
                                                    {Object.entries(chunk.metadata).map(([k, v]) => (
                                                        <div key={k} className="flex items-center text-xs text-gray-500 bg-white/5 px-2 py-1 rounded border border-white/5">
                                                            <span className="font-medium text-gray-400 mr-1">{k}:</span>
                                                            <span className="truncate max-w-[200px]">{String(v)}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </SidePanel>
        </div>
    );
}
