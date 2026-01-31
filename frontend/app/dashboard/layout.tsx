"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Cpu, Database, Bot, LogOut, Menu, X, Sun, Moon, Users, FileText, ShoppingBag, Shield, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import Logo from "@/components/Logo";
import { useTheme } from "@/contexts/ThemeContext";
import TenantSwitcher from "@/components/layout/TenantSwitcher";
import { useAuth } from "@/contexts/AuthContext";
import AuthGuard from "@/components/layout/AuthGuard";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(false);

    // Use AuthContext for correct active tenant context
    const { user, role } = useAuth();

    const { theme, toggleTheme } = useTheme();
    const isDark = theme === "dark";

    const navigation = [
        { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { name: "Providers", href: "/dashboard/providers", icon: Cpu },
        { name: "Knowledge Base", href: "/dashboard/kb", icon: Database },
        { name: "Agents", href: "/dashboard/agents", icon: Bot },
        { name: "MCP Hub", href: "/dashboard/mcp", icon: ShoppingBag },
        { name: "Audit Logs", href: "/dashboard/audit", icon: FileText },
    ];

    if (user?.is_superuser) {
        navigation.push({ name: "Visitors", href: "/dashboard/visitors", icon: Users });
    }

    // Check if current active role is Admin or Owner OR if user is a Superuser
    // We match case-insensitive or specific names from backend seeding
    const isAdmin = user?.is_superuser || role?.name === "Owner" || role?.name === "Admin";

    return (
        <AuthGuard>
            <div className={`h-[100dvh] flex overflow-hidden ${isDark ? "bg-black" : "bg-gray-50"}`}>
                {/* Mobile Backdrop */}
                {isMobileMenuOpen && (
                    <div
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden transition-opacity duration-300"
                        onClick={() => setIsMobileMenuOpen(false)}
                    />
                )}

                {/* Sidebar */}
                <div className={`fixed inset-y-0 left-0 z-50 transform transition-all duration-300 ease-in-out ${isMobileMenuOpen ? "translate-x-0 w-64" : "-translate-x-full"} md:translate-x-0 md:static md:inset-0 ${isCollapsed ? "md:w-20" : "md:w-64"} ${isDark ? "bg-nvidia-dark border-r border-white/10" : "bg-white border-r border-gray-200"}`}>
                    <div className="flex flex-col h-full transition-all duration-300">
                        {/* Logo & Toggle */}
                        <div className={`flex items-center ${isCollapsed ? "flex-col justify-center space-y-2 py-4" : "flex-row justify-between px-4"} h-auto min-h-[5rem] border-b ${isDark ? "border-white/10" : "border-gray-200"}`}>
                            {!isCollapsed && (
                                <Link href="/dashboard" className="flex items-center space-x-3 transition-opacity duration-200">
                                    <Logo size="sm" />
                                    <span className={`text-xl font-bold tracking-tight whitespace-nowrap ${isDark ? "text-white" : "text-gray-900"}`}>Basivo</span>
                                </Link>
                            )}
                            {isCollapsed && (
                                <Link href="/dashboard" className="mb-1">
                                    <Logo size="sm" />
                                </Link>
                            )}

                            {/* Desktop Toggle Button */}
                            <button
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                className={`hidden md:flex p-1.5 rounded-lg transition-colors ${isDark ? "text-gray-400 hover:text-white hover:bg-white/10" : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"}`}
                                title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                            >
                                {isCollapsed ? <PanelLeftOpen className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
                            </button>

                            {/* Mobile Close */}
                            <button
                                onClick={() => setIsMobileMenuOpen(false)}
                                className={`md:hidden p-2 ${isDark ? "text-gray-400 hover:text-white" : "text-gray-600 hover:text-gray-900"}`}
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>


                        {/* Scrollable Content (Nav + Admin) */}
                        <div className="flex-1 overflow-y-auto py-6 space-y-6 custom-scrollbar">
                            <nav className={`space-y-2 ${isCollapsed ? "px-2" : "px-4"}`}>
                                {navigation.map((item) => {
                                    const isActive = pathname === item.href;
                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            onClick={() => setIsMobileMenuOpen(false)}
                                            title={isCollapsed ? item.name : undefined}
                                            className={`flex items-center ${isCollapsed ? "justify-center p-3" : "px-4 py-3"} text-sm font-medium rounded-xl transition-all duration-200 ${isActive
                                                ? "bg-nvidia-green text-black shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                                                : isDark
                                                    ? "text-gray-400 hover:bg-white/5 hover:text-white"
                                                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                                }`}
                                        >
                                            <item.icon className={`w-5 h-5 ${isCollapsed ? "" : "mr-3"} ${isActive ? "text-black" : isDark ? "text-gray-400" : "text-gray-600"}`} />
                                            {!isCollapsed && <span className="whitespace-nowrap">{item.name}</span>}
                                        </Link>
                                    );
                                })}
                            </nav>

                            {/* Administration Section - Scoped to Active Tenant via isAdmin check */}
                            {isAdmin && (
                                <div>
                                    {!isCollapsed && (
                                        <div className={`text-xs font-bold uppercase mb-2 px-4 whitespace-nowrap ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                                            Administration
                                        </div>
                                    )}
                                    {isCollapsed && <div className={`h-px mx-4 my-2 ${isDark ? "bg-white/10" : "bg-gray-200"}`} />}

                                    <div className={`space-y-1 ${isCollapsed ? "px-2" : ""}`}>
                                        {[
                                            { name: "Users & Groups", href: "/dashboard/admin/users", icon: Users },
                                            { name: "Roles & Permissions", href: "/dashboard/admin/roles", icon: Shield }
                                        ].map((item) => {
                                            const isActive = pathname === item.href;
                                            return (
                                                <Link
                                                    key={item.name}
                                                    href={item.href}
                                                    onClick={() => setIsMobileMenuOpen(false)}
                                                    title={isCollapsed ? item.name : undefined}
                                                    className={`flex items-center ${isCollapsed ? "justify-center p-2.5" : "px-4 py-2"} text-sm font-medium rounded-xl transition-all duration-200 ${isActive
                                                        ? "bg-nvidia-green text-black shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                                                        : isDark
                                                            ? "text-gray-400 hover:bg-white/5 hover:text-white"
                                                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                                        }`}
                                                >
                                                    <item.icon className={`w-4 h-4 ${isCollapsed ? "" : "mr-3"} ${isActive ? "text-black" : isDark ? "text-gray-400" : "text-gray-600"}`} />
                                                    {!isCollapsed && <span className="whitespace-nowrap">{item.name}</span>}
                                                </Link>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Tenant Switcher */}
                        <div className={isCollapsed ? "hidden" : "block"}>
                            <TenantSwitcher user={user} />
                        </div>

                        {/* Footer Actions */}
                        <div className={`border-t ${isDark ? "border-white/10" : "border-gray-200"}`}>
                            {/* Desktop: Unified button group */}
                            <div className={`hidden md:block ${isCollapsed ? "p-2" : "p-3"}`}>
                                <div className={`${isCollapsed ? "space-y-1" : "flex items-center gap-2 p-1 rounded-xl"} ${!isCollapsed && (isDark ? "bg-white/5" : "bg-gray-100")}`}>
                                    <button
                                        onClick={toggleTheme}
                                        title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
                                        className={`${isCollapsed ? "w-full p-2.5" : "flex-1 px-3 py-2"} flex items-center justify-center text-sm font-medium rounded-lg transition-colors ${isDark ? "text-gray-400 hover:bg-white/10 hover:text-white" : "text-gray-600 hover:bg-white hover:text-gray-900"}`}
                                    >
                                        {isDark ? <Sun className={`w-5 h-5 ${isCollapsed ? "" : "mr-2"}`} /> : <Moon className={`w-5 h-5 ${isCollapsed ? "" : "mr-2"}`} />}
                                        {!isCollapsed && <span className="whitespace-nowrap">{isDark ? "Light" : "Dark"}</span>}
                                    </button>
                                    {!isCollapsed && <div className={`w-px h-6 ${isDark ? "bg-white/10" : "bg-gray-300"}`} />}
                                    <button
                                        onClick={() => {
                                            localStorage.removeItem("token");
                                            window.location.href = "/";
                                        }}
                                        title="Sign Out"
                                        className={`${isCollapsed ? "w-full p-2.5" : "flex-1 px-3 py-2"} flex items-center justify-center text-sm font-medium rounded-lg transition-colors ${isDark ? "text-gray-400 hover:bg-red-900/20 hover:text-red-400" : "text-gray-600 hover:bg-red-50 hover:text-red-600"}`}
                                    >
                                        <LogOut className={`w-5 h-5 ${isCollapsed ? "" : "mr-2"}`} />
                                        {!isCollapsed && <span className="whitespace-nowrap">Sign Out</span>}
                                    </button>
                                </div>
                            </div>

                            {/* Mobile: Compact horizontal layout with divider */}
                            <div className="md:hidden p-3">
                                <div className={`flex items-center justify-around gap-0 rounded-xl p-1 ${isDark ? "bg-white/5" : "bg-gray-100"}`}>
                                    <button
                                        onClick={toggleTheme}
                                        title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
                                        className={`flex-1 p-2.5 rounded-lg transition-colors ${isDark ? "text-gray-400 hover:bg-white/10 hover:text-white" : "text-gray-600 hover:bg-white hover:text-gray-900"}`}
                                    >
                                        {isDark ? <Sun className="w-5 h-5 mx-auto" /> : <Moon className="w-5 h-5 mx-auto" />}
                                    </button>
                                    <div className={`w-px h-6 ${isDark ? "bg-white/10" : "bg-gray-300"}`} />
                                    <button
                                        onClick={() => {
                                            localStorage.removeItem("token");
                                            window.location.href = "/";
                                        }}
                                        title="Sign Out"
                                        className={`flex-1 p-2.5 rounded-lg transition-colors ${isDark ? "text-gray-400 hover:bg-red-900/20 hover:text-red-400" : "text-gray-600 hover:bg-red-50 hover:text-red-600"}`}
                                    >
                                        <LogOut className="w-5 h-5 mx-auto" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Main Content */}
                <div className={`flex-1 flex flex-col min-w-0 overflow-hidden relative ${isDark ? "bg-black" : "bg-gray-50"}`}>
                    {/* Mobile Header */}
                    <div className={`md:hidden flex items-center justify-between px-4 py-3 border-b sticky top-0 z-40 ${isDark ? "border-white/10 bg-nvidia-dark" : "border-gray-200 bg-white"}`}>
                        <div className="flex items-center space-x-3">
                            <Logo size="sm" />
                            <span className={`text-lg font-bold ${isDark ? "text-white" : "text-gray-900"}`}>Basivo</span>
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
            </div>
        </AuthGuard>
    );
}
