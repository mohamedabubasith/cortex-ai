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
        <div className="min-h-screen bg-black flex overflow-hidden">
            {/* Left Side - Hero Section (Hidden on mobile) */}
            <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden bg-nvidia-dark/20">
                {/* Background Effects */}
                <TubesBackground />
                <div className="absolute inset-0 bg-gradient-to-br from-black/80 via-transparent to-black/40 z-0" />

                {/* Branding */}
                <div className="relative z-10">
                    <Logo size="lg" />
                </div>

                {/* Hero Content */}
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
                        Orchestrate AI agents, manage knowledge, and build the future of automated workflows with Basivo.
                    </motion.p>
                </div>

                {/* Footer/Copyright */}
                <div className="relative z-10 text-sm text-gray-500">
                    &copy; {new Date().getFullYear()} Basivo Inc.
                </div>
            </div>

            {/* Right Side - Form Section */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative">
                {/* Mobile Background (Subtle) */}
                <div className="lg:hidden absolute inset-0 z-0 opacity-20 bg-[url('/grid-pattern.svg')]"></div>

                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-[420px] space-y-8 relative z-10"
                >
                    {/* Mobile Header */}
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
