"use client";

import { useState, useEffect } from "react";
import { X, Users, UserPlus, Trash2, Edit, Crown, Shield, User as UserIcon, Eye } from "lucide-react";
import api from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

interface TenantMembersModalProps {
    isOpen: boolean;
    onClose: () => void;
    tenantId: string;
}

interface TenantMember {
    user_id: string;
    user_email: string;
    user_name: string | null;
    role: string;
    joined_at: string;
}

const roleIcons = {
    owner: Crown,
    admin: Shield,
    member: UserIcon,
    viewer: Eye,
};

const roleColors = {
    owner: "text-yellow-500",
    admin: "text-nvidia-green",
    member: "text-blue-500",
    viewer: "text-gray-500",
};

const TenantMembersModal: React.FC<TenantMembersModalProps> = ({
    isOpen,
    onClose,
    tenantId,
}) => {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [members, setMembers] = useState<TenantMember[]>([]);
    const [loading, setLoading] = useState(false);
    const [showAddMember, setShowAddMember] = useState(false);
    const [newUserEmail, setNewUserEmail] = useState("");
    const [newUserRole, setNewUserRole] = useState("member");
    const [allUsers, setAllUsers] = useState<any[]>([]);

    useEffect(() => {
        if (isOpen) {
            fetchMembers();
            fetchAllUsers();
        }
    }, [isOpen, tenantId]);

    const fetchMembers = async () => {
        if (!tenantId) {
            console.error("No tenant ID provided");
            return;
        }

        setLoading(true);
        try {
            console.log(`Fetching members for tenant: ${tenantId}`);
            const response = await api.get(`/tenants/${tenantId}/members`);
            setMembers(response.data);
        } catch (error: any) {
            console.error("Failed to fetch members", error);
            console.error("Error details:", error.response?.data);
            console.error("Request URL:", error.config?.url);
        } finally {
            setLoading(false);
        }
    };

    const fetchAllUsers = async () => {
        try {
            const response = await api.get("/admin/users");
            setAllUsers(response.data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        }
    };

    const handleAddMember = async () => {
        try {
            // Find user by email
            const user = allUsers.find(u => u.email === newUserEmail);
            if (!user) {
                alert("User not found");
                return;
            }

            await api.post(`/tenants/${tenantId}/members`, {
                user_id: user.id,
                role: newUserRole
            });

            alert("Member added successfully!");
            setShowAddMember(false);
            setNewUserEmail("");
            fetchMembers();
        } catch (error: any) {
            alert(`Failed to add member: ${error.response?.data?.detail || error.message}`);
        }
    };

    const handleRemoveMember = async (userId: string) => {
        if (!confirm("Are you sure you want to remove this member?")) return;

        try {
            await api.delete(`/tenants/${tenantId}/members/${userId}`);
            fetchMembers();
        } catch (error: any) {
            alert(`Failed to remove member: ${error.response?.data?.detail || error.message}`);
        }
    };

    const handleUpdateRole = async (userId: string, newRole: string) => {
        try {
            await api.put(`/tenants/${tenantId}/members/${userId}`, { role: newRole });
            fetchMembers();
        } catch (error: any) {
            alert(`Failed to update role: ${error.response?.data?.detail || error.message}`);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
            <div className={cn("relative w-full max-w-3xl mx-4 rounded-2xl shadow-2xl max-h-[90vh] overflow-hidden", isDark ? "bg-nvidia-dark border border-white/10" : "bg-white")}>

                {/* Header */}
                <div className={cn("p-6 border-b", isDark ? "border-white/10" : "border-gray-200")}>
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className={cn("text-2xl font-bold flex items-center gap-2", isDark ? "text-white" : "text-gray-900")}>
                                <Users className="w-6 h-6 text-nvidia-green" />
                                Tenant Members
                            </h2>
                            <p className={cn("text-sm mt-1", isDark ? "text-gray-400" : "text-gray-600")}>
                                Manage users in your tenant
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className={cn("p-2 rounded-lg transition-colors", isDark ? "hover:bg-white/5" : "hover:bg-gray-100")}
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-200px)]">

                    {/* Add Member Button */}
                    <button
                        onClick={() => setShowAddMember(!showAddMember)}
                        className="w-full p-4 rounded-lg border-2 border-dashed border-nvidia-green/30 hover:border-nvidia-green/50 hover:bg-nvidia-green/5 transition-all flex items-center justify-center gap-2 text-nvidia-green font-medium"
                    >
                        <UserPlus className="w-5 h-5" />
                        Add Member
                    </button>

                    {/* Add Member Form */}
                    {showAddMember && (
                        <div className={cn("p-4 rounded-lg border space-y-3", isDark ? "bg-white/5 border-white/10" : "bg-gray-50 border-gray-200")}>
                            <div>
                                <label className={cn("block text-sm font-medium mb-2", isDark ? "text-gray-300" : "text-gray-700")}>
                                    User Email
                                </label>
                                <select
                                    value={newUserEmail}
                                    onChange={(e) => setNewUserEmail(e.target.value)}
                                    className={cn("w-full px-4 py-2 rounded-lg border", isDark
                                        ? "bg-white/5 border-white/10 text-white"
                                        : "bg-white border-gray-300 text-gray-900"
                                    )}
                                >
                                    <option value="">Select user...</option>
                                    {allUsers.map((user) => (
                                        <option key={user.id} value={user.email}>
                                            {user.email} {user.full_name && `(${user.full_name})`}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className={cn("block text-sm font-medium mb-2", isDark ? "text-gray-300" : "text-gray-700")}>
                                    Role
                                </label>
                                <select
                                    value={newUserRole}
                                    onChange={(e) => setNewUserRole(e.target.value)}
                                    className={cn("w-full px-4 py-2 rounded-lg border", isDark
                                        ? "bg-white/5 border-white/10 text-white"
                                        : "bg-white border-gray-300 text-gray-900"
                                    )}
                                >
                                    <option value="viewer">Viewer</option>
                                    <option value="member">Member</option>
                                    <option value="admin">Admin</option>
                                    <option value="owner">Owner</option>
                                </select>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setShowAddMember(false)}
                                    className={cn("flex-1 px-4 py-2 rounded-lg font-medium", isDark
                                        ? "bg-white/5 hover:bg-white/10"
                                        : "bg-gray-200 hover:bg-gray-300"
                                    )}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAddMember}
                                    disabled={!newUserEmail}
                                    className="flex-1 px-4 py-2 bg-nvidia-green hover:bg-[#8CD600] text-black font-bold rounded-lg disabled:opacity-50"
                                >
                                    Add
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Members List */}
                    <div className="space-y-2">
                        {loading ? (
                            <div className="text-center py-8 text-gray-400">Loading...</div>
                        ) : members.length === 0 ? (
                            <div className="text-center py-8 text-gray-400">No members found</div>
                        ) : (
                            members.map((member) => {
                                const RoleIcon = roleIcons[member.role as keyof typeof roleIcons] || UserIcon;
                                const roleColor = roleColors[member.role as keyof typeof roleColors] || "text-gray-500";

                                return (
                                    <div
                                        key={member.user_id}
                                        className={cn("p-4 rounded-lg border transition-colors", isDark
                                            ? "bg-white/5 border-white/10 hover:bg-white/10"
                                            : "bg-white border-gray-200 hover:border-gray-300"
                                        )}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <RoleIcon className={cn("w-5 h-5", roleColor)} />
                                                <div>
                                                    <div className={cn("font-medium", isDark ? "text-white" : "text-gray-900")}>
                                                        {member.user_name || "Unknown"}
                                                    </div>
                                                    <div className={cn("text-sm", isDark ? "text-gray-400" : "text-gray-600")}>
                                                        {member.user_email}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <select
                                                    value={member.role}
                                                    onChange={(e) => handleUpdateRole(member.user_id, e.target.value)}
                                                    className={cn("px-3 py-1 rounded-lg border text-sm font-medium", isDark
                                                        ? "bg-white/5 border-white/10 text-white"
                                                        : "bg-white border-gray-300 text-gray-900"
                                                    )}
                                                >
                                                    <option value="viewer">Viewer</option>
                                                    <option value="member">Member</option>
                                                    <option value="admin">Admin</option>
                                                    <option value="owner">Owner</option>
                                                </select>
                                                <button
                                                    onClick={() => handleRemoveMember(member.user_id)}
                                                    className={cn("p-2 rounded-lg transition-colors", isDark
                                                        ? "hover:bg-red-900/20 hover:text-red-400"
                                                        : "hover:bg-red-50 hover:text-red-600"
                                                    )}
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className={cn("p-6 border-t flex justify-end", isDark ? "border-white/10" : "border-gray-200")}>
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 bg-nvidia-green hover:bg-[#8CD600] text-black font-bold rounded-lg transition-all"
                    >
                        Done
                    </button>
                </div>
            </div>
        </div>
    );
};

export default TenantMembersModal;
