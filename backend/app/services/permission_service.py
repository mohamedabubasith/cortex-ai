
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import models
from app.services.auth_service import AuthService

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_effective_permissions(self, user_id: str, tenant_id: str) -> List[str]:
        """
        Calculate effective permissions for a user in a tenant.
        Source 1: Direct Tenant Role
        Source 2: Roles inherited via Groups (TODO)
        """
        permissions = set()

        # 1. Direct Membership Role
        stmt = select(models.TenantMember).where(
            models.TenantMember.user_id == user_id,
            models.TenantMember.tenant_id == tenant_id
        ).options(
            selectinload(models.TenantMember.tenant_role).selectinload(models.TenantRole.permissions)
        )
        result = await self.db.execute(stmt)
        member = result.scalars().first()

        if member and member.tenant_role:
             # Check for wildcard (Owner/Admin) optimization? or just list all?
             # For now, list all explicitly.
             for rp in member.tenant_role.permissions:
                 permissions.add(rp.permission_slug)

        # 2. Group Roles (Future Scope / TODO)
        # stmt = select(models.TenantGroupMember)...
        
        return list(permissions)

    async def can(self, user: models.User, action: str, tenant_id: str) -> bool:
        """
        Check if user can perform action in tenant.
        """
        # 1. Super Admin Bypass
        if user.is_superuser:
            return True

        # 2. Check Effective Permissions
        effective_perms = await self.get_user_effective_permissions(user.id, tenant_id)
        
        # 3. Check Match
        # Handle wildcards: if user has "kb.*", they can do "kb.create"
        for user_perm in effective_perms:
            if user_perm == action:
                return True
            if user_perm.endswith(".*"):
                prefix = user_perm[:-2]
                if action.startswith(prefix):
                    return True
                    
        return False
