from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.auth_service import get_current_active_user, get_current_tenant
from app.services.database_service import database_service
from app.services.mcp_service import mcp_service
import json

from app.repositories.database_repository import DatabaseRepository
from app.repositories.mcp_repository import MCPRepository
from app.services.access_control_service import AccessControlService

router = APIRouter()

def get_db_repo(db: AsyncSession = Depends(get_db)) -> DatabaseRepository:
    return DatabaseRepository(db)

def get_mcp_repo(db: AsyncSession = Depends(get_db)) -> MCPRepository:
    return MCPRepository(db)

def get_access_service(db: AsyncSession = Depends(get_db)) -> AccessControlService:
    return AccessControlService(db)

# MCP Hub Registry
MCP_HUB_REGISTRY = [
    {
        "id": "filesystem",
        "name": "Local Filesystem",
        "description": "Access and manage local files and directories securely.",
        "icon": "FolderOpen",
        "server_url": "http://localhost:8000/mcp/filesystem",
        "protocol": "sse",
        "documentation": "Run: npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/dir",
        "env_vars": []
    },
    {
        "id": "github",
        "name": "GitHub",
        "description": "Search repositories, manage issues, and view pull requests.",
        "icon": "Github",
        "server_url": "http://localhost:8000/mcp/github",
        "protocol": "sse",
        "documentation": "Run: npx -y @modelcontextprotocol/server-github",
        "env_vars": [
            {"name": "GITHUB_PERSONAL_ACCESS_TOKEN", "label": "Personal Access Token", "type": "password", "required": True}
        ]
    },
    {
        "id": "postgres",
        "name": "PostgreSQL",
        "description": "Read-only database access for querying data and schema.",
        "icon": "Database",
        "server_url": "http://localhost:8000/mcp/postgres",
        "protocol": "sse",
        "documentation": "Run: npx -y @modelcontextprotocol/server-postgres postgresql://user:pass@localhost:5432/db",
         "env_vars": [
             {"name": "POSTGRES_URL", "label": "Connection String", "type": "text", "placeholder": "postgresql://user:pass@localhost:5432/db", "required": True}
        ]
    },
    {
        "id": "brave",
        "name": "Brave Search",
        "description": "Web search capabilities using Brave Search API.",
        "icon": "Globe",
        "server_url": "http://localhost:8000/mcp/brave",
        "protocol": "sse",
        "documentation": "Run: npx -y @modelcontextprotocol/server-brave-search",
        "env_vars": [
             {"name": "BRAVE_API_KEY", "label": "Brave API Key", "type": "password", "required": True}
        ]
    },
    {
        "id": "gmail",
        "name": "Gmail",
        "description": "Read and manage emails, drafts, and attachments.",
        "icon": "Mail",
        "server_url": "http://localhost:8000/mcp/gmail",
        "protocol": "sse",
        "documentation": "Custom Python server required.",
        "env_vars": [
             {"name": "GMAIL_CLIENT_ID", "label": "Client ID", "type": "password", "required": True},
             {"name": "GMAIL_CLIENT_SECRET", "label": "Client Secret", "type": "password", "required": True},
             {"name": "GMAIL_REFRESH_TOKEN", "label": "Refresh Token", "type": "password", "required": True}
        ]
    },
    {
        "id": "slack",
        "name": "Slack",
        "description": "Send messages, read channels, and manage workspace.",
        "icon": "MessageSquare",
        "server_url": "http://localhost:8000/mcp/slack",
        "protocol": "sse",
        "documentation": "Custom Python server required.",
        "env_vars": [
             {"name": "SLACK_BOT_TOKEN", "label": "Bot Token", "type": "password", "required": True},
             {"name": "SLACK_TEAM_ID", "label": "Team ID", "type": "text", "required": True}
        ]
    }
]

@router.get("/mcp/hub")
async def get_mcp_hub_registry(
    current_user: models.User = Depends(get_current_active_user)
):
    """Return the list of available MCP plugins in the Hub."""
    return MCP_HUB_REGISTRY


@router.post("/databases", response_model=schemas.DatabaseConnectionResponse)
async def create_db_connection(
    connection: schemas.DatabaseConnectionCreate,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: DatabaseRepository = Depends(get_db_repo)
):
    # Port validation
    if not (1 <= connection.port <= 65535):
        raise HTTPException(status_code=400, detail="Port must be between 1 and 65535")
        
    encrypted_password = database_service.encrypt_password(connection.password)
    
    db_connection = await repo.create(
        {
            "name": connection.name,
            "type": connection.type,
            "host": connection.host,
            "port": connection.port,
            "username": connection.username,
            "encrypted_password": encrypted_password,
            "database_name": connection.database_name,
            "ssl_mode": connection.ssl_mode
        },
        user_id=current_user.id,
        tenant_id=current_tenant.id
    )
    return db_connection

