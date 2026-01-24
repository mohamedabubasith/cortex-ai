"use client";

// Disable static generation for authenticated pages
export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Database, FileText, Trash2, Loader2, Plus, Upload, Search, X, Edit, Check, AlertTriangle, Server, RefreshCw, Link } from "lucide-react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import Dialog from "@/components/ui/Dialog";
import SidePanel from "@/components/ui/SidePanel";
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
    const [querying, setQuerying] = useState(false);



    useEffect(() => {
        fetchResources();
    }, []);

    const [processingFiles, setProcessingFiles] = useState<Set<string>>(new Set());

    // Polling for status updates with exponential backoff
    useEffect(() => {
        const filesToPoll = kbFiles.filter(f =>
            ['pending', 'processing', 'initiated', 'unknown'].includes(f.status || '') || !f.status
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
                ['pending', 'processing', 'initiated', 'unknown'].includes(f.status || '') || !f.status
            );

            if (stillProcessing) {
                timeoutId = setTimeout(poll, 3000); // Poll every 3 seconds
            }
        };

        poll();

        return () => clearTimeout(timeoutId);
    }, [kbFiles.length]); // Only reset polling when file count changes (e.g. new upload)



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

        // We no longer attach llm_config_id here, backend handles defaults or specific embedding selection


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
        if (!queryText) return;
        setQuerying(true);
        try {
            const res = await api.post(`/kb/${queryDocId}/query`, {
                query: queryText
                // llm_config_id is now optional and handled by backend defaults/KB settings
            });

            if (res.data.success && Array.isArray(res.data.data)) {
                // Handle results
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
            {/* ... other code ... */}

            {/* Query Side Panel */}
            <SidePanel
                isOpen={queryDialogOpen}
                onClose={() => setQueryDialogOpen(false)}
                title="Test Query"
                width="50%"
            >
                <div className="space-y-6">
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
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
                                <div className="flex items-center">
                                    <span className="w-1 h-6 bg-nvidia-green rounded-full mr-3"></span>
                                    Results
                                </div>
                                <span className="text-xs font-normal text-gray-500 bg-white/5 px-2 py-1 rounded-full border border-white/5">
                                    {queryResults.length} matches found
                                </span>
                            </h3>

                            <div className="space-y-4">
                                {queryResults.length === 0 ? (
                                    <div className="text-center py-10 bg-white/5 rounded-xl border border-white/5 border-dashed">
                                        <div className="bg-white/5 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                                            <Search className="w-5 h-5 text-gray-400" />
                                        </div>
                                        <p className="text-gray-400 font-medium">No relevant results found.</p>
                                        <p className="text-xs text-gray-500 mt-1">Try rewording your query.</p>
                                    </div>
                                ) : (
                                    queryResults.map((chunk, i) => (
                                        <div key={i} className="bg-white/5 rounded-xl border border-white/10 overflow-hidden group hover:border-nvidia-green/30 transition-all shadow-sm">
                                            {/* Header with Score */}
                                            <div className="bg-white/5 px-4 py-2 flex justify-between items-center border-b border-white/5">
                                                <span className="text-xs font-bold text-nvidia-green uppercase tracking-wider">
                                                    Match #{i + 1}
                                                </span>
                                                {chunk.score !== undefined && (
                                                    <div className="flex items-center space-x-1" title="Similarity Score (lower is better for L2 distance, higher for Cosine)">
                                                        <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                                            <div
                                                                className="h-full bg-nvidia-green"
                                                                style={{ width: `${Math.min((chunk.score || 0) * 100, 100)}%` }} // Adjust specific to your score metric if needed
                                                            />
                                                        </div>
                                                        <span className="text-xs font-mono text-gray-400">{typeof chunk.score === 'number' ? chunk.score.toFixed(4) : chunk.score}</span>
                                                    </div>
                                                )}
                                            </div>

                                            <div className="p-5">
                                                {/* Content - Handling both 'content' (new RAG) and 'text' (fallback) */}
                                                <p className="text-sm md:text-base text-gray-200 leading-relaxed whitespace-pre-wrap font-sans">
                                                    {chunk.content || chunk.text || "No text content available."}
                                                </p>
                                            </div>

                                            {/* Metadata Footer */}
                                            {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                                                <div className="bg-black/20 px-4 py-3 border-t border-white/5">
                                                    <div className="flex flex-wrap gap-2">
                                                        {Object.entries(chunk.metadata).map(([k, v]) => (
                                                            <div key={k} className="flex items-center text-[10px] md:text-xs text-gray-400 bg-white/5 px-2 py-1.5 rounded border border-white/5 hover:bg-white/10 transition-colors">
                                                                <span className="font-semibold text-gray-500 uppercase mr-1.5">{k.replace(/_/g, ' ')}:</span>
                                                                <span className="truncate max-w-[200px] font-mono text-gray-300">{String(v)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
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
