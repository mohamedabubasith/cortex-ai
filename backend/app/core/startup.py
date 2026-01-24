"""
Startup Script - Auto-create admin user if none exists
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import User, Tenant, TenantMember
from app.services.auth_service import AuthService
from app.schemas.schemas import UserCreate
from app.core.config import settings


async def create_default_admin(db: AsyncSession):
    """
    Create default admin user if no superuser exists.
    Credentials can be set via environment variables:
    - DEFAULT_ADMIN_EMAIL (default: admin@cortex.ai)
    - DEFAULT_ADMIN_PASSWORD (default: admin123)
    - DEFAULT_ADMIN_NAME (default: System Administrator)
    """
    
    # Check if any superuser exists
    result = await db.execute(select(User).where(User.is_superuser == True))
    existing_superuser = result.scalars().first()
    
    if existing_superuser:
        print(f"✓ Superuser already exists: {existing_superuser.email}")
        return
    
    # Get credentials from environment or use defaults
    admin_email = settings.admin_email
    admin_password = settings.admin_password
    admin_name = getattr(settings, 'DEFAULT_ADMIN_NAME', 'System Administrator')
    
    print(f"\n{'='*60}")
    print("🔧 CREATING DEFAULT ADMIN USER")
    print(f"{'='*60}")
    print(f"Email: {admin_email}")
    print(f"Password: {'*' * len(admin_password)}") # Don't log actual password
    print(f"Name: {admin_name}")
    
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
        
        print(f"\n✅ ADMIN USER CREATED SUCCESSFULLY!")
        print(f"   User ID: {new_user.id}")
        print(f"   Tenant ID: {membership.tenant_id if membership else 'N/A'}")
        print(f"   Role: {membership.role if membership else 'N/A'}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Failed to create admin user: {e}")
        print(f"{'='*60}\n")
        # Don't raise - let the app start anyway


async def run_admin_creation():
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await create_default_admin(db)

if __name__ == "__main__":
    print("🚀 Starting admin user creation script...")
    asyncio.run(run_admin_creation())
