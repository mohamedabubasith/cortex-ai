"use client";

import { MessageSquare, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ChatSession {
    id: string;
    title: string;
    timestamp: number;
}

interface ChatListProps {
    sessionGroups: { [key: string]: ChatSession[] };
    currentSessionId?: string;
    onSelect: (sessionId: string) => void;
    onDelete?: (sessionId: string) => void;
    theme?: "dark" | "light";
}

export default function ChatList({
    sessionGroups,
    currentSessionId,
    onSelect,
    onDelete,
    theme = "dark"
}: ChatListProps) {
    return (
        <div className="flex-1 overflow-y-auto px-2 pb-2">
            {Object.entries(sessionGroups).map(([group, groupSessions]) => {
                if (groupSessions.length === 0) return null;
                return (
                    <div key={group} className="mb-3">
                        <h3 className={cn(
                            "text-xs font-semibold px-3 py-2",
                            theme === 'dark' ? "text-gray-500" : "text-gray-600"
                        )}>
                            {group}
                        </h3>
                        <div className="space-y-1">
                            {groupSessions.map((session) => (
                                <div
                                    key={session.id}
                                    className={cn(
                                        "w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all group flex items-center gap-3 relative cursor-pointer",
                                        session.id === currentSessionId
                                            ? theme === 'dark'
                                                ? "bg-[#2A2A2A] text-white"
                                                : "bg-gray-200 text-gray-900"
                                            : theme === 'dark'
                                                ? "hover:bg-[#2A2A2A] text-gray-300 hover:text-white"
                                                : "hover:bg-gray-100 text-gray-700 hover:text-gray-900"
                                    )}
                                    onClick={() => onSelect(session.id)}
                                >
                                    <MessageSquare className="w-4 h-4 flex-shrink-0" />
                                    <span className="truncate flex-1">{session.title}</span>
                                    {onDelete && (
                                        <div
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onDelete(session.id);
                                            }}
                                            className={cn(
                                                "opacity-0 group-hover:opacity-100 p-1 rounded transition-all flex-shrink-0 cursor-pointer",
                                                theme === 'dark'
                                                    ? "hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                                                    : "hover:bg-red-100 text-gray-500 hover:text-red-600"
                                            )}
                                            title="Delete chat"
                                        >
                                            <X className="w-3.5 h-3.5" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
