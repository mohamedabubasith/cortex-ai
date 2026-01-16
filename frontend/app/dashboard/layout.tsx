"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Cpu, Database, Bot, LogOut, Menu, X, Sun, Moon, Users, FileText, ChevronDown, Check, Plus } from "lucide-react";
import Logo from "@/components/Logo";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { useEffect } from "react";
import TenantMembersModal from "@/components/TenantMembersModal";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [user, setUser] = useState<any>(null);
    const [showTeamModal, setShowTeamModal] = useState(false);

    const { theme, toggleTheme } = useTheme();
    const isDark = theme === "dark";

    useEffect(() => {
        api.get("/auth/me").then(res => setUser(res.data)).catch(console.error);
    }, []);

    const navigation = [
        { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { name: "Providers", href: "/dashboard/providers", icon: Cpu },
        { name: "Knowledge Base", href: "/dashboard/kb", icon: Database },
        { name: "Agents", href: "/dashboard/agents", icon: Bot },
        { name: "Organization", href: "/dashboard/organization", icon: Users },
        { name: "Audit Logs", href: "/dashboard/audit", icon: FileText },
    ];

    if (user?.is_superuser) {
        navigation.push({ name: "Visitors", href: "/dashboard/visitors", icon: Users });
    }

    return (
        <div className={`h-[100dvh] flex overflow-hidden ${isDark ? "bg-black" : "bg-gray-50"}`}>
            {/* Sidebar */}
            <div className={`fixed inset-y-0 left-0 z-50 w-64 border-r transform transition-transform duration-200 ease-in-out ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0 md:static md:inset-0 ${isDark ? "bg-nvidia-dark border-white/10" : "bg-white border-gray-200"}`}>
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    {/* Logo & Tenant Switcher */}
                    <div className={cn("flex items-center justify-between px-4 h-20 border-b relative", isDark ? "border-white/10" : "border-gray-200")}>
                        {/* Tenant Switcher Dropdown */}
                        <div className="relative w-full mr-2">
                            <button
                                onClick={() => setUser((prev: any) => ({ ...prev, _isTenantDropdownOpen: !prev?._isTenantDropdownOpen }))}
                                className={cn(
                                    "flex items-center w-full px-2 py-2 rounded-lg transition-colors group",
                                    isDark ? "hover:bg-white/5" : "hover:bg-gray-100"
                                )}
                            >
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-nvidia-green to-emerald-600 flex items-center justify-center shrink-0 shadow-lg shadow-nvidia-green/20 mr-3">
                                    <Bot className="w-5 h-5 text-black" />
                                </div>
                                <div className="flex-1 text-left overflow-hidden">
                                    <span className={cn("block text-xs font-medium text-gray-500 mb-0.5")}>
                                        Organization
                                    </span>
                                    <div className="flex items-center justify-between">
                                        <span className={cn("text-sm font-bold truncate", isDark ? "text-white" : "text-gray-900")}>
                                            {user?.tenant_memberships?.find((m: any) => m.tenant_id === (typeof window !== 'undefined' ? localStorage.getItem('activeTenantId') : null))?.tenant?.name || "Cortex AI"}
                                        </span>
                                        <ChevronDown className="w-4 h-4 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                </div>
                            </button>

                            {/* Dropdown Menu */}
                            {user?._isTenantDropdownOpen && (
                                <>
                                    <div
                                        className="fixed inset-0 z-40"
                                        onClick={() => setUser((prev: any) => ({ ...prev, _isTenantDropdownOpen: false }))}
                                    />
                                    <div className={cn(
                                        "absolute top-full left-0 w-full mt-2 rounded-xl border p-2 shadow-xl z-50 animate-in fade-in zoom-in-95 duration-200",
                                        isDark ? "bg-[#0A0A0A] border-white/10" : "bg-white border-gray-200"
                                    )}>
                                        <div className="px-2 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                                            Switch Organization
                                        </div>
                                        {user?.tenant_memberships?.map((membership: any) => {
                                            const isActive = membership.tenant_id === localStorage.getItem('activeTenantId');
                                            return (
                                                <button
                                                    key={membership.tenant_id}
                                                    onClick={() => {
                                                        localStorage.setItem('activeTenantId', membership.tenant_id);
                                                        window.location.reload();
                                                    }}
                                                    className={cn(
                                                        "w-full flex items-center px-3 py-2.5 rounded-lg text-sm transition-colors mb-1",
                                                        isActive
                                                            ? (isDark ? "bg-white/10 text-white" : "bg-gray-100 text-gray-900")
                                                            : (isDark ? "text-gray-400 hover:text-white hover:bg-white/5" : "text-gray-600 hover:text-gray-900 hover:bg-gray-50")
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "w-2 h-2 rounded-full mr-3",
                                                        isActive ? "bg-nvidia-green shadow-[0_0_8px_rgba(118,185,0,0.5)]" : "bg-gray-500"
                                                    )} />
                                                    <span className="flex-1 text-left truncate">{membership.tenant.name}</span>
                                                    {isActive && <Check className="w-4 h-4 text-nvidia-green ml-2" />}
                                                </button>
                                            )
                                        })}

                                        <div className="h-px bg-white/10 my-1.5 mx-1" />

                                        <Link
                                            href="/dashboard/organization"
                                            onClick={() => setUser((prev: any) => ({ ...prev, _isTenantDropdownOpen: false }))}
                                            className={cn(
                                                "w-full flex items-center px-3 py-2.5 rounded-lg text-sm transition-colors",
                                                isDark ? "text-gray-400 hover:text-white hover:bg-white/5" : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                            )}
                                        >
                                            <div className="w-5 h-5 rounded-md border border-dashed border-gray-500 flex items-center justify-center mr-2">
                                                <Plus className="w-3 h-3" />
                                            </div>
                                            Create / Manage
                                        </Link>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Close Button (Mobile Only) */}
                        <button
                            onClick={() => setIsMobileMenuOpen(false)}
                            className={`md:hidden p-2 ml-2 ${isDark ? "text-gray-400 hover:text-white" : "text-gray-600 hover:text-gray-900"}`}
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href;
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    onClick={() => setIsMobileMenuOpen(false)}
                                    className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${isActive
                                        ? "bg-nvidia-green text-black shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                                        : isDark
                                            ? "text-gray-400 hover:bg-white/5 hover:text-white"
                                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                        }`}
                                >
                                    <item.icon className={`w-5 h-5 mr-3 ${isActive ? "text-black" : isDark ? "text-gray-400" : "text-gray-600"}`} />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User / Logout */}
                    <div className={`p-4 border-t ${isDark ? "border-white/10" : "border-gray-200"}`}>
                        <button
                            onClick={toggleTheme}
                            className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-xl transition-colors mb-2 ${isDark ? "text-gray-400 hover:bg-white/5 hover:text-white" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"}`}
                        >
                            {isDark ? (
                                <>
                                    <Sun className="w-5 h-5 mr-3" />
                                    Light Mode
                                </>
                            ) : (
                                <>
                                    <Moon className="w-5 h-5 mr-3" />
                                    Dark Mode
                                </>
                            )}
                        </button>
                        <button
                            onClick={() => {
                                localStorage.removeItem("token");
                                window.location.href = "/";
                            }}
                            className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-xl transition-colors ${isDark ? "text-gray-400 hover:bg-red-900/20 hover:text-red-400" : "text-gray-600 hover:bg-red-50 hover:text-red-600"}`}
                        >
                            <LogOut className="w-5 h-5 mr-3" />
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className={`flex-1 flex flex-col min-w-0 overflow-hidden relative ${isDark ? "bg-black" : "bg-gray-50"}`}>
                {/* Mobile Header */}
                <div className={`md:hidden flex items-center justify-between px-4 py-3 border-b sticky top-0 z-40 ${isDark ? "border-white/10 bg-nvidia-dark" : "border-gray-200 bg-white"}`}>
                    <div className="flex items-center space-x-3">
                        <Logo size="sm" />
                        <span className={`text-lg font-bold ${isDark ? "text-white" : "text-gray-900"}`}>Cortex AI</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={toggleTheme}
                            className={`p-2 rounded-lg ${isDark ? "text-gray-400 hover:text-white hover:bg-white/5" : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"}`}
                        >
                            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>
                        <button
                            onClick={() => setIsMobileMenuOpen(true)}
                            className={`p-2 ${isDark ? "text-gray-400 hover:text-white" : "text-gray-600 hover:text-gray-900"}`}
                        >
                            <Menu className="w-6 h-6" />
                        </button>
                    </div>
                </div>



                {/* Background Pattern */}
                <div className={`absolute inset-0 z-0 opacity-20 pointer-events-none ${isDark ? "" : "opacity-10"}`} style={{ backgroundImage: "radial-gradient(circle at 50% 50%, #1a1a1a 1px, transparent 1px)", backgroundSize: "24px 24px" }}></div>

                <main className="flex-1 overflow-y-auto p-4 md:p-8 relative z-10">
                    {children}
                </main>
            </div>

            {/* Team Management Modal */}
            {user && (
                <TenantMembersModal
                    isOpen={showTeamModal}
                    onClose={() => setShowTeamModal(false)}
                    tenantId={user.tenant_memberships?.[0]?.tenant_id || ""}
                />
            )}
        </div>
    );
}
