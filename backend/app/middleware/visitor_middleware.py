from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import AsyncSessionLocal
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService
import httpx
import logging
import asyncio

import time

logger = logging.getLogger(__name__)

class VisitorMiddleware(BaseHTTPMiddleware):
    _recent_ips = {}

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only log API requests, skip health checks and static files
        if request.url.path.startswith("/api/v1") and not request.url.path.endswith("/health"):
            # Fire and forget logging using asyncio.create_task
            asyncio.create_task(self.log_visit(request.headers, request.client.host, request.url.path, request.method))
            
        return response

    async def log_visit(self, headers, client_host, path, method):
        try:
            # Extract IP
            forwarded = headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0]
            else:
                ip = client_host
            
            # De-duplication: Check if IP visited in last 30 minutes
            now = time.time()
            last_visit = self._recent_ips.get(ip)
            if last_visit and now - last_visit < 1800: # 30 minutes
                return
            
            self._recent_ips[ip] = now
            
            user_agent = headers.get("User-Agent")
            
            # Resolve Country
            country = "Unknown"
            if ip and ip not in ["127.0.0.1", "::1", "localhost"]:
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        resp = await client.get(f"http://ip-api.com/json/{ip}")
                        if resp.status_code == 200:
                            data = resp.json()
                            country = data.get("country", "Unknown")
                except Exception as e:
                    # logger.warning(f"Failed to resolve country for {ip}: {e}")
                    pass

            # Log to DB
            async with AsyncSessionLocal() as session:
                repo = AnalyticsRepository(session)
                service = AnalyticsService(repo)
                
                await service.log_event(
                    event_type="api_hit",
                    event_data={
                        "path": path,
                        "method": method
                    },
                    meta_data={
                        "ip": ip,
                        "user_agent": user_agent,
                        "country": country
                    }
                )
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error logging visit: {e}")
