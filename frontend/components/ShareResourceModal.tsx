"use client";

import { useState, useEffect } from "react";
import { X, Users, UserPlus, Trash2, Shield, Eye, Edit, Settings } from "lucide-react";
import api from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

interface ShareResourceModalProps {
    isOpen: boolean;
    onClose: () => void;
    resourceId: string;
    resourceType: "agent" | "knowledge_base" | "database_connection" | "mcp_connection" | "llm_config";
    resourceName: string;
    tenantId?: string;
}

interface Role {
    id: string;
    name: string;
    type: string;
}

interface User {
    id: string;
    email: string;
    full_name: string;
}

const ShareResourceModal: React.FC<ShareResourceModalProps> = ({
    isOpen,
    onClose,
    resourceId,
    resourceType,
    resourceName,
    tenantId,
}) => {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [shareType, setShareType] = useState<"user" | "role">("user");
    const [selectedUser, setSelectedUser] = useState<string>("");
    const [selectedRole, setSelectedRole] = useState<string>("member");
    const [accessLevel, setAccessLevel] = useState<string>("viewer");
    const [loading, setLoading] = useState(false);
    const [users, setUsers] = useState<User[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);
    const [searchEmail, setSearchEmail] = useState("");

    useEffect(() => {
        if (isOpen) {
            if (shareType === "user" && users.length === 0) {
                fetchUsers();
            } else if (shareType === "role" && roles.length === 0 && tenantId) {
                fetchRoles();
            }
        }
    }, [isOpen, shareType, tenantId]);

    const fetchRoles = async () => {
        try {
            const res = await api.get(`/organization/roles?tenant_id=${tenantId}`);
            setRoles(res.data);
        } catch (error) {
            console.error("Failed to fetch roles", error);
        }
    };

    const fetchUsers = async () => {
        try {
            // This would need a "list all users in tenant" endpoint
            // For now, we'll use a simple search
            const response = await api.get("/admin/users");
            setUsers(response.data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        }
    };

    const handleShare = async () => {
        setLoading(true);
        try {
            const payload = shareType === "user"
                ? { user_id: selectedUser, access_level: accessLevel }
                : { tenant_role: selectedRole, access_level: accessLevel };

            await api.post(`/access/${resourceType}/${resourceId}/share`, payload);
            alert(`${resourceName} shared successfully!`);
            onClose();
        } catch (error: any) {
            alert(`Failed to share: ${error.response?.data?.detail || error.message}`);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
            <div className={cn("relative w-full max-w-2xl mx-4 rounded-2xl shadow-2xl max-h-[90vh] overflow-hidden", isDark ? "bg-nvidia-dark border border-white/10" : "bg-white")}>

                {/* Header */}
                <div className={cn("p-6 border-b", isDark ? "border-white/10" : "border-gray-200")}>
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className={cn("text-2xl font-bold flex items-center gap-2", isDark ? "text-white" : "text-gray-900")}>
                                <Users className="w-6 h-6 text-nvidia-green" />
                                Share Resource
                            </h2>
                            <p className={cn("text-sm mt-1", isDark ? "text-gray-400" : "text-gray-600")}>
                                Share "{resourceName}" with users or roles
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
                <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-200px)]">

                    {/* Share Type Toggle */}
                    <div>
                        <label className={cn("block text-sm font-medium mb-3", isDark ? "text-gray-300" : "text-gray-700")}>
                            Share with
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                onClick={() => setShareType("user")}
                                className={cn("p-4 rounded-lg border-2 transition-all", shareType === "user"
                                    ? "border-nvidia-green bg-nvidia-green/10"
                                    : isDark ? "border-white/10 hover:border-white/20" : "border-gray-200 hover:border-gray-300"
                                )}
                            >
                                <UserPlus className={cn("w-5 h-5 mx-auto mb-2", shareType === "user" ? "text-nvidia-green" : isDark ? "text-gray-400" : "text-gray-600")} />
                                <div className={cn("text-sm font-medium", shareType === "user" ? "text-nvidia-green" : isDark ? "text-white" : "text-gray-900")}>
                                    Specific User
                                </div>
                            </button>
                            <button
                                onClick={() => setShareType("role")}
                                className={cn("p-4 rounded-lg border-2 transition-all", shareType === "role"
                                    ? "border-nvidia-green bg-nvidia-green/10"
                                    : isDark ? "border-white/10 hover:border-white/20" : "border-gray-200 hover:border-gray-300"
                                )}
                            >
                                <Shield className={cn("w-5 h-5 mx-auto mb-2", shareType === "role" ? "text-nvidia-green" : isDark ? "text-gray-400" : "text-gray-600")} />
                                <div className={cn("text-sm font-medium", shareType === "role" ? "text-nvidia-green" : isDark ? "text-white" : "text-gray-900")}>
                                    Tenant Role
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* User Selection */}
                    {shareType === "user" && (
                        <div>
                            <label className={cn("block text-sm font-medium mb-2", isDark ? "text-gray-300" : "text-gray-700")}>
                                Select User
                            </label>
                            <select
                                value={selectedUser}
                                onChange={(e) => setSelectedUser(e.target.value)}
                                className={cn("w-full px-4 py-3 rounded-lg border", isDark
                                    ? "bg-white/5 border-white/10 text-white focus:border-nvidia-green"
                                    : "bg-white border-gray-300 text-gray-900 focus:border-nvidia-green"
                                )}
                            >
                                <option value="">Choose a user...</option>
                                {users.map((user) => (
                                    <option key={user.id} value={user.id}>
                                        {user.email} {user.full_name && `(${user.full_name})`}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {/* Role Selection */}
                    {shareType === "role" && (
                        <div>
                            <label className={cn("block text-sm font-medium mb-2", isDark ? "text-gray-300" : "text-gray-700")}>
                                Select Role
                            </label>
                            <select
                                value={selectedRole}
                                onChange={(e) => setSelectedRole(e.target.value)}
                                className={cn("w-full px-4 py-3 rounded-lg border", isDark
                                    ? "bg-white/5 border-white/10 text-white focus:border-nvidia-green"
                                    : "bg-white border-gray-300 text-gray-900 focus:border-nvidia-green"
                                )}
                                disabled={!tenantId} // Disable if no tenantId provided
                            >
                                <option value="">Select a role...</option>
                                {roles.length > 0 ? (
                                    roles.map(role => (
                                        <option key={role.id} value={role.name.toLowerCase()}>{role.name}</option>
                                    ))
                                ) : (
                                    // Fallback if fetch failed or empty
                                    <>
                                        <option value="owner">Owner</option>
                                        <option value="admin">Admin</option>
                                        <option value="member">Member</option>
                                        <option value="viewer">Viewer</option>
                                    </>
                                )}
                            </select>
                            <p className={cn("text-xs mt-2", isDark ? "text-gray-400" : "text-gray-500")}>
                                {tenantId
                                    ? "All users with this role in your tenant will get access"
                                    : "Tenant context missing. Unable to fetch custom roles."}
                            </p>
                        </div>
                    )}

                    {/* Access Level */}
                    <div>
                        <label className={cn("block text-sm font-medium mb-3", isDark ? "text-gray-300" : "text-gray-700")}>
                            Permission Level
                        </label>
                        <div className="grid grid-cols-3 gap-3">
                            <button
                                onClick={() => setAccessLevel("viewer")}
                                className={cn("p-4 rounded-lg border-2 transition-all", accessLevel === "viewer"
                                    ? "border-nvidia-green bg-nvidia-green/10"
                                    : isDark ? "border-white/10 hover:border-white/20" : "border-gray-200 hover:border-gray-300"
                                )}
                            >
                                <Eye className={cn("w-5 h-5 mx-auto mb-2", accessLevel === "viewer" ? "text-nvidia-green" : isDark ? "text-gray-400" : "text-gray-600")} />
                                <div className={cn("text-sm font-medium", accessLevel === "viewer" ? "text-nvidia-green" : isDark ? "text-white" : "text-gray-900")}>
                                    Viewer
                                </div>
                                <div className={cn("text-xs mt-1", isDark ? "text-gray-400" : "text-gray-500")}>Read only</div>
                            </button>
                            <button
                                onClick={() => setAccessLevel("editor")}
                                className={cn("p-4 rounded-lg border-2 transition-all", accessLevel === "editor"
                                    ? "border-nvidia-green bg-nvidia-green/10"
                                    : isDark ? "border-white/10 hover:border-white/20" : "border-gray-200 hover:border-gray-300"
                                )}
                            >
                                <Edit className={cn("w-5 h-5 mx-auto mb-2", accessLevel === "editor" ? "text-nvidia-green" : isDark ? "text-gray-400" : "text-gray-600")} />
                                <div className={cn("text-sm font-medium", accessLevel === "editor" ? "text-nvidia-green" : isDark ? "text-white" : "text-gray-900")}>
                                    Editor
                                </div>
                                <div className={cn("text-xs mt-1", isDark ? "text-gray-400" : "text-gray-500")}>Can edit</div>
                            </button>
                            <button
                                onClick={() => setAccessLevel("admin")}
                                className={cn("p-4 rounded-lg border-2 transition-all", accessLevel === "admin"
                                    ? "border-nvidia-green bg-nvidia-green/10"
                                    : isDark ? "border-white/10 hover:border-white/20" : "border-gray-200 hover:border-gray-300"
                                )}
                            >
                                <Settings className={cn("w-5 h-5 mx-auto mb-2", accessLevel === "admin" ? "text-nvidia-green" : isDark ? "text-gray-400" : "text-gray-600")} />
                                <div className={cn("text-sm font-medium", accessLevel === "admin" ? "text-nvidia-green" : isDark ? "text-white" : "text-gray-900")}>
                                    Admin
                                </div>
                                <div className={cn("text-xs mt-1", isDark ? "text-gray-400" : "text-gray-500")}>Full control</div>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className={cn("p-6 border-t flex justify-end gap-3", isDark ? "border-white/10" : "border-gray-200")}>
                    <button
                        onClick={onClose}
                        className={cn("px-6 py-2.5 rounded-lg font-medium transition-colors", isDark
                            ? "bg-white/5 hover:bg-white/10 text-white"
                            : "bg-gray-100 hover:bg-gray-200 text-gray-900"
                        )}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleShare}
                        disabled={loading || (shareType === "user" && !selectedUser)}
                        className="px-6 py-2.5 bg-nvidia-green hover:bg-[#8CD600] text-black font-bold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? "Sharing..." : "Share"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ShareResourceModal;
