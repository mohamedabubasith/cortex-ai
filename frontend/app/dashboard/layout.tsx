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
                    <div className="flex items-center justify-center h-20 border-b border-white/10">
                        <Link href="/dashboard" className="flex items-center space-x-3">
                            <Logo size="sm" />
                            <span className="text-xl font-bold text-white tracking-tight">Cortex AI</span>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href;
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
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

            {/* Mobile Menu Button */}
            <div className="md:hidden fixed top-4 left-4 z-50">
                <button
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                    className="p-2 bg-nvidia-dark rounded-lg border border-white/10 text-white"
                >
                    {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-black relative">
                {/* Background Pattern */}
                <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" style={{ backgroundImage: "radial-gradient(circle at 50% 50%, #1a1a1a 1px, transparent 1px)", backgroundSize: "24px 24px" }}></div>

                <main className="flex-1 overflow-y-auto p-8 relative z-10">
                    {children}
                </main>
            </div>
        </div>
    );
}
