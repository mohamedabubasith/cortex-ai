"use client";

export const dynamic = 'force-dynamic';

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// Create agent flow moved to /dashboard/agents (inline modal).
// This page exists only to redirect old links gracefully.
export default function NewAgentRedirect() {
    const router = useRouter();
    useEffect(() => { router.replace("/dashboard/agents"); }, [router]);
    return null;
}
