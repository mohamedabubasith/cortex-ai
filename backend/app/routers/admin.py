from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.schemas import schemas
from app.services.auth_service import AuthService
from app.models import models

router = APIRouter()

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

@router.post("/create", response_model=schemas.User)
async def create_admin_user(
    user_in: schemas.UserCreate,
    x_admin_key: str = Header(..., alias="X-ADMIN-KEY"),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create a new admin user.
    Requires X-ADMIN-KEY header.
    """
    if x_admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin Key"
        )
    
    # Check if user already exists
    existing_user = await auth_service.repo.get_by_email(user_in.email)
    if existing_user:
        if not existing_user.is_superuser:
            # Promote existing user
            existing_user.is_superuser = True
            await db.commit()
            await db.refresh(existing_user)
            return existing_user
        else:
            raise HTTPException(
                status_code=400,
                detail="Admin user with this email already exists."
            )

    # Create new user (handles password hashing and Cognee creation)
    user = await auth_service.create_user(user_in)
    
    # Promote to superuser
    user.is_superuser = True
    await db.commit()
    await db.refresh(user)
    
    return user

from sqlalchemy import select
from typing import List

@router.get("/visitors", response_model=List[schemas.AnalyticsEvent])
async def get_visitors(
    limit: int = 100,
    x_admin_key: str = Header(..., alias="X-ADMIN-KEY"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get visitor statistics (API hits).
    Requires X-ADMIN-KEY header.
    """
    if x_admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin Key"
        )
    
    stmt = select(models.Analytics).where(
        models.Analytics.event_type == "api_hit"
    ).order_by(models.Analytics.created_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    return events

from app.services.auth_service import get_current_active_user

@router.get("/visitors/list", response_model=List[schemas.AnalyticsEvent])
async def get_visitors_authenticated(
    limit: int = 100,
    x_tenant_id: str = Header(None, alias="X-Tenant-ID"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get visitor statistics (API hits) for authenticated superusers.
    """
    query = select(models.Analytics).where(
        models.Analytics.event_type == "api_hit"
    )
    
    # Filter for non-superusers
    if not current_user.is_superuser:
        tenant_membership = None
        if x_tenant_id and current_user.tenant_memberships:
             tenant_membership = next((m for m in current_user.tenant_memberships if str(m.tenant_id) == str(x_tenant_id)), None)
        
        if not tenant_membership and current_user.tenant_memberships:
            tenant_membership = current_user.tenant_memberships[0]
            
        if not tenant_membership:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenant membership found")

        # Check tenant role
        if tenant_membership.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized for this tenant"
            )
        
        query = query.where(models.Analytics.tenant_id == tenant_membership.tenant_id)
    
    stmt = query.order_by(models.Analytics.created_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    
    return events


from sqlalchemy import delete

@router.delete("/visitors/list")
async def clear_visitors_authenticated(
    x_tenant_id: str = Header(None, alias="X-Tenant-ID"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear visitor statistics for authenticated superusers.
    """
    stmt = delete(models.Analytics).where(
        models.Analytics.event_type == "api_hit"
    )
    
    if not current_user.is_superuser:
        tenant_membership = None
        if x_tenant_id and current_user.tenant_memberships:
             tenant_membership = next((m for m in current_user.tenant_memberships if str(m.tenant_id) == str(x_tenant_id)), None)
        
        if not tenant_membership and current_user.tenant_memberships:
            tenant_membership = current_user.tenant_memberships[0]
            
        if not tenant_membership:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenant membership found")

        # Check tenant role
        if tenant_membership.role not in ["owner", "admin"]:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized for this tenant"
            )
        
        stmt = stmt.where(models.Analytics.tenant_id == tenant_membership.tenant_id)
        
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Visitor logs cleared"}

@router.get("/users", response_model=List[schemas.User])
async def list_all_users(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users in the system.
    Available to any authenticated user for sharing/collaboration purposes.
    """
    from sqlalchemy.orm import selectinload
    
    stmt = select(models.User).options(
        selectinload(models.User.tenant_memberships).selectinload(models.TenantMember.tenant)
    ).order_by(models.User.email)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return users
