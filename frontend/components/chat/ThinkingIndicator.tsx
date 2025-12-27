"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Database, Search, Sparkles, Brain } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThinkingIndicatorProps {
    theme?: "dark" | "light";
    isQuerying?: boolean; // If true, forces "Querying" state
    hasKB?: boolean; // If true, shows "Querying Knowledge Base" step
}

export default function ThinkingIndicator({ theme = "dark", isQuerying = false, hasKB = false }: ThinkingIndicatorProps) {
    const [step, setStep] = useState<"thinking" | "querying" | "synthesizing">("thinking");

    // Cycle through states to simulate "agentic" behavior
    useEffect(() => {
        if (isQuerying) {
            setStep("querying");
            return;
        }

        const thinkingDuration = 2000 + Math.random() * 1000; // 2-3s
        const queryingDuration = 2500 + Math.random() * 1000; // 2.5-3.5s

        const t1 = setTimeout(() => {
            if (hasKB) {
                setStep("querying");
            } else {
                setStep("synthesizing");
            }
        }, thinkingDuration);

        const t2 = setTimeout(() => {
            if (hasKB) {
                setStep("synthesizing");
            }
        }, thinkingDuration + (hasKB ? queryingDuration : 0));

        return () => {
            clearTimeout(t1);
            clearTimeout(t2);
        };
    }, [isQuerying, hasKB]);

    const getIcon = () => {
        switch (step) {
            case "thinking":
                return <Brain className="w-4 h-4 animate-pulse" />;
            case "querying":
                return <Database className="w-4 h-4 animate-bounce" />;
            case "synthesizing":
                return <Sparkles className="w-4 h-4 animate-spin-slow" />;
        }
    };

    const getText = () => {
        switch (step) {
            case "thinking":
                return "Thinking...";
            case "querying":
                return "Fetching from knowledge...";
            case "synthesizing":
                return "Synthesizing Response...";
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
                        "text-sm font-medium",
                        theme === 'dark' ? "text-gray-200" : "text-gray-800"
                    )}
                >
                    {getText()}
                </motion.span>
            </div>
        </div>
    );
}
