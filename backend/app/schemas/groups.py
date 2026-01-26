from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.schemas import UserSimple

class TenantGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class TenantGroupCreate(TenantGroupBase):
    pass

class TenantGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TenantGroup(TenantGroupBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class TenantGroupMemberBase(BaseModel):
    user_id: str

class TenantGroupMemberCreate(TenantGroupMemberBase):
    pass

class TenantGroupMember(TenantGroupMemberBase):
    group_id: str
    created_at: datetime
    user: Optional["UserSimple"] = None
    
    class Config:
        from_attributes = True

class GroupDetail(TenantGroup):
    members: List[TenantGroupMember] = []