@router.get("/databases", response_model=List[schemas.DatabaseConnectionResponse])
async def get_db_connections(
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: DatabaseRepository = Depends(get_db_repo)
):
    return await repo.get_all(user=current_user, tenant_id=current_tenant.id)

@router.post("/databases/test")
async def test_db_connection(
    connection: schemas.DatabaseConnectionCreate,
    current_user: models.User = Depends(get_current_active_user)
):
    """Test database connection without saving it"""
    # Create a temporary connection object for testing
    temp_connection = models.DatabaseConnection(
        name=connection.name,
        type=connection.type,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        encrypted_password=database_service.encrypt_password(connection.password),
        database_name=connection.database_name,
        ssl_mode=connection.ssl_mode
    )
    
    try:
        success = await database_service.test_connection(temp_connection)
        if success:
            return {"status": "success", "message": "Connection successful!"}
        else:
            return {"status": "failed", "message": "Connection failed. Please check your credentials."}
    except Exception as e:
        error_message = str(e)
        # Provide more user-friendly error messages for common issues
        if "password authentication failed" in error_message.lower():
            return {"status": "failed", "message": "Authentication failed. Please check your username and password."}
        elif "does not exist" in error_message.lower():
            return {"status": "failed", "message": "Database does not exist. Please check the database name."}
        elif "connection refused" in error_message.lower() or "could not connect" in error_message.lower():
            return {"status": "failed", "message": "Could not connect to database server. Please check host and port."}
        else:
            return {"status": "failed", "message": error_message if error_message else "Connection failed. Please check your credentials."}

