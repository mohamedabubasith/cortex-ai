"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Menu, Bot, Loader2, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import MessageBubble from "./MessageBubble";

interface Message {
    role: "user" | "assistant";
    content: string;
}

interface ChatWindowProps {
    messages: Message[];
    onSendMessage: (message: string) => Promise<void>;
    isStreaming?: boolean;
    agentName?: string;
    theme?: "dark" | "light";
    onToggleTheme?: () => void;
    onToggleSidebar?: () => void;
    sidebarOpen?: boolean;
    onRetryMessage?: (messageIndex: number) => void;
}

export default function ChatWindow({
    messages,
    onSendMessage,
    isStreaming = false,
    agentName = "Cortex AI",
    theme = "dark",
    onToggleTheme,
    onToggleSidebar,
    sidebarOpen = true,
    onRetryMessage
}: ChatWindowProps) {
    const [input, setInput] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const lastMessageLengthRef = useRef(0);

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
    }, [input]);

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
            theme === 'dark' ? "bg-black" : "bg-gray-50"
        )}>
            {/* Header */}
            <motion.div
                className={cn(
                    "border-b backdrop-blur-lg px-4 py-3 flex items-center justify-between sticky top-0 z-10 transition-colors duration-300",
                    theme === 'dark' ? "bg-[#0B0F19]/90 border-gray-800" : "bg-white/90 border-gray-200"
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
                            <h2 className={cn("text-sm font-bold", theme === 'dark' ? "text-white" : "text-gray-900")}>
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
                    "flex-1 overflow-y-auto transition-colors duration-300",
                    theme === 'dark' ? "bg-black" : "bg-gray-50"
                )}
            >
                <div className="max-w-3xl mx-auto p-2 md:p-4 space-y-6">
                    <AnimatePresence>
                        {messages.map((msg, index) => (
                            <MessageBubble
                                key={index}
                                message={msg}
                                theme={theme}
                                onRetry={onRetryMessage ? () => onRetryMessage(index) : undefined}
                            />
                        ))}
                    </AnimatePresence>

                    {isStreaming && messages[messages.length - 1]?.role === "assistant" && !messages[messages.length - 1]?.content && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex w-full justify-start"
                        >
                            <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#76B900] flex items-center justify-center text-black shadow-lg shadow-[#76B900]/20">
                                    <Bot className="w-4 h-4" />
                                </div>
                                <div className="p-4 rounded-2xl rounded-tl-sm bg-transparent pl-0">
                                    <div className="flex space-x-1.5">
                                        <div className="w-1.5 h-1.5 bg-[#76B900] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                        <div className="w-1.5 h-1.5 bg-[#76B900] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                        <div className="w-1.5 h-1.5 bg-[#76B900] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className={cn(
                "border-t backdrop-blur-lg p-3 md:p-4 sticky bottom-0 transition-colors duration-300",
                theme === 'dark' ? "bg-[#0B0F19]/90 border-gray-800" : "bg-white/90 border-gray-200"
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
                            animate={{
                                scale: [1, 1.02, 1],
                            }}
                            transition={{
                                duration: 3,
                                repeat: Infinity,
                                repeatType: "reverse"
                            }}
                        />
                        <motion.div
                            className={cn(
                                "relative flex items-center border rounded-xl shadow-lg transition-all duration-300",
                                theme === 'dark' ? "bg-[#1A1F2E] border-gray-600" : "bg-white border-gray-300"
                            )}
                            whileFocus={{
                                borderColor: "#76B900",
                                boxShadow: "0 0 0 1px #76B900"
                            }}
                        >
                            <textarea
                                ref={textareaRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Message Cortex AI..."
                                className={cn(
                                    "w-full py-3 px-4 bg-transparent focus:outline-none focus:ring-0 border-none text-sm font-medium resize-none overflow-y-auto",
                                    theme === 'dark' ? "text-white placeholder-gray-400" : "text-gray-900 placeholder-gray-500"
                                )}
                                disabled={isStreaming}
                                rows={1}
                            />
                            <motion.button
                                type="submit"
                                disabled={!input.trim() || isStreaming}
                                className="p-2 mr-2 text-gray-400 hover:text-black hover:bg-[#76B900] rounded-lg disabled:opacity-50 disabled:hover:bg-transparent disabled:cursor-not-allowed transition-all duration-200"
                                whileHover={!isStreaming && input.trim() ? { scale: 1.1, rotate: -15 } : {}}
                                whileTap={!isStreaming && input.trim() ? { scale: 0.9 } : {}}
                            >
                                {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            </motion.button>
                        </motion.div>
                    </motion.form>
                    <motion.p
                        className={cn("text-center text-[10px] mt-2 font-medium tracking-wide uppercase", theme === 'dark' ? "text-gray-600" : "text-gray-400")}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                    >
                        Powered by <span className="text-[#76B900]">Cortex AI</span>
                    </motion.p>
                </div>
            </div>
        </div>
    );
}
