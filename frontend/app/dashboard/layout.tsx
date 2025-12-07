"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Cpu, Database, Bot, LogOut, Menu, X } from "lucide-react";
import Logo from "@/components/Logo";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const navigation = [
        { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { name: "LLM", href: "/dashboard/llm", icon: Cpu },
        { name: "Knowledge Base", href: "/dashboard/kb", icon: Database },
        { name: "Agents", href: "/dashboard/agents", icon: Bot },
    ];

    return (
        <div className="min-h-screen bg-black flex">
            {/* Sidebar */}
            <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-nvidia-dark border-r border-white/10 transform transition-transform duration-200 ease-in-out ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0 md:static md:inset-0`}>
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="flex items-center justify-between px-4 h-20 border-b border-white/10">
                        <Link href="/dashboard" className="flex items-center space-x-3">
                            <Logo size="sm" />
                            <span className="text-xl font-bold text-white tracking-tight">Cortex AI</span>
                        </Link>
                        {/* Close Button (Mobile Only) */}
                        <button
                            onClick={() => setIsMobileMenuOpen(false)}
                            className="md:hidden p-2 text-gray-400 hover:text-white"
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
                                        : "text-gray-400 hover:bg-white/5 hover:text-white"
                                        }`}
                                >
                                    <item.icon className={`w-5 h-5 mr-3 ${isActive ? "text-black" : "text-gray-400 group-hover:text-white"}`} />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User / Logout */}
                    <div className="p-4 border-t border-white/10">
                        <button
                            onClick={() => {
                                localStorage.removeItem("token");
                                window.location.href = "/";
                            }}
                            className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-400 rounded-xl hover:bg-red-900/20 hover:text-red-400 transition-colors"
                        >
                            <LogOut className="w-5 h-5 mr-3" />
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-black relative">
                {/* Mobile Header */}
                <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-white/10 bg-nvidia-dark sticky top-0 z-40">
                    <div className="flex items-center space-x-3">
                        <Logo size="sm" />
                        <span className="text-lg font-bold text-white">Cortex AI</span>
                    </div>
                    <button
                        onClick={() => setIsMobileMenuOpen(true)}
                        className="p-2 text-gray-400 hover:text-white"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                </div>

                {/* Background Pattern */}
                <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" style={{ backgroundImage: "radial-gradient(circle at 50% 50%, #1a1a1a 1px, transparent 1px)", backgroundSize: "24px 24px" }}></div>

                <main className="flex-1 overflow-y-auto p-4 md:p-8 relative z-10">
                    {children}
                </main>
            </div>
        </div>
    );
}
