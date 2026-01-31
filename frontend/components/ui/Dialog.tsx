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
    className?: string; // Content container override
}

export default function Dialog({
    isOpen,
    onClose,
    title,
    description,
    children,
    buttons = [],
    theme: propTheme,
    maxWidth = "max-w-lg", // Default
    className
}: DialogProps) {
    const { theme: globalTheme } = useTheme();
    const theme = propTheme || globalTheme;

    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    // Close on escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };
        if (isOpen) document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, [isOpen, onClose]);

    if (!mounted) return null;

    return createPortal(
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] overflow-y-auto block">
                    <div className="flex min-h-screen items-center justify-center p-4 text-center">
                        {/* Backdrop with stronger blur for focus */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-all"
                            aria-hidden="true"
                        />

                        {/* Dialog Panel */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            transition={{ type: "spring", duration: 0.4, bounce: 0.2 }}
                            className={cn(
                                "relative z-10 w-full rounded-2xl shadow-2xl flex flex-col mx-4 text-left overflow-hidden ring-1",
                                maxWidth, // Apply dynamic max-width
                                theme === 'dark'
                                    ? "bg-[#0f0f0f]/90 backdrop-blur-xl ring-white/10 shadow-[0_0_50px_-12px_rgba(0,0,0,0.5)]"
                                    : "bg-white/90 backdrop-blur-xl ring-black/5 shadow-xl"
                            )}
                        >
                            {/* Decorative Top Gradient Line */}
                            <div className={cn("absolute top-0 left-0 w-full h-1 bg-gradient-to-r",
                                theme === 'dark' ? "from-nvidia-green/40 via-nvidia-green to-nvidia-green/40" : "from-gray-200 via-gray-400 to-gray-200"
                            )} />

                            {/* Header */}
                            <div className={cn(
                                "px-8 py-6 flex items-start justify-between shrink-0",
                                theme === 'dark' ? "text-white" : "text-gray-900"
                            )}>
                                <div>
                                    <h3 className="text-xl font-bold tracking-tight">
                                        {title}
                                    </h3>
                                    {description && (
                                        <p className={cn("mt-2 text-sm leading-relaxed", theme === 'dark' ? "text-gray-400" : "text-gray-500")}>
                                            {description}
                                        </p>
                                    )}
                                </div>
                                <button
                                    onClick={onClose}
                                    className={cn(
                                        "p-2 rounded-full transition-all duration-200 -mr-2 -mt-2",
                                        theme === 'dark' ? "text-gray-500 hover:text-white hover:bg-white/10" : "text-gray-400 hover:text-black hover:bg-black/5"
                                    )}
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="px-8 pb-8 pt-2">
                                {children}
                            </div>

                            {/* Footer / Buttons */}
                            {(buttons.length > 0) && (
                                <div className={cn(
                                    "px-4 sm:px-8 py-4 sm:py-5 flex flex-col sm:flex-row justify-end gap-3 shrink-0",
                                    theme === 'dark' ? "bg-white/5 border-t border-white/5" : "bg-gray-50 border-t border-gray-100"
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
                                                "px-4 sm:px-5 py-2 sm:py-2.5 rounded-lg text-sm font-bold transition-all duration-200 flex items-center justify-center shadow-sm w-full sm:w-auto",
                                                btn.variant === 'primary' && "bg-nvidia-green text-black hover:bg-[#8CD600] ring-1 ring-[#6aa600]/50 hover:shadow-[0_0_15px_rgba(118,185,0,0.3)]",
                                                btn.variant === 'secondary' && (theme === 'dark' ? "bg-white text-black hover:bg-gray-200" : "bg-black text-white hover:bg-gray-800"),
                                                btn.variant === 'danger' && "bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20",
                                                (!btn.variant || btn.variant === 'outline') && (theme === 'dark' ? "ring-1 ring-white/10 text-gray-300 hover:bg-white/5 hover:text-white" : "ring-1 ring-gray-200 text-gray-700 hover:bg-gray-50 hover:text-gray-900"),
                                                btn.isLoading && "opacity-50 cursor-not-allowed"
                                            )}
                                        >
                                            {btn.isLoading && (
                                                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                                            )}
                                            {btn.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </motion.div>
                    </div>
                </div>
            )}
        </AnimatePresence>,
        document.body
    );
}
