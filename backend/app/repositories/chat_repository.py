from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import ChatSession, Message
from app.repositories.base_repository import BaseRepository

class ChatRepository(BaseRepository[ChatSession]):
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        return await self.get(session_id)

    async def create_session(self, session_id: str, agent_id: str) -> ChatSession:
        return await self.create({"id": session_id, "agent_id": agent_id})

    async def add_message(self, session_id: str, role: str, content: str) -> Message:
        message = Message(session_id=session_id, role=role, content=content)
        self.db.add(message)
        await self.db.commit()
        return message

    async def get_history(self, session_id: str) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        return result.scalars().all()
    
    async def get_sessions_by_agent(self, agent_id: str, limit: int = 50) -> List[ChatSession]:
        """Get all chat sessions for an agent with messages eagerly loaded"""
        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.agent_id == agent_id)
            .order_by(ChatSession.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_session_with_messages(self, session_id: str) -> Optional[ChatSession]:
        """Get a session with all its messages"""
        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages"""
        session = await self.get_session(session_id)
        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True
        return False
