"use client";

import { useEffect, useState } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import { Shield, Lock, Plus, X, Edit, Trash } from "lucide-react";
import api from "@/lib/api";
import { TenantRole, Permission } from "@/types/rbac";
import RoleMatrix from "@/components/rbac/RoleMatrix";
import Dialog from "@/components/ui/Dialog";
import { Can } from "@/contexts/AuthContext";

export default function RolesPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [roles, setRoles] = useState<TenantRole[]>([]);
    const [permissions, setPermissions] = useState<Permission[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateOpen, setIsCreateOpen] = useState(false);

    // Form State
    const [roleName, setRoleName] = useState("");
    const [roleDesc, setRoleDesc] = useState("");
    const [selectedPerms, setSelectedPerms] = useState<string[]>([]);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [rolesRes, permsRes] = await Promise.all([
                api.get("/tenant/roles"),
                api.get("/tenant/roles/permissions")
            ]);
            setRoles(rolesRes.data);
            setPermissions(permsRes.data);
        } catch (error) {
            console.error("Failed to fetch roles", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateRole = async () => {
        if (!roleName) return;
        setSubmitting(true);
        try {
            await api.post("/tenant/roles", {
                name: roleName,
                description: roleDesc,
                permissions: selectedPerms
            });
            await fetchData();
            setIsCreateOpen(false);
            resetForm();
        } catch (error) {
            console.error("Failed to create role", error);
            alert("Failed to create role. Check console.");
        } finally {
            setSubmitting(false);
        }
    };

    const resetForm = () => {
        setRoleName("");
        setRoleDesc("");
        setSelectedPerms([]);
    };

    const handleDeleteRole = async (roleId: string) => {
        if (!confirm("Are you sure you want to delete this role?")) return;
        try {
            await api.delete(`/tenant/roles/${roleId}`);
            fetchData();
        } catch (error) {
            alert("Failed to delete role. It might be in use or a system role.");
        }
    };

    if (loading) return <div className="p-10 text-center">Loading roles...</div>;

    return (
        <div className="max-w-6xl mx-auto space-y-8 pb-20">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className={cn("text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>
                        Roles & Permissions
                    </h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                        Manage access levels and custom roles for your workspace.
                    </p>
                </div>
                <Can permission="iam.role.manage">
                    <button
                        onClick={() => { resetForm(); setIsCreateOpen(true); }}
                        className="flex items-center px-4 py-2 bg-nvidia-green text-black font-semibold rounded-lg hover:bg-nvidia-green/90 transition-colors shadow-[0_0_15px_rgba(118,185,0,0.3)]"
                    >
                        <Plus className="w-5 h-5 mr-2" />
                        Create Custom Role
                    </button>
                </Can>
            </div>

            {/* System Roles Section */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-gray-200 dark:border-white/10">
                    <Lock className="w-4 h-4 text-nvidia-green" />
                    <h2 className={cn("text-lg font-bold tracking-tight", isDark ? "text-white" : "text-gray-900")}>
                        System Roles
                    </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {roles.filter(r => r.is_system_role).map((role) => (
                        <RoleCard key={role.id} role={role} isDark={isDark} onDelete={handleDeleteRole} />
                    ))}
                </div>
            </div>

            {/* Custom Roles Section */}
            <div className="space-y-4 mt-8">
                <div className="flex items-center gap-2 pb-2 border-b border-gray-200 dark:border-white/10">
                    <Shield className="w-4 h-4 text-blue-500" />
                    <h2 className={cn("text-lg font-bold tracking-tight", isDark ? "text-white" : "text-gray-900")}>
                        Custom Roles
                    </h2>
                </div>
                {roles.filter(r => !r.is_system_role).length === 0 ? (
                    <div className={cn("p-8 text-center rounded-2xl border border-dashed", isDark ? "border-white/10 text-gray-500" : "border-gray-300 text-gray-400")}>
                        No custom roles created yet.
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {roles.filter(r => !r.is_system_role).map((role) => (
                            <RoleCard key={role.id} role={role} isDark={isDark} onDelete={handleDeleteRole} />
                        ))}
                    </div>
                )}
            </div>

            {/* Create Role Dialog */}
            <Dialog
                isOpen={isCreateOpen}
                onClose={() => setIsCreateOpen(false)}
                title="Create Custom Role"
                description="Define a new role and assign specific permissions."
                maxWidth="max-w-4xl"
                buttons={[
                    { label: "Cancel", onClick: () => setIsCreateOpen(false), variant: "outline" },
                    { label: submitting ? "Creating..." : "Create Role", onClick: handleCreateRole, variant: "primary", isLoading: submitting }
                ]}
            >
                <div className="flex flex-col h-[65vh]">
                    <div className="space-y-4 shrink-0 mb-4 px-1">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className={cn("block text-xs font-bold uppercase tracking-wider mb-1.5 ml-1", isDark ? "text-gray-400" : "text-gray-500")}>Role Name</label>
                                <input
                                    type="text"
                                    value={roleName}
                                    onChange={(e) => setRoleName(e.target.value)}
                                    placeholder="e.g. Content Manager"
                                    className={cn("w-full px-3.5 py-3 text-base sm:py-2.5 sm:text-sm rounded-xl border outline-none focus:ring-2 focus:ring-nvidia-green/20 transition-all",
                                        isDark ? "bg-black/40 border-white/10 placeholder:text-gray-600 text-white focus:bg-black/60 focus:border-nvidia-green/50" : "bg-white border-gray-200 text-gray-900 focus:border-nvidia-green"
                                    )}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className={cn("block text-xs font-bold uppercase tracking-wider mb-1.5 ml-1", isDark ? "text-gray-400" : "text-gray-500")}>Description</label>
                                <input
                                    type="text"
                                    value={roleDesc}
                                    onChange={(e) => setRoleDesc(e.target.value)}
                                    placeholder="Brief description of responsibilities"
                                    className={cn("w-full px-3.5 py-3 text-base sm:py-2.5 sm:text-sm rounded-xl border outline-none focus:ring-2 focus:ring-nvidia-green/20 transition-all",
                                        isDark ? "bg-black/40 border-white/10 placeholder:text-gray-600 text-white focus:bg-black/60 focus:border-nvidia-green/50" : "bg-white border-gray-200 text-gray-900 focus:border-nvidia-green"
                                    )}
                                />
                            </div>
                        </div>
                        <div className={cn("text-xs font-bold uppercase tracking-wider pt-2", isDark ? "text-gray-500" : "text-gray-400")}>
                            Permissions
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto min-h-0 pr-2 pb-2 custom-scrollbar">
                        <RoleMatrix
                            permissions={permissions}
                            selectedSlugs={selectedPerms}
                            onChange={setSelectedPerms}
                        />
                    </div>
                </div>
            </Dialog>
        </div>
    );
}

function RoleCard({ role, isDark, onDelete }: { role: TenantRole, isDark: boolean, onDelete: (id: string) => void }) {
    return (
        <div className={cn("p-6 rounded-2xl border transition-all duration-300 group relative overflow-hidden",
            isDark ? "bg-[#0f0f0f]/60 backdrop-blur-md border-white/5 hover:border-nvidia-green/30" : "bg-white border-gray-200 shadow-sm hover:shadow-md")}>

            <div className="flex items-start justify-between mb-6">
                <div className="flex items-center">
                    <div className={cn("p-2.5 rounded-xl mr-4 transition-colors",
                        isDark ? "bg-white/5 text-nvidia-green" : "bg-green-50 text-green-600")}>
                        {role.is_system_role ? <Lock className="w-6 h-6" /> : <Shield className="w-6 h-6" />}
                    </div>
                    <div>
                        <h3 className={cn("text-xl font-bold tracking-tight flex items-center gap-3", isDark ? "text-white" : "text-gray-900")}>
                            {role.name}
                            {role.is_system_role && (
                                <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider bg-gray-500/20 text-gray-500 border border-gray-500/20">
                                    System
                                </span>
                            )}
                        </h3>
                        <p className={cn("text-sm mt-1", isDark ? "text-gray-400" : "text-gray-600")}>
                            {role.description}
                        </p>
                    </div>
                </div>

                {!role.is_system_role && (
                    <button
                        onClick={() => onDelete(role.id)}
                        className="text-red-500 hover:text-red-400 p-2 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                        title="Delete Role"
                    >
                        <Trash className="w-4 h-4" />
                    </button>
                )}
            </div>

            <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {role.permissions.slice(0, 6).map((rp) => (
                        <div key={rp.permission_slug} className={cn("flex items-center text-xs px-2 py-1.5 rounded border",
                            isDark ? "bg-white/5 border-white/10 text-gray-300" : "bg-gray-50 border-gray-200 text-gray-700"
                        )}>
                            <div className="w-1.5 h-1.5 rounded-full bg-nvidia-green mr-2" />
                            {rp.permission_slug}
                        </div>
                    ))}
                    {role.permissions.length > 6 && (
                        <div className={cn("flex items-center text-xs px-2 py-1.5 rounded border border-dashed",
                            isDark ? "border-white/10 text-gray-500" : "border-gray-300 text-gray-500"
                        )}>
                            +{role.permissions.length - 6} more
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
