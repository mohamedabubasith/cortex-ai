"""
Startup Script - Auto-create admin user if none exists
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import User, TenantMember
from app.services.auth_service import AuthService
from app.schemas.schemas import UserCreate
from app.core.config import settings

logger = logging.getLogger(__name__)


async def create_default_admin(db: AsyncSession, override_email: str = None, override_password: str = None):
    """
    Create default admin user if no superuser exists.
    """
    
    # Check if any superuser exists
    result = await db.execute(select(User).where(User.is_superuser == True))
    existing_superuser = result.scalars().first()
    
    if existing_superuser:
        logger.info("Superuser already exists: %s", existing_superuser.email)
        return

    # Get credentials from environment or use defaults
    admin_email = override_email or settings.admin_email
    admin_password = (override_password or settings.admin_password)[:72]  # bcrypt max is 72 bytes
    admin_name = getattr(settings, "DEFAULT_ADMIN_NAME", "System Administrator")

    logger.info(
        "Creating default admin user (email=%s, name=%s)",
        admin_email,
        admin_name,
    )
    
    try:
        auth_service = AuthService(db)
        
        # Create admin user
        user_in = UserCreate(
            email=admin_email,
            password=admin_password,
            full_name=admin_name,
            is_active=True
        )
        
        # Create user (this also creates personal tenant)
        new_user = await auth_service.create_user(user_in)
        
        # Make superuser
        new_user.is_superuser = True
        await db.commit()
        await db.refresh(new_user)
        
        # Get tenant info
        tenant_result = await db.execute(
            select(TenantMember).where(TenantMember.user_id == new_user.id)
        )
        membership = tenant_result.scalars().first()
        
        logger.info(
            "Default admin created: user_id=%s tenant_id=%s role=%s",
            new_user.id,
            membership.tenant_id if membership else None,
            membership.role if membership else None,
        )

    except Exception as e:
        logger.exception("Failed to create default admin user: %s", e)
        # Don't raise - let the app start anyway


async def run_admin_creation():
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await create_default_admin(db)

if __name__ == "__main__":
    from pathlib import Path

    from dotenv import load_dotenv

    _repo_root = Path(__file__).resolve().parent.parent.parent.parent
    load_dotenv(_repo_root / ".env")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_admin_creation())
