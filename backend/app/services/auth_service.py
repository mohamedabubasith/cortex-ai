from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
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

    async def create_user(self, user_in: schemas.UserCreate) -> models.User:
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
        
        # Create user in Cognee as well
        try:
            from cognee.api.v1.users.create_user import create_user as create_cognee_user
            # We use the original password here
            await create_cognee_user(email=user_in.email, password=user_in.password)
        except Exception as e:
            # Log error but allow app registration to succeed
            print(f"Failed to create Cognee user: {e}")
            
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
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    repo = UserRepository(models.User, db)
    user = await repo.get_by_email(email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
