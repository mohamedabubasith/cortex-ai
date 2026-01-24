"use client";

import { useEffect, useState } from "react";
import { Plus, Users, Shield, Trash2, Edit, Search } from "lucide-react";
import api from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import Dialog from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/Toast";

export default function UsersPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const { toast } = useToast();

    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [inviteData, setInviteData] = useState({
        email: "",
        full_name: "",
        role: "member",
        password: ""
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const res = await api.get("/tenant/users");
            setUsers(res.data);
        } catch (error) {
            console.error(error);
            toast("Failed to load users", "error");
        } finally {
            setLoading(false);
        }
    };

    const handleInvite = async () => {
        setIsSubmitting(true);
        try {
            await api.post("/tenant/users", inviteData);
            toast("User invited/added successfully", "success");
            setIsModalOpen(false);
            setInviteData({ email: "", full_name: "", role: "member", password: "" });
            fetchUsers();
        } catch (error: any) {
            toast(error.response?.data?.detail || "Failed to invite user", "error");
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

    const handleRoleUpdate = async (userId: string, newRole: string) => {
        try {
            await api.put(`/tenant/users/${userId}/role`, { role: newRole });
            toast("Role updated", "success");
            fetchUsers();
        } catch (error: any) {
            toast(error.response?.data?.detail || "Failed to update role", "error");
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
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center justify-center px-4 py-2 bg-nvidia-green text-black font-bold rounded-lg hover:bg-[#8CD600] transition-all"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    Add User
                </button>
            </div>

            {/* Users Table */}
            <div className={cn("rounded-xl border overflow-hidden", isDark ? "bg-nvidia-dark/50 border-white/10" : "bg-white border-gray-200")}>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className={isDark ? "bg-white/5 border-b border-white/10" : "bg-gray-50 border-b border-gray-200"}>
                                <th className={cn("p-4 font-medium text-sm", isDark ? "text-gray-300" : "text-gray-600")}>User</th>
                                <th className={cn("p-4 font-medium text-sm", isDark ? "text-gray-300" : "text-gray-600")}>Email</th>
                                <th className={cn("p-4 font-medium text-sm", isDark ? "text-gray-300" : "text-gray-600")}>Role</th>
                                <th className={cn("p-4 font-medium text-sm", isDark ? "text-gray-300" : "text-gray-600")}>Status</th>
                                <th className="p-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((member) => (
                                <tr key={member.user_id} className={cn("border-b last:border-0", isDark ? "border-white/5 hover:bg-white/5" : "border-gray-100 hover:bg-gray-50")}>
                                    <td className="p-4">
                                        <div className="flex items-center">
                                            <div className={cn("w-8 h-8 rounded-full flex items-center justify-center mr-3 font-bold text-xs", isDark ? "bg-nvidia-green/20 text-nvidia-green" : "bg-green-100 text-green-700")}>
                                                {member.user?.full_name?.[0] || member.user?.email?.[0] || "U"}
                                            </div>
                                            <span className={cn("font-medium", isDark ? "text-white" : "text-gray-900")}>
                                                {member.user?.full_name || "Unknown"}
                                            </span>
                                        </div>
                                    </td>
                                    <td className={cn("p-4 text-sm font-mono", isDark ? "text-gray-400" : "text-gray-600")}>
                                        {member.user?.email}
                                    </td>
                                    <td className="p-4">
                                        <select
                                            value={member.role}
                                            onChange={(e) => handleRoleUpdate(member.user_id, e.target.value)}
                                            className={cn("text-xs font-bold uppercase px-2 py-1 rounded border bg-transparent cursor-pointer",
                                                member.role === 'owner' ? "text-purple-400 border-purple-400/30 bg-purple-400/10" :
                                                    member.role === 'admin' ? "text-nvidia-green border-nvidia-green/30 bg-nvidia-green/10" :
                                                        "text-gray-400 border-gray-500/30"
                                            )}
                                        >
                                            <option value="member">Member</option>
                                            <option value="viewer">Viewer</option>
                                            <option value="admin">Admin</option>
                                            {/* Owner usually transferred, but allowed here if backend permits */}
                                        </select>
                                    </td>
                                    <td className="p-4">
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-500">
                                            Active
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button
                                            onClick={() => handleRemove(member.user_id)}
                                            disabled={member.role === 'owner'}
                                            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

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
                    <Input
                        label="Email Address"
                        type="email"
                        placeholder="colleague@company.com"
                        value={inviteData.email}
                        onChange={e => setInviteData({ ...inviteData, email: e.target.value })}
                    />
                    <Input
                        label="Full Name"
                        placeholder="John Doe"
                        value={inviteData.full_name}
                        onChange={e => setInviteData({ ...inviteData, full_name: e.target.value })}
                    />
                    <div className="grid grid-cols-2 gap-4">
                        <Select
                            label="Role"
                            value={inviteData.role}
                            onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
                            options={[
                                { label: "Admin", value: "admin" },
                                { label: "Member", value: "member" },
                                { label: "Viewer", value: "viewer" }
                            ]}
                        />
                        <Input
                            label="Password (for new users)"
                            type="password"
                            placeholder="Set a password"
                            value={inviteData.password}
                            onChange={e => setInviteData({ ...inviteData, password: e.target.value })}
                        />
                    </div>
                    <p className="text-xs text-gray-500">
                        If the user already exists, they will be added to the workspace. If not, a new account will be created with this password.
                    </p>
                </div>
            </Dialog>
        </div>
    );
}
