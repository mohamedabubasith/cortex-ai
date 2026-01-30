"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Menu, Bot, Loader2, Sun, Moon, Globe, Search, Plus, X, Brain, FlaskConical, ShoppingBag, ImageIcon, GraduationCap } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import MessageBubble from "./MessageBubble";

interface Message {
    role: "user" | "assistant";
    content: string;
    thinking?: string;
    status?: string;
}

interface ChatWindowProps {
    messages: Message[];
    onSendMessage: (message: string) => Promise<void>;
    isStreaming?: boolean;
    agentName?: string;
    hasKB?: boolean;
    theme?: "dark" | "light";
    onToggleTheme?: () => void;
    onToggleSidebar?: () => void;
    sidebarOpen?: boolean;
    onRetryMessage?: (messageIndex: number) => void;
    isSearchEnabled?: boolean;
    onToggleSearch?: () => void;
    isKBEnabled?: boolean;
    onToggleKB?: () => void;
    hasDB?: boolean;
    isDBEnabled?: boolean;
    onToggleDB?: () => void;
    hasMCP?: boolean;
}

export default function ChatWindow({
    messages,
    onSendMessage,
    isStreaming = false,
    agentName = "Cortex AI",
    hasKB = false,
    theme = "dark",
    onToggleTheme,
    onToggleSidebar,
    sidebarOpen = true,
    onRetryMessage,
    isSearchEnabled = false,
    onToggleSearch,
    isKBEnabled = true,
    onToggleKB,
    hasDB = false,
    isDBEnabled = true,
    onToggleDB,
    hasMCP = false
}: ChatWindowProps) {
    const [input, setInput] = useState("");
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isTagHovered, setIsTagHovered] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const lastMessageLengthRef = useRef(0);
    const isExpandedMode = isSearchEnabled || (isKBEnabled && hasKB) || (isDBEnabled && hasDB) || hasMCP;

    // Auto-scroll to bottom when messages change or during streaming
    useEffect(() => {
        const scrollToBottom = (instant = false) => {
            if (messagesEndRef.current) {
                const behavior = instant ? "auto" : "smooth";
                messagesEndRef.current.scrollIntoView({ behavior, block: "end" });
            }
        };

        // Calculate current message length
        const currentLength = messages.reduce((sum, msg) => sum + msg.content.length, 0);

        // Only scroll if content actually changed
        if (currentLength !== lastMessageLengthRef.current) {
            lastMessageLengthRef.current = currentLength;
            scrollToBottom(isStreaming);
        }
    }, [messages, isStreaming]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [input, isExpandedMode]); // Add isExpandedMode to re-calculate height if padding changes

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isStreaming) return;

        const userMessage = input.trim();
        setInput("");

        await onSendMessage(userMessage);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as any);
        }
    };

    return (
        <div className={cn(
            "flex flex-col flex-1 overflow-hidden relative transition-all duration-300",
            theme === 'dark' ? "bg-[#05070A]" : "bg-gray-50"
        )}>
            {/* Header */}
            <motion.div
                className={cn(
                    "border-b backdrop-blur-xl px-4 py-3 flex items-center justify-between z-10 transition-colors duration-300 shrink-0",
                    theme === 'dark' ? "bg-[#05070A]/80 border-white/5" : "bg-white/90 border-gray-200"
                )}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
            >
                <div className="flex items-center space-x-3">
                    {!sidebarOpen && onToggleSidebar && (
                        <motion.button
                            onClick={onToggleSidebar}
                            className={cn(
                                "p-2 rounded-lg transition-colors",
                                theme === 'dark' ? "hover:bg-gray-800 text-gray-300" : "hover:bg-gray-100 text-gray-600"
                            )}
                            whileHover={{ scale: 1.1, rotate: 90 }}
                            whileTap={{ scale: 0.9 }}
                        >
                            <Menu className="w-5 h-5" />
                        </motion.button>
                    )}
                    <motion.div
                        className="flex items-center space-x-2"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1, duration: 0.5 }}
                    >
                        <motion.div
                            className="w-8 h-8 bg-gradient-to-br from-[#76B900] to-[#8CD600] rounded-full flex items-center justify-center shadow-lg shadow-[#76B900]/30"
                            whileHover={{ rotate: 360, scale: 1.1 }}
                            transition={{ duration: 0.6 }}
                        >
                            <Bot className="w-5 h-5 text-black" />
                        </motion.div>
                        <div>
                            <h2 className={cn("text-sm font-semibold", theme === 'dark' ? "text-white" : "text-gray-900")}>
                                {agentName}
                            </h2>
                            <p className={cn("text-[10px]", theme === 'dark' ? "text-gray-400" : "text-gray-500")}>
                                AI Assistant
                            </p>
                        </div>
                    </motion.div>
                </div>
                {onToggleTheme && (
                    <motion.button
                        onClick={onToggleTheme}
                        className={cn(
                            "p-2 rounded-lg transition-all duration-300",
                            theme === 'dark' ? "hover:bg-gray-800 text-gray-300" : "hover:bg-gray-100 text-gray-600"
                        )}
                        whileHover={{ scale: 1.1, rotate: 180 }}
                        whileTap={{ scale: 0.9 }}
                        initial={{ opacity: 0, rotate: -180 }}
                        animate={{ opacity: 1, rotate: 0 }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                    >
                        {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                    </motion.button>
                )}
            </motion.div>

            {/* Messages Area */}
            <div
                ref={messagesContainerRef}
                className={cn(
                    "flex-1 overflow-y-auto transition-colors duration-300 overscroll-behavior-y-none flex flex-col justify-start",
                    theme === 'dark' ? "bg-[#05070A]" : "bg-gray-50"
                )}
            >
                <div className="max-w-3xl mx-auto p-2 md:p-4 space-y-6">
                    <AnimatePresence>
                        {messages.map((msg, index) => (
                            <MessageBubble
                                key={index}
                                message={msg}
                                theme={theme}
                                isStreaming={isStreaming && index === messages.length - 1}
                                hasKB={hasKB}
                                isKBEnabled={isKBEnabled}
                                onRetry={onRetryMessage ? () => onRetryMessage(index) : undefined}
                            />
                        ))}
                    </AnimatePresence>



                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className={cn(
                "border-t backdrop-blur-xl p-3 md:p-4 transition-colors duration-300 shrink-0 pb-safe",
                theme === 'dark' ? "bg-[#05070A]/80 border-white/5" : "bg-white/90 border-gray-200"
            )}>
                <div className="max-w-3xl mx-auto">
                    <motion.form
                        onSubmit={handleSubmit}
                        className="relative group"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                    >
                        <motion.div
                            className="absolute inset-0 bg-gradient-to-r from-[#76B900]/20 to-[#76B900]/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                        />
                        <motion.div
                            className={cn(
                                "relative flex border rounded-2xl shadow-lg transition-all duration-300",
                                isExpandedMode ? "flex-col bg-[#1A1F2E]/80 backdrop-blur-sm" : "flex-row items-center",
                                theme === 'dark' ? "bg-[#1A1F2E] border-white/10" : "bg-white border-gray-200",
                                "focus-within:border-[#76B900] focus-within:ring-1 focus-within:ring-[#76B900]/30"
                            )}
                        >
                            {/* Top Section: Textarea (and Plus/Send in single-row mode) */}
                            <div className={cn(
                                "flex items-center flex-1 min-w-0",
                                isExpandedMode ? "w-full" : "pr-2"
                            )}>
                                {!isExpandedMode && (
                                    <div className="pl-3">
                                        <div className="relative">
                                            <motion.button
                                                type="button"
                                                onClick={() => setIsMenuOpen(!isMenuOpen)}
                                                className={cn(
                                                    "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200",
                                                    theme === 'dark' ? "text-gray-400 hover:text-white hover:bg-white/10" : "text-gray-500 hover:text-black hover:bg-black/5"
                                                )}
                                                whileHover={{ scale: 1.1 }}
                                                whileTap={{ scale: 0.9 }}
                                            >
                                                <Plus className={cn("w-5 h-5 transition-transform duration-200", isMenuOpen && "rotate-45")} />
                                            </motion.button>
                                            <AnimatePresence>
                                                {isMenuOpen && (
                                                    <>
                                                        <div className="fixed inset-0 z-40" onClick={() => setIsMenuOpen(false)} />
                                                        <motion.div
                                                            initial={{ opacity: 0, scale: 0.95, y: -10 }}
                                                            animate={{ opacity: 1, scale: 1, y: 0 }}
                                                            exit={{ opacity: 0, scale: 0.95, y: -10 }}
                                                            className={cn(
                                                                "absolute bottom-full left-0 mb-3 w-56 p-1.5 rounded-2xl border shadow-2xl z-50",
                                                                theme === 'dark' ? "bg-[#232627] border-white/10" : "bg-white border-gray-200"
                                                            )}
                                                        >
                                                            <div className="flex flex-col">
                                                                <button
                                                                    onClick={() => {
                                                                        onToggleSearch?.();
                                                                        setIsMenuOpen(false);
                                                                    }}
                                                                    className={cn(
                                                                        "flex items-center justify-between w-full p-2.5 rounded-xl text-left text-sm transition-colors",
                                                                        isSearchEnabled
                                                                            ? (theme === 'dark' ? "bg-[#76B900]/10 text-[#76B900]" : "bg-gray-100 text-[#76B900]")
                                                                            : (theme === 'dark' ? "text-gray-300 hover:bg-white/5" : "text-gray-700 hover:bg-black/5")
                                                                    )}
                                                                >
                                                                    <div className="flex items-center gap-3">
                                                                        <Globe className={cn("w-4 h-4", isSearchEnabled ? "text-[#76B900]" : "text-gray-400")} />
                                                                        <span className="font-medium">Web search</span>
                                                                    </div>
                                                                    {isSearchEnabled && <div className="w-1.5 h-1.5 rounded-full bg-[#76B900]" />}
                                                                </button>

                                                                {hasKB && (
                                                                    <button
                                                                        onClick={() => {
                                                                            onToggleKB?.();
                                                                            setIsMenuOpen(false);
                                                                        }}
                                                                        className={cn(
                                                                            "flex items-center justify-between w-full p-2.5 rounded-xl text-left text-sm transition-colors",
                                                                            isKBEnabled
                                                                                ? (theme === 'dark' ? "bg-[#76B900]/10 text-[#76B900]" : "bg-gray-100 text-[#76B900]")
                                                                                : (theme === 'dark' ? "text-gray-300 hover:bg-white/5" : "text-gray-700 hover:bg-black/5")
                                                                        )}
                                                                    >
                                                                        <div className="flex items-center gap-3">
                                                                            <Brain className={cn("w-4 h-4", isKBEnabled ? "text-[#76B900]" : "text-gray-400")} />
                                                                            <span className="font-medium">Knowledge base</span>
                                                                        </div>
                                                                        {isKBEnabled && <div className="w-1.5 h-1.5 rounded-full bg-[#76B900]" />}
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </motion.div>
                                                    </>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    </div>
                                )}
                                <textarea
                                    ref={textareaRef}
                                    value={input}
                                    onChange={(e) => {
                                        setInput(e.target.value);
                                        if (sidebarOpen && onToggleSidebar) {
                                            onToggleSidebar();
                                        }
                                    }}
                                    onKeyDown={handleKeyDown}
                                    placeholder={isExpandedMode ? "Type a message..." : "Message Cortex AI..."}
                                    className={cn(
                                        "w-full py-3 px-4 bg-transparent focus:outline-none focus:ring-0 border-none text-base md:text-sm font-medium resize-none overflow-y-auto min-h-[44px]",
                                        theme === 'dark' ? "text-white placeholder-gray-400" : "text-gray-900 placeholder-gray-500"
                                    )}
                                    disabled={isStreaming}
                                    rows={1}
                                />
                                {!isExpandedMode && (
                                    <motion.button
                                        type="submit"
                                        disabled={!input.trim() || isStreaming}
                                        className={cn(
                                            "p-1.5 rounded-full transition-all duration-200 shrink-0",
                                            input.trim()
                                                ? "bg-[#76B900] text-black hover:bg-[#8CD600]"
                                                : theme === 'dark' ? "bg-[#2A2D30] text-gray-500 cursor-not-allowed" : "bg-gray-200 text-gray-400 cursor-not-allowed"
                                        )}
                                        whileHover={!isStreaming && input.trim() ? { scale: 1.05 } : {}}
                                        whileTap={!isStreaming && input.trim() ? { scale: 0.95 } : {}}
                                    >
                                        {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                                    </motion.button>
                                )}
                            </div>

                            {/* Bottom Section: Full Tools Row (only in search/expanded mode) */}
                            {isExpandedMode && (
                                <div className="flex items-center justify-between px-3 pb-3 pt-1">
                                    <div className="flex items-center gap-2">
                                        <div className="relative">
                                            <motion.button
                                                type="button"
                                                onClick={() => setIsMenuOpen(!isMenuOpen)}
                                                className={cn(
                                                    "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200",
                                                    theme === 'dark' ? "text-gray-400 hover:text-white hover:bg-white/10" : "text-gray-500 hover:text-black hover:bg-black/5"
                                                )}
                                                whileHover={{ scale: 1.1 }}
                                                whileTap={{ scale: 0.9 }}
                                            >
                                                <Plus className={cn("w-5 h-5 transition-transform duration-200", isMenuOpen && "rotate-45")} />
                                            </motion.button>
                                            <AnimatePresence>
                                                {isMenuOpen && (
                                                    <>
                                                        <div className="fixed inset-0 z-40" onClick={() => setIsMenuOpen(false)} />
                                                        <motion.div
                                                            initial={{ opacity: 0, scale: 0.95, y: -10 }}
                                                            animate={{ opacity: 1, scale: 1, y: 0 }}
                                                            exit={{ opacity: 0, scale: 0.95, y: -10 }}
                                                            className={cn(
                                                                "absolute bottom-full left-0 mb-3 w-56 p-1.5 rounded-2xl border shadow-2xl z-50",
                                                                theme === 'dark' ? "bg-[#232627] border-white/10" : "bg-white border-gray-200"
                                                            )}
                                                        >
                                                            {/* Menu Items */}
                                                            <div className="flex flex-col">
                                                                <button
                                                                    onClick={() => {
                                                                        onToggleSearch?.();
                                                                        setIsMenuOpen(false);
                                                                    }}
                                                                    className={cn(
                                                                        "flex items-center justify-between w-full p-2.5 rounded-xl text-left text-sm transition-colors",
                                                                        isSearchEnabled
                                                                            ? (theme === 'dark' ? "bg-[#76B900]/10 text-[#76B900]" : "bg-gray-100 text-[#76B900]")
                                                                            : (theme === 'dark' ? "text-gray-300 hover:bg-white/5" : "text-gray-700 hover:bg-black/5")
                                                                    )}
                                                                >
                                                                    <div className="flex items-center gap-3">
                                                                        <Globe className={cn("w-4 h-4", isSearchEnabled ? "text-[#76B900]" : "text-gray-400")} />
                                                                        <span className="font-medium">Web search</span>
                                                                    </div>
                                                                    {isSearchEnabled && <div className="w-1.5 h-1.5 rounded-full bg-[#76B900]" />}
                                                                </button>

                                                                {hasKB && (
                                                                    <button
                                                                        onClick={() => {
                                                                            onToggleKB?.();
                                                                            setIsMenuOpen(false);
                                                                        }}
                                                                        className={cn(
                                                                            "flex items-center justify-between w-full p-2.5 rounded-xl text-left text-sm transition-colors",
                                                                            isKBEnabled
                                                                                ? (theme === 'dark' ? "bg-[#76B900]/10 text-[#76B900]" : "bg-gray-100 text-[#76B900]")
                                                                                : (theme === 'dark' ? "text-gray-300 hover:bg-white/5" : "text-gray-700 hover:bg-black/5")
                                                                        )}
                                                                    >
                                                                        <div className="flex items-center gap-3">
                                                                            <Brain className={cn("w-4 h-4", isKBEnabled ? "text-[#76B900]" : "text-gray-400")} />
                                                                            <span className="font-medium">Knowledge base</span>
                                                                        </div>
                                                                        {isKBEnabled && <div className="w-1.5 h-1.5 rounded-full bg-[#76B900]" />}
                                                                    </button>
                                                                )}

                                                                {hasDB && (
                                                                    <button
                                                                        onClick={() => {
                                                                            onToggleDB?.();
                                                                            setIsMenuOpen(false);
                                                                        }}
                                                                        className={cn(
                                                                            "flex items-center justify-between w-full p-2.5 rounded-xl text-left text-sm transition-colors",
                                                                            isDBEnabled
                                                                                ? (theme === 'dark' ? "bg-[#76B900]/10 text-[#76B900]" : "bg-gray-100 text-[#76B900]")
                                                                                : (theme === 'dark' ? "text-gray-300 hover:bg-white/5" : "text-gray-700 hover:bg-black/5")
                                                                        )}
                                                                    >
                                                                        <div className="flex items-center gap-3">
                                                                            <FlaskConical className={cn("w-4 h-4", isDBEnabled ? "text-[#76B900]" : "text-gray-400")} />
                                                                            <span className="font-medium">Database</span>
                                                                        </div>
                                                                        {isDBEnabled && <div className="w-1.5 h-1.5 rounded-full bg-[#76B900]" />}
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </motion.div>
                                                    </>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                        {(() => {
                                            const activeTools = [
                                                { id: 'search', enabled: isSearchEnabled, label: 'SEARCH', Icon: Globe, toggle: onToggleSearch },
                                                { id: 'kb', enabled: isKBEnabled && hasKB, label: 'KNOWLEDGE', Icon: Brain, toggle: onToggleKB },
                                                { id: 'db', enabled: isDBEnabled && hasDB, label: 'DATABASE', Icon: FlaskConical, toggle: onToggleDB },
                                                { id: 'mcp', enabled: hasMCP, label: 'MCP TOOLS', Icon: ShoppingBag, toggle: undefined }
                                            ].filter(t => t.enabled);

                                            if (activeTools.length === 0) return null;

                                            // Show all for now even if it's 4
                                            const maxVisible = 4;
                                            const visibleTools = activeTools.slice(0, maxVisible);
                                            const remaining = activeTools.length - maxVisible;

                                            return (
                                                <div className="flex items-center gap-2 overflow-x-auto no-scrollbar scroll-smooth">
                                                    {visibleTools.map((tool) => (
                                                        <motion.div
                                                            key={tool.id}
                                                            initial={{ opacity: 0, scale: 0.9 }}
                                                            animate={{ opacity: 1, scale: 1 }}
                                                            className={cn(
                                                                "flex items-center gap-1.5 pl-2.5 pr-1.5 py-1 rounded-full border transition-all duration-200 cursor-default shadow-sm h-7",
                                                                theme === 'dark'
                                                                    ? "bg-[#76B900]/10 border-[#76B900]/30 text-[#76B900]"
                                                                    : "bg-[#76B900]/5 border-[#76B900]/20 text-[#76B900]"
                                                            )}
                                                        >
                                                            <tool.Icon className="w-3.5 h-3.5" />
                                                            <span className="text-[11px] font-bold tracking-tight uppercase whitespace-nowrap">
                                                                {tool.label}
                                                            </span>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    tool.toggle?.();
                                                                }}
                                                                className={cn(
                                                                    "ml-0.5 p-0.5 rounded-full transition-all duration-200",
                                                                    theme === 'dark' ? "hover:bg-[#76B900]/20" : "hover:bg-[#76B900]/10"
                                                                )}
                                                            >
                                                                <X className="w-3 h-3" />
                                                            </button>
                                                        </motion.div>
                                                    ))}
                                                    {remaining > 0 && (
                                                        <div className={cn(
                                                            "px-2 py-1 rounded-full border text-[10px] font-bold h-7 flex items-center shadow-sm",
                                                            theme === 'dark'
                                                                ? "bg-[#76B900]/10 border-[#76B900]/30 text-[#76B900]"
                                                                : "bg-[#76B900]/5 border-[#76B900]/20 text-[#76B900]"
                                                        )}>
                                                            +{remaining}
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })()}
                                    </div>
                                    <motion.button
                                        type="submit"
                                        disabled={!input.trim() || isStreaming}
                                        className={cn(
                                            "p-1.5 rounded-full transition-all duration-200",
                                            input.trim()
                                                ? "bg-[#76B900] text-black hover:bg-[#8CD600]"
                                                : theme === 'dark' ? "bg-[#2A2D30] text-gray-500 cursor-not-allowed" : "bg-gray-200 text-gray-400 cursor-not-allowed"
                                        )}
                                        whileHover={!isStreaming && input.trim() ? { scale: 1.05 } : {}}
                                        whileTap={!isStreaming && input.trim() ? { scale: 0.95 } : {}}
                                    >
                                        {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                                    </motion.button>
                                </div>
                            )}
                        </motion.div>
                    </motion.form>
                    <motion.p
                        className={cn("text-center text-[10px] mt-2 font-medium tracking-wide uppercase", theme === 'dark' ? "text-gray-600" : "text-gray-400")}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                    >
                        Powered by <span className="text-[#76B900]">Basivo</span>
                    </motion.p>
                </div>
            </div>
        </div>
    );
}
