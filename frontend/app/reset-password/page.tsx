"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Lock, ArrowRight, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import api from "@/lib/api";
import TubesBackground from "@/components/TubesBackground";
import Logo from "@/components/Logo";
import { calculatePasswordStrength, PasswordStrength } from "@/lib/validation";

function ResetPasswordForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get("token");

    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [errors, setErrors] = useState({ password: "", confirmPassword: "", global: "" });
    const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({ score: 0, label: "Weak", color: "bg-gray-600" });

    const handlePasswordChange = (value: string) => {
        setPassword(value);
        setPasswordStrength(calculatePasswordStrength(value));
        if (errors.password) setErrors(prev => ({ ...prev, password: "" }));
    };

    const validateForm = () => {
        const newErrors = { password: "", confirmPassword: "", global: "" };
        let isValid = true;

        if (!password) {
            newErrors.password = "Password is required";
            isValid = false;
        } else if (password.length < 8) {
            newErrors.password = "Password must be at least 8 characters";
            isValid = false;
        }

        if (password !== confirmPassword) {
            newErrors.confirmPassword = "Passwords do not match";
            isValid = false;
        }

        if (!token) {
            newErrors.global = "Invalid or missing reset token.";
            isValid = false;
        }

        setErrors(newErrors);
        return isValid;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({ password: "", confirmPassword: "", global: "" });

        if (!validateForm()) return;

        setLoading(true);

        try {
            await api.post("/auth/reset-password", {
                token,
                new_password: password
            });
            setSuccess(true);
            setTimeout(() => {
                router.push("/");
            }, 2000);
        } catch (err: any) {
            console.error(err);
            setErrors(prev => ({
                ...prev,
                global: err.response?.data?.detail || "Failed to reset password. Token may be invalid or expired."
            }));
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="text-center text-white">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold mb-2">Invalid Link</h2>
                <p className="text-gray-400 mb-6">This password reset link is missing the token.</p>
                <Link href="/forgot-password" className="text-nvidia-green hover:underline">
                    Request a new link
                </Link>
            </div>
        );
    }

    return (
        <>
            <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center mb-6">
                    <Logo size="xl" />
                </div>
                <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">Set New Password</h1>
                <p className="text-gray-400">
                    Enter your new password below
                </p>
            </div>

            {errors.global && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-4 bg-red-900/20 border border-red-500/50 text-red-200 rounded-lg text-sm flex items-center"
                >
                    <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                    {errors.global}
                </motion.div>
            )}

            {success && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-4 bg-green-900/20 border border-green-500/50 text-green-200 rounded-lg text-sm flex items-center"
                >
                    <CheckCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                    Password reset successful! Redirecting to login...
                </motion.div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">New Password</label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock className={`h-5 w-5 ${errors.password ? "text-red-500" : "text-gray-500"}`} />
                        </div>
                        <input
                            type="password"
                            className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${errors.password
                                ? "border-red-500 focus:ring-red-500"
                                : "border-gray-700 focus:ring-nvidia-green"
                                }`}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => handlePasswordChange(e.target.value)}
                            disabled={success}
                        />
                    </div>
                    {password && (
                        <div className="mt-2">
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-xs text-gray-400">Strength</span>
                                <span className={`text-xs font-medium ${passwordStrength.score <= 1 ? 'text-red-500' :
                                    passwordStrength.score === 2 ? 'text-yellow-500' :
                                        passwordStrength.score === 3 ? 'text-blue-500' :
                                            'text-green-500'
                                    }`}>
                                    {passwordStrength.label}
                                </span>
                            </div>
                            <div className="h-1 w-full bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-300 ${passwordStrength.color}`}
                                    style={{ width: `${(passwordStrength.score / 4) * 100}%` }}
                                />
                            </div>
                        </div>
                    )}
                    {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password}</p>}
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Confirm Password</label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock className={`h-5 w-5 ${errors.confirmPassword ? "text-red-500" : "text-gray-500"}`} />
                        </div>
                        <input
                            type="password"
                            className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${errors.confirmPassword
                                ? "border-red-500 focus:ring-red-500"
                                : "border-gray-700 focus:ring-nvidia-green"
                                }`}
                            placeholder="••••••••"
                            value={confirmPassword}
                            onChange={(e) => {
                                setConfirmPassword(e.target.value);
                                if (errors.confirmPassword) setErrors(prev => ({ ...prev, confirmPassword: "" }));
                            }}
                            disabled={success}
                        />
                    </div>
                    {errors.confirmPassword && <p className="mt-1 text-xs text-red-500">{errors.confirmPassword}</p>}
                </div>

                <button
                    type="submit"
                    disabled={loading || success}
                    className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-lg shadow-lg text-sm font-bold text-black bg-nvidia-green hover:bg-[#8CD600] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-nvidia-green disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02]"
                >
                    {loading ? (
                        <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Resetting password...
                        </>
                    ) : success ? (
                        <>
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Password Reset
                        </>
                    ) : (
                        <>
                            Reset Password
                            <ArrowRight className="w-4 h-4 ml-2" />
                        </>
                    )}
                </button>
            </form>

            {!success && (
                <div className="mt-8 text-center">
                    <p className="text-sm text-gray-400">
                        Remember your password?{" "}
                        <Link href="/" className="font-medium text-nvidia-green hover:text-green-400 transition-colors">
                            Back to Login
                        </Link>
                    </p>
                </div>
            )}
        </>
    );
}

export default function ResetPasswordPage() {
    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-3 sm:p-4 relative overflow-hidden">
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
                className="w-full max-w-[380px] sm:max-w-md relative z-10"
            >
                <div className="bg-nvidia-dark/80 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
                    <div className="p-6 sm:p-8">
                        <Suspense fallback={<div className="text-white text-center">Loading...</div>}>
                            <ResetPasswordForm />
                        </Suspense>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
