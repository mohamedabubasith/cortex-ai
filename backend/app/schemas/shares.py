from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
import uuid

class ResourceShareBase(BaseModel):
    resource_id: str
    resource_type: Literal['agent', 'kb', 'db_connection', 'mcp_connection', 'llm_config']
    grantee_id: str
    grantee_type: Literal['user', 'group'] = 'user'
    permission: Literal['read', 'write', 'admin'] = 'read'

class ResourceShareCreate(ResourceShareBase):
    pass

class ResourceShareResponse(ResourceShareBase):
    id: str
    tenant_id: str
    shared_by: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
