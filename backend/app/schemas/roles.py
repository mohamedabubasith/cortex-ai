
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Permission(BaseModel):
    slug: str
    description: str
    category: str
    
    class Config:
        from_attributes = True

class RolePermission(BaseModel):
    permission_slug: str
    
    class Config:
        from_attributes = True

class TenantRoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class TenantRoleCreate(TenantRoleBase):
    permissions: List[str] # List of slugs

class TenantRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class TenantRole(TenantRoleBase):
    id: str
    tenant_id: str
    is_system_role: bool
    created_at: datetime
    permissions: List[RolePermission] = []
    
    class Config:
        from_attributes = True
