"""
Organization Service - User and role management for organizations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List, Optional
from app.models.models import User, Tenant, TenantMember, ResourceAccess
from app.schemas.schemas import UserCreate


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_organization_users(self, tenant_id: str, requesting_user: User) -> List[dict]:
        """
        List all users in the organization (tenant).
        Returns user info with their roles.
        """
        # Check if requesting user is a member
        check_query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == requesting_user.id
            )
        )
        check_result = await self.db.execute(check_query)
        if not check_result.scalars().first() and not requesting_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized to view this organization")
        
        # Get all members
        query = select(TenantMember).where(
            TenantMember.tenant_id == tenant_id
        ).options(
            selectinload(TenantMember.user)
        )
        result = await self.db.execute(query)
        members = result.scalars().all()
        
        users_data = []
        for member in members:
            users_data.append({
                "id": member.user.id,
                "email": member.user.email,
                "full_name": member.user.full_name,
                "is_active": member.user.is_active,
                "is_superuser": member.user.is_superuser,
                "role": member.role,
                "joined_at": member.created_at.isoformat() if member.created_at else None
            })
        
        return users_data
    
        return built_in_roles
    
    async def create_organization_role(self, role_data: dict, tenant_id: str, requesting_user: User) -> dict:
        """
        Create a new custom role.
        """
        # Check permissions (only owner/admin can create roles)
        # For simplicity, checking if user is admin or owner
        # Real impl would check 'roles:add' permission
        
        from app.models.models import OrganizationRole
        
        # Create role
        new_role = OrganizationRole(
            tenant_id=tenant_id,
            name=role_data['name'],
            description=role_data.get('description'),
            permissions=role_data.get('permissions', {}),
            type="custom"
        )
        self.db.add(new_role)
        await self.db.commit()
        await self.db.refresh(new_role)
        
        return {
            "id": new_role.id,
            "name": new_role.name,
            "description": new_role.description,
            "permissions": new_role.permissions,
            "type": "custom",
            "user_count": 0
        }

    async def get_organization_roles(self, tenant_id: str, requesting_user: User) -> List[dict]:
        """
        Get all roles in the organization (built-in + custom).
        """
        # 1. Get Built-in Roles (as before)
        # Check authorization
        check_query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == requesting_user.id
            )
        )
        check_result = await self.db.execute(check_query)
        if not check_result.scalars().first() and not requesting_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Count users per role
        query = select(
            TenantMember.role,
            func.count(TenantMember.user_id).label('user_count')
        ).where(
            TenantMember.tenant_id == tenant_id
        ).group_by(TenantMember.role)
        
        result = await self.db.execute(query)
        role_counts = {row[0]: row[1] for row in result.fetchall()}
        
        built_in_roles = [
            {
                "id": "owner",
                "name": "Owner",
                "description": "Full control over the organization and all resources",
                "type": "built-in",
                "user_count": role_counts.get("owner", 0),
                "permissions": {
                    "agents": {"view": True, "edit": True, "delete": True, "share": True},
                    "knowledge_bases": {"view": True, "edit": True, "delete": True, "share": True},
                    "mcps": {"view": True, "edit": True, "delete": True, "share": True},
                    "users": {"view": True, "add": True, "remove": True, "edit": True}
                }
            },
            {
                "id": "admin",
                "name": "Admin",
                "description": "Manage resources and view all organization data",
                "type": "built-in",
                "user_count": role_counts.get("admin", 0),
                "permissions": {
                    "agents": {"view": True, "edit": True, "delete": True, "share": True},
                    "knowledge_bases": {"view": True, "edit": True, "delete": True, "share": True},
                    "mcps": {"view": True, "edit": True, "delete": True, "share": True},
                    "users": {"view": True, "add": False, "remove": False, "edit": False}
                }
            },
            {
                "id": "member",
                "name": "Member",
                "description": "Standard access to organization resources",
                "type": "built-in",
                "user_count": role_counts.get("member", 0),
                "permissions": {
                    "agents": {"view": True, "edit": False, "delete": False, "share": False},
                    "knowledge_bases": {"view": True, "edit": False, "delete": False, "share": False},
                    "mcps": {"view": True, "edit": False, "delete": False, "share": False},
                    "users": {"view": True, "add": False, "remove": False, "edit": False}
                }
            },
            {
                "id": "viewer",
                "name": "Viewer",
                "description": "Read-only access to organization resources",
                "type": "built-in",
                "user_count": role_counts.get("viewer", 0),
                "permissions": {
                    "agents": {"view": True, "edit": False, "delete": False, "share": False},
                    "knowledge_bases": {"view": True, "edit": False, "delete": False, "share": False},
                    "mcps": {"view": True, "edit": False, "delete": False, "share": False},
                    "users": {"view": False, "add": False, "remove": False, "edit": False}
                }
            }
        ]

        # 2. Get Custom Roles from DB
        from app.models.models import OrganizationRole
        custom_roles_query = select(OrganizationRole).where(OrganizationRole.tenant_id == tenant_id)
        custom_roles_result = await self.db.execute(custom_roles_query)
        custom_roles = custom_roles_result.scalars().all()
        
        custom_roles_data = []
        for role in custom_roles:
            # Get user count for this custom role (if we store role string as custom role ID)
            # Currently TenantMember.role stores string. For custom roles, we'd assume it stores role ID?
            # Or role NAME?
            # For simplicity, let's assume TenantMember.role stores role ID for custom roles.
            # But the built-in logic uses "owner", "admin" strings. 
            count = role_counts.get(role.id, 0) # Use ID
            
            custom_roles_data.append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "type": "custom",
                "user_count": count,
                "permissions": role.permissions
            })
            
        return built_in_roles + custom_roles_data
    
        return built_in_roles + custom_roles_data
    
    async def update_organization_role(self, role_id: str, role_data: dict, tenant_id: str, requesting_user: User) -> dict:
        """
        Update a custom role.
        """
        # Check permissions
        from app.models.models import OrganizationRole
        
        # Determine if it's a valid role for this tenant
        role_query = select(OrganizationRole).where(
            and_(
                OrganizationRole.id == role_id,
                OrganizationRole.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(role_query)
        role = result.scalars().first()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
            
        # Update fields
        if 'name' in role_data:
            role.name = role_data['name']
        if 'description' in role_data:
            role.description = role_data['description']
        if 'permissions' in role_data:
            role.permissions = role_data['permissions']
            
        await self.db.commit()
        await self.db.refresh(role)
        
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
            "type": "custom"
        }

    async def delete_organization_role(self, role_id: str, tenant_id: str, requesting_user: User) -> dict:
        """
        Delete a custom role.
        """
        from app.models.models import OrganizationRole, TenantMember
        
        # Check if role exists
        role_query = select(OrganizationRole).where(
            and_(
                OrganizationRole.id == role_id,
                OrganizationRole.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(role_query)
        role = result.scalars().first()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
            
        # Check if any user is assigned this role
        usage_query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.role == role_id
            )
        )
        usage_result = await self.db.execute(usage_query)
        if usage_result.scalars().first():
             raise HTTPException(status_code=400, detail="Cannot delete role that is currently assigned to users. Reassign them first.")

        await self.db.delete(role)
        await self.db.commit()
        
        return {"message": "Role deleted successfully"}

    async def get_sharing_overview(self, tenant_id: str, requesting_user: User) -> dict:
        """
        Get overview of all shared resources in the organization.
        """
        # Check authorization
        check_query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == requesting_user.id
            )
        )
        check_result = await self.db.execute(check_query)
        member = check_result.scalars().first()
        
        if not member and not requesting_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get all shared resources in this tenant
        query = select(ResourceAccess).where(
            ResourceAccess.tenant_id == tenant_id
        ).options(
            selectinload(ResourceAccess.user)
        )
        result = await self.db.execute(query)
        shares = result.scalars().all()
        
        # Group by resource type
        sharing_data = {
            "agent": [],
            "knowledge_base": [],
            "database_connection": [],
            "mcp_connection": []
        }
        
        for share in shares:
            share_info = {
                "id": share.id,
                "resource_id": share.resource_id,
                "resource_type": share.resource_type,
                "access_level": share.access_level,
                "shared_with_user": share.user.email if share.user else None,
                "shared_with_role": share.tenant_role,
                "created_at": share.created_at.isoformat() if share.created_at else None
            }
            
            if share.resource_type in sharing_data:
                sharing_data[share.resource_type].append(share_info)
        
        return {
            "tenant_id": tenant_id,
            "total_shares": len(shares),
            "by_type": {
                "agents": len(sharing_data["agent"]),
                "knowledge_bases": len(sharing_data["knowledge_base"]),
                "database_connections": len(sharing_data["database_connection"]),
                "mcp_connections": len(sharing_data["mcp_connection"])
            },
            "shares": sharing_data
        }
