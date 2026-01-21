from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.models import ResourceAccess, TenantMember, User

class AccessControlService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def has_access(
        self, 
        user: User, 
        resource_id: str, 
        resource_type: str, 
        required_level: str = "viewer",
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if a user has access to a resource at a required level.
        Access Levels: viewer, editor, admin
        """
        # 1. Superusers have access to everything
        if user.is_superuser:
            return True

        # Convert access levels to a hierarchy for comparison
        level_map = {"viewer": 0, "editor": 1, "admin": 2}
        req_val = level_map.get(required_level, 0)

        # 2. Check if user is the OWNER of the resource
        # Map resource types to their model classes
        from app.models.models import Agent, KnowledgeBase, DatabaseConnection, MCPConnection
        model_map = {
            "agent": Agent,
            "knowledge_base": KnowledgeBase,
            "database_connection": DatabaseConnection,
            "mcp_connection": MCPConnection
        }
        
        resource_model = model_map.get(resource_type)
        if resource_model:
            # Query the resource to check ownership
            resource_query = select(resource_model).where(resource_model.id == resource_id)
            resource_result = await self.db.execute(resource_query)
            resource = resource_result.scalars().first()
            
            if resource and hasattr(resource, 'owner_id'):
                if resource.owner_id == user.id:
                    # Owner has full access
                    return True

        # 3. Check if user is a member of the tenant and what their role is
        if tenant_id:
            member_query = select(TenantMember).where(
                and_(
                    TenantMember.tenant_id == tenant_id,
                    TenantMember.user_id == user.id
                )
            )
            member_result = await self.db.execute(member_query)
            member = member_result.scalars().first()
            
            if member:
                # Owners and Admins of a tenant have access to all resources in that tenant
                # BUT only if the resource belongs to that tenant
                if member.role in ["owner", "admin"]:
                    # Verify the resource is in this tenant
                    if resource and hasattr(resource, 'tenant_id') and resource.tenant_id == tenant_id:
                        return True
                
                # Check Custom Roles
                elif resource and hasattr(resource, 'tenant_id') and resource.tenant_id == tenant_id:
                    # Skip standard roles that are not UUIDs (or explicitly defined standard ones)
                    if member.role not in ["member", "viewer"]:
                         if await self._check_custom_role_permission(member.role, resource_type, required_level):
                            return True


        # 4. Check explicit resource access (sharing permissions)
        # This checks for direct user-level access OR role-based access for the tenant
        access_query = select(ResourceAccess).where(
            and_(
                ResourceAccess.resource_id == resource_id,
                ResourceAccess.resource_type == resource_type,
                or_(
                    ResourceAccess.user_id == user.id,
                    and_(
                        ResourceAccess.tenant_id == tenant_id,
                        ResourceAccess.tenant_role.is_not(None)
                    )
                )
            )
        )
        
        access_result = await self.db.execute(access_query)
        permissions = access_result.scalars().all()
        
        for perm in permissions:
            # If shared with specific user, check level
            if perm.user_id == user.id:
                if level_map.get(perm.access_level, 0) >= req_val:
                    return True
            
            # If shared with specific role, check if user has that role in the tenant
            if perm.tenant_role and tenant_id:
                # We already fetched 'member' above
                if member and member.role == perm.tenant_role:
                    if level_map.get(perm.access_level, 0) >= req_val:
                        return True
                        
        return False

    async def _check_custom_role_permission(self, role_id: str, resource_type: str, required_level: str) -> bool:
        """Helper to check permissions for a custom role."""
        # Fetch custom role definition
        from app.models.models import OrganizationRole
        role_query = select(OrganizationRole).where(OrganizationRole.id == role_id)
        role_result = await self.db.execute(role_query)
        role_obj = role_result.scalars().first()
        
        if not role_obj or not role_obj.permissions:
            return False

        # Map resource_type to permission key (plural)
        perm_key_map = {
            "agent": "agents",
            "knowledge_base": "knowledge_bases",
            "database_connection": "database_connections",
            "mcp_connection": "mcp_connections",
            "user": "users"
        }
        perm_key = perm_key_map.get(resource_type, resource_type + "s")
        
        # Map required_level to action key calling convention
        action_map = {
            "viewer": "view",
            "editor": "edit",
            "admin": "delete"
        }
        required_action = action_map.get(required_level, "view")
        
        # Check if permission is granted
        resource_perms = role_obj.permissions.get(perm_key, {})
        if resource_perms.get(required_action) is True:
            return True
        
        # Hierarchy Check
        if required_level == "viewer":
            if resource_perms.get("edit") is True or resource_perms.get("delete") is True:
                return True
        if required_level == "editor":
            if resource_perms.get("delete") is True:
                return True
                
        return False

    async def share_resource(
        self, 
        resource_id: str, 
        resource_type: str, 
        tenant_id: str,
        user_id: Optional[str] = None, 
        tenant_role: Optional[str] = None,
        access_level: str = "viewer"
    ) -> ResourceAccess:
        """Share a resource with a user or a tenant role."""
        new_access = ResourceAccess(
            resource_id=resource_id,
            resource_type=resource_type,
            tenant_id=tenant_id,
            user_id=user_id,
            tenant_role=tenant_role,
            access_level=access_level
        )
        self.db.add(new_access)
        await self.db.commit()
        await self.db.refresh(new_access)
        return new_access

    async def revoke_access(self, access_id: str):
        """Revoke a specific access permission."""
        query = select(ResourceAccess).where(ResourceAccess.id == access_id)
        result = await self.db.execute(query)
        access = result.scalars().first()
        if access:
            await self.db.delete(access)
            await self.db.commit()
            return True
        return False
