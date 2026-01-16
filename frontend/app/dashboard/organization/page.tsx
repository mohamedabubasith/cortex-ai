"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect } from "react";
import { Users, Shield, Share2, UserPlus, Crown, Eye, Edit, Plus } from "lucide-react";
import api from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import Dialog from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

interface OrgUser {
    id: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
    joined_at: string;
}

interface Role {
    id: string;
    name: string;
    description: string;
    type: string;
    user_count: number;
    permissions: any;
}

const roleIcons: Record<string, any> = {
    owner: Crown,
    admin: Shield,
    member: Users,
    viewer: Eye,
};

const roleColors: Record<string, string> = {
    owner: "text-yellow-500",
    admin: "text-nvidia-green",
    member: "text-blue-500",
    viewer: "text-gray-500",
};

export default function OrganizationPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [activeTab, setActiveTab] = useState<"users" | "roles" | "sharing">("users");
    const [users, setUsers] = useState<OrgUser[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);
    const [sharing, setSharing] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [tenantId, setTenantId] = useState<string>("");

    useEffect(() => {
        // Get tenant ID from current user
        api.get("/auth/me").then(res => {
            const tid = res.data.tenant_memberships?.[0]?.tenant_id;
            if (tid) {
                setTenantId(tid);
                fetchData(tid);
            }
        });
    }, []);

    const fetchData = async (tid: string) => {
        setLoading(true);
        try {
            if (activeTab === "users") {
                const res = await api.get(`/organization/users?tenant_id=${tid}`);
                setUsers(res.data);
            } else if (activeTab === "roles") {
                const res = await api.get(`/organization/roles?tenant_id=${tid}`);
                setRoles(res.data);
            } else if (activeTab === "sharing") {
                const res = await api.get(`/organization/sharing?tenant_id=${tid}`);
                setSharing(res.data);
            }
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setLoading(false);
        }
    };

    const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
    const [isCreateRoleOpen, setIsCreateRoleOpen] = useState(false);
    const [newItemEmail, setNewItemEmail] = useState("");
    const [newItemRole, setNewItemRole] = useState("member");
    const [newRoleName, setNewRoleName] = useState("");
    const [newRoleDesc, setNewRoleDesc] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [allUsers, setAllUsers] = useState<any[]>([]);

    // Create Tenant State
    const [isCreateTenantOpen, setIsCreateTenantOpen] = useState(false);
    const [newTenantName, setNewTenantName] = useState("");
    const [newTenantSlug, setNewTenantSlug] = useState("");
    const [creatingTenant, setCreatingTenant] = useState(false);

    // Edit Role State
    const [isEditRoleOpen, setIsEditRoleOpen] = useState(false);
    const [editingRole, setEditingRole] = useState<Role | null>(null);
    const [editRoleName, setEditRoleName] = useState("");
    const [editRoleDesc, setEditRoleDesc] = useState("");
    const [assignUserId, setAssignUserId] = useState("");
    const [userSearch, setUserSearch] = useState(""); // New: Search filter


    useEffect(() => {
        if (tenantId) {
            fetchData(tenantId);
        }
    }, [activeTab]);

    useEffect(() => {
        if (isAddMemberOpen) {
            // Fetch potential users to add
            api.get("/admin/users").then(res => setAllUsers(res.data)).catch(err => console.error(err));
        }
    }, [isAddMemberOpen]);

    const handleAddMember = async () => {
        setSubmitting(true);
        try {
            // Find user ID if email is selected
            const user = allUsers.find(u => u.email === newItemEmail);
            const payload = user ? { user_id: user.id, role: newItemRole } : { email: newItemEmail, role: newItemRole };

            // Check if using user_id or email based on backend logic (TenantMembersModal used user_id)
            if (user) {
                await api.post(`/tenants/${tenantId}/members`, {
                    user_id: user.id,
                    role: newItemRole
                });
            } else {
                // Maybe invite functionality if API supports email?
                // For now assume user MUST exist
                alert("Please select a valid user from the list");
                setSubmitting(false);
                return;
            }

            setIsAddMemberOpen(false);
            setNewItemEmail("");
            fetchData(tenantId);
        } catch (error: any) {
            alert(`Failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    const handleCreateRole = async () => {
        setSubmitting(true);
        try {
            await api.post(`/organization/roles`, {
                name: newRoleName,
                description: newRoleDesc,
                tenant_id: tenantId,
                permissions: {} // Default empty permissions for MVP
            });
            setIsCreateRoleOpen(false);
            setNewRoleName("");
            setNewRoleDesc("");
            fetchData(tenantId);
        } catch (error: any) {
            alert(`Failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    const handleEditRole = (role: Role) => {
        setEditingRole(role);
        setEditRoleName(role.name);
        setEditRoleDesc(role.description);
        setIsEditRoleOpen(true);
    };

    const handleUpdateRole = async () => {
        if (!editingRole) return;
        setSubmitting(true);
        try {
            await api.put(`/organization/roles/${editingRole.id}`, {
                name: editRoleName,
                description: editRoleDesc,
                tenant_id: tenantId,
                permissions: editingRole.permissions // Preserve permissions for now
            });
            setIsEditRoleOpen(false);
            fetchData(tenantId);
        } catch (error: any) {
            alert(`Failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteRole = async () => {
        if (!editingRole) return;
        if (!confirm("Are you sure you want to delete this role? This cannot be undone.")) return;

        setSubmitting(true);
        try {
            await api.delete(`/organization/roles/${editingRole.id}?tenant_id=${tenantId}`);
            setIsEditRoleOpen(false);
            fetchData(tenantId);
        } catch (error: any) {
            alert(`Failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSubmitting(false);
        }

    };

    const handleAssignUserToRole = async () => {
        if (!editingRole || !assignUserId) return;
        setSubmitting(true);
        try {
            // Update user's role to this role
            await api.put(`/tenants/${tenantId}/members/${assignUserId}`, {
                role: editingRole.id
            });
            setAssignUserId("");
            fetchData(tenantId);
            // Refresh users list too as it changes
            // fetchData already refreshes activeTab, but we might need both if we display users in dialog
            if (activeTab === "roles") {
                // Refresh users explicitly if we are in roles tab
                const res = await api.get(`/organization/users?tenant_id=${tenantId}`);
                setUsers(res.data);
            }

        } catch (error: any) {
            alert(`Failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    const handleCreateTenant = async () => {
        setCreatingTenant(true);
        try {
            await api.post("/tenants", {
                name: newTenantName,
                slug: newTenantSlug
            });
            alert("Organization created successfully! You are now the owner.");
            setIsCreateTenantOpen(false);
            setNewTenantName("");
            setNewTenantSlug("");
            // Optionally, switch to new tenant or reload
            // window.location.reload(); 
        } catch (error: any) {
            alert(`Failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setCreatingTenant(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className={cn("text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>
                        Organization
                    </h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                        Manage users, roles, and resource sharing
                    </p>
                </div>
                <button
                    onClick={() => setIsCreateTenantOpen(true)}
                    className="flex items-center justify-center px-4 py-2 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-colors shadow-[0_0_20px_rgba(118,185,0,0.3)]"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    New Organization
                </button>
            </div>

            {/* Tabs */}
            <div className={cn("border-b", isDark ? "border-white/10" : "border-gray-200")}>
                <div className="flex space-x-8">
                    <button
                        onClick={() => setActiveTab("users")}
                        className={cn(
                            "pb-4 px-1 border-b-2 font-medium text-sm transition-colors",
                            activeTab === "users"
                                ? "border-nvidia-green text-nvidia-green"
                                : isDark
                                    ? "border-transparent text-gray-400 hover:text-white hover:border-gray-300"
                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                        )}
                    >
                        <Users className="w-4 h-4 inline mr-2" />
                        Users
                    </button>
                    <button
                        onClick={() => setActiveTab("roles")}
                        className={cn(
                            "pb-4 px-1 border-b-2 font-medium text-sm transition-colors",
                            activeTab === "roles"
                                ? "border-nvidia-green text-nvidia-green"
                                : isDark
                                    ? "border-transparent text-gray-400 hover:text-white hover:border-gray-300"
                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                        )}
                    >
                        <Shield className="w-4 h-4 inline mr-2" />
                        Roles
                    </button>
                    <button
                        onClick={() => setActiveTab("sharing")}
                        className={cn(
                            "pb-4 px-1 border-b-2 font-medium text-sm transition-colors",
                            activeTab === "sharing"
                                ? "border-nvidia-green text-nvidia-green"
                                : isDark
                                    ? "border-transparent text-gray-400 hover:text-white hover:border-gray-300"
                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                        )}
                    >
                        <Share2 className="w-4 h-4 inline mr-2" />
                        Sharing
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {loading ? (
                    <div className="flex justify-center py-20">
                        <div className="animate-spin h-8 w-8 border-4 border-nvidia-green border-t-transparent rounded-full" />
                    </div>
                ) : (
                    <>
                        {activeTab === "users" && <UsersTab users={users} isDark={isDark} onAddMember={() => setIsAddMemberOpen(true)} />}
                        {activeTab === "roles" && <RolesTab roles={roles} isDark={isDark} onCreateRole={() => setIsCreateRoleOpen(true)} onEditRole={handleEditRole} />}
                        {activeTab === "sharing" && <SharingTab sharing={sharing} isDark={isDark} />}
                    </>
                )}
            </div>

            {/* Add Member Dialog */}
            <Dialog
                isOpen={isAddMemberOpen}
                onClose={() => setIsAddMemberOpen(false)}
                title="Add Member"
                buttons={[
                    { label: "Cancel", onClick: () => setIsAddMemberOpen(false), variant: "outline" },
                    { label: submitting ? "Adding..." : "Add Member", onClick: handleAddMember, variant: "primary", isLoading: submitting }
                ]}
            >
                <div className="space-y-4">
                    <div className="space-y-2">
                        <label className={cn("text-sm font-medium", isDark ? "text-gray-300" : "text-gray-700")}>Select User</label>
                        <Input
                            placeholder="Search by email or name..."
                            value={userSearch}
                            onChange={(e) => setUserSearch(e.target.value)}
                            className="mb-2"
                        />
                        <select
                            value={newItemEmail}
                            onChange={(e) => setNewItemEmail(e.target.value)}
                            size={5} // Show multiple items
                            className={cn(
                                "flex w-full rounded-md border px-3 py-2 text-sm ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
                                isDark ? "bg-white/5 border-white/10 text-white focus-visible:ring-nvidia-green" : "border-input bg-background"
                            )}
                        >
                            <option value="" disabled>Select a user...</option>
                            {allUsers
                                .filter(u =>
                                    (u.email || "").toLowerCase().includes(userSearch.toLowerCase()) ||
                                    (u.full_name || "").toLowerCase().includes(userSearch.toLowerCase())
                                )
                                .map(u => (
                                    <option key={u.id} value={u.email} className={cn("p-2", isDark ? "bg-gray-900" : "")}>
                                        {u.email} ({u.full_name || "No Name"})
                                    </option>
                                ))}
                        </select>
                    </div>
                    <Select
                        label="Role"
                        value={newItemRole}
                        onChange={(e) => setNewItemRole(e.target.value)}
                        options={roles.map(r => ({ label: r.name, value: r.id }))}
                    />
                </div>
            </Dialog>

            {/* Create Role Dialog */}
            <Dialog
                isOpen={isCreateRoleOpen}
                onClose={() => setIsCreateRoleOpen(false)}
                title="Create Custom Role"
                buttons={[
                    { label: "Cancel", onClick: () => setIsCreateRoleOpen(false), variant: "outline" },
                    { label: submitting ? "Creating..." : "Create Role", onClick: handleCreateRole, variant: "primary", isLoading: submitting }
                ]}
            >
                <div className="space-y-4">
                    <Input
                        label="Role Name"
                        placeholder="e.g. Editor"
                        value={newRoleName}
                        onChange={(e) => setNewRoleName(e.target.value)}
                    />
                    <Input
                        label="Description"
                        placeholder="Can edit content but not settings"
                        value={newRoleDesc}
                        onChange={(e) => setNewRoleDesc(e.target.value)}
                    />
                </div>
            </Dialog>


            {/* Edit Role Dialog */}
            <Dialog
                isOpen={isEditRoleOpen}
                onClose={() => setIsEditRoleOpen(false)}
                title="Edit Custom Role"
                buttons={[
                    { label: "Delete", onClick: handleDeleteRole, variant: "danger" },
                    { label: "Cancel", onClick: () => setIsEditRoleOpen(false), variant: "outline" },
                    { label: submitting ? "Saving..." : "Save Changes", onClick: handleUpdateRole, variant: "primary", isLoading: submitting }
                ]}
            >
                <div className="space-y-6">
                    <div className="space-y-4">
                        <p className="text-sm text-red-500 mb-2">Warning: Deleting a role will fail if users are assigned to it.</p>
                        <Input
                            label="Role Name"
                            value={editRoleName}
                            onChange={(e) => setEditRoleName(e.target.value)}
                        />
                        <Input
                            label="Description"
                            value={editRoleDesc}
                            onChange={(e) => setEditRoleDesc(e.target.value)}
                        />
                    </div>

                    {/* Users Management */}
                    <div className="border-t pt-4">
                        <h4 className={cn("text-sm font-medium mb-3", isDark ? "text-white" : "text-gray-900")}>Users in this Role</h4>

                        {/* List current users */}
                        <div className="mb-4 space-y-2 max-h-40 overflow-y-auto">
                            {users.filter(u => u.role === editingRole?.id).length === 0 ? (
                                <p className={cn("text-xs italic", isDark ? "text-gray-500" : "text-gray-400")}>No users assigned to this role</p>
                            ) : (
                                users.filter(u => u.role === editingRole?.id).map(u => (
                                    <div key={u.id} className={cn("text-sm flex items-center justify-between p-2 rounded", isDark ? "bg-white/5" : "bg-gray-50")}>
                                        <div className="flex items-center gap-2">
                                            <div className="w-6 h-6 rounded-full bg-nvidia-green/20 flex items-center justify-center text-xs text-nvidia-green font-bold">
                                                {u.full_name?.charAt(0) || u.email.charAt(0)}
                                            </div>
                                            <span className={isDark ? "text-gray-300" : "text-gray-700"}>{u.full_name || u.email}</span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Add User */}
                        <div className="space-y-2">
                            <label className={cn("text-xs font-medium", isDark ? "text-gray-400" : "text-gray-600")}>Assign User</label>
                            <div className="flex gap-2">
                                <select
                                    value={assignUserId}
                                    onChange={(e) => setAssignUserId(e.target.value)}
                                    className={cn(
                                        "flex-1 h-9 rounded-md border px-3 text-sm bg-transparent",
                                        isDark ? "border-white/10 text-white" : "border-gray-200"
                                    )}
                                >
                                    <option value="" className="text-black">Select user to assign...</option>
                                    {users.filter(u => u.role !== editingRole?.id).map(u => (
                                        <option key={u.id} value={u.id} className="text-black">
                                            {u.full_name || u.email} (Current: {u.role})
                                        </option>
                                    ))}
                                </select>
                                <button
                                    onClick={handleAssignUserToRole}
                                    disabled={!assignUserId || submitting}
                                    className="px-3 py-1 bg-nvidia-green/20 text-nvidia-green rounded hover:bg-nvidia-green/30 text-sm font-medium disabled:opacity-50"
                                >
                                    Add
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </Dialog>

            {/* Create Tenant Dialog */}
            <Dialog
                isOpen={isCreateTenantOpen}
                onClose={() => setIsCreateTenantOpen(false)}
                title="Create New Organization"
                description="Create a new organization workspace. You will be the owner."
                buttons={[
                    { label: "Cancel", onClick: () => setIsCreateTenantOpen(false), variant: "outline" },
                    { label: creatingTenant ? "Creating..." : "Create Organization", onClick: handleCreateTenant, variant: "primary", isLoading: creatingTenant }
                ]}
            >
                <div className="space-y-4">
                    <Input
                        label="Organization Name"
                        placeholder="Acme Corp"
                        value={newTenantName}
                        onChange={(e) => {
                            setNewTenantName(e.target.value);
                            // Auto-generate slug
                            setNewTenantSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, '-'));
                        }}
                    />
                    <Input
                        label="URL Slug (ID)"
                        placeholder="acme-corp"
                        value={newTenantSlug}
                        onChange={(e) => setNewTenantSlug(e.target.value)}
                    />
                </div>
            </Dialog>
        </div >
    );
}

function UsersTab({ users, isDark, onAddMember }: { users: OrgUser[]; isDark: boolean; onAddMember: () => void }) {
    return (
        <div className="space-y-4">
            {/* Header with Add button */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className={cn("text-lg font-semibold", isDark ? "text-white" : "text-gray-900")}>
                        Organization Members
                    </h3>
                    <p className={cn("text-sm", isDark ? "text-gray-400" : "text-gray-600")}>
                        {users.length} {users.length === 1 ? "member" : "members"}
                    </p>
                </div>
                <button
                    onClick={onAddMember}
                    className="px-4 py-2 bg-nvidia-green hover:bg-[#8CD600] text-black font-medium rounded-lg transition-colors flex items-center gap-2"
                >
                    <UserPlus className="w-4 h-4" />
                    Add Member
                </button>
            </div>

            {/* Users Table */}
            <div className={cn("rounded-xl border overflow-hidden", isDark ? "border-white/10" : "border-gray-200")}>
                <table className="w-full">
                    <thead className={isDark ? "bg-white/5" : "bg-gray-50"}>
                        <tr>
                            <th className={cn("px-6 py-3 text-left text-xs font-medium uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>
                                User
                            </th>
                            <th className={cn("px-6 py-3 text-left text-xs font-medium uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>
                                Role
                            </th>
                            <th className={cn("px-6 py-3 text-left text-xs font-medium uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>
                                Status
                            </th>
                            <th className={cn("px-6 py-3 text-left text-xs font-medium uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>
                                Joined
                            </th>
                        </tr>
                    </thead>
                    <tbody className={cn("divide-y", isDark ? "divide-white/10" : "divide-gray-200")}>
                        {users.map((user) => {
                            const RoleIcon = roleIcons[user.role] || Users;
                            const roleColor = roleColors[user.role] || "text-gray-500";

                            return (
                                <tr key={user.id} className={cn("transition-colors", isDark ? "hover:bg-white/5" : "hover:bg-gray-50")}>
                                    <td className="px-6 py-4">
                                        <div>
                                            <div className={cn("font-medium", isDark ? "text-white" : "text-gray-900")}>
                                                {user.full_name || "Unknown"}
                                            </div>
                                            <div className={cn("text-sm", isDark ? "text-gray-400" : "text-gray-500")}>
                                                {user.email}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <RoleIcon className={cn("w-4 h-4", roleColor)} />
                                            <span className={cn("capitalize", isDark ? "text-white" : "text-gray-900")}>
                                                {user.role}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={cn("px-2 py-1 text-xs font-medium rounded-full",
                                            user.is_active
                                                ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                                                : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                                        )}>
                                            {user.is_active ? "Active" : "Inactive"}
                                        </span>
                                    </td>
                                    <td className={cn("px-6 py-4 text-sm", isDark ? "text-gray-400" : "text-gray-500")}>
                                        {user.joined_at ? new Date(user.joined_at).toLocaleDateString() : "N/A"}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function RolesTab({ roles, isDark, onCreateRole, onEditRole }: { roles: Role[]; isDark: boolean; onCreateRole: () => void; onEditRole: (role: Role) => void }) {
    // Filter to show only custom roles (for now, none exist)
    const customRoles = roles.filter(role => role.type === "custom");

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h3 className={cn("text-lg font-semibold", isDark ? "text-white" : "text-gray-900")}>
                        Custom Roles
                    </h3>
                    <p className={cn("text-sm", isDark ? "text-gray-400" : "text-gray-600")}>
                        Create custom roles with specific permissions
                    </p>
                </div>
                <button
                    onClick={onCreateRole}
                    className="px-4 py-2 bg-nvidia-green hover:bg-[#8CD600] text-black font-medium rounded-lg transition-colors flex items-center gap-2"
                >
                    <Shield className="w-4 h-4" />
                    Create Role
                </button>
            </div>

            {customRoles.length === 0 ? (
                <div className={cn(
                    "rounded-xl border-2 border-dashed p-12 text-center transition-all hover:border-nvidia-green/30 group",
                    isDark ? "border-white/10 bg-white/5" : "border-gray-200 bg-gray-50"
                )}>
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-nvidia-green/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                        <Shield className="w-8 h-8 text-nvidia-green" />
                    </div>
                    <h3 className={cn("text-xl font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>
                        No Custom Roles
                    </h3>
                    <p className={cn("text-sm mb-8 max-w-sm mx-auto", isDark ? "text-gray-400" : "text-gray-600")}>
                        Create roles to grant specific permissions (e.g. "Editor", "Auditor") to your team members.
                    </p>
                    <button
                        onClick={onCreateRole}
                        className="px-6 py-3 bg-nvidia-green hover:bg-[#8CD600] text-black font-bold rounded-full transition-all shadow-lg hover:shadow-[0_0_20px_rgba(118,185,0,0.4)] inline-flex items-center gap-2"
                    >
                        <Shield className="w-4 h-4" />
                        Create Your First Role
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {customRoles.map((role) => {
                        const RoleIcon = Shield;

                        return (
                            <div
                                key={role.id}
                                onClick={() => onEditRole(role)}
                                className={cn(
                                    "rounded-xl border p-6 transition-all hover:shadow-lg cursor-pointer",
                                    isDark
                                        ? "bg-white/5 border-white/10 hover:border-nvidia-green/50"
                                        : "bg-white border-gray-200 hover:border-nvidia-green/50"
                                )}
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("p-2 rounded-lg", isDark ? "bg-white/10" : "bg-gray-100")}>
                                            <RoleIcon className="w-6 h-6 text-nvidia-green" />
                                        </div>
                                        <div>
                                            <h4 className={cn("font-semibold text-lg", isDark ? "text-white" : "text-gray-900")}>
                                                {role.name}
                                            </h4>
                                            <p className={cn("text-sm", isDark ? "text-gray-400" : "text-gray-600")}>
                                                {role.user_count} {role.user_count === 1 ? "user" : "users"}
                                            </p>
                                        </div>
                                    </div>
                                    <Edit className="w-4 h-4 text-gray-400" />
                                </div>
                                <p className={cn("text-sm mb-4", isDark ? "text-gray-400" : "text-gray-600")}>
                                    {role.description}
                                </p>

                                {/* Permissions Preview */}
                                {role.permissions && (role.permissions.agents?.edit || role.permissions.knowledge_bases?.edit || role.permissions.users?.add) && (
                                    <div className={cn("text-xs space-y-1 pt-4 border-t", isDark ? "border-white/10" : "border-gray-200")}>
                                        <div className={isDark ? "text-gray-400" : "text-gray-500"}>Permissions:</div>
                                        <div className="flex flex-wrap gap-1">
                                            {role.permissions.agents?.edit && (
                                                <span className="px-2 py-1 bg-nvidia-green/20 text-nvidia-green rounded">Edit Agents</span>
                                            )}
                                            {role.permissions.knowledge_bases?.edit && (
                                                <span className="px-2 py-1 bg-nvidia-green/20 text-nvidia-green rounded">Edit KB</span>
                                            )}
                                            {role.permissions.users?.add && (
                                                <span className="px-2 py-1 bg-nvidia-green/20 text-nvidia-green rounded">Add Users</span>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

function SharingTab({ sharing, isDark }: { sharing: any; isDark: boolean }) {
    if (!sharing) return null;

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <div>
                    <h3 className={cn("text-lg font-semibold", isDark ? "text-white" : "text-gray-900")}>
                        Resource Sharing
                    </h3>
                    <p className={cn("text-sm", isDark ? "text-gray-400" : "text-gray-600")}>
                        {sharing.total_shares} shared {sharing.total_shares === 1 ? "resource" : "resources"}
                    </p>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(sharing.by_type).map(([type, count]: [string, any]) => (
                    <div
                        key={type}
                        className={cn(
                            "rounded-lg border p-4",
                            isDark ? "bg-white/5 border-white/10" : "bg-white border-gray-200"
                        )}
                    >
                        <div className={cn("text-2xl font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>
                            {count}
                        </div>
                        <div className={cn("text-sm capitalize", isDark ? "text-gray-400" : "text-gray-600")}>
                            {type.replace(/_/g, " ")}
                        </div>
                    </div>
                ))}
            </div>

            {/* Detailed List */}
            <div className={cn("rounded-xl border p-6", isDark ? "border-white/10 bg-white/5" : "border-gray-200 bg-white")}>
                <p className={cn("text-center", isDark ? "text-gray-400" : "text-gray-600")}>
                    Detailed sharing management coming soon
                </p>
            </div>
        </div>
    );
}
