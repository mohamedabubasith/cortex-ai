import { useState, useEffect } from "react";
import Dialog from "./ui/Dialog";
import { User, Trash2, Shield, Loader2, Plus } from "lucide-react";
import api from "@/lib/api";
import { useToast } from "./ui/Toast";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

interface ShareDialogProps {
    isOpen: boolean;
    onClose: () => void;
    resourceId: string;
    resourceType: 'kb' | 'db_connection' | 'agent';
    resourceName: string;
}

interface TenantMember {
    user_id: string;
    role: string;
    user: {
        id: string;
        email: string;
        full_name?: string;
    };
}

interface HelperShare {
    id: string;
    grantee_id: string;
    permission: string;
    grantee_type: string;
}

export default function ShareDialog({ isOpen, onClose, resourceId, resourceType, resourceName }: ShareDialogProps) {
    const { toast } = useToast();
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [loading, setLoading] = useState(false);
    const [shares, setShares] = useState<HelperShare[]>([]);
    const [users, setUsers] = useState<TenantMember[]>([]);

    const [selectedUser, setSelectedUser] = useState("");
    const [permission, setPermission] = useState("read");
    const [sharing, setSharing] = useState(false);

    useEffect(() => {
        if (isOpen && resourceId) {
            fetchData();
        }
    }, [isOpen, resourceId]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [usersRes, sharesRes] = await Promise.all([
                api.get("/tenant/users"),
                api.get(`/share/resource/${resourceId}`)
            ]);
            setUsers(usersRes.data);
            setShares(sharesRes.data);
        } catch (error) {
            console.error("Failed to fetch share data", error);
            // toast("Failed to load sharing info", "error"); 
        } finally {
            setLoading(false);
        }
    };

    const handleShare = async () => {
        if (!selectedUser) return;
        setSharing(true);
        try {
            const payload = {
                resource_id: resourceId,
                resource_type: resourceType,
                grantee_id: selectedUser,
                grantee_type: "user",
                permission: permission
            };

            const res = await api.post("/share/", payload);
            toast("Resource shared successfully", "success");

            // Refresh
            const sharesRes = await api.get(`/share/resource/${resourceId}`);
            setShares(sharesRes.data);
            setSelectedUser(""); // Reset
        } catch (error: any) {
            console.error("Share failed", error);
            const msg = error.response?.data?.detail || "Sharing failed";
            toast(msg, "error");
        } finally {
            setSharing(false);
        }
    };

    const handleRevoke = async (shareId: string) => {
        if (!confirm("Are you sure you want to revoke access?")) return;
        try {
            await api.delete(`/share/${shareId}`);
            toast("Access revoked", "success");
            setShares(shares.filter(s => s.id !== shareId));
        } catch (error) {
            console.error("Revoke failed", error);
            toast("Failed to revoke access", "error");
        }
    };

    // Filter out users who already have access
    // Note: shares use grantee_id. 
    // We should map shares to users to show emails in the list.

    const getEmailForShare = (share: HelperShare) => {
        const member = users.find(u => u.user.id === share.grantee_id);
        return member ? member.user.email : share.grantee_id;
    };

    // Filter available users: Exclude checking for existing shares because 
    // maybe we want to change permission (update)? 
    // The backend supports upsert on POST. So we can just list all.
    // Or users might want to see who doesn't have it.

    return (
        <Dialog
            isOpen={isOpen}
            onClose={onClose}
            title={`Share "${resourceName}"`}
            buttons={[
                { label: "Close", onClick: onClose, variant: "outline" }
            ]}
        >
            <div className="space-y-6">

                {/* Add Share Form */}
                <div className={cn("p-4 rounded-xl border space-y-4", isDark ? "bg-white/5 border-white/10" : "bg-gray-50 border-gray-200")}>
                    <h4 className={cn("text-sm font-bold uppercase tracking-wider", isDark ? "text-gray-400" : "text-gray-600")}>Add People</h4>
                    <div className="flex gap-2">
                        <select
                            className={cn("flex-1 p-2 rounded-lg border focus:ring-2 focus:ring-nvidia-green outline-none",
                                isDark ? "bg-black/50 border-white/10 text-white" : "bg-white border-gray-300 text-gray-900")}
                            value={selectedUser}
                            onChange={(e) => setSelectedUser(e.target.value)}
                        >
                            <option value="">Select a user...</option>
                            {users.map((member) => (
                                <option key={member.user.id} value={member.user.id}>
                                    {member.user.email} ({member.role})
                                </option>
                            ))}
                        </select>
                        <select
                            className={cn("w-24 p-2 rounded-lg border focus:ring-2 focus:ring-nvidia-green outline-none",
                                isDark ? "bg-black/50 border-white/10 text-white" : "bg-white border-gray-300 text-gray-900")}
                            value={permission}
                            onChange={(e) => setPermission(e.target.value)}
                        >
                            <option value="read">Read</option>
                            <option value="write">Write</option>
                            <option value="admin">Admin</option>
                        </select>
                        <button
                            onClick={handleShare}
                            disabled={!selectedUser || sharing}
                            className="bg-nvidia-green text-black px-3 py-2 rounded-lg hover:bg-[#8CD600] disabled:opacity-50 font-bold transition-colors"
                        >
                            {sharing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                        </button>
                    </div>
                </div>

                {/* Existing Shares List */}
                <div>
                    <h4 className={cn("text-sm font-bold uppercase tracking-wider mb-3", isDark ? "text-gray-400" : "text-gray-600")}>Who has access</h4>
                    {loading ? (
                        <div className="flex justify-center py-4"><Loader2 className="w-6 h-6 text-nvidia-green animate-spin" /></div>
                    ) : shares.length === 0 ? (
                        <p className="text-sm text-gray-500 italic">No custom shares. Only Tenant Admins can access.</p>
                    ) : (
                        <div className="space-y-2">
                            {shares.map(share => (
                                <div key={share.id} className={cn("flex justify-between items-center p-3 rounded-lg border", isDark ? "bg-white/5 border-white/5" : "bg-white border-gray-100")}>
                                    <div className="flex items-center gap-3">
                                        <div className="bg-gradient-to-br from-purple-500 to-blue-500 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs">
                                            {getEmailForShare(share)[0].toUpperCase()}
                                        </div>
                                        <div>
                                            <p className={cn("text-sm font-medium", isDark ? "text-white" : "text-gray-900")}>
                                                {getEmailForShare(share)}
                                            </p>
                                            <p className="text-xs text-gray-400 capitalize">{share.permission}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleRevoke(share.id)}
                                        className="text-gray-500 hover:text-red-500 p-2 hover:bg-red-500/10 rounded-lg"
                                        title="Revoke Access"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </Dialog>
    );
}
