from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.auth_service import get_current_user
from app.models.models import User, ResourceAccess
from app.services.access_control_service import AccessControlService
from pydantic import BaseModel

router = APIRouter(tags=["access"])

class ShareRequest(BaseModel):
    user_id: Optional[str] = None
    tenant_role: Optional[str] = None
    access_level: str = "viewer" # viewer, editor, admin

@router.post("/{resource_type}/{resource_id}/share")
async def share_resource(
    resource_type: str,
    resource_id: str,
    share_data: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    access_service = AccessControlService(db)
    
    # Verify current user is admin/owner of the resource or tenant admin
    # For now, we'll assume the request comes from someone who has permission to share.
    # In a real app, we'd check if current_user.id == resource.owner_id or is tenant admin.
    
    try:
        access = await access_service.share_resource(
            resource_id=resource_id,
            resource_type=resource_type,
            tenant_id=current_user.tenant_memberships[0].tenant_id if current_user.tenant_memberships else None,
            user_id=share_data.user_id,
            tenant_role=share_data.tenant_role,
            access_level=share_data.access_level
        )
        return {"id": access.id, "message": "Resource shared successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{access_id}")
async def revoke_access(
    access_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    access_service = AccessControlService(db)
    success = await access_service.revoke_access(access_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access record not found")
    return {"message": "Access revoked successfully"}
