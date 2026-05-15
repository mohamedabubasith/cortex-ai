from pathlib import Path

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent
# Repository root `.env` only (no `backend/.env`).
load_dotenv(_repo_root / ".env")

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
# Enable verbose logs for DLT if LOG_LEVEL is DEBUG
if settings.LOG_LEVEL == "DEBUG":
    logging.getLogger("dlt").setLevel(logging.DEBUG)

from contextlib import asynccontextmanager

async def _run_migrations() -> None:
    """Run alembic upgrade head at startup (idempotent)."""
    import asyncio
    from pathlib import Path
    try:
        backend_dir = Path(__file__).resolve().parent
        proc = await asyncio.create_subprocess_exec(
            "alembic", "upgrade", "head",
            cwd=str(backend_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            logging.getLogger(__name__).info("alembic upgrade head: OK")
        else:
            logging.getLogger(__name__).error(
                "alembic upgrade head failed (rc=%s): %s",
                proc.returncode,
                stderr.decode()[:500],
            )
    except Exception as exc:
        logging.getLogger(__name__).error("alembic upgrade head error: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Validate critical configuration
    settings.validate_providers()

    # Run DB migrations before anything else
    await _run_migrations()

    from app.core.database import AsyncSessionLocal
    # Import models to ensure they are registered with Base
    from app.models import models  # noqa: F401
    from app.core.startup import create_default_admin

    # Create first superuser from ADMIN_EMAIL / ADMIN_PASSWORD when none exists.
    async with AsyncSessionLocal() as db:
        await create_default_admin(db)

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
    allow_headers=["*"],
    expose_headers=["x-session-id"],
)

from app.middleware.visitor_middleware import VisitorMiddleware
app.add_middleware(VisitorMiddleware)

from app.middleware.audit_middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)

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

# Import and include routers
from app.routers import auth, agents, chat, resources, knowledgebase, llm, analytics, admin, tenant, shares

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(agents.router, prefix=f"{settings.API_V1_STR}/agents", tags=["agents"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(resources.router, prefix=f"{settings.API_V1_STR}/resources", tags=["resources"])
app.include_router(knowledgebase.router, prefix=f"{settings.API_V1_STR}/kb", tags=["knowledge-base"])
app.include_router(llm.router, prefix=f"{settings.API_V1_STR}/llm", tags=["llm-config"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(tenant.router, prefix=f"{settings.API_V1_STR}/tenant", tags=["tenant"])
# Generic Sharing
app.include_router(shares.router, prefix=f"{settings.API_V1_STR}/share", tags=["sharing"])
from app.routers import groups
app.include_router(groups.router, prefix=f"{settings.API_V1_STR}/tenant/groups", tags=["tenant-groups"])
from app.routers import roles
app.include_router(roles.router, prefix=f"{settings.API_V1_STR}/tenant/roles", tags=["tenant-roles"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
