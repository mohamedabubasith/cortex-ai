"""API Hit Tracking Middleware"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

class HitTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log hit to analytics if database session available
        if hasattr(request.state, 'db'):
            from app.repositories.analytics_repository import AnalyticsRepository
            
            analytics_repo = AnalyticsRepository(request.state.db)
            
            # Extract user ID if available
            user_id = None
            if hasattr(request.state, 'user'):
                user_id = request.state.user.id
            
            await analytics_repo.create_event(
                event_type="api_hit",
                tenant_id=request.headers.get("x-tenant-id") or request.headers.get("X-Tenant-ID"),
                user_id=user_id,
                event_data={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                },
                meta_data={
                    "user_agent": request.headers.get("user-agent"),
                    "ip": request.client.host if request.client else None
                }
            )
        
        return response
