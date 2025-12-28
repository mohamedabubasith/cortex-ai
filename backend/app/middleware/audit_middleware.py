from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import AsyncSessionLocal
from app.repositories.audit_repository import AuditLogRepository
from app.services.audit_service import AuditService
from app.services.auth_service import oauth2_scheme
from jose import jwt, JWTError
from app.core.config import settings
import logging
import asyncio
import ipaddress

logger = logging.getLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only log API requests (skip health checks, static files, and auth endpoints)
        if (request.url.path.startswith("/api/v1") and 
            not request.url.path.endswith("/health") and
            not request.url.path.startswith("/api/v1/auth/")):
            
            # Fire and forget logging
            asyncio.create_task(self.log_audit(request, response.status_code))
            
        return response

    async def log_audit(self, request: Request, status_code: int):
        try:
            # Extract user from token
            user_id = None
            user_email = None
            
            token = await oauth2_scheme(request)
            if token:
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                    user_email = payload.get("sub")
                    
                    # Fetch user_id from database
                    if user_email:
                        async with AsyncSessionLocal() as session:
                            from app.models import models
                            from sqlalchemy import select
                            result = await session.execute(
                                select(models.User).where(models.User.email == user_email)
                            )
                            user = result.scalar_one_or_none()
                            if user:
                                user_id = user.id
                except JWTError:
                    pass
            
            # Extract IP
            ip = None
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0].strip()
            if not ip:
                ip = request.headers.get("X-Real-IP")
            if not ip:
                ip = request.client.host if request.client else None
            
            user_agent = request.headers.get("User-Agent")
            
            # Determine action from HTTP method
            method = request.method
            action_map = {
                "GET": "access",
                "POST": "create",
                "PUT": "update",
                "PATCH": "update",
                "DELETE": "delete"
            }
            action = action_map.get(method, "access")
            
            # Extract resource type from path
            # e.g., /api/v1/agents/123 -> resource_type="agents", resource_id="123"
            path_parts = request.url.path.split("/")
            resource_type = "api"
            resource_id = None
            
            if len(path_parts) >= 4:
                resource_type = path_parts[3]  # /api/v1/{resource_type}/...
                if len(path_parts) >= 5 and path_parts[4]:
                    # Check if it's a UUID or ID
                    resource_id = path_parts[4]
            
            # Log to DB
            async with AsyncSessionLocal() as session:
                repo = AuditLogRepository(session)
                service = AuditService(repo)
                
                await service.log_action(
                    action=action,
                    resource_type=resource_type,
                    user_id=user_id,  # Will be None for now, can be improved
                    resource_id=resource_id,
                    details={
                        "method": method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "user_email": user_email
                    },
                    ip_address=ip,
                    user_agent=user_agent
                )
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
