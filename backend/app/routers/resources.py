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

router = APIRouter()

# MCP Hub Registry
MCP_HUB_REGISTRY = [

    {
        "id": "github",
        "name": "GitHub",
        "description": "Search repositories, manage issues, and view pull requests.",
        "icon": "Github",
        "server_url": "",
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
        "server_url": "",
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
        "server_url": "",
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
        "server_url": "",
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
        "server_url": "",
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
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    # Validation
    if not (1 <= connection.port <= 65535):
        raise HTTPException(status_code=400, detail="Port must be between 1 and 65535")
    if not connection.host.strip():
        raise HTTPException(status_code=400, detail="Host cannot be empty")
    if not connection.database_name.strip():
        raise HTTPException(status_code=400, detail="Database name cannot be empty")
    if not connection.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    encrypted_password = database_service.encrypt_password(connection.password)
    
    db_connection = models.DatabaseConnection(
        user_id=current_user.id,
        tenant_id=current_tenant.id, # Multi-tenancy
        name=connection.name,
        type=connection.type,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        encrypted_password=encrypted_password,
        database_name=connection.database_name,
        ssl_mode=connection.ssl_mode
    )
    db.add(db_connection)
    await db.commit()
    await db.refresh(db_connection)
    return db_connection

@router.get("/databases", response_model=List[schemas.DatabaseConnectionResponse])
async def get_db_connections(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    result = await db.execute(select(models.DatabaseConnection).where(models.DatabaseConnection.tenant_id == current_tenant.id))
    return result.scalars().all()

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
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    """Test an existing saved database connection by ID"""
    result = await db.execute(
        select(models.DatabaseConnection).where(
            models.DatabaseConnection.id == db_id,
            models.DatabaseConnection.tenant_id == current_tenant.id
        )
    )
    db_conn = result.scalars().first()
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    try:
        success = await database_service.test_connection(db_conn)
        if success:
            return {"status": "success", "message": "Connection successful!"}
        else:
            return {"status": "failed", "message": "Connection failed. Please check your credentials."}
    except Exception as e:
        # Handle decryption errors (e.g., when encryption key has changed)
        error_message = str(e)
        if "InvalidToken" in error_message or "Signature did not match" in error_message:
            return {
                "status": "failed", 
                "message": "Unable to decrypt password. The encryption key may have changed. Please delete and recreate this connection."
            }
        # Provide more user-friendly error messages for common database issues
        elif "password authentication failed" in error_message.lower():
            return {"status": "failed", "message": "Authentication failed. Please check your username and password."}
        elif "does not exist" in error_message.lower():
            return {"status": "failed", "message": "Database does not exist. Please check the database name."}
        elif "connection refused" in error_message.lower() or "could not connect" in error_message.lower():
            return {"status": "failed", "message": "Could not connect to database server. Please check host and port."}
        else:
            return {"status": "failed", "message": error_message if error_message else "Connection test failed. Please check your credentials."}

@router.put("/databases/{db_id}", response_model=schemas.DatabaseConnectionResponse)
async def update_db_connection(
    db_id: str,
    connection_update: schemas.DatabaseConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    """Update an existing database connection"""
    result = await db.execute(
        select(models.DatabaseConnection).where(
            models.DatabaseConnection.id == db_id,
            models.DatabaseConnection.tenant_id == current_tenant.id
        )
    )
    db_conn = result.scalars().first()
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    # Update fields if provided
    if connection_update.port is not None and not (1 <= connection_update.port <= 65535):
        raise HTTPException(status_code=400, detail="Port must be between 1 and 65535")

    if connection_update.name is not None:
        db_conn.name = connection_update.name
    if connection_update.type is not None:
        db_conn.type = connection_update.type
    if connection_update.host is not None:
        db_conn.host = connection_update.host
    if connection_update.port is not None:
        db_conn.port = connection_update.port
    if connection_update.username is not None:
        db_conn.username = connection_update.username
    if connection_update.database_name is not None:
        db_conn.database_name = connection_update.database_name
    if connection_update.ssl_mode is not None:
        db_conn.ssl_mode = connection_update.ssl_mode
    if connection_update.password is not None:
        db_conn.encrypted_password = database_service.encrypt_password(connection_update.password)
    
    await db.commit()
    await db.refresh(db_conn)
    return db_conn

@router.delete("/databases/{db_id}")
async def delete_db_connection(
    db_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    result = await db.execute(select(models.DatabaseConnection).where(models.DatabaseConnection.id == db_id, models.DatabaseConnection.tenant_id == current_tenant.id))
    db_conn = result.scalars().first()
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    

# MCP Endpoints

@router.post("/mcp", response_model=schemas.MCPConnectionResponse)
async def create_mcp_connection(
    connection: schemas.MCPConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    # Determine auth headers (encrypt if provided)
    encrypted_headers = None
    if connection.auth_headers:
        # Re-using database_service for encryption as it uses Fernet
        encrypted_headers = database_service.encrypt_password(json.dumps(connection.auth_headers))

    mcp_conn = models.MCPConnection(
        user_id=current_user.id,
        tenant_id=current_tenant.id, # Multi-tenancy
        name=connection.name,
        server_url=connection.server_url,
        auth_headers=encrypted_headers,
        protocol=connection.protocol
    )
    db.add(mcp_conn)
    await db.commit()
    await db.refresh(mcp_conn)
    return mcp_conn

@router.put("/mcp/{mcp_id}", response_model=schemas.MCPConnectionResponse)
async def update_mcp_connection(
    mcp_id: str,
    connection: schemas.MCPConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    result = await db.execute(select(models.MCPConnection).where(models.MCPConnection.id == mcp_id, models.MCPConnection.tenant_id == current_tenant.id))
    mcp_conn = result.scalars().first()
    if not mcp_conn:
        raise HTTPException(status_code=404, detail="MCP connection not found")

    if connection.name is not None:
        mcp_conn.name = connection.name
    if connection.server_url is not None:
        mcp_conn.server_url = connection.server_url
    if connection.protocol is not None:
        mcp_conn.protocol = connection.protocol
    
    if connection.auth_headers is not None:
        # Re-using database_service for encryption
        encrypted_headers = database_service.encrypt_password(json.dumps(connection.auth_headers))
        mcp_conn.auth_headers = encrypted_headers

    await db.commit()
    await db.refresh(mcp_conn)
    return mcp_conn

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
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    result = await db.execute(select(models.MCPConnection).where(models.MCPConnection.tenant_id == current_tenant.id))
    return result.scalars().all()

@router.post("/mcp/{mcp_id}/sync", response_model=schemas.MCPConnectionResponse)
async def sync_mcp_connection(
    mcp_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(models.MCPConnection).where(
            models.MCPConnection.id == mcp_id, 
            models.MCPConnection.tenant_id == current_tenant.id
        )
    )
    mcp_conn = result.scalars().first()
    if not mcp_conn:
        raise HTTPException(status_code=404, detail="MCP connection not found")

    # Decrypt headers
    auth_headers = {}
    if mcp_conn.auth_headers:
        try:
            decrypted_json = database_service.decrypt_password(mcp_conn.auth_headers)
            auth_headers = json.loads(decrypted_json)
        except Exception:
            pass # Handle decryption error gracefully or log it

    # Fetch Tools
    try:
        tools = await mcp_service.connect_and_fetch_tools(mcp_conn.server_url, auth_headers, mcp_conn.protocol)
        mcp_conn.tools_metadata = tools
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch tools: {str(e)}")

    # Summarize Tools
    # Get user's first LLM config for summarization
    llm_result = await db.execute(select(models.LLMConfiguration).where(models.LLMConfiguration.user_id == current_user.id))
    llm_config = llm_result.scalars().first()
    
    if llm_config:
        summary = await mcp_service.summarize_tools(tools, llm_config)
        mcp_conn.summary = summary
    else:
        mcp_conn.summary = "No LLM configuration found to generate summary. Please configure an LLM provider."

    await db.commit()
    await db.refresh(mcp_conn)
    return mcp_conn

@router.delete("/mcp/{mcp_id}")
async def delete_mcp_connection(
    mcp_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    result = await db.execute(select(models.MCPConnection).where(models.MCPConnection.id == mcp_id, models.MCPConnection.tenant_id == current_tenant.id))
    mcp_conn = result.scalars().first()
    if not mcp_conn:
        raise HTTPException(status_code=404, detail="MCP connection not found")
    
    await db.delete(mcp_conn)
    await db.commit()
    return {"status": "success"}
