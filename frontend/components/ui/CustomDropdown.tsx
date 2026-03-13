"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

interface CustomDropdownProps<T> {
    options: T[];
    value: T | null;
    onChange: (value: T) => void;
    getLabel: (option: T) => string;
    getSubtitle?: (option: T) => string;
    getKey: (option: T) => string | number;
    placeholder?: string;
    className?: string;
    disabled?: boolean;
    theme?: "dark" | "light";
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
    disabled = false,
    theme: propTheme
}: CustomDropdownProps<T>) {
    const [isOpen, setIsOpen] = useState(false);
    const [menuStyle, setMenuStyle] = useState<React.CSSProperties>({});
    const [mounted, setMounted] = useState(false);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);
    const { theme: globalTheme } = useTheme();
    const theme = propTheme || globalTheme;
    const isDark = theme === "dark";

    useEffect(() => { setMounted(true); }, []);

    const updateMenuPosition = useCallback(() => {
        if (!buttonRef.current) return;
        const rect = buttonRef.current.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom - 8;
        const spaceAbove = rect.top - 8;
        const maxMenu = 240;

        // Prefer upward if below space is insufficient
        const openUpward = spaceBelow < maxMenu && spaceAbove > spaceBelow;

        setMenuStyle({
            position: "fixed",
            left: rect.left,
            width: rect.width,
            maxHeight: openUpward
                ? Math.min(maxMenu, spaceAbove)
                : Math.min(maxMenu, spaceBelow),
            ...(openUpward
                ? { bottom: window.innerHeight - rect.top + 4 }
                : { top: rect.bottom + 4 }),
            zIndex: 99999,
        });
    }, []);

    const handleOpen = () => {
        if (disabled) return;
        updateMenuPosition();
        setIsOpen(prev => !prev);
    };

    // Close on outside click
    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (
                buttonRef.current?.contains(e.target as Node) ||
                menuRef.current?.contains(e.target as Node)
            ) return;
            setIsOpen(false);
        };
        if (isOpen) document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, [isOpen]);

    // Close on outside scroll, reposition on resize
    useEffect(() => {
        const handleScroll = (e: Event) => {
            // Don't close when scrolling inside the dropdown menu itself
            if (menuRef.current?.contains(e.target as Node)) return;
            setIsOpen(false);
        };
        const reposition = () => { if (isOpen) updateMenuPosition(); };
        window.addEventListener("resize", reposition);
        window.addEventListener("scroll", handleScroll, true);
        return () => {
            window.removeEventListener("resize", reposition);
            window.removeEventListener("scroll", handleScroll, true);
        };
    }, [isOpen, updateMenuPosition]);

    const handleSelect = (option: T) => {
        onChange(option);
        setIsOpen(false);
    };

    const menu = (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    ref={menuRef}
                    style={menuStyle}
                    initial={{ opacity: 0, y: 4, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 4, scale: 0.97 }}
                    transition={{ duration: 0.1, ease: "easeOut" }}
                    className={cn(
                        "rounded-xl border shadow-2xl overflow-y-auto",
                        isDark
                            ? "bg-[#1a1a1a] border-gray-700 text-white"
                            : "bg-white border-gray-200 text-black"
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
                                            "w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-colors",
                                            isSelected
                                                ? "bg-nvidia-green/10 text-nvidia-green font-medium"
                                                : isDark
                                                    ? "text-white hover:bg-white/10"
                                                    : "text-black hover:bg-gray-100"
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
                                        {isSelected && <Check className="w-4 h-4 ml-2 flex-shrink-0" />}
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
    );

    return (
        <div className={cn("relative", className)}>
            <button
                ref={buttonRef}
                type="button"
                onClick={handleOpen}
                disabled={disabled}
                className={cn(
                    "w-full flex items-center justify-between px-4 py-3 rounded-xl border text-base transition-all duration-200 text-left",
                    isDark
                        ? "bg-black/50 border-gray-700 text-white hover:border-nvidia-green/50"
                        : "bg-white border-gray-200 text-black hover:border-nvidia-green/50",
                    disabled && "opacity-50 cursor-not-allowed",
                    isOpen && "ring-2 ring-nvidia-green/20 border-nvidia-green"
                )}
            >
                <span className={cn("block truncate", !value && "text-gray-500")}>
                    {value ? getLabel(value) : placeholder}
                </span>
                <ChevronDown className={cn("w-4 h-4 transition-transform duration-200 opacity-50 shrink-0 ml-2", isOpen && "rotate-180")} />
            </button>

            {mounted && createPortal(menu, document.body)}
        </div>
    );
}
