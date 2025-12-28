"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import Sidebar from "./chat/Sidebar";
import ChatWindow from "./chat/ChatWindow";
import { ChatSession } from "./chat/ChatList";

interface Message {
    role: "user" | "assistant";
    content: string;
    thinking?: string;
}

interface ChatInterfaceProps {
    initialMessages?: Message[];
    onSendMessage: (message: string) => Promise<void>;
    isStreaming?: boolean;
    className?: string;
    agentName?: string;
    hasKB?: boolean;
    sessions?: ChatSession[];
    currentSessionId?: string;
    onNewChat?: () => void;
    onSelectSession?: (sessionId: string) => void;
    onDeleteSession?: (sessionId: string) => void;
    onRetryMessage?: (messageIndex: number) => void;
}

export default function ChatInterface({
    initialMessages = [],
    onSendMessage,
    isStreaming = false,
    className,
    agentName = "Cortex AI",
    hasKB = false,
    sessions = [],
    currentSessionId,
    onNewChat,
    onSelectSession,
    onDeleteSession,
    onRetryMessage,
}: ChatInterfaceProps) {
    const [theme, setTheme] = useState<"dark" | "light">("dark");
    const [sidebarOpen, setSidebarOpen] = useState(true);

    // Initialize sidebar state based on screen size
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 768) {
                setSidebarOpen(false);
            } else {
                setSidebarOpen(true);
            }
        };

        // Set initial state
        handleResize();

        // Add event listener
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const toggleTheme = () => {
        setTheme(prev => prev === "dark" ? "light" : "dark");
    };

    const toggleSidebar = () => {
        setSidebarOpen(prev => !prev);
    };

    const handleSendMessage = async (message: string) => {
        // Auto-hide sidebar when user starts chatting (like ChatGPT)
        if (sidebarOpen) {
            setSidebarOpen(false);
        }
        // Don't add optimistic update here - parent already does it
        await onSendMessage(message);
    };

    return (
        <div className={cn(
            "flex h-[100dvh] font-sans overflow-hidden relative transition-colors duration-300",
            theme === 'dark' ? "bg-[#05070A] text-white" : "bg-gray-50 text-gray-900",
            className
        )}>
            <Sidebar
                isOpen={sidebarOpen}
                sessions={sessions}
                currentSessionId={currentSessionId}
                onToggle={toggleSidebar}
                onNewChat={onNewChat || (() => { })}
                onSelectSession={onSelectSession || (() => { })}
                onDeleteSession={onDeleteSession}
                theme={theme}
            />

            <ChatWindow
                messages={initialMessages}
                onSendMessage={handleSendMessage}
                isStreaming={isStreaming}
                agentName={agentName}
                hasKB={hasKB}
                theme={theme}
                onToggleTheme={toggleTheme}
                onToggleSidebar={toggleSidebar}
                sidebarOpen={sidebarOpen}
                onRetryMessage={onRetryMessage}
            />
        </div>
    );
}

export type { Message, ChatSession };
