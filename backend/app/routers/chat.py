from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.auth_service import get_current_active_user
from app.services.chat_service import ChatService

router = APIRouter()

def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)

# Public Chat Endpoint
@router.get("/public/{share_token}")
async def get_public_agent_info(
    share_token: str,
    service: ChatService = Depends(get_chat_service)
):
    agent = await service.get_public_agent(share_token)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or invalid token")
    
    return schemas.PublicAgentInfo(
        name=agent.name,
        description=agent.description,
        first_message=agent.first_message
    )

@router.post("/public/{share_token}/chat")
async def public_chat(
    share_token: str,
    request: schemas.ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    agent = await service.get_public_agent(share_token)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or invalid token")
        
    return StreamingResponse(
        service.process_chat(agent, request.message, request.session_id),
        media_type="text/event-stream"
    )

# Get all sessions for a public agent
@router.get("/public/{share_token}/sessions", response_model=List[schemas.ChatSession])
async def get_public_agent_sessions(
    share_token: str,
    service: ChatService = Depends(get_chat_service)
):
    agent = await service.get_public_agent(share_token)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or invalid token")
    
    sessions = await service.get_agent_sessions(agent.id)
    return sessions

# Get messages for a specific session
@router.get("/public/{share_token}/sessions/{session_id}/messages", response_model=List[schemas.Message])
async def get_session_messages(
    share_token: str,
    session_id: str,
    service: ChatService = Depends(get_chat_service)
):
    agent = await service.get_public_agent(share_token)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or invalid token")
    
    messages = await service.get_session_messages(session_id)
    return messages

# Delete a chat session
@router.delete("/public/{share_token}/sessions/{session_id}")
async def delete_session(
    share_token: str,
    session_id: str,
    service: ChatService = Depends(get_chat_service)
):
    agent = await service.get_public_agent(share_token)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or invalid token")
    
    deleted = await service.delete_session(session_id)
    if deleted:
        return {"message": "Session deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# Admin Test Chat Endpoint
@router.post("/test/{agent_id}/chat")
async def test_chat(
    agent_id: str,
    request: schemas.ChatRequest,
    service: ChatService = Depends(get_chat_service),
    current_user: models.User = Depends(get_current_active_user)
):
    agent = await service.get_agent_for_user(agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    return StreamingResponse(
        service.process_chat(agent, request.message, request.session_id),
        media_type="text/event-stream"
    )
