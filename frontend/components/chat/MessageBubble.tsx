"use client";

import { useState } from "react";
import { User, Bot, Copy, Check, RotateCw, ChevronDown, ChevronUp, Brain } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { motion, AnimatePresence } from "framer-motion";
import ThinkingIndicator from "./ThinkingIndicator";

interface Message {
    role: "user" | "assistant";
    content: string;
    thinking?: string;
}

interface MessageBubbleProps {
    message: Message;
    isStreaming?: boolean;
    isQuerying?: boolean;
    hasKB?: boolean;
    theme?: "dark" | "light";
    onRetry?: () => void;
}

function MessageBubbleBase({ message, isStreaming = false, isQuerying = false, hasKB = false, theme = "dark", onRetry }: MessageBubbleProps) {
    const [copied, setCopied] = useState(false);
    const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);

    // Don't render empty assistant messages unless streaming (typing indicator)
    if (message.role === "assistant" && !message.content && !message.thinking && !isStreaming) {
        return null;
    }

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const isUser = message.role === "user";
    // Only show retry for actual errors, not truncated or interrupted messages
    const isError = !isUser && (
        message.content.toLowerCase().startsWith("error:") ||
        message.content.includes("❌") ||
        message.content.includes("Failed to") ||
        message.content.toLowerCase().includes("timeout")
    ) && !message.content.includes("[Response truncated]") && !message.content.includes("[Stream interrupted]");

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
                duration: 0.4,
                ease: [0.25, 0.1, 0.25, 1],
                opacity: { duration: 0.3 },
                scale: { duration: 0.3 }
            }}
            className={cn(
                "flex w-full",
                isUser ? "justify-end" : "justify-start"
            )}
        >
            <div className={cn(
                "flex items-start space-x-3 max-w-[90%] md:max-w-[80%]",
                isUser && "flex-row-reverse space-x-reverse"
            )}>
                {/* Avatar */}
                <motion.div
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{
                        delay: 0.1,
                        duration: 0.5,
                        type: "spring",
                        stiffness: 200,
                        damping: 15
                    }}
                    className={cn(
                        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-lg",
                        isUser
                            ? "bg-gradient-to-br from-[#76B900] to-[#8CD600] shadow-[#76B900]/30"
                            : "bg-gradient-to-br from-[#76B900] to-[#8CD600] shadow-[#76B900]/20"
                    )}
                >
                    {isUser ? (
                        <User className="w-4 h-4 text-black" />
                    ) : (
                        <Bot className="w-4 h-4 text-black" />
                    )}
                </motion.div>

                {/* Message Content */}
                <div className="flex flex-col space-y-2 w-full">
                    {/* Thinking Section */}
                    {!isUser && message.thinking && (
                        <motion.div
                            initial={{ opacity: 0, y: 5 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={cn(
                                "rounded-xl border overflow-hidden",
                                theme === 'dark'
                                    ? "bg-[#0A0C12] border-white/5"
                                    : "bg-gray-50 border-gray-200 shadow-sm"
                            )}
                        >
                            <button
                                onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                                className={cn(
                                    "w-full flex items-center justify-between px-4 py-3 text-xs font-medium transition-colors outline-none",
                                    theme === 'dark'
                                        ? "text-gray-400 hover:bg-white/5"
                                        : "text-gray-600 hover:bg-black/5"
                                )}
                            >
                                <div className="flex items-center space-x-3">
                                    <div className="flex items-center justify-center w-5 h-5 rounded-full bg-[#76B900]/10 text-[#76B900]">
                                        <Brain className="w-3 h-3" />
                                    </div>
                                    <span className="text-sm">Thought Process</span>
                                </div>
                                <motion.div
                                    animate={{ rotate: isThinkingExpanded ? 180 : 0 }}
                                    transition={{ duration: 0.3, ease: "easeInOut" }}
                                >
                                    <ChevronDown className="w-4 h-4 opacity-50" />
                                </motion.div>
                            </button>

                            <AnimatePresence>
                                {isThinkingExpanded && (
                                    <motion.div
                                        key="thinking-content"
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{
                                            height: "auto",
                                            opacity: 1
                                        }}
                                        exit={{
                                            height: 0,
                                            opacity: 0
                                        }}
                                        transition={{
                                            height: { duration: 0.4, ease: [0.4, 0, 0.2, 1] },
                                            opacity: { duration: 0.25 }
                                        }}
                                        className={cn(
                                            "px-4 pb-4 text-sm leading-relaxed italic border-t font-light overflow-hidden",
                                            theme === 'dark'
                                                ? "text-gray-400 border-gray-800"
                                                : "text-gray-600 border-gray-200"
                                        )}
                                    >
                                        <div className="pl-4 border-l-2 border-[#76B900]/30 py-1 mt-2">
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {message.thinking}
                                            </ReactMarkdown>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    )}

                    <motion.div
                        initial={{ opacity: 0, x: isUser ? 20 : -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.15, duration: 0.4, ease: "easeOut" }}
                        className={cn(
                            "group relative p-4 rounded-2xl shadow-sm",
                            isUser
                                ? theme === 'dark'
                                    ? "bg-gradient-to-br from-[#76B900] to-[#8CD600] text-black rounded-tr-sm shadow-lg shadow-[#76B900]/20"
                                    : "bg-[#76B900] text-black rounded-tr-sm"
                                : theme === 'dark'
                                    ? "bg-[#0A0C12] text-gray-100 rounded-tl-sm border border-white/5"
                                    : "bg-white text-gray-900 rounded-tl-sm border border-gray-300 shadow-md"
                        )}
                    >
                        {isUser ? (
                            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                                {message.content}
                            </p>
                        ) : (
                            message.content ? (
                                <div className={cn(
                                    "prose prose-sm max-w-none",
                                    theme === 'dark'
                                        ? "prose-invert prose-headings:text-gray-100 prose-p:text-gray-100 prose-strong:text-gray-100 prose-code:text-[#76B900]"
                                        : "prose-headings:text-gray-900 prose-p:text-gray-800 prose-strong:text-gray-900 prose-code:text-blue-600 prose-a:text-blue-600"
                                )}>
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            code({ node, inline, className, children, ...props }: any) {
                                                const match = /language-(\w+)/.exec(className || "");
                                                const codeString = String(children).replace(/\n$/, "");

                                                return !inline && match ? (
                                                    <div className="relative group/code">
                                                        <button
                                                            onClick={() => handleCopy(codeString)}
                                                            className={cn(
                                                                "absolute right-2 top-2 p-1.5 rounded opacity-0 group-hover/code:opacity-100 transition-opacity",
                                                                theme === 'dark'
                                                                    ? "bg-gray-700 hover:bg-gray-600"
                                                                    : "bg-gray-200 hover:bg-gray-300"
                                                            )}
                                                        >
                                                            {copied ? (
                                                                <Check className="w-3.5 h-3.5 text-green-500" />
                                                            ) : (
                                                                <Copy className="w-3.5 h-3.5" />
                                                            )}
                                                        </button>
                                                        <SyntaxHighlighter
                                                            style={theme === 'dark' ? oneDark : oneLight}
                                                            language={match[1]}
                                                            PreTag="div"
                                                            {...props}
                                                        >
                                                            {codeString}
                                                        </SyntaxHighlighter>
                                                    </div>
                                                ) : (
                                                    <code
                                                        className={cn(
                                                            "px-1.5 py-0.5 rounded text-sm font-mono",
                                                            theme === 'dark'
                                                                ? "bg-gray-800 text-[#76B900]"
                                                                : "bg-gray-200 text-gray-900 border border-gray-300"
                                                        )}
                                                        {...props}
                                                    >
                                                        {children}
                                                    </code>
                                                );
                                            },
                                        }}
                                    >
                                        {message.content}
                                    </ReactMarkdown>
                                    {/* Streaming cursor */}
                                    {isStreaming && (
                                        <motion.span
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: [0, 1, 0] }}
                                            transition={{ duration: 0.8, repeat: Infinity }}
                                            className="inline-block w-1 h-4 ml-1 bg-[#76B900]"
                                        />
                                    )}
                                </div>
                            ) : (
                                <ThinkingIndicator theme={theme} isQuerying={isQuerying} hasKB={hasKB} />
                            )
                        )}

                        {/* Copy button for text messages */}
                        {!isUser && (
                            <motion.button
                                whileHover={{ scale: 1.1, y: -2 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => handleCopy(message.content)}
                                className={cn(
                                    "absolute -bottom-2 right-2 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all shadow-md",
                                    theme === 'dark'
                                        ? "bg-[#2A2A2A] hover:bg-[#333333] text-gray-300"
                                        : "bg-white hover:bg-gray-50 text-gray-600"
                                )}
                            >
                                {copied ? (
                                    <Check className="w-3.5 h-3.5 text-green-500" />
                                ) : (
                                    <Copy className="w-3.5 h-3.5" />
                                )}
                            </motion.button>
                        )}

                        {/* Retry button for error messages */}
                        {isError && onRetry && (
                            <motion.button
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={onRetry}
                                className={cn(
                                    "mt-3 flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                                    theme === 'dark'
                                        ? "bg-[#76B900] hover:bg-[#6aa600] text-black"
                                        : "bg-[#76B900] hover:bg-[#6aa600] text-black"
                                )}
                            >
                                <RotateCw className="w-4 h-4" />
                                Retry
                            </motion.button>
                        )}
                    </motion.div>
                </div>
            </div>
        </motion.div >
    );
}

import React from "react";

const MessageBubble = React.memo(MessageBubbleBase, (prev, next) => {
    return (
        prev.message === next.message &&
        prev.isStreaming === next.isStreaming &&
        prev.isQuerying === next.isQuerying &&
        prev.hasKB === next.hasKB &&
        prev.theme === next.theme
        // Ignore onRetry as it's a new closure every render but functionally identical for the same message
    );
});

export default MessageBubble;
