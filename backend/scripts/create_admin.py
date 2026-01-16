"""
Admin User Setup Script

This script creates an initial admin/super user for new Cortex AI installations.
Run this ONCE when setting up a new instance.

Usage:
    python -m scripts.create_admin
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.models import User, Tenant, TenantMember
from app.services.auth_service import AuthService
from app.schemas.schemas import UserCreate
import uuid


async def create_admin_user():
    """Create a super admin user with their own tenant"""
    
    print("=" * 60)
    print("CORTEX AI - ADMIN USER SETUP")
    print("=" * 60)
    
    # Get admin details
    print("\nEnter admin user details:")
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    full_name = input("Full Name (optional): ").strip() or "System Administrator"
    
    if not email or not password:
        print("❌ Email and password are required!")
        return
    
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Check if user already exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"\n❌ User with email '{email}' already exists!")
            print(f"   User ID: {existing_user.id}")
            print(f"   Is Superuser: {existing_user.is_superuser}")
            
            # Offer to make them superuser
            if not existing_user.is_superuser:
                make_super = input("\nMake this user a superuser? (yes/no): ").lower()
                if make_super == 'yes':
                    existing_user.is_superuser = True
                    await db.commit()
                    print("✅ User upgraded to superuser!")
            return
        
        # Create the user
        auth_service = AuthService(db)
        user_in = UserCreate(
            email=email,
            password=password,
            full_name=full_name,
            is_active=True
        )
        
        try:
            # Create user (this also creates a personal tenant)
            new_user = await auth_service.create_user(user_in)
            
            # Make them a superuser
            new_user.is_superuser = True
            await db.commit()
            await db.refresh(new_user)
            
            # Get their tenant
            tenant_result = await db.execute(
                select(TenantMember).where(TenantMember.user_id == new_user.id)
            )
            membership = tenant_result.scalars().first()
            
            print("\n" + "=" * 60)
            print("✅ ADMIN USER CREATED SUCCESSFULLY!")
            print("=" * 60)
            print(f"\nUser Details:")
            print(f"  Email: {new_user.email}")
            print(f"  Name: {new_user.full_name}")
            print(f"  User ID: {new_user.id}")
            print(f"  Is Superuser: {new_user.is_superuser}")
            print(f"  Is Active: {new_user.is_active}")
            
            if membership:
                print(f"\nTenant Details:")
                print(f"  Tenant ID: {membership.tenant_id}")
                print(f"  Role: {membership.role}")
            
            print("\n" + "=" * 60)
            print("You can now login with these credentials!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error creating admin user: {e}")
            raise


async def list_users():
    """List all users in the system"""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(User).options(selectinload(User.tenant_memberships))
        )
        users = result.scalars().all()
        
        if not users:
            print("\nNo users found in the system.")
            return
        
        print("\n" + "=" * 80)
        print("EXISTING USERS")
        print("=" * 80)
        print(f"{'Email':<40} {'Name':<25} {'Superuser':<12} {'Active'}")
        print("-" * 80)
        
        for user in users:
            print(f"{user.email:<40} {user.full_name or 'N/A':<25} {'Yes' if user.is_superuser else 'No':<12} {'Yes' if user.is_active else 'No'}")
        
        print("=" * 80)


async def main():
    """Main menu"""
    
    print("\n" + "=" * 60)
    print("CORTEX AI - USER MANAGEMENT")
    print("=" * 60)
    print("\n1. Create Admin User")
    print("2. List All Users")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        await create_admin_user()
    elif choice == "2":
        await list_users()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid option!")


if __name__ == "__main__":
    asyncio.run(main())
