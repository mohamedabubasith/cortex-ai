"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { User, Mail, Lock, ArrowRight, Loader2, Check, X, AlertCircle } from "lucide-react";
import api from "@/lib/api";
import TubesBackground from "@/components/TubesBackground";
import Logo from "@/components/Logo";
import { isValidEmail, calculatePasswordStrength, PasswordStrength } from "@/lib/validation";

export default function RegisterPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
        agreeTerms: false
    });
    const [formErrors, setFormErrors] = useState({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
        agreeTerms: "",
        global: ""
    });
    const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({ score: 0, label: "Weak", color: "bg-gray-600" });

    useEffect(() => {
        setPasswordStrength(calculatePasswordStrength(formData.password));
    }, [formData.password]);

    const validateForm = () => {
        const errors = {
            full_name: "",
            email: "",
            password: "",
            confirmPassword: "",
            agreeTerms: "",
            global: ""
        };
        let isValid = true;

        if (!formData.full_name.trim()) {
            errors.full_name = "Full name is required";
            isValid = false;
        }

        if (!formData.email) {
            errors.email = "Email is required";
            isValid = false;
        } else if (!isValidEmail(formData.email)) {
            errors.email = "Please enter a valid email address";
            isValid = false;
        }

        if (!formData.password) {
            errors.password = "Password is required";
            isValid = false;
        } else if (formData.password.length < 8) {
            errors.password = "Password must be at least 8 characters";
            isValid = false;
        }

        if (formData.password !== formData.confirmPassword) {
            errors.confirmPassword = "Passwords do not match";
            isValid = false;
        }

        if (!formData.agreeTerms) {
            errors.agreeTerms = "You must agree to the terms and conditions";
            isValid = false;
        }

        setFormErrors(errors);
        return isValid;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormErrors({ full_name: "", email: "", password: "", confirmPassword: "", agreeTerms: "", global: "" });

        if (!validateForm()) return;

        setLoading(true);

        try {
            await api.post("/auth/register", {
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name
            });

            setSuccess(true);
            setTimeout(() => {
                router.push("/");
            }, 2000);
        } catch (err: any) {
            console.error(err);
            setFormErrors(prev => ({
                ...prev,
                global: err.response?.data?.detail || "Registration failed. Please try again."
            }));
            setLoading(false);
        }
    };

    const handleChange = (field: string, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        if (formErrors[field as keyof typeof formErrors]) {
            setFormErrors(prev => ({ ...prev, [field]: "" }));
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
                            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">Create Account</h1>
                            <p className="text-gray-400">Join Cortex AI today</p>
                        </div>

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

                        {success && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="mb-6 p-4 bg-green-900/20 border border-green-500/50 text-green-200 rounded-lg text-sm flex items-center"
                            >
                                <Check className="w-4 h-4 mr-2 flex-shrink-0" />
                                Account created! Redirecting to login...
                            </motion.div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Full Name</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <User className={`h-5 w-5 ${formErrors.full_name ? "text-red-500" : "text-gray-500"}`} />
                                    </div>
                                    <input
                                        type="text"
                                        className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${formErrors.full_name
                                                ? "border-red-500 focus:ring-red-500"
                                                : "border-gray-700 focus:ring-nvidia-green"
                                            }`}
                                        placeholder="John Doe"
                                        value={formData.full_name}
                                        onChange={(e) => handleChange("full_name", e.target.value)}
                                    />
                                </div>
                                {formErrors.full_name && <p className="mt-1 text-xs text-red-500">{formErrors.full_name}</p>}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Email Address</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Mail className={`h-5 w-5 ${formErrors.email ? "text-red-500" : "text-gray-500"}`} />
                                    </div>
                                    <input
                                        type="email"
                                        className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${formErrors.email
                                                ? "border-red-500 focus:ring-red-500"
                                                : "border-gray-700 focus:ring-nvidia-green"
                                            }`}
                                        placeholder="you@example.com"
                                        value={formData.email}
                                        onChange={(e) => handleChange("email", e.target.value)}
                                    />
                                </div>
                                {formErrors.email && <p className="mt-1 text-xs text-red-500">{formErrors.email}</p>}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Lock className={`h-5 w-5 ${formErrors.password ? "text-red-500" : "text-gray-500"}`} />
                                    </div>
                                    <input
                                        type="password"
                                        className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${formErrors.password
                                                ? "border-red-500 focus:ring-red-500"
                                                : "border-gray-700 focus:ring-nvidia-green"
                                            }`}
                                        placeholder="••••••••"
                                        value={formData.password}
                                        onChange={(e) => handleChange("password", e.target.value)}
                                    />
                                </div>
                                {formData.password && (
                                    <div className="mt-2">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs text-gray-400">Strength</span>
                                            <span className={`text-xs font-medium ${passwordStrength.color.replace("bg-", "text-")}`}>
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
                                {formErrors.password && <p className="mt-1 text-xs text-red-500">{formErrors.password}</p>}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Confirm Password</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Lock className={`h-5 w-5 ${formErrors.confirmPassword ? "text-red-500" : "text-gray-500"}`} />
                                    </div>
                                    <input
                                        type="password"
                                        className={`block w-full pl-10 pr-3 py-3 md:py-2.5 bg-black/50 border rounded-lg focus:ring-2 focus:border-transparent text-white placeholder-gray-500 transition-all ${formErrors.confirmPassword
                                                ? "border-red-500 focus:ring-red-500"
                                                : "border-gray-700 focus:ring-nvidia-green"
                                            }`}
                                        placeholder="••••••••"
                                        value={formData.confirmPassword}
                                        onChange={(e) => handleChange("confirmPassword", e.target.value)}
                                    />
                                </div>
                                {formErrors.confirmPassword && <p className="mt-1 text-xs text-red-500">{formErrors.confirmPassword}</p>}
                            </div>

                            <div className="flex items-start">
                                <div className="flex items-center h-5">
                                    <input
                                        id="terms"
                                        type="checkbox"
                                        className="w-4 h-4 rounded border-gray-600 bg-black/50 text-nvidia-green focus:ring-nvidia-green focus:ring-offset-0"
                                        checked={formData.agreeTerms}
                                        onChange={(e) => handleChange("agreeTerms", e.target.checked)}
                                    />
                                </div>
                                <div className="ml-3 text-sm">
                                    <label htmlFor="terms" className="text-gray-400">
                                        I agree to the{" "}
                                        <a href="#" className="text-nvidia-green hover:underline">
                                            Terms of Service
                                        </a>{" "}
                                        and{" "}
                                        <a href="#" className="text-nvidia-green hover:underline">
                                            Privacy Policy
                                        </a>
                                    </label>
                                    {formErrors.agreeTerms && <p className="mt-1 text-xs text-red-500">{formErrors.agreeTerms}</p>}
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
                                        Creating account...
                                    </>
                                ) : (
                                    <>
                                        Create Account
                                        <ArrowRight className="w-4 h-4 ml-2" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-8 text-center">
                            <p className="text-sm text-gray-400">
                                Already have an account?{" "}
                                <Link href="/" className="font-medium text-nvidia-green hover:text-green-400 transition-colors">
                                    Sign in
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}

