
export interface Permission {
    slug: string;
    description: string;
    category: string;
}

export interface RolePermission {
    permission_slug: string;
}

export interface TenantRole {
    id: string;
    tenant_id: string;
    name: string;
    description?: string;
    is_system_role: boolean;
    created_at: string;
    permissions: RolePermission[];
}

export interface TenantRoleCreate {
    name: string;
    description?: string;
    permissions: string[];
}

export interface TenantRoleUpdate {
    name?: string;
    description?: string;
    permissions?: string[];
}
