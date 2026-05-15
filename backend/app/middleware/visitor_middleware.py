from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import AsyncSessionLocal
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService
import httpx
import logging
import asyncio

import time
import ipaddress

logger = logging.getLogger(__name__)

class VisitorMiddleware(BaseHTTPMiddleware):
    _recent_ips = {}

    async def dispatch(self, request: Request, call_next):
        # 1. Early exclusion check - VERY IMPORTANT for streaming compatibility
        if (not request.url.path.startswith("/api/v1") or 
            request.url.path.endswith("/health") or
            request.url.path.startswith("/api/v1/chat/")):
            return await call_next(request)

        # Capture metadata BEFORE call_next and background task
        headers = dict(request.headers)
        client_host = request.client.host if request.client else None
        path = request.url.path
        method = request.method

        response = await call_next(request)
        
        # Fire and forget logging using asyncio.create_task with extracted data
        asyncio.create_task(self.log_visit(headers, client_host, path, method))
            
        return response

    async def log_visit(self, headers, client_host, path, method):
        try:
            # Extract Real Client IP (handling reverse proxies)
            # Priority: X-Forwarded-For > X-Real-IP > client.host
            ip = None
            
            # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
            # We want the FIRST one (the original client)
            forwarded = headers.get("X-Forwarded-For")
            if forwarded:
                # Take the first IP in the list
                ip = forwarded.split(",")[0].strip()
            
            # Fallback to X-Real-IP
            if not ip:
                ip = headers.get("X-Real-IP")
            
            # Final fallback to direct connection IP
            if not ip:
                ip = client_host
            
            # Skip if we still don't have a valid IP
            if not ip:
                return
            
            # De-duplication: Check if IP+User visited in last 30 minutes
            auth_header = headers.get("Authorization", "anon")
            auth_key = auth_header[:50] if auth_header else "anon"
            dedup_key = f"{ip}:{auth_key}"
            
            now = time.time()
            last_visit = self._recent_ips.get(dedup_key)
            if last_visit and now - last_visit < 1800: # 30 minutes
                return
            
            self._recent_ips[dedup_key] = now
            
            user_agent = headers.get("User-Agent")
            
            # Resolve Country and Details
            country = "Unknown"
            location_data = {}
            
            # Check if IP is private/local
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private:
                    country = "Local Network"
                    location_data = {"country": "Local Network", "city": "Local", "isp": "Internal"}
            except ValueError:
                pass

            if country == "Unknown" and ip and ip not in ["127.0.0.1", "::1", "localhost"]:
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        resp = await client.get(f"http://ip-api.com/json/{ip}")
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("status") == "success":
                                country = data.get("country", "Unknown")
                                location_data = data
                except Exception as e:
                    # logger.warning(f"Failed to resolve country for {ip}: {e}")
                    pass

            # Log to DB
            async with AsyncSessionLocal() as session:
                try:
                    repo = AnalyticsRepository(session)
                    service = AnalyticsService(repo)
                    
                    # Merge location data into metadata
                    meta = {
                        "ip": ip,
                        "user_agent": user_agent,
                        "country": country,
                        **location_data
                    }
                    
                    await service.log_event(
                        event_type="api_hit",
                        tenant_id=headers.get("x-tenant-id") or headers.get("X-Tenant-ID"),
                        event_data={
                            "path": path,
                            "method": method
                        },
                        metadata=meta
                    )
                    await asyncio.shield(session.commit())
                except asyncio.CancelledError:
                    pass
                except Exception as db_exc:
                    logger.error(f"Database error in visitor logging: {db_exc}")
                    await session.rollback()
                finally:
                    await session.close()
                
        except Exception as e:
            logger.error(f"Error logging visit: {e}")
