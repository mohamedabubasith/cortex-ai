"use client";

import React, { useState, useMemo } from "react";
import {
    User, Bot, Copy, Check, RotateCw, ChevronDown,
    Brain, Globe, BookOpen, Search, ImageIcon, Loader2, ExternalLink, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
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
    index: number;
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

// ─── Tag parser ───────────────────────────────────────────────────────────────
type PartType = "text" | "searching" | "reading" | "generating" | "kb_query";
type ContentPart = { type: PartType; content: string };

const parseContent = (raw: string): ContentPart[] => {
    const parts: ContentPart[] = [];
    const TAG = "SEARCHING|READING|GENERATING|KB_QUERY";
    const regex = new RegExp(`<(${TAG})>([\\s\\S]*?)<\\/\\1>|([^<]+|<(?!\\/?(?:${TAG}))[^>]*>)`, "g");
    let match: RegExpExecArray | null;
    while ((match = regex.exec(raw)) !== null) {
        if (match[1]) {
            parts.push({ type: match[1].toLowerCase() as PartType, content: match[2] });
        } else if (match[3]?.trim()) {
            parts.push({ type: "text", content: match[3] });
        }
    }
    return parts.length === 0 && raw ? [{ type: "text", content: raw }] : parts;
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
const faviconUrl = (domain: string) =>
    `https://www.google.com/s2/favicons?sz=32&domain_url=${domain}`;

function extractSources(text: string): Source[] {
    const sources: Source[] = [];
    const seen = new Set<string>();
    let idx = 1;

    const addUrl = (url: string, title: string) => {
        if (seen.has(url)) return;
        try {
            const domain = new URL(url).hostname.replace("www.", "");
            sources.push({ title, url, domain, index: idx++ });
            seen.add(url);
        } catch (_) { /* skip invalid URLs */ }
    };

    // Standard markdown links: [Title](url)
    const mdRegex = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g;
    let match: RegExpExecArray | null;
    while ((match = mdRegex.exec(text)) !== null) addUrl(match[2], match[1]);

    // GPT/thinking model format: 【url】
    const bracketRegex = /【(https?:\/\/[^】]+)】/g;
    while ((match = bracketRegex.exec(text)) !== null) {
        const url = match[1].trim();
        try { addUrl(url, new URL(url).hostname.replace("www.", "")); } catch (_) {}
    }

    return sources;
}

// Replace citation markers with Title<sup>[n]</sup>
function injectCitationNumbers(text: string, sources: Source[]): string {
    if (!sources.length) return text;
    let result = text;
    for (const s of sources) {
        const escaped = s.url.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        // Replace [Title](url)
        result = result.replace(
            new RegExp(`\\[([^\\]]+)\\]\\(${escaped}\\)`, "g"),
            `$1<sup>[${s.index}]</sup>`
        );
        // Replace 【url】
        result = result.replace(
            new RegExp(`【${escaped}】`, "g"),
            `<sup>[${s.index}]</sup>`
        );
    }
    return result;
}

// ─── Status pill ──────────────────────────────────────────────────────────────
type PillColor = "green" | "blue" | "purple" | "orange";
const PILL_COLORS: Record<PillColor, Record<"dark" | "light", string>> = {
    green: {
        dark: "bg-[#76B900]/10 border-[#76B900]/20 text-[#76B900]",
        light: "bg-[#76B900]/10 border-[#76B900]/30 text-[#5a8c00]",
    },
    blue: {
        dark: "bg-blue-500/10 border-blue-500/20 text-blue-400",
        light: "bg-blue-50 border-blue-200 text-blue-600",
    },
    purple: {
        dark: "bg-purple-500/10 border-purple-500/20 text-purple-400",
        light: "bg-purple-50 border-purple-200 text-purple-600",
    },
    orange: {
        dark: "bg-orange-500/10 border-orange-500/20 text-orange-400",
        light: "bg-orange-50 border-orange-200 text-orange-600",
    },
};

function StatusPill({ icon: Icon, label, color, theme }: { icon: React.ElementType; label: string; color: PillColor; theme: "dark" | "light" }) {
    return (
        <div className={cn("flex items-center gap-2 py-1.5 px-3 rounded-lg text-xs font-medium border my-1 not-prose w-fit", PILL_COLORS[color][theme])}>
            <Icon className="w-3.5 h-3.5 shrink-0 animate-pulse" />
            <span className="truncate max-w-xs">{label}</span>
        </div>
    );
}

// ─── Generated image ──────────────────────────────────────────────────────────
function GeneratedImage({ src, alt, theme }: { src: string; alt: string; theme: "dark" | "light" }) {
    const [loaded, setLoaded] = useState(false);
    const [error, setError] = useState(false);
    const [lightbox, setLightbox] = useState(false);

    if (error) return null;

    return (
        <>
            <div className={cn("relative my-3 rounded-xl overflow-hidden border not-prose shadow-lg", theme === "dark" ? "border-white/10" : "border-gray-200")}>
                {!loaded && (
                    <div className={cn("flex items-center justify-center gap-2 h-52 text-sm", theme === "dark" ? "bg-white/5 text-gray-400" : "bg-gray-50 text-gray-500")}>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Loading image…</span>
                    </div>
                )}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src={src}
                    alt={alt}
                    className={cn("max-w-full rounded-t-xl cursor-zoom-in transition-opacity duration-300", loaded ? "opacity-100" : "opacity-0 absolute inset-0")}
                    onLoad={() => setLoaded(true)}
                    onError={() => setError(true)}
                    onClick={() => setLightbox(true)}
                />
                {loaded && (
                    <div className={cn("flex items-center justify-between px-3 py-2 text-xs border-t", theme === "dark" ? "bg-black/30 border-white/5 text-gray-400" : "bg-gray-50 border-gray-100 text-gray-500")}>
                        <div className="flex items-center gap-1.5">
                            <Sparkles className="w-3 h-3 text-[#76B900]" />
                            <span>AI Generated · DALL·E 3</span>
                        </div>
                        <a href={src} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="flex items-center gap-1 hover:text-[#76B900] transition-colors">
                            <ExternalLink className="w-3 h-3" />Open
                        </a>
                    </div>
                )}
            </div>

            <AnimatePresence>
                {lightbox && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 cursor-zoom-out"
                        onClick={() => setLightbox(false)}
                    >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={src} alt={alt} className="max-w-full max-h-full rounded-xl shadow-2xl object-contain" onClick={(e) => e.stopPropagation()} />
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}

// ─── Source card ──────────────────────────────────────────────────────────────
function SourceCard({ source, theme }: { source: Source; theme: "dark" | "light" }) {
    return (
        <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
                "flex items-start gap-2 p-2 rounded-lg border text-xs transition-colors group/card",
                theme === "dark"
                    ? "bg-white/3 border-white/8 hover:border-[#76B900]/40 hover:bg-white/6"
                    : "bg-white border-gray-200 hover:border-[#76B900]/40 shadow-sm"
            )}
        >
            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#76B900]/15 text-[#76B900] flex items-center justify-center text-[10px] font-bold">
                {source.index}
            </span>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
                src={faviconUrl(source.domain)}
                alt=""
                width={14}
                height={14}
                className="mt-0.5 rounded-sm flex-shrink-0"
                onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
            <div className="min-w-0 flex-1">
                <p className={cn("font-medium leading-snug line-clamp-2 group-hover/card:text-[#76B900] transition-colors", theme === "dark" ? "text-gray-200" : "text-gray-800")}>
                    {source.title}
                </p>
                <p className="text-[10px] text-gray-500 mt-0.5 truncate">{source.domain}</p>
            </div>
            <ExternalLink className="w-3 h-3 text-gray-400 shrink-0 opacity-0 group-hover/card:opacity-100 transition-opacity mt-0.5" />
        </a>
    );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
function MessageBubbleBase({ message, isStreaming = false, isQuerying = false, hasKB = false, isKBEnabled = true, theme = "dark", onRetry }: MessageBubbleProps) {
    const [copied, setCopied] = useState(false);
    const [thinkingOpen, setThinkingOpen] = useState(false);
    const [readingsOpen, setReadingsOpen] = useState(false);
    const [sourcesOpen, setSourcesOpen] = useState(false);

    const isUser = message.role === "user";
    const handleCopy = (text: string) => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); };

    const sources = useMemo(() => (!isUser ? extractSources(message.content) : []), [message.content, isUser]);
    const allParts = useMemo(() => (!isUser ? parseContent(message.content) : []), [message.content, isUser]);
    const statusParts = useMemo(() => allParts.filter((p) => p.type !== "text"), [allParts]);
    const textContent = useMemo(() => allParts.filter((p) => p.type === "text").map((p) => p.content).join(""), [allParts]);
    const processedText = useMemo(() => injectCitationNumbers(textContent, sources), [textContent, sources]);
    const readings = useMemo(() => statusParts.filter((p) => p.type === "reading"), [statusParts]);

    const isError = !isUser && (
        message.content.toLowerCase().startsWith("error:") ||
        message.content.includes("Failed to") ||
        message.content.toLowerCase().includes("timeout")
    ) && !message.content.includes("[Response truncated]");

    // Must be after all hooks
    if (!isUser && !message.content && !message.thinking && !isStreaming) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}
        >
            <div className={cn("flex items-start space-x-3 max-w-[95%] md:max-w-[85%]", isUser && "flex-row-reverse space-x-reverse")}>
                {/* Avatar */}
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm mt-1 bg-gradient-to-br from-[#76B900] to-[#8CD600]">
                    {isUser ? <User className="w-4 h-4 text-black" /> : <Bot className="w-4 h-4 text-black" />}
                </div>

                <div className="flex flex-col space-y-1.5 w-full min-w-0">
                    {/* Thinking */}
                    {!isUser && message.thinking && (
                        <div>
                            <button
                                onClick={() => setThinkingOpen(!thinkingOpen)}
                                className={cn("flex items-center gap-2 text-xs font-medium px-2 py-1 rounded-lg transition-colors outline-none", theme === "dark" ? "text-gray-400 hover:text-gray-200 hover:bg-white/5" : "text-gray-500 hover:text-gray-700 hover:bg-black/5")}
                            >
                                <Brain className="w-3.5 h-3.5" />
                                {thinkingOpen ? "Hide thought process" : "Show thought process"}
                                <ChevronDown className={cn("w-3 h-3 transition-transform", thinkingOpen && "rotate-180")} />
                            </button>
                            <AnimatePresence>
                                {thinkingOpen && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
                                        <div className={cn("mt-2 ml-1 pl-3 border-l-2 text-sm italic leading-relaxed", theme === "dark" ? "text-gray-400 border-[#76B900]/30" : "text-gray-600 border-[#76B900]/30")}>
                                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{message.thinking}</ReactMarkdown>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}

                    {/* Status pills */}
                    {!isUser && statusParts.length > 0 && (
                        <div className="space-y-0.5">
                            {statusParts.map((p, i) => {
                                if (p.type === "searching") return <StatusPill key={i} icon={Search} label={`Searching: ${p.content}`} color="green" theme={theme} />;
                                if (p.type === "reading") return <StatusPill key={i} icon={BookOpen} label={`Reading: ${p.content}`} color="purple" theme={theme} />;
                                if (p.type === "generating") return <StatusPill key={i} icon={ImageIcon} label={`Generating image: ${p.content}`} color="orange" theme={theme} />;
                                if (p.type === "kb_query") return <StatusPill key={i} icon={Brain} label="Querying knowledge base…" color="blue" theme={theme} />;
                                return null;
                            })}
                        </div>
                    )}

                    {/* Bubble */}
                    <div className={cn(
                        "group relative p-4 rounded-2xl shadow-sm overflow-hidden",
                        isUser
                            ? theme === "dark" ? "bg-gradient-to-br from-[#76B900] to-[#8CD600] text-black rounded-tr-sm shadow-lg shadow-[#76B900]/10" : "bg-[#76B900] text-black rounded-tr-sm"
                            : theme === "dark" ? "bg-[#0A0C12] text-gray-100 rounded-tl-sm border border-white/5" : "bg-white text-gray-900 rounded-tl-sm border border-gray-200 shadow-sm"
                    )}>
                        {isUser ? (
                            <div className="whitespace-pre-wrap break-words text-sm md:text-base">{message.content}</div>
                        ) : message.content?.trim() ? (
                            <div className={cn(
                                "space-y-3 prose prose-sm max-w-none",
                                theme === "dark"
                                    ? "prose-invert prose-headings:text-gray-100 prose-p:text-gray-200 prose-strong:text-white prose-code:text-[#76B900] prose-pre:bg-gray-800/50"
                                    : "prose-headings:text-gray-900 prose-p:text-gray-800 prose-strong:text-gray-900 prose-code:text-blue-600 prose-pre:bg-gray-50"
                            )}>
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    rehypePlugins={[rehypeRaw]}
                                    components={{
                                        sup({ children }) {
                                            return <sup className="text-[10px] text-[#76B900] font-bold leading-none relative -top-0.5 ml-0.5">{children}</sup>;
                                        },
                                        img({ src, alt }) {
                                            if (!src || typeof src !== "string") return null;
                                            return <GeneratedImage src={src} alt={alt ?? "Generated image"} theme={theme} />;
                                        },
                                        code({ node, inline, className, children, ...props }: any) {
                                            const match = /language-(\w+)/.exec(className || "");
                                            const codeStr = String(children).replace(/\n$/, "");
                                            return !inline && match ? (
                                                <div className="relative group/code my-4 rounded-lg overflow-hidden border border-white/10 shadow-sm">
                                                    <div className={cn("flex items-center justify-between px-3 py-1.5 text-xs font-medium border-b", theme === "dark" ? "bg-gray-800 border-white/5 text-gray-400" : "bg-gray-100 border-gray-200 text-gray-500")}>
                                                        <span>{match[1]}</span>
                                                        <button onClick={() => handleCopy(codeStr)} className="flex items-center gap-1.5 hover:text-[#76B900] transition-colors">
                                                            {copied ? <><Check className="w-3 h-3 text-green-500" /><span className="text-green-500">Copied</span></> : <><Copy className="w-3 h-3" /><span>Copy</span></>}
                                                        </button>
                                                    </div>
                                                    <SyntaxHighlighter style={theme === "dark" ? oneDark : oneLight} language={match[1]} PreTag="div" customStyle={{ margin: 0, padding: "1rem", background: "transparent" }} {...props}>
                                                        {codeStr}
                                                    </SyntaxHighlighter>
                                                </div>
                                            ) : (
                                                <code className={cn("px-1 py-0.5 rounded text-[85%] font-mono font-medium", theme === "dark" ? "bg-white/10 text-gray-200" : "bg-black/5 text-gray-800")} {...props}>{children}</code>
                                            );
                                        },
                                    }}
                                >
                                    {processedText}
                                </ReactMarkdown>
                            </div>
                        ) : (
                            <ThinkingIndicator theme={theme} isQuerying={isQuerying} hasKB={hasKB} isKBEnabled={isKBEnabled} status={message.status} />
                        )}

                        {/* Copy button */}
                        {!isUser && message.content?.trim() && (
                            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button onClick={() => handleCopy(message.content)} className={cn("p-1.5 rounded-lg transition-colors", theme === "dark" ? "hover:bg-white/10 text-gray-400 hover:text-white" : "hover:bg-black/5 text-gray-400 hover:text-black")}>
                                    {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Readings */}
                    {!isUser && readings.length > 0 && (
                        <div className="pl-1">
                            <button onClick={() => setReadingsOpen(!readingsOpen)} className={cn("flex items-center gap-2 px-2 py-1 rounded-lg text-xs font-medium transition-colors", theme === "dark" ? "text-gray-500 hover:text-gray-300 hover:bg-white/5" : "text-gray-400 hover:text-gray-600 hover:bg-black/5")}>
                                <BookOpen className="w-3 h-3" />
                                {readings.length} page{readings.length > 1 ? "s" : ""} read
                                <ChevronDown className={cn("w-3 h-3 transition-transform", readingsOpen && "rotate-180")} />
                            </button>
                            <AnimatePresence>
                                {readingsOpen && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.18 }} className="overflow-hidden mt-1 space-y-1">
                                        {readings.map((r, i) => (
                                            <div key={i} className={cn("flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs", theme === "dark" ? "bg-purple-500/10 border-purple-500/15 text-purple-400" : "bg-purple-50 border-purple-100 text-purple-600")}>
                                                <Globe className="w-3 h-3 shrink-0" />
                                                <span className="truncate">{r.content}</span>
                                            </div>
                                        ))}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}

                    {/* Sources */}
                    {!isUser && sources.length > 0 && (
                        <div className="pl-1">
                            <button onClick={() => setSourcesOpen(!sourcesOpen)} className={cn("flex items-center gap-2 px-2 py-1 rounded-lg text-xs font-semibold transition-colors mb-1.5", theme === "dark" ? "text-gray-400 hover:text-gray-200 hover:bg-white/5" : "text-gray-500 hover:text-gray-700 hover:bg-black/5")}>
                                <Globe className="w-3.5 h-3.5 text-[#76B900]" />
                                {sources.length} source{sources.length > 1 ? "s" : ""}
                                <ChevronDown className={cn("w-3 h-3 transition-transform", sourcesOpen && "rotate-180")} />
                            </button>
                            <AnimatePresence initial={false}>
                                {sourcesOpen && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.18 }} className="overflow-hidden">
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                                            {sources.map((src) => <SourceCard key={src.url} source={src} theme={theme} />)}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}

                    {/* Retry */}
                    {isError && onRetry && (
                        <button onClick={onRetry} className={cn("mt-1 flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors w-fit", theme === "dark" ? "bg-red-900/20 text-red-400 hover:bg-red-900/30" : "bg-red-50 text-red-600 hover:bg-red-100")}>
                            <RotateCw className="w-3 h-3" />Retry
                        </button>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

const MessageBubble = React.memo(MessageBubbleBase, (prev, next) =>
    prev.message === next.message &&
    prev.isStreaming === next.isStreaming &&
    prev.isQuerying === next.isQuerying &&
    prev.hasKB === next.hasKB &&
    prev.theme === next.theme
);

export default MessageBubble;
