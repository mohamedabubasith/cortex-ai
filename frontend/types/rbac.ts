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

export interface Tenant {
    id: string;
    name: string;
    slug: string;
    created_at: string;
}

export interface TenantMember {
    tenant_id: string;
    user_id: string;
    role?: string;
    role_id?: string;
    created_at: string;
    tenant: Tenant;
    tenant_role?: TenantRole;
}

export interface User {
    id: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    is_superuser: boolean;
    tenant_memberships: TenantMember[];
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
