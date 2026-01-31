"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/Toast";

export default function GoogleCallbackPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { toast } = useToast();

    useEffect(() => {
        const token = searchParams.get("token");
        const error = searchParams.get("error");

        if (token) {
            // Success
            localStorage.setItem("token", token);
            window.location.href = "/dashboard";
        } else if (error) {
            // Failure
            toast("Google Sign-In failed: " + error, "error");
            setTimeout(() => {
                router.push("/login?error=" + error);
            }, 2000);
        } else {
            // No token/error?
            router.push("/login");
        }
    }, [searchParams, router, toast]);

    return (
        <div className="min-h-screen bg-black flex flex-col items-center justify-center text-white">
            <Loader2 className="w-10 h-10 text-nvidia-green animate-spin mb-4" />
            <h1 className="text-xl font-bold">Completing Sign-In...</h1>
            <p className="text-gray-400 mt-2">Please wait while we redirect you.</p>
        </div>
    );
}