@router.post("/databases/{db_id}/test")
async def test_existing_db_connection(
    db_id: str,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: DatabaseRepository = Depends(get_db_repo),
    access_service: AccessControlService = Depends(get_access_service)
):
    """Test an existing saved database connection by ID"""
    if not await access_service.has_access(current_user, db_id, "database_connection", "viewer", current_tenant.id):
        raise HTTPException(status_code=403, detail="Access Denied")
        
    db_conn = await repo.get(db_id, user=current_user, tenant_id=current_tenant.id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    try:
        success = await database_service.test_connection(db_conn)
        return {"status": "success" if success else "failed", "message": "Connection successful!" if success else "Connection failed."}
    except Exception as e:
        return {"status": "failed", "message": str(e)}

@router.put("/databases/{db_id}", response_model=schemas.DatabaseConnectionResponse)
async def update_db_connection(
    db_id: str,
    connection_update: schemas.DatabaseConnectionUpdate,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: DatabaseRepository = Depends(get_db_repo),
    access_service: AccessControlService = Depends(get_access_service)
):
    """Update an existing database connection"""
    if not await access_service.has_access(current_user, db_id, "database_connection", "editor", current_tenant.id):
        raise HTTPException(status_code=403, detail="Access Denied")
        
    db_conn = await repo.get(db_id, user=current_user, tenant_id=current_tenant.id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    update_data = connection_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["encrypted_password"] = database_service.encrypt_password(update_data.pop("password"))
        
    return await repo.update(db_conn, update_data)

@router.delete("/databases/{db_id}")
async def delete_db_connection(
    db_id: str,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: DatabaseRepository = Depends(get_db_repo),
    access_service: AccessControlService = Depends(get_access_service)
):
    if not await access_service.has_access(current_user, db_id, "database_connection", "admin", current_tenant.id):
        raise HTTPException(status_code=403, detail="Access Denied")
        
    db_conn = await repo.get(db_id, user=current_user, tenant_id=current_tenant.id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
        
    await repo.delete(db_conn)
    return {"status": "success"}

# MCP Endpoints

@router.post("/mcp", response_model=schemas.MCPConnectionResponse)
async def create_mcp_connection(
    connection: schemas.MCPConnectionCreate,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: MCPRepository = Depends(get_mcp_repo)
):
    encrypted_headers = None
    if connection.auth_headers:
        encrypted_headers = database_service.encrypt_password(json.dumps(connection.auth_headers))

    return await repo.create(
        {
            "name": connection.name,
            "server_url": connection.server_url,
            "auth_headers": encrypted_headers,
            "protocol": connection.protocol
        },
        user_id=current_user.id,
        tenant_id=current_tenant.id
    )

@router.put("/mcp/{mcp_id}", response_model=schemas.MCPConnectionResponse)
async def update_mcp_connection(
    mcp_id: str,
    connection_update: schemas.MCPConnectionUpdate,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: MCPRepository = Depends(get_mcp_repo),
    access_service: AccessControlService = Depends(get_access_service)
):
    if not await access_service.has_access(current_user, mcp_id, "mcp_connection", "editor", current_tenant.id):
        raise HTTPException(status_code=403, detail="Access Denied")
        
    mcp_conn = await repo.get(mcp_id, user=current_user, tenant_id=current_tenant.id)
    if not mcp_conn:
        raise HTTPException(status_code=404, detail="MCP connection not found")

    update_data = connection_update.dict(exclude_unset=True)
    if "auth_headers" in update_data:
        update_data["auth_headers"] = database_service.encrypt_password(json.dumps(update_data.pop("auth_headers")))
        
    return await repo.update(mcp_conn, update_data)

@router.post("/mcp/test")
async def test_mcp_connection(
    connection: schemas.MCPConnectionCreate,
    current_user: models.User = Depends(get_current_active_user)
):
    """Test MCP connection without saving it"""
    try:
        # Determine auth headers
        auth_headers = connection.auth_headers if connection.auth_headers else {}
        
        # Test connection by fetching tools
        tools = await mcp_service.connect_and_fetch_tools(connection.server_url, auth_headers, connection.protocol)
        
        tool_count = len(tools)
        return {
            "status": "success", 
            "message": f"Connection successful! Found {tool_count} tools.",
            "tool_count": tool_count
        }
    except Exception as e:
        error_message = str(e)
        return {
            "status": "failed", 
            "message": f"Connection failed: {error_message}"
        }

@router.get("/mcp", response_model=List[schemas.MCPConnectionResponse])
async def get_mcp_connections(
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: MCPRepository = Depends(get_mcp_repo),
    access_service: AccessControlService = Depends(get_access_service)
):
    all_connections = await repo.get_all(user=current_user, tenant_id=current_tenant.id)
    
    # Filter by access
    allowed_connections = []
    for conn in all_connections:
        if await access_service.has_access(
            user=current_user, 
            resource_id=conn.id, 
            resource_type="mcp_connection", 
            required_level="viewer",
            tenant_id=current_tenant.id
        ):
            allowed_connections.append(conn)
            
    return allowed_connections

@router.post("/mcp/{mcp_id}/sync", response_model=schemas.MCPConnectionResponse)
async def sync_mcp_connection(
    mcp_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: MCPRepository = Depends(get_mcp_repo),
    access_service: AccessControlService = Depends(get_access_service)
):
    if not await access_service.has_access(current_user, mcp_id, "mcp_connection", "editor", current_tenant.id):
        raise HTTPException(status_code=403, detail="Access Denied")
        
    mcp_conn = await repo.get(mcp_id, user=current_user, tenant_id=current_tenant.id)
    if not mcp_conn:
        raise HTTPException(status_code=404, detail="MCP connection not found")

    # Decrypt headers
    auth_headers = {}
    if mcp_conn.auth_headers:
        try:
            auth_headers = json.loads(database_service.decrypt_password(mcp_conn.auth_headers))
        except: pass

    # Fetch Tools
    tools = await mcp_service.connect_and_fetch_tools(mcp_conn.server_url, auth_headers, mcp_conn.protocol)
    mcp_conn.tools_metadata = tools

    # Summarize with first LLM config
    llm_result = await db.execute(select(models.LLMConfiguration).where(models.LLMConfiguration.user_id == current_user.id))
    llm_config = llm_result.scalars().first()
    if llm_config:
        mcp_conn.summary = await mcp_service.summarize_tools(tools, llm_config)

    await db.commit()
    await db.refresh(mcp_conn)
    return mcp_conn

@router.delete("/mcp/{mcp_id}")
async def delete_mcp_connection(
    mcp_id: str,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    repo: MCPRepository = Depends(get_mcp_repo),
    access_service: AccessControlService = Depends(get_access_service)
):
    if not await access_service.has_access(current_user, mcp_id, "mcp_connection", "admin", current_tenant.id):
        raise HTTPException(status_code=403, detail="Access Denied")
        
    mcp_conn = await repo.get(mcp_id, user=current_user, tenant_id=current_tenant.id)
    if not mcp_conn:
        raise HTTPException(status_code=404, detail="MCP connection not found")
        
    await repo.delete(mcp_conn)
    return {"status": "success"}
