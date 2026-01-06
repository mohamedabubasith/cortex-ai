from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class MCPConnection(Base):
    __tablename__ = "mcp_connections"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    server_url = Column(String, nullable=False)
    protocol = Column(String, default="sse")
    auth_headers = Column(Text, nullable=True)  # Store as encrypted JSON string
    summary = Column(Text, nullable=True)       # LLM-generated summary
    tools_metadata = Column(JSON, nullable=True) # Cached tool definitions

    # Relationship to user
    user = relationship("User", back_populates="mcp_connections")
    
    # Relationship to agents
    agents = relationship("Agent", secondary="agent_mcp_connections", back_populates="mcp_connections")
