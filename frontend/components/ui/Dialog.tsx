"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import { createPortal } from "react-dom";

interface DialogButton {
    label: string;
    onClick: () => void;
    variant?: "primary" | "secondary" | "danger" | "outline";
    isLoading?: boolean;
}

interface DialogProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    description?: string;
    children?: React.ReactNode;
    buttons?: DialogButton[];
    theme?: "dark" | "light";
    maxWidth?: string;
    className?: string;
}

export default function Dialog({
    isOpen,
    onClose,
    title,
    description,
    children,
    buttons = [],
    theme: propTheme,
    maxWidth = "max-w-lg",
}: DialogProps) {
    const { theme: globalTheme } = useTheme();
    const theme = propTheme || globalTheme;

    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };
        if (isOpen) {
            document.addEventListener("keydown", handleEscape);
            document.body.style.overflow = "hidden";
        }
        return () => {
            document.removeEventListener("keydown", handleEscape);
            document.body.style.overflow = "";
        };
    }, [isOpen, onClose]);

    if (!mounted) return null;

    return createPortal(
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        aria-hidden="true"
                    />

                    {/* Dialog Panel */}
                    <motion.div
                        initial={{ opacity: 0, y: 40, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 40, scale: 0.97 }}
                        transition={{ type: "spring", duration: 0.35, bounce: 0.15 }}
                        className={cn(
                            "relative z-10 w-full flex flex-col text-left overflow-hidden ring-1",
                            // Mobile: full-width sheet from bottom, capped height
                            "rounded-t-2xl sm:rounded-2xl",
                            "max-h-[92dvh] sm:max-h-[88dvh]",
                            maxWidth,
                            theme === "dark"
                                ? "bg-[#0f0f0f] ring-white/10 shadow-[0_0_50px_-12px_rgba(0,0,0,0.5)]"
                                : "bg-white ring-black/5 shadow-xl"
                        )}
                    >
                        {/* Top accent line */}
                        <div className={cn(
                            "absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r",
                            theme === "dark"
                                ? "from-nvidia-green/30 via-nvidia-green to-nvidia-green/30"
                                : "from-gray-200 via-gray-400 to-gray-200"
                        )} />

                        {/* Mobile drag handle */}
                        <div className="sm:hidden flex justify-center pt-3 pb-1 shrink-0">
                            <div className={cn("w-10 h-1 rounded-full", theme === "dark" ? "bg-white/20" : "bg-gray-300")} />
                        </div>

                        {/* Header */}
                        <div className={cn(
                            "px-5 sm:px-7 py-4 sm:py-5 flex items-start justify-between shrink-0",
                            theme === "dark" ? "text-white" : "text-gray-900"
                        )}>
                            <div className="pr-4">
                                <h3 className="text-lg sm:text-xl font-bold tracking-tight">{title}</h3>
                                {description && (
                                    <p className={cn("mt-1.5 text-sm leading-relaxed", theme === "dark" ? "text-gray-400" : "text-gray-500")}>
                                        {description}
                                    </p>
                                )}
                            </div>
                            <button
                                onClick={onClose}
                                className={cn(
                                    "shrink-0 p-1.5 rounded-full transition-all duration-200",
                                    theme === "dark" ? "text-gray-500 hover:text-white hover:bg-white/10" : "text-gray-400 hover:text-black hover:bg-black/5"
                                )}
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Scrollable Content */}
                        <div className="px-5 sm:px-7 pb-5 sm:pb-6 overflow-y-auto flex-1 overscroll-contain">
                            {children}
                        </div>

                        {/* Footer */}
                        {buttons.length > 0 && (
                            <div className={cn(
                                "px-5 sm:px-7 py-4 flex items-center justify-end gap-2.5 shrink-0",
                                theme === "dark" ? "bg-white/[0.03] border-t border-white/[0.06]" : "bg-gray-50 border-t border-gray-100"
                            )}>
                                {buttons.map((btn, idx) => (
                                    <button
                                        key={idx}
                                        type="button"
                                        onClick={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            btn.onClick();
                                        }}
                                        disabled={btn.isLoading}
                                        className={cn(
                                            "px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 flex items-center justify-center gap-2 shrink-0",
                                            btn.variant === "primary" && "bg-nvidia-green text-black hover:bg-[#8CD600] shadow-sm hover:shadow-[0_0_12px_rgba(118,185,0,0.25)]",
                                            btn.variant === "secondary" && (theme === "dark" ? "bg-white text-black hover:bg-gray-200" : "bg-black text-white hover:bg-gray-800"),
                                            btn.variant === "danger" && "bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20",
                                            (!btn.variant || btn.variant === "outline") && (theme === "dark" ? "ring-1 ring-white/10 text-gray-300 hover:bg-white/5 hover:text-white" : "ring-1 ring-gray-200 text-gray-700 hover:bg-gray-100"),
                                            btn.isLoading && "opacity-50 cursor-not-allowed"
                                        )}
                                    >
                                        {btn.isLoading && (
                                            <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                        )}
                                        {btn.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </motion.div>
                </div>
            )}
        </AnimatePresence>,
        document.body
    );
}
