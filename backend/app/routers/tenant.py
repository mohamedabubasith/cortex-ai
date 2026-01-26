from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.auth_service import get_current_active_user, get_current_tenant, AuthService

router = APIRouter()

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

async def check_admin_privileges(
    user: models.User,
    tenant: models.Tenant, 
    db: AsyncSession
) -> models.TenantMember:
    """Ensure user is owner or admin of the tenant"""
    # Load tenant_role relationship for RBAC checks
    stmt = select(models.TenantMember).where(
        models.TenantMember.user_id == user.id,
        models.TenantMember.tenant_id == tenant.id
    ).options(selectinload(models.TenantMember.tenant_role))
    
    result = await db.execute(stmt)
    membership = result.scalars().first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this tenant")
        
    # Check both legacy role string and modern TenantRole name (case-insensitive)
    role_name = membership.role or ""
    rbac_role_name = membership.tenant_role.name if membership.tenant_role else ""
    
    is_admin = (
        role_name.lower() in ["owner", "admin"] or 
        rbac_role_name.lower() in ["owner", "admin"]
    )
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Insufficient privileges. Admin access required.")
        
    return membership

@router.get("/users", response_model=List[schemas.TenantMember])
async def get_tenant_users(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    """List all users in the current tenant"""
    # Enforce Admin Access?
    # Usually regular members should see who is in the team, but maybe only admins can manage them.
    # User requested "Super admin and Admin can add... and remove".
    # Listing might be allowed for all? Let's check privileges just for safety or leave open?
    # Let's enforce Admin for now since it's "Administration" tab.
    await check_admin_privileges(current_user, current_tenant, db)
    
    stmt = select(models.TenantMember).where(
        models.TenantMember.tenant_id == current_tenant.id
    ).options(
        selectinload(models.TenantMember.user), 
        selectinload(models.TenantMember.tenant_role).selectinload(models.TenantRole.permissions)
    )
    
    result = await db.execute(stmt)
    members = result.scalars().all()
    
    return members

@router.post("/users", response_model=schemas.TenantMember)
async def invite_user(
    invite_in: schemas.TenantUserInvite,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Add user to tenant. Create if not exists."""
    print(f"DEBUG: invite_user called with {invite_in}")
    
    # 1. Check Privileges
    await check_admin_privileges(current_user, current_tenant, db)
    
    try:
        # 2. Check if user exists
        existing_user = await auth_service.repo.get_by_email(invite_in.email)
        print(f"DEBUG: existing_user: {existing_user}")
        
        target_user = existing_user
        
        if not existing_user:
            print("DEBUG: User does not exist, creating...")
            # Create User
            if not invite_in.password:
                print("DEBUG: Password missing for new user")
                raise HTTPException(status_code=400, detail="Password required for new user creation.")
                
            user_create = schemas.UserCreate(
                email=invite_in.email,
                password=invite_in.password,
                full_name=invite_in.full_name or invite_in.email.split("@")[0],
                is_active=True
            )
            # Don't create a personal tenant for invited users, they belong to this one
            target_user = await auth_service.create_user(user_create, auto_create_tenant=True)
            print(f"DEBUG: Created user {target_user.id}")
        
        # 3. Check if already member
        stmt = select(models.TenantMember).where(
            models.TenantMember.user_id == target_user.id,
            models.TenantMember.tenant_id == current_tenant.id
        )
        result = await db.execute(stmt)
        existing_membership = result.scalars().first()
        
        if existing_membership:
            print("DEBUG: User is already a member")
            raise HTTPException(status_code=400, detail="User is already a member of this tenant.")
            
        # 4. Determine Role ID
        role_id = invite_in.role_id
        role_name = invite_in.role or "member"
        print(f"DEBUG: Resolving role. Provided ID: '{role_id}', Name: '{role_name}'")
        
        if not role_id:
            # Resolve by name
            stmt = select(models.TenantRole).where(
                models.TenantRole.tenant_id == current_tenant.id,
                func.lower(models.TenantRole.name) == role_name.lower()
            )
            role_result = await db.execute(stmt)
            role_obj = role_result.scalars().first()
            if role_obj:
                role_id = role_obj.id
            else:
                 # Fallback/Error? For now, if role name doesn't exist, we might default to member or error
                 # Try finding "Member"
                 stmt = select(models.TenantRole).where(models.TenantRole.tenant_id == current_tenant.id, models.TenantRole.name == "Member")
                 fallback = (await db.execute(stmt)).scalars().first()
                 if fallback:
                     role_id = fallback.id
                 else:
                     # Critical error, seeding failed?
                     print("DEBUG: Role resolution failed entirely")
                     raise HTTPException(status_code=500, detail="Default roles configuration missing.")

        print(f"DEBUG: Adding membership role_id={role_id}")
        # 5. Add Membership
        membership = models.TenantMember(
            tenant_id=current_tenant.id,
            user_id=target_user.id,
            role=role_name, # Legacy
            role_id=role_id
        )
        db.add(membership)
        await db.commit()
        await db.refresh(membership)
        
    except Exception as e:
        print(f"DEBUG: Exception in invite_user: {e}")
        raise e
    
    # Eager load user for response
    # Re-fetch with options
    stmt = select(models.TenantMember).where(
        models.TenantMember.tenant_id == current_tenant.id,
        models.TenantMember.user_id == target_user.id
    ).options(selectinload(models.TenantMember.user))
    result = await db.execute(stmt)
    membership = result.scalars().first()
    
    return membership

@router.delete("/users/{user_id}")
async def remove_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    """Remove user from tenant"""
    # 1. Check Privileges
    await check_admin_privileges(current_user, current_tenant, db)
    
    # Prevent removing self?
    if user_id == current_user.id:
         raise HTTPException(status_code=400, detail="Cannot remove yourself. Transfer ownership first or leave tenant.")

    # 2. Find Membership
    stmt = select(models.TenantMember).where(
        models.TenantMember.user_id == user_id,
        models.TenantMember.tenant_id == current_tenant.id
    )
    result = await db.execute(stmt)
    membership = result.scalars().first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if membership.role == "owner":
         raise HTTPException(status_code=400, detail="Cannot remove the Owner. Transfer ownership first.")

    # 3. Delete
    await db.delete(membership)
    await db.commit()
    
    return {"status": "success", "message": "User removed from tenant"}

@router.put("/users/{user_id}/role", response_model=schemas.TenantMember)
async def update_user_role(
    user_id: str,
    update_in: schemas.TenantUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    """Update user role"""
    # 1. Check Privileges
    admin_membership = await check_admin_privileges(current_user, current_tenant, db)
    
    # 2. Find Membership
    stmt = select(models.TenantMember).where(
        models.TenantMember.user_id == user_id,
        models.TenantMember.tenant_id == current_tenant.id
    ).options(selectinload(models.TenantMember.user))
    result = await db.execute(stmt)
    target_membership = result.scalars().first()
    
    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Prevention:
    # 1. Admin cannot change Owner's role
    if target_membership.role == "owner" and admin_membership.role != "owner":
         raise HTTPException(status_code=403, detail="Only the Owner can manage the Owner role.")

    # 2. Admin cannot change their own role (only Owner can change self)
    if user_id == current_user.id and admin_membership.role != "owner":
         raise HTTPException(status_code=403, detail="Admins cannot change their own role. Contact the Owner.")

    # Resolve new role
    new_role_id = update_in.role_id
    new_role_name = update_in.role
    
    if new_role_id:
        # Validate role exists in tenant
        stmt = select(models.TenantRole).where(models.TenantRole.id == new_role_id, models.TenantRole.tenant_id == current_tenant.id)
        role_obj = (await db.execute(stmt)).scalars().first()
        if not role_obj:
            raise HTTPException(status_code=400, detail="Invalid Role ID")
        new_role_name = role_obj.name
    elif new_role_name:
        stmt = select(models.TenantRole).where(
            models.TenantRole.tenant_id == current_tenant.id,
            func.lower(models.TenantRole.name) == new_role_name.lower()
        )
        role_obj = (await db.execute(stmt)).scalars().first()
        if role_obj:
            new_role_id = role_obj.id
        else:
            raise HTTPException(status_code=400, detail="Invalid Role Name")

    # 3. Restrict assignment of "Owner" role to current Owner only
    if new_role_name.lower() == "owner" and admin_membership.role != "owner":
        raise HTTPException(
            status_code=403, 
            detail="Only the current Owner can promote others to the Owner role."
        )

    target_membership.role = new_role_name # Legacy
    target_membership.role_id = new_role_id
    
    await db.commit()
    await db.refresh(target_membership)
    
    # Reload with details
    stmt = select(models.TenantMember).where(
        models.TenantMember.user_id == user_id,
        models.TenantMember.tenant_id == current_tenant.id
    ).options(
        selectinload(models.TenantMember.user), 
        selectinload(models.TenantMember.tenant_role).selectinload(models.TenantRole.permissions)
    )
    result = await db.execute(stmt)
    target_membership = result.scalars().first()
    
    return target_membership
