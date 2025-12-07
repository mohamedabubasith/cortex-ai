"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2 } from "lucide-react";
import api from "@/lib/api";
import TubesBackground from "@/components/TubesBackground";
import Logo from "@/components/Logo";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token) {
            router.push("/dashboard");
        }
    }, [router]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const formData = new FormData();
            formData.append("username", email);
            formData.append("password", password);

            const response = await api.post("/auth/token", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            localStorage.setItem("token", response.data.access_token);
            router.push("/dashboard");
        } catch (err) {
            console.error(err);
            setError("Invalid email or password");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4 relative">
            {/* Background Effects */}
            <div className="absolute inset-0 z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-[#76B900]/10 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-[#76B900]/5 rounded-full blur-[100px] animate-pulse delay-1000" />
            </div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="bg-nvidia-dark/80 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
                    <div className="p-8">
                        <div className="text-center mb-8">
                            <div className="inline-flex items-center justify-center mb-6">
                                <Logo size="xl" />
                            </div>
                            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">Cortex AI</h1>
                            <p className="text-gray-400">Sign in to your account</p>
                        </div>

                        {error && (
                            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/50 text-red-200 rounded-lg text-sm flex items-center">
                                <span className="mr-2">⚠️</span> {error}
                            </div>
                        )}

                        <form onSubmit={handleLogin} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Email Address</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Mail className="h-5 w-5 text-gray-500" />
                                    </div>
                                    <input
                                        type="email"
                                        required
                                        className="block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-nvidia-green focus:border-transparent text-white placeholder-gray-500 transition-all"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <label className="block text-sm font-medium text-gray-300">Password</label>
                                    <Link
                                        href="/forgot-password"
                                        className="text-sm font-medium text-nvidia-green hover:text-green-400 transition-colors"
                                    >
                                        Forgot password?
                                    </Link>
                                </div>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Lock className="h-5 w-5 text-gray-500" />
                                    </div>
                                    <input
                                        type="password"
                                        required
                                        className="block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-nvidia-green focus:border-transparent text-white placeholder-gray-500 transition-all"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-lg shadow-lg text-sm font-bold text-black bg-nvidia-green hover:bg-[#8CD600] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-nvidia-green disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02]"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Signing in...
                                    </>
                                ) : (
                                    <>
                                        Sign In
                                        <ArrowRight className="w-4 h-4 ml-2" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-8 text-center">
                            <p className="text-sm text-gray-400">
                                Don't have an account?{" "}
                                <Link href="/register" className="font-medium text-nvidia-green hover:text-green-400 transition-colors">
                                    Create account
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
