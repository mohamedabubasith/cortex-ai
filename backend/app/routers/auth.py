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
        
        # SOFT MODE: Return token directly for immediate navigation
        # This allows frontend to navigate to /reset-password/<token> immediately
        return {
            "success": True,
            "token": token,
            "message": "Password reset token generated"
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
