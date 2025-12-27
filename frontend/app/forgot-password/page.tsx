"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Mail, ArrowRight, Loader2, ArrowLeft, CheckCircle } from "lucide-react";
import api from "@/lib/api";
import TubesBackground from "@/components/TubesBackground";
import Logo from "@/components/Logo";
import { isValidEmail } from "@/lib/validation";

export default function ForgotPasswordPage() {
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [email, setEmail] = useState("");
    const [emailError, setEmailError] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setEmailError("");

        if (!email) {
            setEmailError("Email is required");
            return;
        } else if (!isValidEmail(email)) {
            setEmailError("Please enter a valid email address");
            return;
        }

        setLoading(true);

        try {
            const response = await api.post("/auth/forgot-password", { email });
            setSuccessMessage(response.data.message);
            setSubmitted(true);
        } catch (err) {
            console.error(err);
            // Even if it fails (e.g. email not found), it's better security practice to show success
            // or a generic message, but for this UI we'll show success.
            setSuccessMessage("If this email is registered, you will receive a password reset link.");
            setSubmitted(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4 relative overflow-hidden">
            {/* Background Effects */}
            <TubesBackground />
            <div className="absolute inset-0 z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-[#76B900]/10 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-[#76B900]/5 rounded-full blur-[100px] animate-pulse delay-1000" />
            </div>
            {/* Background Pattern */}
            <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" style={{ backgroundImage: "radial-gradient(circle at 50% 50%, #1a1a1a 1px, transparent 1px)", backgroundSize: "24px 24px" }}></div>

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
                            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">Reset Password</h1>
                            <p className="text-gray-400">
                                Enter your email to receive reset instructions
                            </p>
                        </div>

                        {submitted ? (
                            <div className="text-center">
                                <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-nvidia-green/20 mb-6 border border-nvidia-green/50">
                                    <CheckCircle className="h-8 w-8 text-nvidia-green" />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-2">Check your email</h3>
                                <p className="text-gray-400 mb-8">
                                    {successMessage}
                                </p>
                                <div>
                                    <Link
                                        href="/"
                                        className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-sm font-bold rounded-lg text-black bg-nvidia-green hover:bg-[#8CD600] transition-all transform hover:scale-[1.02]"
                                    >
                                        <ArrowLeft className="w-4 h-4 mr-2" />
                                        Back to Login
                                    </Link>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">
                                        Email Address
                                    </label>
                                    <div className="relative">
                                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                            <Mail className={`h-5 w-5 ${emailError ? "text-red-500" : "text-gray-500"}`} />
                                        </div>
                                        <input
                                            type="email"
                                            className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${emailError
                                                ? "border-red-500 focus:ring-red-500"
                                                : "border-gray-700 focus:ring-nvidia-green"
                                                }`}
                                            placeholder="you@example.com"
                                            value={email}
                                            onChange={(e) => {
                                                setEmail(e.target.value);
                                                if (emailError) setEmailError("");
                                            }}
                                        />
                                    </div>
                                    {emailError && (
                                        <p className="mt-1 text-xs text-red-500">{emailError}</p>
                                    )}
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-lg shadow-lg text-sm font-bold text-black bg-nvidia-green hover:bg-[#8CD600] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-nvidia-green disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02]"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Sending link...
                                        </>
                                    ) : (
                                        "Send Reset Link"
                                    )}
                                </button>

                                <div className="text-center">
                                    <Link
                                        href="/"
                                        className="inline-flex items-center text-sm font-medium text-gray-400 hover:text-white transition-colors"
                                    >
                                        <ArrowLeft className="w-4 h-4 mr-2" />
                                        Back to Login
                                    </Link>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            </motion.div>
        </div>
    );
}

