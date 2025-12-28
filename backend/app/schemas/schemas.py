from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# LLM Configuration Schemas
class LLMConfigurationBase(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str

class LLMConfigurationCreate(LLMConfigurationBase):
    pass

class LLMConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None

class LLMConfiguration(LLMConfigurationBase):
    id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Knowledge Base Schemas
class KnowledgeBaseBase(BaseModel):
    name: Optional[str] = None
    filename: str
    status: str

class KnowledgeBase(KnowledgeBaseBase):
    id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class KBQueryRequest(BaseModel):
    query: str
    llm_config_id: str
    dataset_names: Optional[List[str]] = []

# Database Schemas
class DatabaseConnectionBase(BaseModel):
    name: str
    type: str
    host: str
    port: int
    username: str
    database_name: str
    ssl_mode: Optional[str] = "prefer"

class DatabaseConnectionCreate(DatabaseConnectionBase):
    password: str

class DatabaseConnectionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: Optional[str] = None
    ssl_mode: Optional[str] = None

class DatabaseConnectionResponse(DatabaseConnectionBase):
    id: str
    user_id: str
    
    class Config:
        from_attributes = True

# Agent Schemas
class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = "You are a helpful AI assistant."
    first_message: Optional[str] = "Hello! How can I help you today?"
    llm_config_id: Optional[str] = None
    mcp_config: Optional[dict] = None
    is_public: Optional[bool] = True

class AgentCreate(AgentBase):
    kb_ids: Optional[List[str]] = []
    db_connection_ids: Optional[List[str]] = []

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    first_message: Optional[str] = None
    llm_config_id: Optional[str] = None
    kb_ids: Optional[List[str]] = None
    db_connection_ids: Optional[List[str]] = None
    mcp_config: Optional[dict] = None
    is_public: Optional[bool] = None

class Agent(AgentBase):
    id: str
    owner_id: str
    share_token: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Expanded details
    llm_config: Optional[LLMConfiguration] = None
    knowledge_bases: List[KnowledgeBase] = []
    database_connections: List[DatabaseConnectionResponse] = []
    
    class Config:
        from_attributes = True

# Chat Schemas
class MessageBase(BaseModel):
    role: str
    content: str
    thinking: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    agent_id: str

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: str
    created_at: datetime
    messages: List[Message] = []
    
    class Config:
        from_attributes = True

# LLM Request Schema
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class LLMConfigCheck(BaseModel):
    llm_base_url: str
    llm_api_key: str

class LLMConnectionTestRequest(BaseModel):
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None

# MCP Schemas
class MCPConfig(BaseModel):
    server_url: str

class SearchQuery(BaseModel):
    query: str
    enabled: bool = True

class QueryExecutionRequest(BaseModel):
    query: str

class SavedQueryBase(BaseModel):
    name: str
    query: str

class SavedQueryCreate(SavedQueryBase):
    pass

class SavedQuery(SavedQueryBase):
    id: str
    connection_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PublicAgentInfo(BaseModel):
    name: str
    description: Optional[str] = None
    first_message: Optional[str] = None
    has_kb: bool = False

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class NewPassword(BaseModel):
    token: str
    new_password: str

class AnalyticsEvent(BaseModel):
    id: str
    event_type: str
    event_data: Optional[dict] = {}
    meta_data: Optional[dict] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True
