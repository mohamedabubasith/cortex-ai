from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.schemas import schemas
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.repositories.user_repository import UserRepository
from app.models import models

# Google OAuth Imports
import httpx
from fastapi.responses import RedirectResponse
import urllib.parse

router = APIRouter()

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

@router.post("/token", response_model=schemas.Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
) -> Any:
    user = await service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.User)
async def register_user(
    user_in: schemas.UserCreate,
    service: AuthService = Depends(get_auth_service)
) -> Any:
    return await service.create_user(user_in)

@router.post("/forgot-password")
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger password recovery.
    In 'soft mode', returns token directly for immediate navigation.
    """
    # Check if user exists
    user_repo = UserRepository(models.User, db)
    user = await user_repo.get_by_email(request.email)
    
    if user:
        # Generate token
        token = service.create_password_reset_token(request.email)
        
        # Send Email via Background Task (Fast & Non-blocking)
        print(f"Queuing background email task for {request.email}...")
        email_service = EmailService()
        background_tasks.add_task(email_service.send_reset_password_email, request.email, token)
        
        return {
            "success": True, 
            "message": "Password reset instructions sent to your email."
        }
    
    # If user doesn't exist, return generic response (security best practice)
    return {
        "success": False,
        "message": "If this email is registered, you will receive password reset instructions."
    }


@router.post("/reset-password")
async def reset_password(
    body: schemas.NewPassword,
    service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using token.
    """
    await service.reset_password(body.token, body.new_password)
    return {"message": "Password updated successfully"}

from app.services.auth_service import get_current_active_user

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    return current_user


# --- Google OAuth Endpoints ---

@router.get("/google/login")
async def google_login():
    """
    Initiates the Google OAuth2 flow by redirecting the user to Google's consent page.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth credentials are not configured on the server."
        )
    
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    scopes = "openid email profile"
    
    # Construct exact callback URL
    domain = settings.FRONTEND_URL.rstrip("/")
    redirect_uri = f"{domain}/api/v1/auth/google/callback"
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "select_account"
    }
    
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str, 
    error: str = None, 
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle the callback from Google. Exchange code for token, get user info, login/register.
    """
    if error:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=google_auth_failed")
    
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
         raise HTTPException(status_code=500, detail="Google credentials missing")

    domain = settings.FRONTEND_URL.rstrip("/")
    redirect_uri = f"{domain}/api/v1/auth/google/callback"
    
    token_url = "https://oauth2.googleapis.com/token"
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    async with httpx.AsyncClient() as client:
        # 1. Exchange code for tokens
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        token_res = await client.post(token_url, data=token_data)
        if token_res.status_code != 200:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=google_token_exchange_failed")
            
        tokens = token_res.json()
        access_token = tokens.get("access_token")
        
        # 2. Get User Info
        user_res = await client.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
        if user_res.status_code != 200:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=google_user_info_failed")
            
        user_info = user_res.json()
        
    # 3. Process User
    email = user_info.get("email")
    if not email:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=email_not_provided_by_google")
        
    # Check if user exists
    user = await service.repo.get_by_email(email)
    
    if not user:
        # JIT Provisioning (Register new user)
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        dummy_password = ''.join(secrets.choice(alphabet) for i in range(32))
        
        user_in = schemas.UserCreate(
            email=email,
            password=dummy_password,
            full_name=user_info.get("name") or email.split("@")[0],
            is_active=True
        )
        
        try:
            user = await service.create_user(user_in)
        except Exception as e:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=account_creation_failed")

    # 4. Generate Session Token (JWT)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # 5. Redirect to Frontend Callback Handler
    frontend_callback = f"{settings.FRONTEND_URL}/auth/google/callback?token={access_token}"
    
    return RedirectResponse(url=frontend_callback)
