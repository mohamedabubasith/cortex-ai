"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect } from "react";
import { useTheme } from "@/contexts/ThemeContext";

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
}

export default function Dialog({
    isOpen,
    onClose,
    title,
    description,
    children,
    buttons = [],
    theme: propTheme
}: DialogProps) {
    const { theme: globalTheme } = useTheme();
    const theme = propTheme || globalTheme;

    // Close on escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };
        if (isOpen) document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, [isOpen, onClose]);

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4 text-center">
                        {/* Backdrop with "Water Tint" (Blur + Color Overlay) */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/40 backdrop-blur-sm"
                            aria-hidden="true"
                        />

                        {/* Dialog Panel */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            transition={{ type: "spring", duration: 0.3 }}
                            className={cn(
                                "relative z-10 w-full max-w-md rounded-2xl shadow-2xl border flex flex-col mx-4 text-left overflow-visible",
                                theme === 'dark'
                                    ? "bg-[#0a0a0a] border-[#76B900]/20 shadow-[#76B900]/5"
                                    : "bg-white border-gray-200 shadow-xl"
                            )}
                        >
                            {/* Header */}
                            <div className={cn(
                                "px-6 py-4 border-b flex items-center justify-between shrink-0 rounded-t-2xl",
                                theme === 'dark' ? "border-gray-800 bg-gray-900/30" : "border-gray-100 bg-gray-50"
                            )}>
                                <h3 className={cn("text-lg font-bold", theme === 'dark' ? "text-white" : "text-gray-900")}>
                                    {title}
                                </h3>
                                <button
                                    onClick={onClose}
                                    className={cn(
                                        "p-1 rounded-lg transition-colors",
                                        theme === 'dark' ? "text-gray-500 hover:text-white hover:bg-white/10" : "text-gray-400 hover:text-black hover:bg-black/5"
                                    )}
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="px-6 py-6">
                                {description && (
                                    <p className={cn("mb-4 text-sm", theme === 'dark' ? "text-gray-400" : "text-gray-600")}>
                                        {description}
                                    </p>
                                )}
                                {children}
                            </div>

                            {/* Footer / Buttons */}
                            {(buttons.length > 0) && (
                                <div className={cn(
                                    "px-6 py-4 flex justify-end space-x-3 shrink-0 rounded-b-2xl",
                                    theme === 'dark' ? "bg-gray-900/30" : "bg-gray-50"
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
                                                "px-4 py-2 rounded-xl text-sm font-bold transition-all flex items-center",
                                                btn.variant === 'primary' && "bg-[#76B900] text-black hover:bg-[#6aa600]",
                                                btn.variant === 'secondary' && (theme === 'dark' ? "bg-white text-black hover:bg-gray-200" : "bg-black text-white hover:bg-gray-800"),
                                                btn.variant === 'danger' && "bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20",
                                                (!btn.variant || btn.variant === 'outline') && (theme === 'dark' ? "border border-gray-700 text-gray-300 hover:bg-gray-800" : "border border-gray-300 text-gray-700 hover:bg-gray-100"),
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
        </AnimatePresence>
    );
}
