"use client";

import { useState, useEffect, createContext, useContext, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
    id: string;
    message: string;
    type: ToastType;
    duration?: number;
}

interface ToastContextType {
    toast: (message: string, type?: ToastType, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const toast = useCallback((message: string, type: ToastType = "info", duration = 3000) => {
        const id = Math.random().toString(36).substring(2, 9);
        setToasts((prev) => [...prev, { id, message, type, duration }]);

        if (duration > 0) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
    }, [removeToast]);

    return (
        <ToastContext.Provider value={{ toast }}>
            {children}
            <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
                <AnimatePresence mode="popLayout">
                    {toasts.map((t) => (
                        <ToastItem key={t.id} toast={t} onRemove={removeToast} />
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    const icons = {
        success: <Check className="w-5 h-5 text-black" />,
        error: <AlertCircle className="w-5 h-5 text-white" />,
        info: <Info className="w-5 h-5 text-white" />,
        warning: <AlertTriangle className="w-5 h-5 text-black" />
    };

    const styles = {
        success: "bg-[#76B900] text-black border-[#76B900]",
        error: "bg-red-600 text-white border-red-500",
        info: "bg-blue-600 text-white border-blue-500",
        warning: "bg-yellow-400 text-black border-yellow-500"
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
            className={cn(
                "pointer-events-auto flex items-center w-full max-w-sm p-4 rounded-xl shadow-2xl border backdrop-blur-md",
                styles[toast.type]
            )}
        >
            <div className="flex-shrink-0 mr-3">
                {icons[toast.type]}
            </div>
            <div className="flex-1 text-sm font-bold mr-2">
                {toast.message}
            </div>
            <button
                onClick={() => onRemove(toast.id)}
                className="flex-shrink-0 p-1 rounded-full hover:bg-black/10 transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </motion.div>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error("useToast must be used within a ToastProvider");
    }
    return context;
}
