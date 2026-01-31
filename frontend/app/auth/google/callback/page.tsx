"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import Logo from "@/components/Logo";

function GoogleCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { toast } = useToast();

    useEffect(() => {
        const token = searchParams.get("token");
        const error = searchParams.get("error");

        if (token) {
            // Success
            localStorage.setItem("token", token);
            // Force a hard reload to ensure AuthContext re-initializes completely with new token
            window.location.href = "/dashboard";
        } else if (error) {
            // Failure
            toast("Google Sign-In failed: " + error, "error");
            setTimeout(() => {
                router.push("/login?error=" + error);
            }, 2000);
        } else {
            // No token/error? - Just wait a bit, maybe it's parsing
            // Check if we already have a token in storage (edge case)
            if (localStorage.getItem("token")) {
                window.location.href = "/dashboard";
            } else {
                router.push("/login");
            }
        }
    }, [searchParams, router, toast]);

    return (
        <div className="min-h-screen bg-black flex flex-col items-center justify-center text-white relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-nvidia-green/10 via-black to-black opacity-50" />
            <div className="absolute inset-0 z-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #333 1px, transparent 0)", backgroundSize: "40px 40px" }}></div>

            <div className="z-10 flex flex-col items-center animate-in fade-in zoom-in duration-500">
                <div className="mb-8 p-6 rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl">
                    <Logo size="xl" />
                </div>

                <div className="flex items-center gap-3 text-nvidia-green mb-2">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="font-mono text-sm tracking-wider uppercase">Authenticating</span>
                </div>

                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                    Welcome to Basivo
                </h1>
                <p className="text-gray-500 mt-2 text-sm">Preparing your workspace...</p>
            </div>
        </div>
    );
}

export default function GoogleCallbackPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-black flex flex-col items-center justify-center text-white">
                <Logo size="lg" />
            </div>
        }>
            <GoogleCallbackContent />
        </Suspense>
    );
}
