"use client";

import React, { useState, useMemo } from "react";
import { User, Bot, Copy, Check, RotateCw, ChevronDown, ChevronUp, Brain, Globe, X, Search, BookOpen } from "lucide-react";
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
    status?: string;
}

interface Source {
    title: string;
    url: string;
    domain: string;
}

interface MessageBubbleProps {
    message: Message;
    isStreaming?: boolean;
    isQuerying?: boolean;
    hasKB?: boolean;
    isKBEnabled?: boolean;
    theme?: "dark" | "light";
    onRetry?: () => void;
}

// Custom Tag Parsers
const parseContent = (content: string) => {
    // Regex for parsing <TAG>content</TAG>
    // This is a simple parser. For nested or complex tags, use a proper parser library.
    const parts: { type: 'text' | 'reading' | 'searching'; content: string }[] = [];
    const regex = /<(READING|SEARCHING)>([\s\S]*?)<\/\1>|([^<]+)/g;

    let match;
    while ((match = regex.exec(content)) !== null) {
        if (match[1] === 'READING') {
            parts.push({ type: 'reading', content: match[2] });
        } else if (match[1] === 'SEARCHING') {
            parts.push({ type: 'searching', content: match[2] });
        } else if (match[3]) {
            // Only add non-empty text
            if (match[3].trim()) {
                parts.push({ type: 'text', content: match[3] });
            }
        }
    }

    // If no tags found, return as single text block
    if (parts.length === 0 && content) {
        return [{ type: 'text' as const, content }];
    }

    return parts;
};

