"""
Database Purge Script - Python version
Drops all tables and recreates them using SQLAlchemy
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.models import Base


async def purge_database():
    """Drop all tables and recreate them"""
    
    print("=" * 60)
    print("DATABASE PURGE - WARNING")
    print("=" * 60)
    print("This will DELETE ALL DATA in the database!")
    print("")
    confirm = input("Are you sure? Type 'yes' to continue: ")
    
    if confirm.lower() != 'yes':
        print("Aborted.")
        return
    
    print("\nPurging database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    try:
        # Drop all tables
        print("Dropping all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("✓ All tables dropped")
        
        # Recreate all tables
        print("Creating all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created")
        
        print("")
        print("=" * 60)
        print("✅ DATABASE PURGED SUCCESSFULLY")
        print("=" * 60)
        print("Status: Fresh and empty")
        print("")
        print("Next steps:")
        print("1. Create admin user:")
        print("   .venv/bin/python -m scripts.create_admin")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(purge_database())
