"use client";

import { motion } from "framer-motion";
import Logo from "@/components/Logo";
import TubesBackground from "@/components/TubesBackground";
import Link from "next/link";

interface AuthLayoutProps {
    children: React.ReactNode;
    title: string;
    subtitle: string;
}

export default function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
    return (
        <div className="min-h-screen bg-black flex relative overflow-hidden">
            {/* Global Background Animation - Visible everywhere */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <TubesBackground />
                {/* Global Gradient Overlay to ensure readability */}
                <div className="absolute inset-0 bg-gradient-to-br from-black/60 via-black/80 to-black z-0" />
            </div>

            {/* Left Side - Hero Section (Hidden on mobile) */}
            <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 z-10">
                {/* Hero Content */}
                <div className="relative z-10">
                    <Logo size="lg" />
                </div>

                <div className="relative z-10 max-w-lg">
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-5xl font-bold text-white mb-6 leading-tight"
                    >
                        Accelerate your <span className="text-nvidia-green">Intelligence</span>
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="text-xl text-gray-400 leading-relaxed"
                    >
                        Orchestrate AI agents, manage knowledge, and build the future of intelligent assistance with Basivo.
                    </motion.p>
                </div>

                <div className="relative z-10 text-sm text-gray-500">
                    &copy; {new Date().getFullYear()} Basivo Inc.
                </div>
            </div>

            {/* Right Side - Form Section */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative z-10">
                {/* Glass Card for Form */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-[480px] space-y-8 relative z-10 bg-black/40 backdrop-blur-xl p-8 rounded-2xl border border-white/10 shadow-2xl"
                >
                    {/* Mobile Header in Form */}
                    <div className="lg:hidden text-center mb-8">
                        <div className="inline-flex justify-center mb-4">
                            <Logo size="xl" />
                        </div>
                    </div>

                    <div className="text-center lg:text-left">
                        <h2 className="text-3xl font-bold text-white mb-2">{title}</h2>
                        <p className="text-gray-400">{subtitle}</p>
                    </div>

                    {children}
                </motion.div>
            </div>
        </div>
    );
}
