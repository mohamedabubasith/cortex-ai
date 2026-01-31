"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { motion } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2, AlertCircle, Eye, EyeOff, Check } from "lucide-react";
import api from "@/lib/api";
import TubesBackground from "@/components/TubesBackground";
import Logo from "@/components/Logo";
import { isValidEmail } from "@/lib/validation";
import AuthLayout from "@/components/auth/AuthLayout";

import { Suspense } from "react";



function LoginForm() {
    // Login page always uses dark theme
    const isDark = true;
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [formErrors, setFormErrors] = useState({ email: "", password: "", global: "" });
    const [loading, setLoading] = useState(false);
    const [initialCheckDone, setInitialCheckDone] = useState(false);
    const router = useRouter();
    const searchParams = useSearchParams();
    const redirectUrl = searchParams.get("redirect");

    const { user, isLoading: authLoading } = useAuth();

    useEffect(() => {
        if (!authLoading) {
            if (user) {
                router.push("/dashboard");
            } else {
                setInitialCheckDone(true);
            }
        }
    }, [user, authLoading, router]);

    const validateForm = () => {
        const errors = { email: "", password: "", global: "" };
        let isValid = true;

        if (!email) {
            errors.email = "Email is required";
            isValid = false;
        } else if (!isValidEmail(email)) {
            errors.email = "Please enter a valid email address";
            isValid = false;
        }

        if (!password) {
            errors.password = "Password is required";
            isValid = false;
        }

        setFormErrors(errors);
        return isValid;
    };


    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormErrors({ email: "", password: "", global: "" });

        if (!validateForm()) return;

        setLoading(true);

        try {
            const formData = new FormData();
            formData.append("username", email);
            formData.append("password", password);

            const response = await api.post("/auth/token", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            localStorage.setItem("token", response.data.access_token);
            // Force full reload to ensure AuthContext and all states are fresh
            window.location.href = redirectUrl || "/dashboard";
        } catch (err: any) {
            console.error(err);
            const detail = err.response?.data?.detail;
            setFormErrors(prev => ({
                ...prev,
                global: detail || "Invalid email or password. Please try again."
            }));
        } finally {
            setLoading(false);
        }
    };

    if (!initialCheckDone) {
        return null;
    }

    return (
        <AuthLayout title="Welcome back" subtitle="Sign in to your account">
            {formErrors.global && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-4 bg-red-900/20 border border-red-500/50 text-red-200 rounded-lg text-sm flex items-center"
                >
                    <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                    {formErrors.global}
                </motion.div>
            )}

            <form onSubmit={handleLogin} className="space-y-5">
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Email Address</label>
                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none transition-colors group-focus-within:text-nvidia-green">
                            <Mail className={`h-5 w-5 ${formErrors.email ? "text-red-500" : "text-gray-500 group-hover:text-gray-400"}`} />
                        </div>
                        <input
                            type="email"
                            className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${formErrors.email
                                ? "border-red-500 focus:ring-red-500"
                                : "border-gray-700 focus:ring-nvidia-green hover:border-gray-600"
                                }`}
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => {
                                setEmail(e.target.value);
                                if (formErrors.email) setFormErrors(prev => ({ ...prev, email: "" }));
                            }}
                        />
                    </div>
                    {formErrors.email && (
                        <p className="mt-1 text-xs text-red-500">{formErrors.email}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none transition-colors group-focus-within:text-nvidia-green">
                            <Lock className={`h-5 w-5 ${formErrors.password ? "text-red-500" : "text-gray-500 group-hover:text-gray-400"}`} />
                        </div>
                        <input
                            type={showPassword ? "text" : "password"}
                            className={`block w-full pl-10 pr-10 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${formErrors.password
                                ? "border-red-500 focus:ring-red-500"
                                : "border-gray-700 focus:ring-nvidia-green hover:border-gray-600"
                                }`}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value);
                                if (formErrors.password) setFormErrors(prev => ({ ...prev, password: "" }));
                            }}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-300 transition-colors focus:outline-none"
                        >
                            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                    </div>
                    {formErrors.password && (
                        <p className="mt-1 text-xs text-red-500">{formErrors.password}</p>
                    )}
                </div>

                <div className="flex justify-end">
                    <Link
                        href="/forgot-password"
                        className="text-sm font-medium text-nvidia-green hover:text-green-400 transition-colors"
                    >
                        Forgot password?
                    </Link>
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

                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t border-gray-800"></span>
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-black px-2 text-gray-500">Or continue with</span>
                    </div>
                </div>

                <button
                    type="button"
                    onClick={() => {
                        window.location.href = `${api.defaults.baseURL}/auth/google/login`;
                    }}
                    className="w-full flex items-center justify-center py-3 px-4 border border-gray-700 rounded-lg shadow-sm bg-black text-white font-medium hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-700 transition-all transform hover:scale-[1.02]"
                >
                    <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                        <path
                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                            fill="#4285F4"
                        />
                        <path
                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                            fill="#34A853"
                        />
                        <path
                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                            fill="#FBBC05"
                        />
                        <path
                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                            fill="#EA4335"
                        />
                    </svg>
                    Sign in with Google
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
        </AuthLayout>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-black" />}>
            <LoginForm />
        </Suspense>
    );
}

