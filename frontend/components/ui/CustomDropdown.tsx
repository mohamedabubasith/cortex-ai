"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

interface CustomDropdownProps<T> {
    options: T[];
    value: T | null;
    onChange: (value: T) => void;
    getLabel: (option: T) => string;
    getSubtitle?: (option: T) => string; // Optional subtitle for rich content
    getKey: (option: T) => string | number;
    placeholder?: string;
    className?: string;
    disabled?: boolean;
}

export default function CustomDropdown<T>({
    options,
    value,
    onChange,
    getLabel,
    getSubtitle,
    getKey,
    placeholder = "Select an option",
    className,
    disabled = false
}: CustomDropdownProps<T>) {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const { theme } = useTheme();
    const isDark = theme === "dark";

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleSelect = (option: T) => {
        onChange(option);
        setIsOpen(false);
    };

    return (
        <div className={cn("relative", className)} ref={containerRef}>
            <button
                type="button"
                onClick={() => !disabled && setIsOpen(!isOpen)}
                disabled={disabled}
                className={cn(
                    "w-full flex items-center justify-between px-4 py-2.5 rounded-xl border transition-all duration-200 text-left",
                    isDark
                        ? "bg-black/50 border-gray-700 text-white hover:border-nvidia-green/50 focus:border-nvidia-green"
                        : "bg-white border-gray-200 text-gray-900 hover:border-nvidia-green/50 focus:border-nvidia-green",
                    disabled && "opacity-50 cursor-not-allowed",
                    isOpen && "ring-2 ring-nvidia-green/20 border-nvidia-green"
                )}
            >
                <span className={cn("block truncate", !value && "text-gray-500")}>
                    {value ? getLabel(value) : placeholder}
                </span>
                <ChevronDown
                    className={cn(
                        "w-4 h-4 transition-transform duration-200 opacity-50",
                        isOpen && "transform rotate-180"
                    )}
                />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 5, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 5, scale: 0.95 }}
                        transition={{ duration: 0.1, ease: "easeOut" }}
                        className={cn(
                            "absolute z-50 w-full mt-2 rounded-xl border shadow-xl overflow-hidden max-h-60 overflow-y-auto",
                            isDark
                                ? "bg-[#1a1a1a] border-gray-700"
                                : "bg-white border-gray-200"
                        )}
                    >
                        <div className="p-1">
                            {options.length > 0 ? (
                                options.map((option) => {
                                    const isSelected = value && getKey(value) === getKey(option);
                                    return (
                                        <button
                                            key={getKey(option)}
                                            type="button"
                                            onClick={() => handleSelect(option)}
                                            className={cn(
                                                "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors",
                                                isSelected
                                                    ? "bg-nvidia-green/10 text-nvidia-green font-medium"
                                                    : isDark
                                                        ? "text-gray-300 hover:bg-white/5 hover:text-white"
                                                        : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                                            )}
                                        >
                                            <div className="flex flex-col items-start overflow-hidden">
                                                <span className="truncate w-full text-left">{getLabel(option)}</span>
                                                {getSubtitle && (
                                                    <span className={cn(
                                                        "text-xs truncate w-full text-left mt-0.5",
                                                        isSelected ? "text-nvidia-green/70" : "text-gray-500"
                                                    )}>
                                                        {getSubtitle(option)}
                                                    </span>
                                                )}
                                            </div>
                                            {isSelected && (
                                                <Check className="w-4 h-4 ml-2 flex-shrink-0" />
                                            )}
                                        </button>
                                    );
                                })
                            ) : (
                                <div className={cn("px-4 py-3 text-sm text-center", isDark ? "text-gray-500" : "text-gray-400")}>
                                    No options available
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
