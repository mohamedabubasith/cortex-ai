"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Database, Search, Sparkles, Brain } from "lucide-react";
import { cn } from "@/lib/utils";

function AnimatedDots({ theme }: { theme: "dark" | "light" }) {
    return (
        <span className="inline-flex gap-px ml-0.5">
            {[0, 1, 2].map((i) => (
                <motion.span
                    key={i}
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2, ease: "easeInOut" }}
                    className={theme === "dark" ? "text-gray-400" : "text-gray-500"}
                >
                    .
                </motion.span>
            ))}
        </span>
    );
}

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

    const getLabel = () => {
        if (status) return status;
        switch (step) {
            case "thinking":     return "Thinking";
            case "querying":     return "Searching library";
            case "web_search":   return "Searching the web";
            case "reading":      return "Reading sources";
            case "synthesizing": return "Responding";
        }
    };

    return (
        <div className="flex items-center gap-3 py-0.5">
            {/* Icon badge */}
            <div className={cn(
                "flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-lg",
                theme === "dark" ? "bg-white/6" : "bg-black/5"
            )}>
                {getIcon()}
            </div>

            {/* Text + animated dots */}
            <motion.span
                key={step}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 6 }}
                transition={{ duration: 0.2 }}
                className={cn(
                    "text-sm font-medium leading-none flex items-baseline",
                    theme === "dark" ? "text-gray-300" : "text-gray-600"
                )}
            >
                {getLabel()}
                <AnimatedDots theme={theme} />
            </motion.span>
        </div>
    );
}
