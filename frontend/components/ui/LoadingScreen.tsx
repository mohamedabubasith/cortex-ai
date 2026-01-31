"use client";

import { motion } from "framer-motion";
import Logo from "@/components/Logo";

export default function LoadingScreen({ text = "Initializing..." }: { text?: string }) {
    return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black overflow-hidden">
            {/* Background Ambience */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-nvidia-green/5 via-black to-black opacity-50" />
            <div className="absolute inset-0 z-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #333 1px, transparent 0)", backgroundSize: "40px 40px" }}></div>

            <div className="z-10 relative flex flex-col items-center">
                {/* Logo with Glow/Pulse */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="mb-8 relative"
                >
                    <div className="absolute inset-0 bg-nvidia-green/20 blur-3xl rounded-full" />
                    <div className="relative bg-white/5 p-6 rounded-2xl backdrop-blur-xl border border-white/10 shadow-2xl">
                        <Logo size="lg" />
                    </div>
                </motion.div>

                {/* Progress Bar / Loader */}
                <div className="w-48 h-1 bg-gray-800 rounded-full overflow-hidden mb-4">
                    <motion.div
                        className="h-full bg-nvidia-green"
                        initial={{ x: "-100%" }}
                        animate={{ x: "100%" }}
                        transition={{
                            repeat: Infinity,
                            duration: 1.5,
                            ease: "easeInOut"
                        }}
                    />
                </div>

                {/* Text */}
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="text-gray-400 font-mono text-xs uppercase tracking-[0.2em]"
                >
                    {text}
                </motion.p>
            </div>
        </div>
    );
}
