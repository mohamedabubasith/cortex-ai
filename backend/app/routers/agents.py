from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.auth_service import get_current_active_user
from app.services.agent_service import AgentService

router = APIRouter()

from app.repositories.agent_repository import AgentRepository
from app.services.agent_service import AgentService
from app.services.access_control_service import AccessControlService
from app.services.auth_service import get_current_active_user, get_current_tenant

router = APIRouter()

def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(db, AgentRepository(db), AccessControlService(db))

@router.post("", response_model=schemas.Agent)
async def create_agent(
    agent: schemas.AgentCreate,
    service: AgentService = Depends(get_agent_service),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    return await service.create_agent(agent, current_user, current_tenant.id)

@router.get("", response_model=List[schemas.Agent])
async def read_agents(
    skip: int = 0,
    limit: int = 100,
    service: AgentService = Depends(get_agent_service),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    return await service.get_agents(current_user, current_tenant.id, skip, limit)

@router.get("/{agent_id}", response_model=schemas.Agent)
async def read_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    return await service.get_agent(agent_id, current_user, current_tenant.id)

@router.put("/{agent_id}", response_model=schemas.Agent)
async def update_agent(
    agent_id: str,
    agent_update: schemas.AgentUpdate,
    service: AgentService = Depends(get_agent_service),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    return await service.update_agent(agent_id, agent_update, current_user, current_tenant.id)

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    return await service.delete_agent(agent_id, current_user, current_tenant.id)

@router.post("/{agent_id}/regenerate-url", response_model=schemas.Agent)
async def regenerate_share_url(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    return await service.regenerate_share_url(agent_id, current_user, current_tenant.id)

@router.post("/{agent_id}/mcp/config")
async def update_mcp_config(
    agent_id: str,
    config: schemas.MCPConfig,
    service: AgentService = Depends(get_agent_service),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant)
):
    return await service.update_mcp_config(agent_id, config, current_user, current_tenant.id)
