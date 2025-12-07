"use client";

import { useState } from "react";
import { X, Plus, MessageSquare, ChevronDown, ChevronRight, Library, Bot, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import ChatList, { ChatSession } from "./ChatList";
import Dialog from "@/components/ui/Dialog";

interface SidebarProps {
    isOpen: boolean;
    sessions: ChatSession[];
    currentSessionId?: string;
    onToggle: () => void;
    onNewChat: () => void;
    onSelectSession: (sessionId: string) => void;
    onDeleteSession?: (sessionId: string) => void;
    theme?: "dark" | "light";
}

export default function Sidebar({
    isOpen,
    sessions,
    currentSessionId,
    onToggle,
    onNewChat,
    onSelectSession,
    onDeleteSession,
    theme = "dark"
}: SidebarProps) {
    const [chatsExpanded, setChatsExpanded] = useState(true);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [sessionToDelete, setSessionToDelete] = useState<{ id: string; title: string } | null>(null);

    const groupSessionsByDate = (sessions: ChatSession[]) => {
        const now = Date.now();
        const oneDay = 24 * 60 * 60 * 1000;
        const sevenDays = 7 * oneDay;

        const groups: { [key: string]: ChatSession[] } = {
            Today: [],
            Yesterday: [],
            "Previous 7 Days": [],
            Older: []
        };

        sessions.forEach(session => {
            const diff = now - session.timestamp;
            if (diff < oneDay) {
                groups.Today.push(session);
            } else if (diff < 2 * oneDay) {
                groups.Yesterday.push(session);
            } else if (diff < sevenDays) {
                groups["Previous 7 Days"].push(session);
            } else {
                groups.Older.push(session);
            }
        });

        return groups;
    };

    const sessionGroups = groupSessionsByDate(sessions);

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    key="sidebar"
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: 280, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: "easeInOut" }}
                    className={cn(
                        "h-screen border-r flex flex-col transition-colors duration-300 overflow-hidden",
                        theme === 'dark' ? "bg-[#0B0F19] border-gray-800" : "bg-white border-gray-200"
                    )}
                >
                    {/* Header with Logo and Minimize */}
                    <div className="p-3 flex items-center justify-between border-b border-gray-800/50">
                        <div className="w-8 h-8 rounded-lg bg-[#76B900] flex items-center justify-center">
                            <Bot className="w-5 h-5 text-black" />
                        </div>
                        <button
                            onClick={onToggle}
                            className={cn(
                                "p-2 rounded-lg transition-all",
                                theme === 'dark' ? "hover:bg-white/10 text-gray-400" : "hover:bg-gray-100 text-gray-600"
                            )}
                            title="Close sidebar"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Action Items */}
                    <div className="px-2 py-3 space-y-1">
                        {/* New Chat */}
                        <button
                            onClick={onNewChat}
                            className={cn(
                                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium",
                                theme === 'dark'
                                    ? "hover:bg-[#1A1F2E] text-gray-300 hover:text-white"
                                    : "hover:bg-gray-100 text-gray-700 hover:text-gray-900"
                            )}
                        >
                            <Plus className="w-5 h-5" />
                            <span>New chat</span>
                        </button>
                    </div>

                    {/* Your Chats Section */}
                    <div className="flex-1 overflow-hidden flex flex-col">
                        <button
                            onClick={() => setChatsExpanded(!chatsExpanded)}
                            className={cn(
                                "flex items-center gap-2 px-3 py-2 text-xs font-semibold uppercase tracking-wide",
                                theme === 'dark' ? "text-gray-500 hover:text-gray-400" : "text-gray-600 hover:text-gray-700"
                            )}
                        >
                            {chatsExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            <span>Your chats</span>
                        </button>

                        {/* Chat List */}
                        {chatsExpanded && (
                            sessions.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 px-4 text-center flex-1">
                                    <div className={cn(
                                        "w-16 h-16 rounded-full flex items-center justify-center mb-4",
                                        theme === 'dark' ? "bg-[#1A1F2E]" : "bg-gray-100"
                                    )}>
                                        <MessageSquare className={cn(
                                            "w-8 h-8",
                                            theme === 'dark' ? "text-gray-700" : "text-gray-300"
                                        )} />
                                    </div>
                                    <p className={cn(
                                        "text-sm font-medium mb-1",
                                        theme === 'dark' ? "text-gray-400" : "text-gray-600"
                                    )}>
                                        No conversations yet
                                    </p>
                                    <p className={cn(
                                        "text-xs",
                                        theme === 'dark' ? "text-gray-600" : "text-gray-500"
                                    )}>
                                        Start a new chat to begin
                                    </p>
                                </div>
                            ) : (
                                <div className="flex-1 overflow-y-auto px-2">
                                    {Object.entries(sessionGroups).map(([group, groupSessions]) => {
                                        if (groupSessions.length === 0) return null;
                                        return (
                                            <div key={group} className="mb-2">
                                                {groupSessions.map((session) => (
                                                    <div
                                                        key={session.id}
                                                        className={cn(
                                                            "group relative px-3 py-2.5 rounded-lg text-sm transition-all flex items-center justify-between",
                                                            session.id === currentSessionId
                                                                ? theme === 'dark'
                                                                    ? "bg-[#1A1F2E]"
                                                                    : "bg-gray-200"
                                                                : theme === 'dark'
                                                                    ? "hover:bg-[#1A1F2E]/50"
                                                                    : "hover:bg-gray-100"
                                                        )}
                                                    >
                                                        <button
                                                            onClick={() => onSelectSession(session.id)}
                                                            className={cn(
                                                                "flex-1 text-left truncate text-sm transition-colors",
                                                                currentSessionId === session.id
                                                                    ? theme === 'dark' ? "text-white" : "text-gray-900"
                                                                    : theme === 'dark' ? "text-gray-400 hover:text-gray-300" : "text-gray-600 hover:text-gray-800"
                                                            )}
                                                        >
                                                            {session.title}
                                                        </button>
                                                        {onDeleteSession && (
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setSessionToDelete({ id: session.id, title: session.title });
                                                                    setDeleteDialogOpen(true);
                                                                }}
                                                                className={cn(
                                                                    "p-1 rounded opacity-0 group-hover:opacity-100 transition-all",
                                                                    theme === 'dark'
                                                                        ? "hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                                                                        : "hover:bg-red-50 text-gray-400 hover:text-red-500"
                                                                )}
                                                                title="Delete chat"
                                                            >
                                                                <Trash2 className="w-3.5 h-3.5" />
                                                            </button>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        );
                                    })}
                                </div>
                            )
                        )}
                    </div>
                </motion.div>
            )}

            {/* Delete Confirmation Dialog */}
            <Dialog
                isOpen={deleteDialogOpen}
                onClose={() => {
                    setDeleteDialogOpen(false);
                    setSessionToDelete(null);
                }}
                title="Delete Chat"
                description={sessionToDelete ? `Are you sure you want to delete "${sessionToDelete.title.substring(0, 50)}${sessionToDelete.title.length > 50 ? '...' : ''}"?` : ''}
                theme={theme}
                buttons={[
                    {
                        label: "Cancel",
                        onClick: () => {
                            setDeleteDialogOpen(false);
                            setSessionToDelete(null);
                        },
                        variant: "outline"
                    },
                    {
                        label: "Delete",
                        onClick: () => {
                            if (sessionToDelete && onDeleteSession) {
                                onDeleteSession(sessionToDelete.id);
                            }
                            setDeleteDialogOpen(false);
                            setSessionToDelete(null);
                        },
                        variant: "danger"
                    }
                ]}
            >
                <p className={cn("text-sm", theme === 'dark' ? "text-gray-400" : "text-gray-600")}>
                    This action cannot be undone. All messages in this conversation will be permanently deleted.
                </p>
            </Dialog>
        </AnimatePresence>
    );
}
