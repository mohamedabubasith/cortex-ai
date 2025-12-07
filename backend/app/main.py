from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import logging
import os

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Enable verbose logs for Cognee and DLT if LOG_LEVEL is DEBUG
if log_level == "DEBUG":
    logging.getLogger("cognee").setLevel(logging.DEBUG)
    logging.getLogger("dlt").setLevel(logging.DEBUG)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def root():
    return {"message": "Welcome to Chatbot Admin Dashboard API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Import and include routers here later
from app.routers import auth, agents, chat, resources, knowledgebase, llm, analytics

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(agents.router, prefix=f"{settings.API_V1_STR}/agents", tags=["agents"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(resources.router, prefix=f"{settings.API_V1_STR}/resources", tags=["resources"])
app.include_router(knowledgebase.router, prefix=f"{settings.API_V1_STR}/kb", tags=["knowledge-base"])
app.include_router(llm.router, prefix=f"{settings.API_V1_STR}/llm", tags=["llm-config"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
# from app.routers import databases
# app.include_router(databases.router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/databases", tags=["databases"])

@app.on_event("startup")
async def startup_event():
    from app.services.cognee_service import cognee_service
    from app.core.database import engine, Base
    # Import models to ensure they are registered with Base
    from app.models import models
    
    # Create tables automatically (User's request)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize Cognee (creates tables if needed)
    await cognee_service.initialize()
