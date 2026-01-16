from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
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
import json

logger = logging.getLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Early exclusion check - VERY IMPORTANT for streaming compatibility
        # We MUST NOT touch the request body or use BaseHTTPMiddleware wrapping for chat
        if (not request.url.path.startswith("/api/v1") or 
            request.url.path.endswith("/health") or
            request.url.path.startswith("/api/v1/auth/") or
            request.url.path.startswith("/api/v1/chat/")):
            return await call_next(request)

        # Capture request body for non-chat POST/PUT/PATCH requests
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = body_bytes.decode('utf-8')
                # Re-create request with body for downstream
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception:
                pass
        
        # Capture metadata BEFORE call_next and background task
        # This ensures we don't depend on the request object after it might be disposed
        path = request.url.path
        method = request.method
        query_params = dict(request.query_params)
        user_agent = request.headers.get("User-Agent")
        
        # Extract IP
        ip = None
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        if not ip:
            ip = request.headers.get("X-Real-IP")
        if not ip:
            ip = request.client.host if request.client else None

        # Extract token early
        token = None
        try:
            token = await oauth2_scheme(request)
        except Exception:
            pass

        response = await call_next(request)
        
        # Extract X-Tenant-ID header
        x_tenant_id = request.headers.get("X-Tenant-ID")

        # Fire and forget logging with extracted data
        asyncio.create_task(self.log_audit(
            path=path,
            method=method,
            status_code=response.status_code,
            request_body=request_body,
            query_params=query_params,
            user_agent=user_agent,
            ip=ip,
            token=token,
            x_tenant_id=x_tenant_id
        ))
            
        return response

    async def log_audit(self, 
        path: str, 
        method: str, 
        status_code: int, 
        request_body: str = None,
        query_params: dict = None,
        user_agent: str = None,
        ip: str = None,
        token: str = None,
        x_tenant_id: str = None
    ):
        try:
            # Extract user from token
            user_id = None
            tenant_id = None
            user_email = None
            
            if token:
                try:
                    # Skip decode if it's a dummy token
                    if token.startswith("dummy_sso_"):
                         user_email = token.split("dummy_sso_")[1].replace("_at_", "@")
                    else:
                        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                        user_email = payload.get("sub")
                    
                    # Fetch user_id from database
                    if user_email:
                        async with AsyncSessionLocal() as session:
                            from app.models import models
                            from sqlalchemy import select
                            from sqlalchemy.orm import selectinload
                            
                            result = await session.execute(
                                select(models.User)
                                .where(models.User.email == user_email)
                                .options(selectinload(models.User.tenant_memberships))
                            )
                            user = result.scalars().first()
                            if user:
                                user_id = user.id
                                if user.tenant_memberships:
                                    # Logic to select tenant:
                                    # 1. Try to use header if valid membership matches
                                    if x_tenant_id:
                                        for membership in user.tenant_memberships:
                                            if str(membership.tenant_id) == str(x_tenant_id):
                                                tenant_id = membership.tenant_id
                                                break
                                    
                                    # 2. Fallback to first membership if no header or invalid
                                    if not tenant_id:
                                        tenant_id = user.tenant_memberships[0].tenant_id

                except (JWTError, Exception):
                    pass
            
            # Determine action from HTTP method
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
            path_parts = path.split("/")
            resource_type = "api"
            resource_id = None
            
            if len(path_parts) >= 4:
                resource_type = path_parts[3]  # /api/v1/{resource_type}/...
                if len(path_parts) >= 5 and path_parts[4]:
                    # Check if it's a UUID or ID
                    resource_id = path_parts[4]
            
            # Log to DB
            async with AsyncSessionLocal() as session:
                try:
                    repo = AuditLogRepository(session)
                    service = AuditService(repo)
                    
                    await service.log_action(
                        action=action,
                        resource_type=resource_type,
                        user_id=user_id,
                        resource_id=resource_id,
                        tenant_id=tenant_id,
                        details={
                            "method": method,
                            "path": path,
                            "status_code": status_code,
                            "user_email": user_email,
                            "request_body": request_body[:1000] if request_body else None,  # Limit to 1000 chars
                            "query_params": query_params
                        },
                        ip_address=ip,
                        user_agent=user_agent
                    )
                    await session.commit()
                except Exception as db_exc:
                    logger.error(f"Database error in audit logging: {db_exc}")
                    await session.rollback()
                finally:
                    await session.close()
                
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
