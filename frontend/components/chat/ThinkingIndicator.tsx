"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Database, Search, Sparkles, Brain } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThinkingIndicatorProps {
    theme?: "dark" | "light";
    isQuerying?: boolean; // If true, forces "Querying" state
    hasKB?: boolean; // If true, shows "Querying Knowledge Base" step
    isKBEnabled?: boolean; // If true, allows KB querying step
    status?: string; // Real-time status from stream (e.g. "Searching web...")
}

export default function ThinkingIndicator({ theme = "dark", isQuerying = false, hasKB = false, isKBEnabled = true, status }: ThinkingIndicatorProps) {
    const [step, setStep] = useState<"thinking" | "querying" | "synthesizing" | "web_search" | "reading">("thinking");

    useEffect(() => {
        if (status) {
            if (status.includes("Searching")) setStep("web_search");
            else if (status.includes("Reading")) setStep("reading");
            else if (status.includes("knowledge")) setStep("querying");
            return;
        }

        const thinkingDuration = 2000 + Math.random() * 1000; // 2-3s
        const queryingDuration = 2500 + Math.random() * 1000; // 2.5-3.5s

        // Only show querying step if Agent HAS KB AND KB is ENABLED
        const shouldShowQuerying = hasKB && isKBEnabled;

        const t1 = setTimeout(() => {
            if (shouldShowQuerying) {
                setStep("querying");
            } else {
                setStep("synthesizing");
            }
        }, thinkingDuration);

        const t2 = setTimeout(() => {
            if (shouldShowQuerying) {
                setStep("synthesizing");
            }
        }, thinkingDuration + (shouldShowQuerying ? queryingDuration : 0));

        return () => {
            clearTimeout(t1);
            clearTimeout(t2);
        };
    }, [isQuerying, hasKB, isKBEnabled, status]);

    const getIcon = () => {
        switch (step) {
            case "thinking":
                return <Brain className="w-4 h-4 animate-pulse text-[#76B900]" />;
            case "querying":
                return <Database className="w-4 h-4 animate-bounce text-blue-400" />;
            case "web_search":
                return <Search className="w-4 h-4 animate-spin text-[#76B900]" />;
            case "reading":
                return <Database className="w-4 h-4 animate-pulse text-purple-400" />;
            case "synthesizing":
                return <Sparkles className="w-4 h-4 animate-spin-slow text-yellow-400" />;
        }
    };

    const getText = () => {
        if (status) return status;
        switch (step) {
            case "thinking":
                return "Thinking...";
            case "querying":
                return "Searching library...";
            case "web_search":
                return "Searching the web...";
            case "reading":
                return "Reading sources...";
            case "synthesizing":
                return "Responding...";
        }
    };

    return (
        <div className="flex items-center space-x-3">
            <div className={cn(
                "flex items-center justify-center w-8 h-8 rounded-full shadow-sm",
                theme === 'dark' ? "bg-gray-800 text-[#76B900]" : "bg-gray-100 text-[#76B900]"
            )}>
                {getIcon()}
            </div>
            <div className="flex flex-col">
                <motion.span
                    key={step}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                    className={cn(
                        "text-sm font-medium animate-pulse",
                        theme === 'dark' ? "text-gray-200" : "text-gray-800"
                    )}
                >
                    {getText()}
                </motion.span>
            </div>
        </div>
    );
}
