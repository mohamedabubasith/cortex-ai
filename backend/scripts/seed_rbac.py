
import asyncio
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import models

# 1. Define Standard Permissions
SYSTEM_PERMISSIONS = [
    # KB
    {"slug": "kb.view", "description": "View Knowledge Bases", "category": "kb"},
    {"slug": "kb.read_all", "description": "View All Knowledge Bases in Tenant", "category": "kb"},
    {"slug": "kb.create", "description": "Create Knowledge Bases", "category": "kb"},
    {"slug": "kb.edit", "description": "Edit Knowledge Bases", "category": "kb"},
    {"slug": "kb.delete", "description": "Delete Knowledge Bases", "category": "kb"},
    
    # Agents
    {"slug": "agent.view", "description": "View Agents", "category": "agent"},
    {"slug": "agent.run", "description": "Run/Chat with Agents", "category": "agent"},
    {"slug": "agent.create", "description": "Create/Edit Agents", "category": "agent"},
    {"slug": "agent.delete", "description": "Delete Agents", "category": "agent"},
    
    # IAM (Identity & Access)
    {"slug": "iam.user.view", "description": "View Users", "category": "iam"},
    {"slug": "iam.user.invite", "description": "Invite Users", "category": "iam"},
    {"slug": "iam.role.manage", "description": "Manage Roles (Create/Edit)", "category": "iam"},
    {"slug": "iam.group.manage", "description": "Manage Groups", "category": "iam"},

    # LLM Providers
    {"slug": "llm.view", "description": "View LLM Configurations", "category": "llm"},
    {"slug": "llm.manage", "description": "Manage LLM Configurations", "category": "llm"},
]

# 2. Define Standard Roles & their Permissions
STANDARD_ROLES = {
    "owner": ["kb.*", "agent.*", "iam.*", "llm.*"], # Wildcard logic implemented in seeding
    "admin": ["kb.*", "agent.*", "iam.*", "llm.*"], # Admin same as owner for now permissions-wise, but restricted from editing owner
    "member": ["kb.view", "kb.read_all", "kb.create", "kb.edit", "agent.view", "agent.run", "agent.create", "iam.user.view", "llm.view"],
    "viewer": ["kb.view", "kb.read_all", "agent.view", "agent.run", "llm.view"]
}

def expand_permissions(patterns):
    expanded = set()
    all_slugs = [p["slug"] for p in SYSTEM_PERMISSIONS]
    
    for pattern in patterns:
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            for slug in all_slugs:
                if slug.startswith(prefix):
                    expanded.add(slug)
        else:
            if pattern in all_slugs:
                expanded.add(pattern)
    return list(expanded)

async def seed_permissions(db):
    print("Seeding Permissions...")
    for p in SYSTEM_PERMISSIONS:
        stmt = select(models.Permission).where(models.Permission.slug == p["slug"])
        result = await db.execute(stmt)
        if not result.scalars().first():
            db.add(models.Permission(**p))
    await db.commit()

async def seed_tenant_roles(db):
    print("Seeding Tenant Roles...")
    # Get all tenants
    result = await db.execute(select(models.Tenant))
    tenants = result.scalars().all()
    
    for tenant in tenants:
        print(f"Processing Tenant: {tenant.name} ({tenant.id})")
        
        # For each standard role name
        for role_name, patterns in STANDARD_ROLES.items():
            # Check if role exists
            stmt = select(models.TenantRole).where(
                models.TenantRole.tenant_id == tenant.id,
                models.TenantRole.name == role_name.capitalize() # "Owner", "Admin"
            )
            result = await db.execute(stmt)
            role = result.scalars().first()
            
            if not role:
                role = models.TenantRole(
                    tenant_id=tenant.id,
                    name=role_name.capitalize(),
                    description=f"System {role_name} role",
                    is_system_role=True
                )
                db.add(role)
                await db.flush() # Get ID
            
            # Upsert Permissions for this role
            effective_perms = expand_permissions(patterns)
            
            # Clear existing role perms (simple sync)
            # await db.execute(delete(models.RolePermission).where(models.RolePermission.role_id == role.id))
            # Actually better to check and add missing
            
            for perm_slug in effective_perms:
                 stmt = select(models.RolePermission).where(
                     models.RolePermission.role_id == role.id,
                     models.RolePermission.permission_slug == perm_slug
                 )
                 existing = (await db.execute(stmt)).scalars().first()
                 if not existing:
                     db.add(models.RolePermission(role_id=role.id, permission_slug=perm_slug))
        
        await db.commit()
    
    print("Roles Seeded.")

async def migrate_users(db):
    print("Migrating Legacy Users to Roles...")
    # For every member without a role_id
    stmt = select(models.TenantMember).where(models.TenantMember.role_id == None)
    result = await db.execute(stmt)
    members = result.scalars().all()
    
    for m in members:
        legacy_role = m.role or "member" # owner, admin, member...
        
        # Find corresponding TenantRole
        stmt = select(models.TenantRole).where(
            models.TenantRole.tenant_id == m.tenant_id,
            models.TenantRole.name == legacy_role.capitalize()
        )
        role = (await db.execute(stmt)).scalars().first()
        
        if role:
            m.role_id = role.id
            print(f"Migrated User {m.user_id} in {m.tenant_id} to Role {role.name}")
        else:
            print(f"Warning: Could not find role {legacy_role} for tenant {m.tenant_id}")
            
    await db.commit()

async def main():
    async with AsyncSessionLocal() as db:
        await seed_permissions(db)
        await seed_tenant_roles(db)
        await migrate_users(db)

if __name__ == "__main__":
    asyncio.run(main())
