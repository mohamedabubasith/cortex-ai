"use client";

import { useState, useRef, useEffect } from "react";
import { MoreVertical, Share2, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResourceMenuProps {
    onShare?: () => void;
    onDelete?: () => void;
    isDark?: boolean;
    resourceType?: string;
}

export default function ResourceMenu({
    onShare,
    onDelete,
    isDark = false,
    resourceType = "resource"
}: ResourceMenuProps) {
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
        }

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [isOpen]);

    return (
        <div className="relative" ref={menuRef}>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    setIsOpen(!isOpen);
                }}
                className={cn(
                    "p-2 rounded-lg transition-all hover:scale-110",
                    isDark
                        ? "hover:bg-white/10 text-gray-400 hover:text-white"
                        : "hover:bg-gray-100 text-gray-500 hover:text-gray-900"
                )}
                title="More actions"
            >
                <MoreVertical className="w-4 h-4" />
            </button>

            {isOpen && (
                <div
                    className={cn(
                        "absolute right-0 mt-2 w-48 rounded-lg shadow-lg border z-50 py-1",
                        isDark
                            ? "bg-gray-900 border-white/10"
                            : "bg-white border-gray-200"
                    )}
                >
                    {onShare && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsOpen(false);
                                onShare();
                            }}
                            className={cn(
                                "w-full px-4 py-2 text-left flex items-center gap-3 transition-colors",
                                isDark
                                    ? "hover:bg-white/5 text-gray-300"
                                    : "hover:bg-gray-50 text-gray-700"
                            )}
                        >
                            <Share2 className="w-4 h-4 text-nvidia-green" />
                            <span className="text-sm font-medium">Share {resourceType}</span>
                        </button>
                    )}

                    {onDelete && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsOpen(false);
                                onDelete();
                            }}
                            className={cn(
                                "w-full px-4 py-2 text-left flex items-center gap-3 transition-colors",
                                isDark
                                    ? "hover:bg-red-500/10 text-gray-300 hover:text-red-400"
                                    : "hover:bg-red-50 text-gray-700 hover:text-red-600"
                            )}
                        >
                            <Trash2 className="w-4 h-4 text-red-500" />
                            <span className="text-sm font-medium">Delete {resourceType}</span>
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
