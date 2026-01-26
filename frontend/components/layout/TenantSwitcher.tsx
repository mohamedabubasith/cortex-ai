
"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Check, Building2, Plus, ArrowRightLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

interface Tenant {
    id: string;
    name: string;
    slug: string;
}

interface TenantSwitcherProps {
    user: any;
}

export default function TenantSwitcher({ user }: TenantSwitcherProps) {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Get current tenant from localStorage or default to first
    const [currentTenantId, setCurrentTenantId] = useState<string>("");

    useEffect(() => {
        // Hydrate from storage or user data
        const stored = localStorage.getItem("tenant_id");
        if (stored && user?.tenant_memberships?.some((m: any) => m.tenant?.id === stored)) {
            setCurrentTenantId(stored);
        } else if (user?.tenant_memberships?.length > 0) {
            // Default to first if none selected or invalid
            const first = user.tenant_memberships[0].tenant.id;
            localStorage.setItem("tenant_id", first);
            setCurrentTenantId(first);
        }

        // Click outside to close
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [user]);

    const handleSwitch = (tenantId: string) => {
        localStorage.setItem("tenant_id", tenantId);
        setCurrentTenantId(tenantId);
        setIsOpen(false);
        // Reload to apply new tenant context across the app
        window.location.reload();
    };

    if (!user || !user.tenant_memberships || user.tenant_memberships.length === 0) return null;

    const currentTenant = user.tenant_memberships.find((m: any) => m.tenant?.id === currentTenantId)?.tenant || user.tenant_memberships[0].tenant;

    return (
        <div className="relative mb-2 px-4" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "flex items-center justify-between w-full px-3 py-2.5 rounded-xl transition-all duration-200 border",
                    isDark
                        ? "bg-white/5 border-white/10 hover:bg-white/10 text-white"
                        : "bg-white border-gray-200 hover:bg-gray-50 text-gray-900"
                )}
            >
                <div className="flex items-center gap-3 overflow-hidden">
                    <div className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 font-bold text-xs uppercase",
                        isDark ? "bg-gradient-to-br from-blue-500/20 to-blue-600/20 text-blue-400 border border-blue-500/20" : "bg-blue-100 text-blue-600"
                    )}>
                        {currentTenant?.name?.substring(0, 2) || "WS"}
                    </div>
                    <div className="flex flex-col items-start min-w-0">
                        <span className="text-xs text-gray-500 font-medium">Workspace</span>
                        <span className="text-sm font-bold truncate w-full text-left max-w-[120px]">
                            {currentTenant?.name || "Select Workspace"}
                        </span>
                    </div>
                </div>
                <ChevronDown className={cn("w-4 h-4 text-gray-500 transition-transform duration-200", isOpen && "rotate-180")} />
            </button>

            {/* Dropdown */}
            {isOpen && (
                <div className={cn(
                    "absolute bottom-full left-4 right-4 mb-2 rounded-xl border shadow-xl overflow-hidden z-50",
                    isDark ? "bg-[#1a1a1a] border-white/10" : "bg-white border-gray-200"
                )}>
                    <div className={cn("p-2 text-xs font-bold uppercase tracking-wider border-b", isDark ? "text-gray-500 border-white/5" : "text-gray-400 border-gray-100")}>
                        Switch Workspace
                    </div>
                    <div className="max-h-[200px] overflow-y-auto">
                        {user.tenant_memberships.map((m: any) => (
                            <button
                                key={m.tenant.id}
                                onClick={() => handleSwitch(m.tenant.id)}
                                className={cn(
                                    "w-full flex items-center gap-3 px-3 py-2.5 transition-colors text-left",
                                    isDark ? "hover:bg-white/5 text-gray-300" : "hover:bg-gray-50 text-gray-700",
                                    currentTenantId === m.tenant.id && (isDark ? "bg-white/5 text-nvidia-green" : "bg-gray-50 text-black font-semibold")
                                )}
                            >
                                <div className={cn(
                                    "w-6 h-6 rounded-md flex items-center justify-center shrink-0 font-bold text-[10px] uppercase",
                                    isDark ? "bg-white/10 text-white" : "bg-gray-200 text-gray-600"
                                )}>
                                    {m.tenant.name.substring(0, 2)}
                                </div>
                                <span className="flex-1 truncate text-sm">{m.tenant.name}</span>
                                {currentTenantId === m.tenant.id && <Check className="w-4 h-4 text-nvidia-green" />}
                            </button>
                        ))}
                    </div>
                    {/* Optional: Create New Workspace button if needed */}
                </div>
            )}
        </div>
    );
}