function MessageBubbleBase({ message, isStreaming = false, isQuerying = false, hasKB = false, isKBEnabled = true, theme = "dark", onRetry }: MessageBubbleProps) {
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

    // Extract Citations [Title](URL)
    const extractSources = (text: string): Source[] => {
        const sources: Source[] = [];
        const regex = /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g;
        let match;
        const seenUrls = new Set();

        while ((match = regex.exec(text)) !== null) {
            const url = match[2];
            if (!seenUrls.has(url)) {
                try {
                    const domain = new URL(url).hostname.replace('www.', '');
                    sources.push({ title: match[1], url, domain });
                    seenUrls.add(url);
                } catch (e) { }
            }
        }
        return sources;
    };

    const sources = useMemo(() => !isUser ? extractSources(message.content) : [], [message.content, isUser]);
    const parsedContent = useMemo(() => !isUser ? parseContent(message.content) : [], [message.content, isUser]);

    const [isSourcesExpanded, setIsSourcesExpanded] = useState(false);

    // Only show retry for actual errors
    const isError = !isUser && (
        message.content.toLowerCase().startsWith("error:") ||
        message.content.includes("Failed to") ||
        message.content.toLowerCase().includes("timeout")
    ) && !message.content.includes("[Response truncated]") && !message.content.includes("[Stream interrupted]");

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
                duration: 0.3,
                ease: "easeOut"
            }}
            className={cn(
                "flex w-full",
                isUser ? "justify-end" : "justify-start"
            )}
        >
            <div className={cn(
                "flex items-start space-x-3 max-w-[95%] md:max-w-[85%]", // Increased width
                isUser && "flex-row-reverse space-x-reverse"
            )}>
                {/* Avatar */}
                <div
                    className={cn(
                        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm mt-1",
                        isUser
                            ? "bg-gradient-to-br from-[#76B900] to-[#8CD600]"
                            : "bg-gradient-to-br from-[#76B900] to-[#8CD600]"
                    )}
                >
                    {isUser ? (
                        <User className="w-4 h-4 text-black" />
                    ) : (
                        <Bot className="w-4 h-4 text-black" />
                    )}
                </div>

                {/* Message Content */}
                <div className="flex flex-col space-y-2 w-full min-w-0">
                    {/* Thinking Section - Redesigned */}
                    {!isUser && message.thinking && (
                        <div className="mb-2">
                            <button
                                onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                                className={cn(
                                    "flex items-center gap-2 text-xs font-medium transition-colors outline-none px-2 py-1 rounded-lg",
                                    theme === 'dark'
                                        ? "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                                        : "text-gray-500 hover:text-gray-700 hover:bg-black/5"
                                )}
                            >
                                <Brain className="w-3.5 h-3.5" />
                                <span>{isThinkingExpanded ? "Hide thought process" : "Show thought process"}</span>
                                <ChevronDown className={cn("w-3 h-3 transition-transform", isThinkingExpanded && "rotate-180")} />
                            </button>

                            <AnimatePresence>
                                {isThinkingExpanded && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="overflow-hidden"
                                    >
                                        <div className={cn(
                                            "mt-2 ml-1 pl-3 border-l-2 text-sm italic leading-relaxed",
                                            theme === 'dark'
                                                ? "text-gray-400 border-[#76B900]/30"
                                                : "text-gray-600 border-[#76B900]/30"
                                        )}>
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {message.thinking}
                                            </ReactMarkdown>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}


                    <div
                        className={cn(
                            "group relative p-4 rounded-2xl shadow-sm overflow-hidden",
                            isUser
                                ? theme === 'dark'
                                    ? "bg-gradient-to-br from-[#76B900] to-[#8CD600] text-black rounded-tr-sm shadow-lg shadow-[#76B900]/10"
                                    : "bg-[#76B900] text-black rounded-tr-sm"
                                : theme === 'dark'
                                    ? "bg-[#0A0C12] text-gray-100 rounded-tl-sm border border-white/5"
                                    : "bg-white text-gray-900 rounded-tl-sm border border-gray-200 shadow-sm"
                        )}
                    >
                        {isUser ? (
                            <div className="whitespace-pre-wrap break-words text-sm md:text-base">
                                {message.content}
                            </div>
                        ) : (
                            message.content?.trim() ? (
                                <div className={cn(
                                    "space-y-4",
                                    "prose prose-sm max-w-none",
                                    theme === 'dark'
                                        ? "prose-invert prose-headings:text-gray-100 prose-p:text-gray-200 prose-strong:text-white prose-code:text-[#76B900] prose-pre:bg-gray-800/50"
                                        : "prose-headings:text-gray-900 prose-p:text-gray-800 prose-strong:text-gray-900 prose-code:text-blue-600 prose-pre:bg-gray-50"
                                )}>
                                    {parsedContent.map((part, idx) => {
                                        if (part.type === 'searching') {
                                            return (
                                                <div key={idx} className={cn(
                                                    "flex items-center gap-2 py-2 px-3 rounded-lg text-xs font-medium border my-2 not-prose",
                                                    theme === 'dark'
                                                        ? "bg-[#76B900]/5 border-[#76B900]/20 text-[#76B900]"
                                                        : "bg-blue-50 border-blue-100 text-blue-600"
                                                )}>
                                                    <Search className="w-3.5 h-3.5 animate-pulse" />
                                                    <span>Searching: {part.content}</span>
                                                </div>
                                            );
                                        }
                                        if (part.type === 'reading') {
                                            return (
                                                <div key={idx} className={cn(
                                                    "flex items-center gap-2 py-2 px-3 rounded-lg text-xs font-medium border my-2 not-prose",
                                                    theme === 'dark'
                                                        ? "bg-purple-500/10 border-purple-500/20 text-purple-400"
                                                        : "bg-purple-50 border-purple-100 text-purple-600"
                                                )}>
                                                    <BookOpen className="w-3.5 h-3.5" />
                                                    <span>Reading: {part.content}</span>
                                                </div>
                                            );
                                        }
                                        return (
                                            <ReactMarkdown
                                                key={idx}
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    code({ node, inline, className, children, ...props }: any) {
                                                        const match = /language-(\w+)/.exec(className || "");
                                                        const codeString = String(children).replace(/\n$/, "");

                                                        return !inline && match ? (
                                                            <div className="relative group/code my-4 rounded-lg overflow-hidden border border-white/10 shadow-sm">
                                                                <div className={cn(
                                                                    "flex items-center justify-between px-3 py-1.5 text-xs font-medium border-b",
                                                                    theme === 'dark' ? "bg-gray-800 border-white/5 text-gray-400" : "bg-gray-100 border-gray-200 text-gray-500"
                                                                )}>
                                                                    <span>{match[1]}</span>
                                                                    <button
                                                                        onClick={() => handleCopy(codeString)}
                                                                        className={cn(
                                                                            "flex items-center gap-1.5 hover:text-[#76B900] transition-colors"
                                                                        )}
                                                                    >
                                                                        {copied ? (
                                                                            <>
                                                                                <Check className="w-3 h-3 text-green-500" />
                                                                                <span className="text-green-500">Copied</span>
                                                                            </>
                                                                        ) : (
                                                                            <>
                                                                                <Copy className="w-3 h-3" />
                                                                                <span>Copy</span>
                                                                            </>
                                                                        )}
                                                                    </button>
                                                                </div>
                                                                <SyntaxHighlighter
                                                                    style={theme === 'dark' ? oneDark : oneLight}
                                                                    language={match[1]}
                                                                    PreTag="div"
                                                                    customStyle={{ margin: 0, padding: '1rem', background: 'transparent' }}
                                                                    {...props}
                                                                >
                                                                    {codeString}
                                                                </SyntaxHighlighter>
                                                            </div>
                                                        ) : (
                                                            <code
                                                                className={cn(
                                                                    "px-1 py-0.5 rounded text-[85%] font-mono font-medium",
                                                                    theme === 'dark'
                                                                        ? "bg-white/10 text-gray-200"
                                                                        : "bg-black/5 text-gray-800"
                                                                )}
                                                                {...props}
                                                            >
                                                                {children}
                                                            </code>
                                                        );
                                                    }
                                                }}
                                            >
                                                {part.content}
                                            </ReactMarkdown>
                                        );
                                    })}

                                    {/* Streaming cursor */}
                                    {isStreaming && (
                                        <motion.span
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: [0, 1, 0] }}
                                            transition={{ duration: 0.8, repeat: Infinity }}
                                            className="inline-block w-1.5 h-4 ml-1 bg-[#76B900] align-middle"
                                        />
                                    )}
                                </div>
                            ) : (
                                <ThinkingIndicator theme={theme} isQuerying={isQuerying} hasKB={hasKB} isKBEnabled={isKBEnabled} status={message.status} />
                            )
                        )}

                        {/* Copy button for text messages */}
                        {!isUser && (
                            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={() => handleCopy(message.content)}
                                    className={cn(
                                        "p-1.5 rounded-lg transition-colors",
                                        theme === 'dark'
                                            ? "hover:bg-white/10 text-gray-400 hover:text-white"
                                            : "hover:bg-black/5 text-gray-400 hover:text-black"
                                    )}
                                >
                                    {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Sources Section at the bottom */}
                    {!isUser && sources.length > 0 && (
                        <div className="mt-2 pl-1">
                            <button
                                onClick={() => setIsSourcesExpanded(!isSourcesExpanded)}
                                className={cn(
                                    "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors mb-2",
                                    theme === 'dark' ? "hover:bg-white/5 text-gray-400" : "hover:bg-black/5 text-gray-500"
                                )}
                            >
                                {isSourcesExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronDown className="w-3 h-3 -rotate-90" />}
                                <span>{sources.length} Sources</span>
                            </button>

                            <AnimatePresence>
                                {isSourcesExpanded && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="grid grid-cols-1 sm:grid-cols-2 gap-2 overflow-hidden"
                                    >
                                        {sources.map((source, i) => (
                                            <a
                                                key={i}
                                                href={source.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className={cn(
                                                    "flex flex-col p-2 rounded-lg border text-xs transition-colors truncate",
                                                    theme === 'dark'
                                                        ? "bg-[#1A1F2E]/30 border-white/5 hover:border-[#76B900]/30 hover:bg-[#1A1F2E]"
                                                        : "bg-white border-gray-200 hover:border-[#76B900]/30"
                                                )}
                                            >
                                                <span className="font-medium text-[#76B900] truncate">{source.title}</span>
                                                <span className="text-gray-500 text-[10px] truncate">{source.domain}</span>
                                            </a>
                                        ))}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}

                    {/* Retry button for error messages */}
                    {isError && onRetry && (
                        <button
                            onClick={onRetry}
                            className={cn(
                                "mt-2 flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors w-fit",
                                theme === 'dark'
                                    ? "bg-red-900/20 text-red-400 hover:bg-red-900/30"
                                    : "bg-red-50 text-red-600 hover:bg-red-100"
                            )}
                        >
                            <RotateCw className="w-3 h-3" />
                            Retry
                        </button>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

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
