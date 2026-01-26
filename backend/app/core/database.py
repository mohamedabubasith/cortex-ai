from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_async_engine(settings.constructed_database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

from sqlalchemy import text

async def set_rls_context(session: AsyncSession, user):
    """
    Sets the RLS context variables for the current session based on the authenticated user.
    """
    if not user:
        return

    # Quote values potentially? UUIDs are safe. Booleans are strings 'true'/'false'.
    tenant_id = getattr(user, "tenant_id", None)
    
    params = {
        "user_id": str(user.id),
        "tenant_id": str(tenant_id) if tenant_id else "",
        "is_super": "true" if user.is_superuser else "false",
        # Assuming is_tenant_admin is property or field
        "is_tenant_admin": "true" if getattr(user, "is_tenant_admin", False) else "false"
    }
    
    # We use explicit SET calls or set_config. set_config is cleaner for param binding.
    # set_config(setting_name, new_value, is_local)
    stmt = text("""
        SELECT 
            set_config('app.current_user_id', :user_id, false),
            set_config('app.current_tenant_id', :tenant_id, false),
            set_config('app.is_super_admin', :is_super, false),
            set_config('app.is_tenant_admin', :is_tenant_admin, false)
    """)
    await session.execute(stmt, params)
