"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "@/lib/api";
import { User, TenantRole, Permission } from "@/types/rbac";

interface AuthContextType {
    user: User | null;
    role: TenantRole | null;
    permissions: string[]; // List of permission slugs (e.g., "kb.view")
    isLoading: boolean;
    refreshUser: () => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [role, setRole] = useState<TenantRole | null>(null);
    const [permissions, setPermissions] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const refreshUser = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem("token");
            if (!token) {
                setUser(null);
                setRole(null);
                setPermissions([]);
                return;
            }

            const res = await api.get("/auth/me");
            const userData = res.data as User;
            setUser(userData);

            // Extract role and permissions from current tenant membership
            // "me" endpoint returns the user. We need to find the active tenant membership.
            // Actually, /auth/me returns the user, but we rely on fetching tenant details separately usually.
            // BUT, our User object has `tenant_memberships` loaded.
            const tenantId = localStorage.getItem("tenant_id");
            let activeMembership = null;

            if (tenantId && userData.tenant_memberships) {
                activeMembership = userData.tenant_memberships.find(m => m.tenant_id === tenantId);
            } else if (userData.tenant_memberships && userData.tenant_memberships.length > 0) {
                // Fallback to first
                activeMembership = userData.tenant_memberships[0];
                if (typeof window !== "undefined") {
                    localStorage.setItem("tenant_id", activeMembership.tenant_id);
                }
            }

            if (activeMembership && activeMembership.tenant_role) {
                setRole(activeMembership.tenant_role);
                const perms = activeMembership.tenant_role.permissions?.map(p => p.permission_slug) || [];
                setPermissions(perms);
            } else {
                setRole(null);
                setPermissions([]);
            }
        } catch (error) {
            console.error("Failed to load user", error);
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("tenant_id");
        setUser(null);
        setRole(null);
        setPermissions([]);
        window.location.href = "/";
    };

    useEffect(() => {
        refreshUser();
        // Listen for storage events (if logout happens in another tab)
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === "token" && !e.newValue) {
                logout();
            }
        };
        window.addEventListener("storage", handleStorageChange);
        return () => window.removeEventListener("storage", handleStorageChange);
    }, []);

    return (
        <AuthContext.Provider value={{ user, role, permissions, isLoading, refreshUser, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

export function usePermission(permissionSlug: string): boolean {
    const { permissions, role } = useAuth();
    if (!role) return false;
    // System owner/admin might have implicit permissions?
    // For now, rely on explicit list.
    // If role is owner, maybe allow all?
    if (role.name === "Owner") return true; // Owner override

    return permissions.includes(permissionSlug);
}

export function Can({ permission, children, fallback = null }: { permission: string, children: React.ReactNode, fallback?: React.ReactNode }) {
    const hasPermission = usePermission(permission);
    if (hasPermission) return <>{children}</>;
    return <>{fallback}</>;
}
