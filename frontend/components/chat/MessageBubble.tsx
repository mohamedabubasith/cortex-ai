"use client";

import { useState } from "react";
import { User, Bot, Copy, Check, RotateCw } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { motion } from "framer-motion";

interface Message {
    role: "user" | "assistant";
    content: string;
}

interface MessageBubbleProps {
    message: Message;
    isStreaming?: boolean;
    theme?: "dark" | "light";
    onRetry?: () => void;
}

export default function MessageBubble({ message, isStreaming = false, theme = "dark", onRetry }: MessageBubbleProps) {
    const [copied, setCopied] = useState(false);

    // Don't render empty assistant messages unless streaming (typing indicator)
    if (message.role === "assistant" && !message.content && !isStreaming) {
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
                <motion.div
                    initial={{ opacity: 0, x: isUser ? 20 : -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.15, duration: 0.4, ease: "easeOut" }}
                    className={cn(
                        "group relative p-4 rounded-2xl shadow-sm",
                        isUser
                            ? theme === 'dark'
                                ? "bg-[#76B900] text-black rounded-tr-sm"
                                : "bg-[#76B900] text-black rounded-tr-sm"
                            : theme === 'dark'
                                ? "bg-[#1E1E1E] text-gray-100 rounded-tl-sm border border-gray-800"
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
                            <div className="flex items-center space-x-1 h-6">
                                <motion.div
                                    initial={{ opacity: 0.3, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse", delay: 0 }}
                                    className={cn("w-2 h-2 rounded-full", theme === 'dark' ? "bg-gray-400" : "bg-gray-500")}
                                />
                                <motion.div
                                    initial={{ opacity: 0.3, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse", delay: 0.2 }}
                                    className={cn("w-2 h-2 rounded-full", theme === 'dark' ? "bg-gray-400" : "bg-gray-500")}
                                />
                                <motion.div
                                    initial={{ opacity: 0.3, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse", delay: 0.4 }}
                                    className={cn("w-2 h-2 rounded-full", theme === 'dark' ? "bg-gray-400" : "bg-gray-500")}
                                />
                            </div>
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
        </motion.div >
    );
}
