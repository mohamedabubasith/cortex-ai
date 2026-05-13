from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.mcp_connection import MCPConnection
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# Association Tables
agent_knowledge_bases = Table(
    'agent_knowledge_bases',
    Base.metadata,
    Column('agent_id', String, ForeignKey('projects.id', ondelete="CASCADE")),
    Column('kb_id', String, ForeignKey('knowledge_bases.id', ondelete="CASCADE"))
)

agent_database_connections = Table(
    'agent_database_connections',
    Base.metadata,
    Column('agent_id', String, ForeignKey('projects.id', ondelete="CASCADE")),
    Column('db_connection_id', String, ForeignKey('database_connections.id', ondelete="CASCADE"))
)

agent_mcp_connections = Table(
    'agent_mcp_connections',
    Base.metadata,
    Column('agent_id', String, ForeignKey('projects.id', ondelete="CASCADE")),
    Column('mcp_connection_id', String, ForeignKey('mcp_connections.id', ondelete="CASCADE"))
)

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    members = relationship("TenantMember", back_populates="tenant", cascade="all, delete-orphan")
    
    # Resources
    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="tenant", cascade="all, delete-orphan")
    llm_configs = relationship("LLMConfiguration", back_populates="tenant", cascade="all, delete-orphan")
    database_connections = relationship("DatabaseConnection", back_populates="tenant", cascade="all, delete-orphan")
    database_connections = relationship("DatabaseConnection", back_populates="tenant", cascade="all, delete-orphan")
    mcp_connections = relationship("MCPConnection", back_populates="tenant", cascade="all, delete-orphan")
    groups = relationship("TenantGroup", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("TenantRole", back_populates="tenant", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"
    
    slug = Column(String, primary_key=True) # e.g. "kb.create", "agent.run"
    description = Column(String)
    category = Column(String) # "kb", "agent", "iam"

class TenantRole(Base):
    __tablename__ = "tenant_roles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    is_system_role = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="roles")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    role_id = Column(String, ForeignKey("tenant_roles.id", ondelete="CASCADE"), primary_key=True)
    permission_slug = Column(String, ForeignKey("permissions.slug", ondelete="CASCADE"), primary_key=True)
    
    role = relationship("TenantRole", back_populates="permissions")
    permission = relationship("Permission")

class TenantMember(Base):
    __tablename__ = "tenant_members"
    
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Legacy Role String (to be deprecated/migrated)
    role = Column(String, default="member") 
    
    # New RBAC Role
    role_id = Column(String, ForeignKey("tenant_roles.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="members")
    user = relationship("User", back_populates="tenant_memberships")
    tenant_role = relationship("TenantRole")

class TenantGroup(Base):
    __tablename__ = "tenant_groups"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    role_id = Column(String, ForeignKey("tenant_roles.id", ondelete="SET NULL"), nullable=True)
    
    tenant = relationship("Tenant", back_populates="groups")
    members = relationship("TenantGroupMember", back_populates="group", cascade="all, delete-orphan")
    default_role = relationship("TenantRole")

class TenantGroupMember(Base):
    __tablename__ = "tenant_group_members"
    
    group_id = Column(String, ForeignKey("tenant_groups.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("TenantGroup", back_populates="members")
    user = relationship("User")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Direct resource ownership (Legacy/Personal) - keeping for backward compatibility if needed,
    # but strictly we should move to tenant ownership.
    agents = relationship("Agent", back_populates="owner")
    llm_configs = relationship("LLMConfiguration", back_populates="owner")
    knowledge_bases = relationship("KnowledgeBase", back_populates="owner")
    database_connections = relationship("DatabaseConnection", back_populates="owner")
    mcp_connections = relationship("MCPConnection", back_populates="user")
    
    tenant_memberships = relationship("TenantMember", back_populates="user", cascade="all, delete-orphan")

class LLMConfiguration(Base):
    __tablename__ = "llm_configurations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # New
    name = Column(String)
    provider = Column(String, default="openai")
    base_url = Column(String)
    api_key = Column(String)
    model = Column(String)
    context_window = Column(Integer, default=128000)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="llm_configs")
    tenant = relationship("Tenant", back_populates="llm_configs")
    agents = relationship("Agent", back_populates="llm_config")

class Agent(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    description = Column(String)
    system_prompt = Column(Text, nullable=True, default="You are a helpful AI assistant.")
    first_message = Column(Text, nullable=True, default="Hello! How can I help you today?")
    owner_id = Column(String, ForeignKey("users.id"))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # New
    
    # Linked Resources
    llm_config_id = Column(String, ForeignKey("llm_configurations.id"), nullable=True)
    
    # MCP Config (Still per agent for now, or could be global too)
    mcp_config = Column(JSON, default={})
    
    # Shareable URL Config
    share_token = Column(String, unique=True, index=True, default=generate_uuid)
    is_public = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", back_populates="agents")
    tenant = relationship("Tenant", back_populates="agents")
    llm_config = relationship("LLMConfiguration", back_populates="agents")
    
    # Many-to-Many Relationships
    knowledge_bases = relationship("KnowledgeBase", secondary=agent_knowledge_bases, back_populates="agents")
    database_connections = relationship("DatabaseConnection", secondary=agent_database_connections, back_populates="agents")
    mcp_connections = relationship("MCPConnection", secondary=agent_mcp_connections, back_populates="agents")
    
    chat_sessions = relationship("ChatSession", back_populates="agent", cascade="all, delete-orphan")
    members = relationship("AgentMember", back_populates="agent", cascade="all, delete-orphan")

class AgentMember(Base):
    __tablename__ = "project_members"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String, default="viewer") # admin, editor, viewer
    
    agent = relationship("Agent", back_populates="members")
    user = relationship("User")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id")) 
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # New
    name = Column(String)
    filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    status = Column(String, default="queued")  # queued, parsing, chunking, embedding, indexing, completed, failed

    # RAG Config
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    embedding_model = Column(String, nullable=True)  # Snapshot of embedding model (Ollama)
    parsing_strategy = Column(String, nullable=False, default="fast")  # fast | hi_res (Unstructured)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="knowledge_bases")
    tenant = relationship("Tenant", back_populates="knowledge_bases")
    agents = relationship("Agent", secondary=agent_knowledge_bases, back_populates="knowledge_bases")
    members = relationship("KnowledgeBaseMember", back_populates="knowledge_base", cascade="all, delete-orphan")

class KnowledgeBaseMember(Base):
    __tablename__ = "knowledge_base_members"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    kb_id = Column(String, ForeignKey("knowledge_bases.id", ondelete="CASCADE"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String, default="viewer") # viewer, editor
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    knowledge_base = relationship("KnowledgeBase", back_populates="members")
    user = relationship("User")

class DatabaseConnection(Base):
    __tablename__ = "database_connections"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # New
    name = Column(String)
    type = Column(String) # postgres, mysql, mongodb
    host = Column(String)
    port = Column(Integer)
    username = Column(String)
    encrypted_password = Column(String)
    database_name = Column(String)
    ssl_mode = Column(String, default="prefer")
    
    owner = relationship("User", back_populates="database_connections")
    tenant = relationship("Tenant", back_populates="database_connections")
    agents = relationship("Agent", secondary=agent_database_connections, back_populates="database_connections")
    saved_queries = relationship("SavedQuery", back_populates="connection")

class SavedQuery(Base):
    __tablename__ = "saved_queries"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    connection_id = Column(String, ForeignKey("database_connections.id"))
    name = Column(String)
    query = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    connection = relationship("DatabaseConnection", back_populates="saved_queries")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Optional for now to avoid breaking existing? Actually should be required for auth.
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    agent = relationship("Agent", back_populates="chat_sessions")
    user = relationship("User")
    tenant = relationship("Tenant")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"))
    role = Column(String) # user, assistant, system
    content = Column(Text)
    thinking = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ChatSession", back_populates="messages")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    agent_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # New
    event_type = Column(String, nullable=False)  # chat, kb_upload, kb_query, etc.
    event_data = Column(JSON, default={})
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    agent = relationship("Agent")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # New
    action = Column(String, nullable=False)  # create, update, delete, access
    resource_type = Column(String, nullable=False)  # agent, kb, llm_config, etc.
    resource_id = Column(String, nullable=True)
    details = Column(JSON, default={})
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class AgentAuditLog(Base):
    __tablename__ = "agent_audit_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String, nullable=True)
    
    # LLM Details
    model_name = Column(String, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    
    # Input/Output
    user_message = Column(Text, nullable=True)
    llm_response = Column(Text, nullable=True)
    
    # Tool Calls
    tool_calls = Column(JSON, default=[])  # [{name, args, result}]
    
    # Context
    rag_context = Column(JSON, default={})  # KB sources used
    
    # Metadata
    ip_address = Column(String, nullable=True)
    status = Column(String, default="success")  # success, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    user = relationship("User")
    agent = relationship("Agent")

class ResourceShare(Base):
    __tablename__ = "resource_shares"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String, nullable=False)
    resource_type = Column(String, nullable=False) # agent, kb, db_connection
    grantee_id = Column(String, nullable=False) # user_id or group_id
    grantee_type = Column(String, default="user") # user, group
    permission = Column(String, default="read") # read, write, admin
    shared_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Optional relationships to help ORM if we want to eager load
    # grantee_user = relationship("User", foreign_keys=[grantee_id], primaryjoin="remote(User.id) == foreign(ResourceShare.grantee_id)", viewonly=True)
    # sharer = relationship("User", foreign_keys=[shared_by])
