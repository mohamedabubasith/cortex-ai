"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Home, AlertTriangle } from "lucide-react";
import TubesBackground from "@/components/TubesBackground";

export default function NotFound() {
    // 404 page always uses dark theme
    const isDark = true;
    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4 relative overflow-hidden font-sans text-white">
            {/* Background Effects */}
            <TubesBackground />

            {/* Ambient Glow */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-nvidia-green/5 rounded-full blur-[150px] animate-pulse-slow" />
            </div>

            {/* Content */}
            <div className="relative z-10 text-center max-w-2xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                >
                    {/* Glitchy 404 */}
                    <div className="relative inline-block mb-4">
                        <h1 className="text-[150px] md:text-[200px] font-black leading-none tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/10 select-none">
                            404
                        </h1>
                        <motion.div
                            className="absolute inset-0 text-[150px] md:text-[200px] font-black leading-none tracking-tighter text-nvidia-green/50 select-none"
                            animate={{
                                x: [-2, 2, -1, 0],
                                y: [1, -1, 0],
                                opacity: [0.5, 0.8, 0.5]
                            }}
                            transition={{
                                duration: 0.2,
                                repeat: Infinity,
                                repeatType: "reverse",
                                repeatDelay: 3
                            }}
                            style={{ mixBlendMode: "screen" }}
                        >
                            404
                        </motion.div>
                    </div>

                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3, duration: 0.5 }}
                        className="space-y-6"
                    >
                        <div className="flex items-center justify-center space-x-3 text-nvidia-green mb-2">
                            <AlertTriangle className="w-6 h-6" />
                            <span className="text-xl font-mono uppercase tracking-widest">System Error</span>
                        </div>

                        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                            Page Not Found
                        </h2>

                        <p className="text-gray-400 text-lg md:text-xl max-w-lg mx-auto leading-relaxed">
                            The requested data segment appears to be corrupted or missing from the neural network.
                        </p>

                        <div className="pt-8">
                            <Link
                                href="/"
                                className="inline-flex items-center justify-center px-8 py-4 text-base font-bold text-black transition-all duration-200 bg-nvidia-green rounded-lg hover:bg-[#8CD600] hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-nvidia-green focus:ring-offset-black shadow-[0_0_20px_rgba(118,185,0,0.3)] hover:shadow-[0_0_30px_rgba(118,185,0,0.5)]"
                            >
                                <Home className="w-5 h-5 mr-2" />
                                Return to Dashboard
                            </Link>
                        </div>
                    </motion.div>
                </motion.div>
            </div>

            {/* Decorative Code Elements */}
            <div className="absolute bottom-10 left-10 text-nvidia-green/20 font-mono text-xs hidden md:block">
                <div>Error: 0x404_NOT_FOUND</div>
                <div>at NeuralNet.locate(Segment)</div>
                <div>at Cortex.Process(Request)</div>
            </div>
        </div>
    );
}
