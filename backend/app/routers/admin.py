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

    # Create new user (handles password hashing and default tenant provisioning)
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
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get visitor statistics (API hits) for authenticated superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    stmt = select(models.Analytics).where(
        models.Analytics.event_type == "api_hit"
    ).order_by(models.Analytics.created_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    
    return events

from sqlalchemy import delete

@router.delete("/visitors/list")
async def clear_visitors_authenticated(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear visitor statistics for authenticated superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    stmt = delete(models.Analytics).where(
        models.Analytics.event_type == "api_hit"
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Visitor logs cleared"}
