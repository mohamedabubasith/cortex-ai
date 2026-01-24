"use client";

import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import { Shield, Lock, Check } from "lucide-react";

export default function RolesPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const roles = [
        {
            name: "Owner",
            description: "Full access to all resources and billing. Can delete the workspace.",
            permissions: ["Manage Users", "Manage Billing", "Delete Workspace", "Create/Edit/Delete Agents", "Manage Knowledge Base", "View Audit Logs"]
        },
        {
            name: "Admin",
            description: "Can manage users and resources, but cannot delete the workspace.",
            permissions: ["Manage Users", "Create/Edit/Delete Agents", "Manage Knowledge Base", "View Audit Logs"]
        },
        {
            name: "Member",
            description: "Can create and edit their own resources. Can view shared resources.",
            permissions: ["Create/Edit Own Agents", "View Shared Agents", "Chat with Agents"]
        },
        {
            name: "Viewer",
            description: "Read-only access to shared resources.",
            permissions: ["View Shared Agents", "Chat with Agents"]
        }
    ];

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div>
                <h1 className={cn("text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>
                    Roles & Permissions
                </h1>
                <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                    Overview of access levels in your workspace.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {roles.map((role) => (
                    <div key={role.name} className={cn("p-6 rounded-xl border", isDark ? "bg-nvidia-dark/50 border-white/10" : "bg-white border-gray-200")}>
                        <div className="flex items-center mb-4">
                            <div className={cn("p-2 rounded-lg mr-3", isDark ? "bg-white/5 text-nvidia-green" : "bg-green-50 text-green-600")}>
                                <Shield className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className={cn("text-lg font-bold", isDark ? "text-white" : "text-gray-900")}>{role.name}</h3>
                            </div>
                        </div>

                        <p className={cn("text-sm mb-6 min-h-[40px]", isDark ? "text-gray-400" : "text-gray-600")}>
                            {role.description}
                        </p>

                        <div className="space-y-2">
                            <div className={cn("text-xs font-bold uppercase mb-2", isDark ? "text-gray-500" : "text-gray-400")}>
                                Permissions
                            </div>
                            {role.permissions.map((perm) => (
                                <div key={perm} className="flex items-center text-sm">
                                    <Check className="w-4 h-4 text-nvidia-green mr-2" />
                                    <span className={isDark ? "text-gray-300" : "text-gray-700"}>{perm}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className={cn("p-4 rounded-lg border flex items-start", isDark ? "bg-blue-500/10 border-blue-500/20 text-blue-200" : "bg-blue-50 border-blue-200 text-blue-800")}>
                <Lock className="w-5 h-5 mr-3 mt-0.5 shrink-0" />
                <div className="text-sm">
                    <p className="font-bold mb-1">Row Level Security (RLS)</p>
                    <p>
                        Data isolation is enforced at the database level. Users can only access resources belonging to their tenant.
                        Within a tenant, permissions are validated against the user's role before any action.
                    </p>
                </div>
            </div>
        </div>
    );
}
