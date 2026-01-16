from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import logging
import os

# Configure logging
log_level = settings.LOG_LEVEL.upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Enable verbose logs for Cognee and DLT if LOG_LEVEL is DEBUG
if log_level == "DEBUG":
    logging.getLogger("cognee").setLevel(logging.DEBUG)
    logging.getLogger("dlt").setLevel(logging.DEBUG)

# Apply Cognee patches - REMOVED as per user request
# from app.core.cognee_patch import apply_cognee_patches
# apply_cognee_patches()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Validate critical configuration
    settings.validate_providers()

    from app.core.database import engine, Base, get_db
    # Import models to ensure they are registered with Base
    from app.models import models
    
    # Database schema is managed by Alembic migrations.
    # Automatic table creation is disabled to prevent conflicts.
    # See backend/alembic for migration scripts.
    
    # Auto-create default admin user if none exists
    from app.core.startup import initialize_database
    async for db in get_db():
        await initialize_database(db)
        break
    
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Tenant-ID", "Content-Type", "Authorization"],
    expose_headers=["x-session-id"],
)

from app.middleware.visitor_middleware import VisitorMiddleware
app.add_middleware(VisitorMiddleware)

from app.middleware.audit_middleware import AuditMiddleware
# app.add_middleware(AuditMiddleware)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.get("/")
async def root():
    return {"message": "Welcome to Chatbot Admin Dashboard API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Import and include routers here later
from app.routers import auth, agents, chat, resources, knowledgebase, llm, analytics, admin, access, tenants, organization

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(agents.router, prefix=f"{settings.API_V1_STR}/agents", tags=["agents"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(resources.router, prefix=f"{settings.API_V1_STR}/resources", tags=["resources"])
app.include_router(knowledgebase.router, prefix=f"{settings.API_V1_STR}/kb", tags=["knowledge-base"])
app.include_router(llm.router, prefix=f"{settings.API_V1_STR}/llm", tags=["llm-config"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(access.router, prefix=f"{settings.API_V1_STR}/access", tags=["access"])
app.include_router(tenants.router, prefix=f"{settings.API_V1_STR}/tenants", tags=["tenants"])
app.include_router(organization.router, prefix=f"{settings.API_V1_STR}/organization", tags=["organization"])
