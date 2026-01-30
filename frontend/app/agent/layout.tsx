"use client";

import AuthGuard from "@/components/layout/AuthGuard";

export default function AgentLayout({ children }: { children: React.ReactNode }) {
    return (
        <AuthGuard>
            {children}
        </AuthGuard>
    );
}
