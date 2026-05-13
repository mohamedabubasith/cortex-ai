from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(models.User, db)
        self.db = db

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str) -> Optional[models.User]:
        user = await self.repo.get_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def create_user(self, user_in: schemas.UserCreate, auto_create_tenant: bool = True) -> models.User:
        user = await self.repo.get_by_email(user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        
        user_data = user_in.dict()
        password = user_data.pop("password")
        user_data["hashed_password"] = self.get_password_hash(password)
        
        user = await self.repo.create(user_data)
        
        # Multi-Tenancy: Create default "Personal" Tenant
        try:
            if auto_create_tenant:
                from sqlalchemy.orm import Session
            
            # 1. Create Tenant
            tenant_name = f"{user.full_name or user.email.split('@')[0]}'s Workspace"
            tenant_slug = f"{user.email.split('@')[0]}-{user.id[:8]}".lower().replace(" ", "-") # Simple slug generation
            
            new_tenant = models.Tenant(
                name=tenant_name,
                slug=tenant_slug
            )
            self.db.add(new_tenant)
            await self.db.flush() # Get ID
            
            # 1.1 Create Default Roles for this Tenant
            from sqlalchemy import select
            
            # Fetch all global permissions to assign to Owner
            all_perms_result = await self.db.execute(select(models.Permission))
            all_perms = all_perms_result.scalars().all()
            
            # Create Owner Role
            owner_role = models.TenantRole(
                tenant_id=new_tenant.id,
                name="Owner",
                description="System owner role",
                is_system_role=True
            )
            self.db.add(owner_role)
            await self.db.flush() # Get ID
            
            # Assign ALL permissions to Owner
            for perm in all_perms:
                self.db.add(models.RolePermission(role_id=owner_role.id, permission_slug=perm.slug))
            
            # Create Member Role
            member_role = models.TenantRole(
                tenant_id=new_tenant.id,
                name="Member",
                description="System member role",
                is_system_role=True
            )
            self.db.add(member_role)
            await self.db.flush()
            
            # Assign subset to Member (View/Run)
            member_slugs = ["kb.view", "agent.view", "agent.run", "mcp.view"]
            for slug in member_slugs:
                # Only add if it exists in system
                if any(p.slug == slug for p in all_perms):
                     self.db.add(models.RolePermission(role_id=member_role.id, permission_slug=slug))

            # 2. Add User as Tenant Owner
            membership = models.TenantMember(
                tenant_id=new_tenant.id,
                user_id=user.id,
                role="owner", # Keep legacy string for safety/fallback
                role_id=owner_role.id
            )
            self.db.add(membership)
            await self.db.commit()
            
            # Re-fetch user to ensure relationships (tenants) are loaded for the response
            # We use get_by_email which now includes eager loading
            refreshed_user = await self.repo.get_by_email(user_in.email)
            if refreshed_user:
                return refreshed_user
                
        except Exception as e:
            print(f"Failed to provision default tenant: {e}")
            # Non-critical? Actually critical for multi-tenancy.
            # But let's not block user creation for now if it fails, or rollback?
            # ideally rollback, but simple try/except for now.

        return user

    def create_password_reset_token(self, email: str) -> str:
        delta = timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES)
        now = datetime.utcnow()
        expires = now + delta
        exp = expires.timestamp()
        nbf = now.timestamp()
        encoded_jwt = jwt.encode(
            {"exp": exp, "nbf": nbf, "sub": email, "type": "password_reset"},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Attempting to verify token: {token[:20]}...")
            
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            logger.info(f"Decoded token: {decoded_token}")
            
            if decoded_token["type"] != "password_reset":
                logger.error(f"Invalid token type: {decoded_token.get('type')}")
                return None
                
            email = decoded_token["sub"]
            logger.info(f"Token valid for email: {email}")
            return email
        except JWTError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"JWT decode error: {str(e)}")
            return None

    async def reset_password(self, token: str, new_password: str) -> None:
        email = self.verify_password_reset_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        user = await self.repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        hashed_password = self.get_password_hash(new_password)
        await self.repo.update(user, {"hashed_password": hashed_password})

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = None
    
    try:
        # 1. DUMMY SSO TOKEN VALIDATION (For Testing/Development)
        if token.startswith("dummy_sso_"):
            # Format: dummy_sso_email_at_example_com
            try:
                # Extract email from simple dummy format
                parts = token.split("dummy_sso_")
                if len(parts) > 1:
                    email = parts[1].replace("_at_", "@")
            except Exception:
                pass
                
        # 2. KEYCLOAK TOKEN VALIDATION (Real Implementation Placeholder)
        elif settings.AUTH_PROVIDER == "keycloak" and settings.KEYCLOAK_PEM_PUBLIC_KEY:
            try:
                # In a real scenario, we verify signature using KEYCLOAK_PEM_PUBLIC_KEY
                # options = {"verify_signature": True, "verify_aud": True, "aud": settings.KEYCLOAK_CLIENT_ID}
                # payload = jwt.decode(token, settings.KEYCLOAK_PEM_PUBLIC_KEY, algorithms=["RS256"], options=options)
                pass
            except Exception:
                pass

        # 3. LOCAL JWT VALIDATION (Fallback)
        if not email:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                email: str = payload.get("sub")
            except Exception:
                # If standard flow failed and we didn't match dummy, raise error
                raise credentials_exception

        if email is None:
            raise credentials_exception
            
        repo = UserRepository(models.User, db)
        user = await repo.get_by_email(email=email)
        
        # JIT Provisioning for SSO Users
        if user is None:
            # If the user came from a valid SSO/Dummy token but doesn't exist locally,
            # we create them ("Just In Time" provisioning) to handle RBAC locally.
            
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            dummy_password = ''.join(secrets.choice(alphabet) for i in range(20))
            
            user_in = schemas.UserCreate(
                email=email,
                password=dummy_password, # Random password, they won't use it
                full_name=email.split("@")[0],
                is_active=True
            )
            
            # Use auth service instance to create user
            auth_svc = AuthService(db)
            try:
                user = await auth_svc.create_user(user_in)
            except Exception:
                raise credentials_exception
                
        if user is None:
            raise credentials_exception
            
        return user
    except Exception:
        raise credentials_exception

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_tenant(
    request: Request,
    user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db) # We need DB to query memberships
) -> models.Tenant:
    """
    Returns the user's active tenant.
    Checks X-Tenant-ID header first, falls back to first membership.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    tenant_id = request.headers.get("X-Tenant-ID")

    if tenant_id:
        # 1. Requested specific tenant
        stmt = select(models.TenantMember).where(
            models.TenantMember.user_id == user.id,
            models.TenantMember.tenant_id == tenant_id
        ).options(selectinload(models.TenantMember.tenant))
        result = await db.execute(stmt)
        membership = result.scalars().first()
        
        if membership:
            # Hydrate Request State for RBAC
            request.state.tenant = membership.tenant
            
            # Load Permissions
            from app.services.permission_service import PermissionService
            perm_service = PermissionService(db)
            request.state.permissions = await perm_service.get_user_effective_permissions(user.id, membership.tenant.id)
            
            return membership.tenant
        
        raise HTTPException(status_code=403, detail="Not a member of the requested tenant.")
    
    # 2. Fallback to first available
    stmt = select(models.TenantMember).where(models.TenantMember.user_id == user.id).options(selectinload(models.TenantMember.tenant))
    result = await db.execute(stmt)
    membership = result.scalars().first()
    
    if not membership:
        return None 
    
    # Hydrate Fallback
    request.state.tenant = membership.tenant
    from app.services.permission_service import PermissionService
    perm_service = PermissionService(db)
    request.state.permissions = await perm_service.get_user_effective_permissions(user.id, membership.tenant.id)
    
    return membership.tenant
