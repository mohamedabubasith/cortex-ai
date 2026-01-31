"use client";

import { useState } from "react";
import Image from "next/image";
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
        <>
            <AnimatePresence mode="wait">
                {isOpen && (
                    <motion.div
                        key="backdrop"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onToggle}
                        className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
                    />
                )}
                {isOpen && (
                    <motion.div
                        key="sidebar"
                        initial={{ x: -280, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: -280, opacity: 0 }}
                        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                        className={cn(
                            "fixed inset-y-0 left-0 z-50 w-[280px] h-full border-r flex flex-col transition-colors duration-300 overflow-hidden shadow-2xl",
                            "md:relative md:translate-x-0",
                            theme === 'dark'
                                ? "bg-[#05070A] border-white/5"
                                : "bg-white border-gray-200"
                        )}
                    >
                        {/* Header with Logo and Minimize */}
                        <div className={cn(
                            "p-4 flex items-center justify-between border-b sticky top-0 z-10 backdrop-blur-xl",
                            theme === 'dark' ? "bg-[#05070A]/80 border-white/5" : "bg-white/90 border-gray-100"
                        )}>
                            <div className="flex items-center gap-3">
                                <div className="relative w-9 h-9 rounded-xl overflow-hidden shadow-lg shadow-[#76B900]/20">
                                    <Image
                                        src="/logo-basivo-v3.png"
                                        alt="Basivo"
                                        fill
                                        className="object-cover"
                                    />
                                </div>
                                <span className={cn(
                                    "font-bold tracking-tight text-lg",
                                    theme === 'dark' ? "text-white" : "text-gray-900"
                                )}>
                                    Basivo
                                </span>
                            </div>
                            <button
                                onClick={onToggle}
                                className={cn(
                                    "p-2 rounded-xl transition-all duration-200",
                                    theme === 'dark'
                                        ? "hover:bg-white/5 text-gray-500 hover:text-white"
                                        : "hover:bg-gray-100 text-gray-400 hover:text-gray-900"
                                )}
                                title="Close sidebar"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Action Items */}
                        <div className="px-3 py-4">
                            {/* New Chat */}
                            <button
                                onClick={() => {
                                    onNewChat();
                                    if (window.innerWidth < 768) onToggle();
                                }}
                                className={cn(
                                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 text-sm font-semibold shadow-sm",
                                    theme === 'dark'
                                        ? "bg-white/5 hover:bg-white/10 text-white border border-white/5 hover:border-white/10"
                                        : "bg-gray-100 hover:bg-gray-200 text-gray-900 border border-gray-200"
                                )}
                            >
                                <div className="w-5 h-5 rounded-md bg-[#76B900]/20 flex items-center justify-center">
                                    <Plus className="w-4 h-4 text-[#76B900]" />
                                </div>
                                <span>New conversation</span>
                            </button>
                        </div>

                        {/* Your Chats Section */}
                        <div className="flex-1 overflow-hidden flex flex-col">
                            <div className="px-4 py-2 flex items-center justify-between">
                                <button
                                    onClick={() => setChatsExpanded(!chatsExpanded)}
                                    className={cn(
                                        "flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.1em]",
                                        theme === 'dark' ? "text-gray-500 hover:text-gray-300" : "text-gray-400 hover:text-gray-600"
                                    )}
                                >
                                    {chatsExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                                    <span>Recent Chats</span>
                                </button>
                            </div>

                            {/* Chat List */}
                            {chatsExpanded && (
                                sessions.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-12 px-6 text-center flex-1">
                                        <div className={cn(
                                            "w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-colors duration-300",
                                            theme === 'dark' ? "bg-white/5" : "bg-gray-50"
                                        )}>
                                            <MessageSquare className={cn(
                                                "w-6 h-6",
                                                theme === 'dark' ? "text-gray-600" : "text-gray-300"
                                            )} />
                                        </div>
                                        <p className={cn(
                                            "text-sm font-semibold mb-1",
                                            theme === 'dark' ? "text-gray-400" : "text-gray-600"
                                        )}>
                                            Empty history
                                        </p>
                                        <p className={cn(
                                            "text-xs leading-relaxed",
                                            theme === 'dark' ? "text-gray-600" : "text-gray-400"
                                        )}>
                                            Your conversations will appear here
                                        </p>
                                    </div>
                                ) : (
                                    <div className="flex-1 overflow-y-auto px-2 space-y-0.5 custom-scrollbar">
                                        {Object.entries(sessionGroups).map(([group, groupSessions]) => {
                                            if (groupSessions.length === 0) return null;
                                            return (
                                                <div key={group} className="mb-4">
                                                    <div className={cn(
                                                        "px-3 py-2 text-[10px] font-bold text-gray-600 uppercase tracking-wider",
                                                        theme === 'dark' ? "text-gray-600" : "text-gray-400"
                                                    )}>
                                                        {group}
                                                    </div>
                                                    <div className="space-y-0.5">
                                                        {groupSessions.map((session) => (
                                                            <div
                                                                key={session.id}
                                                                className={cn(
                                                                    "group relative px-3 py-2 rounded-xl text-sm transition-all duration-200 flex items-center gap-3",
                                                                    session.id === currentSessionId
                                                                        ? theme === 'dark'
                                                                            ? "bg-white/10 text-white shadow-sm"
                                                                            : "bg-gray-100 text-gray-900"
                                                                        : theme === 'dark'
                                                                            ? "hover:bg-white/5 text-gray-400 hover:text-gray-200"
                                                                            : "hover:bg-gray-50 text-gray-600 hover:text-gray-900"
                                                                )}
                                                            >
                                                                <MessageSquare className={cn(
                                                                    "w-4 h-4 shrink-0 transition-colors",
                                                                    session.id === currentSessionId
                                                                        ? "text-[#76B900]"
                                                                        : "text-gray-600 group-hover:text-gray-400"
                                                                )} />
                                                                <button
                                                                    onClick={() => {
                                                                        onSelectSession(session.id);
                                                                        if (window.innerWidth < 768) onToggle();
                                                                    }}
                                                                    className="flex-1 text-left truncate font-medium"
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
                                                                            "p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200",
                                                                            theme === 'dark'
                                                                                ? "hover:bg-red-500/20 text-gray-500 hover:text-red-400"
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
                                                </div>
                                            );
                                        })}
                                    </div>
                                )
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

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
        </>
    );
}
