"use client";

import { useEffect, useState } from "react";
import { Plus, Users, Shield, Trash2, Edit, Search, X } from "lucide-react";
import api from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import { Can, useAuth } from "@/contexts/AuthContext";
import Dialog from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/Toast";

export default function UsersPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const { toast } = useToast();
    const { role: currentActiveRole } = useAuth();

    const [users, setUsers] = useState<any[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"users" | "groups">("users");

    // Modal
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isGroupModalOpen, setIsGroupModalOpen] = useState(false); // Groups

    const [inviteData, setInviteData] = useState({
        email: "",
        full_name: "",
        role: "member",
        role_id: "",
        password: ""
    });

    // Group Form Data
    const [groupData, setGroupData] = useState({
        name: "",
        description: ""
    });

    const [isSubmitting, setIsSubmitting] = useState(false);

    const [currentUser, setCurrentUser] = useState<any>(null);

    const [availableRoles, setAvailableRoles] = useState<any[]>([]);

    useEffect(() => {
        fetchCurrentUser();
        fetchUsers();
        fetchGroups();
        fetchRoles();
    }, []);

    const fetchRoles = async () => {
        try {
            const res = await api.get("/tenant/roles");
            setAvailableRoles(res.data);
        } catch (error) {
            console.error(error);
        }
    };

    const fetchCurrentUser = async () => {
        try {
            const res = await api.get("/auth/me");
            setCurrentUser(res.data);
        } catch (error) {
            console.error(error);
        }
    };

    const fetchUsers = async () => {
        try {
            const res = await api.get("/tenant/users");
            setUsers(res.data);
        } catch (error) {
            console.error(error);
            toast("Failed to load users", "error");
        }
    };

    const fetchGroups = async () => {
        try {
            const res = await api.get("/tenant/groups");
            setGroups(res.data);
        } catch (error) {
            console.error(error);
            // toast("Failed to load groups", "error"); // Optional
        } finally {
            setLoading(false);
        }
    };

    const [formErrors, setFormErrors] = useState<{ email?: string, password?: string, full_name?: string }>({});

    const validateForm = () => {
        const errors: any = {};
        if (!inviteData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteData.email)) {
            errors.email = "Please enter a valid email address.";
        }
        if (!inviteData.full_name || inviteData.full_name.trim().length < 2) {
            errors.full_name = "Full name must be at least 2 characters.";
        }
        if (inviteData.password && inviteData.password.length < 6) {
            errors.password = "Password must be at least 6 characters.";
        }
        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleInvite = async () => {
        if (!validateForm()) {
            toast("Please fix the errors in the form.", "error");
            return;
        }

        setIsSubmitting(true);
        try {
            await api.post("/tenant/users", inviteData);
            toast("User added successfully", "success");
            setIsModalOpen(false);
            setInviteData({ email: "", full_name: "", role: "member", role_id: "", password: "" });
            setFormErrors({});
            fetchUsers();
        } catch (error: any) {
            console.error("Invite failed", error);
            const msg = error.response?.data?.detail || "Failed to invite user";
            toast(msg, "error");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleRemove = async (userId: string) => {
        if (!confirm("Are you sure you want to remove this user from the workspace?")) return;
        try {
            await api.delete(`/tenant/users/${userId}`);
            toast("User removed", "success");
            fetchUsers();
        } catch (error: any) {
            toast(error.response?.data?.detail || "Failed to remove user", "error");
        }
    };

    const handleRoleUpdate = async (userId: string, newRoleId: string) => {
        try {
            await api.put(`/tenant/users/${userId}/role`, { role_id: newRoleId }); // Send ID
            toast("Role updated", "success");
            fetchUsers();
        } catch (error: any) {
            toast(error.response?.data?.detail || "Failed to update role", "error");
        }
    };

    // Group Details
    const [selectedGroup, setSelectedGroup] = useState<any>(null);
    const [isGroupDetailOpen, setIsGroupDetailOpen] = useState(false);
    const [groupMembers, setGroupMembers] = useState<any[]>([]);
    const [newMemberId, setNewMemberId] = useState("");

    const fetchGroupDetails = async (groupId: string) => {
        try {
            const res = await api.get(`/tenant/groups/${groupId}`);
            setSelectedGroup(res.data);
            setGroupMembers(res.data.members || []);
            setIsGroupDetailOpen(true);
        } catch (error: any) {
            toast("Failed to load group details", "error");
        }
    };

    const handleAddMember = async () => {
        if (!selectedGroup || !newMemberId) return;
        try {
            await api.post(`/tenant/groups/${selectedGroup.id}/members`, { user_id: newMemberId });
            toast("Member added", "success");
            fetchGroupDetails(selectedGroup.id); // Reload
            setNewMemberId("");
            fetchGroups(); // Update count
        } catch (error: any) {
            toast(error.response?.data?.detail || "Failed to add member", "error");
        }
    };

    const handleRemoveMember = async (userId: string) => {
        if (!confirm("Remove user from group?")) return;
        try {
            await api.delete(`/tenant/groups/${selectedGroup.id}/members/${userId}`);
            toast("Member removed", "success");
            fetchGroupDetails(selectedGroup.id);
            fetchGroups();
        } catch (error: any) {
            toast("Failed to remove member", "error");
        }
    };

    const handleCreateGroup = async () => {
        if (!groupData.name) {
            toast("Group name is required", "error");
            return;
        }
        setIsSubmitting(true);
        try {
            await api.post("/tenant/groups", groupData);
            toast("Group created successfully", "success");
            setIsGroupModalOpen(false);
            setGroupData({ name: "", description: "" });
            fetchGroups();
        } catch (error: any) {
            toast(error.response?.data?.detail || "Failed to create group", "error");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDeleteGroup = async (groupId: string) => {
        if (!confirm("Are you sure you want to delete this group?")) return;
        try {
            await api.delete(`/tenant/groups/${groupId}`);
            toast("Group deleted", "success");
            fetchGroups();
        } catch (error: any) {
            toast("Failed to delete group", "error");
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className={cn("text-3xl font-bold tracking-tight mb-2", isDark ? "text-white" : "text-gray-900")}>
                        Users & Groups
                    </h1>
                    <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                        Manage access to your workspace.
                    </p>
                </div>
                {activeTab === 'users' ? (
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className={cn(
                            "flex items-center justify-center px-5 py-2.5 rounded-xl font-bold transition-all duration-300 shadow-lg hover:shadow-nvidia-green/20 group",
                            "bg-gradient-to-r from-nvidia-green to-[#8CD600] text-black hover:scale-[1.02]"
                        )}
                    >
                        <Plus className="w-5 h-5 mr-2 group-hover:rotate-90 transition-transform duration-300" />
                        Add User
                    </button>
                ) : (
                    <button
                        onClick={() => setIsGroupModalOpen(true)}
                        className={cn(
                            "flex items-center justify-center px-5 py-2.5 rounded-xl font-bold transition-all duration-300 shadow-lg hover:shadow-nvidia-green/20 group",
                            "bg-gradient-to-r from-nvidia-green to-[#8CD600] text-black hover:scale-[1.02]"
                        )}
                    >
                        <Plus className="w-5 h-5 mr-2 duration-300" />
                        Create Group
                    </button>
                )}
            </div>

            {/* Tabs */}
            <div className="flex space-x-1 bg-gray-100 dark:bg-white/5 p-1 rounded-xl w-fit">
                <button
                    onClick={() => setActiveTab("users")}
                    className={cn(
                        "px-4 py-2 rounded-lg text-sm font-bold transition-all",
                        activeTab === "users"
                            ? (isDark ? "bg-nvidia-green text-black" : "bg-white text-black shadow-sm")
                            : (isDark ? "text-gray-400 hover:text-white" : "text-gray-500 hover:text-black")
                    )}
                >
                    Users
                </button>
                <button
                    onClick={() => setActiveTab("groups")}
                    className={cn(
                        "px-4 py-2 rounded-lg text-sm font-bold transition-all",
                        activeTab === "groups"
                            ? (isDark ? "bg-nvidia-green text-black" : "bg-white text-black shadow-sm")
                            : (isDark ? "text-gray-400 hover:text-white" : "text-gray-500 hover:text-black")
                    )}
                >
                    Groups
                </button>
            </div>

            {activeTab === "users" ? (
                /* Users Table */
                <div className={
                    cn("rounded-2xl border overflow-hidden shadow-sm transition-all duration-300",
                        isDark ? "bg-[#0f0f0f]/60 backdrop-blur-md border-white/5 hover:border-white/10" : "bg-white border-gray-200 shadow-md")}>

                    {/* Desktop Table */}
                    <div className="hidden md:block overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className={isDark ? "bg-white/5 border-b border-white/5" : "bg-gray-50/50 border-b border-gray-200"}>
                                    <th className={cn("px-6 py-5 font-bold text-xs uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>User</th>
                                    <th className={cn("px-6 py-5 font-bold text-xs uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>Email</th>
                                    <th className={cn("px-6 py-5 font-bold text-xs uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>Role</th>
                                    <th className={cn("px-6 py-5 font-bold text-xs uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>Status</th>
                                    <th className="px-6 py-5 text-right"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {users.map((member) => (
                                    <tr key={member.user_id} className={cn("transition-colors duration-200 group", isDark ? "hover:bg-white/5" : "hover:bg-gray-50")}>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center">
                                                <div className={cn("w-10 h-10 rounded-full flex items-center justify-center mr-4 font-bold text-sm shadow-inner",
                                                    isDark ? "bg-gradient-to-br from-nvidia-green/20 to-emerald-900/40 text-nvidia-green border border-nvidia-green/20" : "bg-gradient-to-br from-green-100 to-green-200 text-green-700")}>
                                                    {member.user?.full_name?.[0] || member.user?.email?.[0] || "U"}
                                                </div>
                                                <div>
                                                    <div className={cn("font-bold text-base", isDark ? "text-white group-hover:text-nvidia-green transition-colors" : "text-gray-900")}>
                                                        {member.user?.full_name || "Unknown"}
                                                    </div>
                                                    <div className="text-xs text-gray-500 mt-0.5">ID: {member.user_id?.substring(0, 8)}...</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className={cn("px-6 py-4 text-sm font-medium", isDark ? "text-gray-300" : "text-gray-600")}>
                                            {member.user?.email}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="relative inline-flex">
                                                {currentUser?.role !== 'owner' && (member.role === 'owner' || (currentUser && member.user_id === currentUser.id)) ? (
                                                    <span className={cn("px-3 py-1.5 rounded-lg text-xs font-bold uppercase border select-none",
                                                        member.role === 'owner'
                                                            ? "text-purple-400 border-purple-500/30 bg-purple-500/10"
                                                            : "text-gray-400 border-gray-700 bg-white/5"
                                                    )}>
                                                        {member.tenant_role?.name || member.role}
                                                    </span>
                                                ) : (
                                                    <select
                                                        value={member.role_id || ""}
                                                        onChange={(e) => handleRoleUpdate(member.user_id, e.target.value)}
                                                        className={cn("appearance-none pl-3 pr-8 py-1.5 text-xs font-bold uppercase rounded-lg border bg-transparent outline-none focus:ring-2 focus:ring-nvidia-green/50 transition-all cursor-pointer",
                                                            member.role === 'owner' ? "text-purple-400 border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20" :
                                                                member.role === 'admin' ? "text-nvidia-green border-nvidia-green/30 bg-nvidia-green/10 hover:bg-nvidia-green/20" :
                                                                    "text-gray-400 border-gray-700 hover:border-gray-500"
                                                        )}
                                                    >
                                                        {availableRoles
                                                            .filter(r => {
                                                                if (r.name.toLowerCase() === 'owner') {
                                                                    return currentActiveRole?.name.toLowerCase() === 'owner';
                                                                }
                                                                return true;
                                                            })
                                                            .map(r => (
                                                                <option key={r.id} value={r.id} className="bg-gray-900">{r.name}</option>
                                                            ))}
                                                    </select>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-500 ring-1 ring-emerald-500/20">
                                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2 animate-pulse" />
                                                Active
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => handleRemove(member.user_id)}
                                                disabled={member.role === 'owner'}
                                                className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100 disabled:invisible focus:opacity-100"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Mobile Card List */}
                    <div className="md:hidden divide-y divide-white/5">
                        {users.map((member) => (
                            <div key={member.user_id} className="p-4 space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center">
                                        <div className={cn("w-10 h-10 rounded-full flex items-center justify-center mr-3 font-bold text-sm",
                                            isDark ? "bg-nvidia-green/20 text-nvidia-green" : "bg-green-100 text-green-700")}>
                                            {member.user?.full_name?.[0] || "U"}
                                        </div>
                                        <div>
                                            <div className={cn("font-bold text-sm", isDark ? "text-white" : "text-gray-900")}>
                                                {member.user?.full_name || "Unknown"}
                                            </div>
                                            <div className="text-[10px] text-gray-500">{member.user?.email}</div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleRemove(member.user_id)}
                                        disabled={member.role === 'owner'}
                                        className="p-2 text-gray-500 hover:text-red-400"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="relative">
                                        {currentUser?.role !== 'owner' && (member.role === 'owner' || (currentUser && member.user_id === currentUser.id)) ? (
                                            <span className={cn("px-2 py-1 rounded-lg text-[10px] font-bold uppercase border",
                                                member.role === 'owner' ? "text-purple-400 border-purple-500/20 bg-purple-500/10" : "text-gray-400 border-gray-700"
                                            )}>
                                                {member.tenant_role?.name || member.role}
                                            </span>
                                        ) : (
                                            <select
                                                value={member.role_id || ""}
                                                onChange={(e) => handleRoleUpdate(member.user_id, e.target.value)}
                                                className={cn("appearance-none pl-3 pr-8 py-1.5 text-[10px] font-bold uppercase rounded-lg border bg-transparent outline-none",
                                                    member.role === 'owner' ? "text-purple-400 border-purple-500/20 bg-purple-500/10" :
                                                        member.role === 'admin' ? "text-nvidia-green border-nvidia-green/20 bg-nvidia-green/10" :
                                                            "text-gray-400 border-gray-700"
                                                )}
                                            >
                                                {availableRoles.filter(r => r.name.toLowerCase() === 'owner' ? currentActiveRole?.name.toLowerCase() === 'owner' : true).map(r => (
                                                    <option key={r.id} value={r.id} className="bg-gray-900">{r.name}</option>
                                                ))}
                                            </select>
                                        )}
                                    </div>
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-500">
                                        Active
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                /* Groups Table */
                <div className={cn("rounded-2xl border overflow-hidden shadow-sm transition-all duration-300",
                    isDark ? "bg-[#0f0f0f]/60 backdrop-blur-md border-white/5 hover:border-white/10" : "bg-white border-gray-200 shadow-md")}>
                    {/* Desktop Table */}
                    <div className="hidden md:block overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className={isDark ? "bg-white/5 border-b border-white/5" : "bg-gray-50/50 border-b border-gray-200"}>
                                    <th className={cn("px-6 py-5 font-bold text-xs uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>Group Name</th>
                                    <th className={cn("px-6 py-5 font-bold text-xs uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>Description</th>
                                    <th className={cn("px-6 py-5 font-bold text-xs uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-500")}>Members</th>
                                    <th className="px-6 py-5 text-right"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {groups.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                                            No groups created yet.
                                        </td>
                                    </tr>
                                )}
                                {groups.map((group) => (
                                    <tr key={group.id} className={cn("transition-colors duration-200 group", isDark ? "hover:bg-white/5" : "hover:bg-gray-50")}>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center">
                                                <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mr-4 font-bold text-sm shadow-inner",
                                                    isDark ? "bg-gradient-to-br from-blue-500/20 to-blue-900/40 text-blue-400 border border-blue-500/20" : "bg-gradient-to-br from-blue-100 to-blue-200 text-blue-600")}>
                                                    <Users className="w-5 h-5" />
                                                </div>
                                                <span className={cn("font-bold text-base", isDark ? "text-white" : "text-gray-900")}>
                                                    {group.name}
                                                </span>
                                            </div>
                                        </td>
                                        <td className={cn("px-6 py-4 text-sm font-medium", isDark ? "text-gray-300" : "text-gray-600")}>
                                            {group.description || "-"}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={cn("px-3 py-1 rounded-full text-xs font-bold", isDark ? "bg-white/10 text-white" : "bg-gray-100 text-gray-700")}>
                                                {group.member_count || 0} Members
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right flex justify-end space-x-2">
                                            <button
                                                onClick={() => fetchGroupDetails(group.id)}
                                                className="p-2 text-gray-500 hover:text-blue-500 hover:bg-blue-500/10 rounded-lg transition-all focus:opacity-100"
                                            >
                                                <Edit className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleDeleteGroup(group.id)}
                                                className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Mobile Card List */}
                    <div className="md:hidden divide-y divide-white/5">
                        {groups.length === 0 && (
                            <div className="p-8 text-center text-sm text-gray-500">
                                No groups created yet.
                            </div>
                        )}
                        {groups.map((group) => (
                            <div key={group.id} className="p-4 space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center">
                                        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mr-3",
                                            isDark ? "bg-blue-500/10 text-blue-400" : "bg-blue-50 text-blue-600")}>
                                            <Users className="w-5 h-5" />
                                        </div>
                                        <span className={cn("font-bold text-sm", isDark ? "text-white" : "text-gray-900")}>
                                            {group.name}
                                        </span>
                                    </div>
                                    <div className="flex items-center space-x-1">
                                        <button
                                            onClick={() => fetchGroupDetails(group.id)}
                                            className="p-2 text-gray-500 hover:text-blue-500"
                                        >
                                            <Edit className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteGroup(group.id)}
                                            className="p-2 text-gray-500 hover:text-red-400"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between text-[10px]">
                                    <span className="text-gray-500 truncate max-w-[150px]">{group.description || "No description"}</span>
                                    <span className={cn("px-2 py-0.5 rounded-full font-bold", isDark ? "bg-white/10 text-white" : "bg-gray-100 text-gray-700")}>
                                        {group.member_count || 0} Members
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )
            }

            {/* Invite Modal */}
            <Dialog
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="Add User to Workspace"
                buttons={[
                    { label: "Cancel", onClick: () => setIsModalOpen(false), variant: "outline" },
                    { label: isSubmitting ? "Adding..." : "Add User", onClick: handleInvite, variant: "primary", isLoading: isSubmitting }
                ]}
            >
                <div className="space-y-4">
                    <div>
                        <Input
                            label="Email Address"
                            type="email"
                            placeholder="colleague@company.com"
                            value={inviteData.email}
                            onChange={e => {
                                setInviteData({ ...inviteData, email: e.target.value });
                                if (formErrors.email) setFormErrors({ ...formErrors, email: undefined });
                            }}
                            className={formErrors.email ? "border-red-500 focus:ring-red-500" : ""}
                        />
                        {formErrors.email && <p className="text-red-500 text-xs mt-1">{formErrors.email}</p>}
                    </div>

                    <div>
                        <Input
                            label="Full Name"
                            placeholder="John Doe"
                            value={inviteData.full_name}
                            onChange={e => {
                                setInviteData({ ...inviteData, full_name: e.target.value });
                                if (formErrors.full_name) setFormErrors({ ...formErrors, full_name: undefined });
                            }}
                            className={formErrors.full_name ? "border-red-500 focus:ring-red-500" : ""}
                        />
                        {formErrors.full_name && <p className="text-red-500 text-xs mt-1">{formErrors.full_name}</p>}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <Select
                            label="Role"
                            value={inviteData.role_id}
                            onChange={(e) => setInviteData({ ...inviteData, role_id: e.target.value })}
                            options={[
                                { label: "Select Role...", value: "" },
                                ...availableRoles
                                    .filter(r => {
                                        // Only Owner can see/assign Owner role
                                        if (r.name.toLowerCase() === 'owner') {
                                            return currentActiveRole?.name.toLowerCase() === 'owner';
                                        }
                                        return true;
                                    })
                                    .map(r => ({ label: r.name, value: r.id }))
                            ]}
                        />
                        <div>
                            <Input
                                label="Password (Optional for existing)"
                                type="password"
                                placeholder="Set a password"
                                value={inviteData.password}
                                onChange={e => {
                                    setInviteData({ ...inviteData, password: e.target.value });
                                    if (formErrors.password) setFormErrors({ ...formErrors, password: undefined });
                                }}
                                className={formErrors.password ? "border-red-500 focus:ring-red-500" : ""}
                            />
                            {formErrors.password && <p className="text-red-500 text-xs mt-1">{formErrors.password}</p>}
                        </div>
                    </div>

                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                        <p className="text-xs text-blue-200">
                            <strong>Note:</strong> If the email matches an existing user, they will be added to this workspace. Otherwise, a new account is created.
                        </p>
                    </div>
                </div>
            </Dialog>

            {/* Create Group Modal */}
            <Dialog
                isOpen={isGroupModalOpen}
                onClose={() => setIsGroupModalOpen(false)}
                title="Create New Group"
                buttons={[
                    { label: "Cancel", onClick: () => setIsGroupModalOpen(false), variant: "outline" },
                    { label: isSubmitting ? "Creating..." : "Create Group", onClick: handleCreateGroup, variant: "primary", isLoading: isSubmitting }
                ]}
            >
                <div className="space-y-4">
                    <div>
                        <Input
                            label="Group Name"
                            placeholder="e.g. Developers, Testers"
                            value={groupData.name}
                            onChange={e => setGroupData({ ...groupData, name: e.target.value })}
                        />
                    </div>
                    <div>
                        <Input
                            label="Description"
                            placeholder="Optional description"
                            value={groupData.description}
                            onChange={e => setGroupData({ ...groupData, description: e.target.value })}
                        />
                    </div>
                </div>
            </Dialog>

            {/* Group Details / Manage Members Modal */}
            <Dialog
                isOpen={isGroupDetailOpen}
                onClose={() => setIsGroupDetailOpen(false)}
                title={`Manage Group: ${selectedGroup?.name || 'Group'}`}
                buttons={[
                    { label: "Close", onClick: () => setIsGroupDetailOpen(false), variant: "outline" }
                ]}
            >
                <div className="space-y-6">
                    {/* Add Member */}
                    <div className="flex space-x-2 items-end">
                        <div className="flex-1">
                            <Select
                                label="Add User to Group"
                                value={newMemberId}
                                onChange={(e) => setNewMemberId(e.target.value)}
                                options={[
                                    { label: "Select a user...", value: "" },
                                    ...users
                                        .filter(u => !groupMembers.some(m => m.user_id === u.user_id))
                                        .map(u => ({ label: `${u.user?.full_name} (${u.user?.email})`, value: u.user_id }))
                                ]}
                            />
                        </div>
                        <button
                            onClick={handleAddMember}
                            disabled={!newMemberId}
                            className={cn("px-4 py-2.5 rounded-xl font-bold mb-[1px] transition-colors",
                                !newMemberId ? "bg-gray-200 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600" : "bg-nvidia-green text-black hover:bg-[#8CD600]")}
                        >
                            <Plus className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Members List */}
                    <div>
                        <h4 className={cn("text-xs font-bold uppercase tracking-wider mb-3", isDark ? "text-gray-500" : "text-gray-400")}>
                            Current Members ({groupMembers.length})
                        </h4>

                        <div className={cn("rounded-xl border max-h-[300px] overflow-y-auto", isDark ? "border-white/10 bg-black/20" : "border-gray-200 bg-gray-50")}>
                            {groupMembers.length === 0 ? (
                                <div className="p-8 text-center text-sm text-gray-500">
                                    No members in this group yet.
                                </div>
                            ) : (
                                <div className="divide-y divide-white/5">
                                    {groupMembers.map((member: any) => (
                                        <div key={member.user_id} className="p-3 flex items-center justify-between">
                                            <div className="flex items-center">
                                                <div className={cn("w-8 h-8 rounded-full flex items-center justify-center mr-3 font-bold text-xs",
                                                    isDark ? "bg-white/10 text-white" : "bg-gray-200 text-gray-700")}>
                                                    {member.user?.full_name?.[0] || "U"}
                                                </div>
                                                <div>
                                                    <div className={cn("text-sm font-bold", isDark ? "text-white" : "text-gray-900")}>
                                                        {member.user?.full_name}
                                                    </div>
                                                    <div className="text-xs text-gray-500">{member.user?.email}</div>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => handleRemoveMember(member.user_id)}
                                                className="p-1.5 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </Dialog>
        </div >
    );
}
