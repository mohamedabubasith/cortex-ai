import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

interface SidePanelProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    width?: string; // e.g., "50%", "600px", "max-w-2xl"
}

export default function SidePanel({ isOpen, onClose, title, children, width = "50%" }: SidePanelProps) {
    const panelRef = useRef<HTMLDivElement>(null);
    const { theme } = useTheme();
    const isDark = theme === "dark";

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
            document.body.style.overflow = "unset";
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[60] flex justify-end">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity animate-in fade-in duration-200"
                onClick={onClose}
            />

            {/* Panel */}
            <div
                ref={panelRef}
                className={cn(
                    "relative h-full border-l shadow-2xl flex flex-col animate-in slide-in-from-right duration-300 w-full md:w-[var(--panel-width)]",
                    isDark ? "bg-[#0a0a0a] border-white/10" : "bg-white border-gray-200"
                )}
                style={{ '--panel-width': typeof width === 'number' ? `${width}px` : width } as React.CSSProperties}
            >
                {/* Header */}
                <div className={cn("flex items-center justify-between px-6 py-4 border-b", isDark ? "border-white/10 bg-[#0a0a0a]" : "border-gray-100 bg-gray-50")}>
                    <h2 className={cn("text-xl font-bold tracking-tight", isDark ? "text-white" : "text-gray-900")}>{title}</h2>
                    <button
                        onClick={onClose}
                        className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                    {children}
                </div>
            </div>
        </div>
    );
}
