from typing import List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models import models
from app.repositories.chat_repository import ChatRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.llm_service import llm_service
from app.services.cognee_service import cognee_service

class ChatService:
    def __init__(self, db: AsyncSession):
        self.chat_repo = ChatRepository(models.ChatSession, db)
        self.agent_repo = AgentRepository(models.Agent, db)
        self.analytics_repo = AnalyticsRepository(db)
        self.db = db

    async def get_public_agent(self, share_token: str) -> models.Agent:
        agent = await self.agent_repo.get_by_share_token(share_token)
        if not agent or not agent.is_public:
            return None
        return agent

    async def get_agent_for_user(self, agent_id: str, owner_id: str) -> models.Agent:
        return await self.agent_repo.get_by_id_and_owner(agent_id, owner_id)
    
    async def get_agent_sessions(self, agent_id: str) -> List[models.ChatSession]:
        """Get all sessions for an agent"""
        return await self.chat_repo.get_sessions_by_agent(agent_id)
    
    async def get_session_messages(self, session_id: str) -> List[models.Message]:
        """Get all messages for a session"""
        return await self.chat_repo.get_history(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        return await self.chat_repo.delete_session(session_id)

    async def process_chat(self, agent: models.Agent, message: str, session_id: str = None) -> AsyncGenerator[str, None]:
        try:
            # 0. Validate Agent Config
            if not agent.llm_config:
                yield "Error: This agent has no LLM configuration linked. Please configure an LLM for this agent."
                return

            # 1. Manage Session
            # 1. Manage Session
            new_session_created = False
            if not session_id:
                session_id = str(uuid.uuid4())
                await self.chat_repo.create_session(session_id, agent.id)
                new_session_created = True
            else:
                session = await self.chat_repo.get_session(session_id)
                if not session:
                    session_id = str(uuid.uuid4())
                    await self.chat_repo.create_session(session_id, agent.id)
                    new_session_created = True
            
            # Add first message to history if it's a new session
            if new_session_created and agent.first_message:
                await self.chat_repo.add_message(session_id, "assistant", agent.first_message)

            # 2. Save User Message
            await self.chat_repo.add_message(session_id, "user", message)

            # 3. Get History
            history = await self.chat_repo.get_history(session_id)
            messages = [{"role": m.role, "content": m.content} for m in history]

            # 4. RAG: Retrieve Context
            context_parts = []
            if agent.knowledge_bases and agent.llm_config:
                for kb in agent.knowledge_bases:
                    # Assuming dataset_name follows the convention doc_{kb.id}
                    dataset_name = f"doc_{kb.id}"
                    kb_context = await cognee_service.query(agent.llm_config, message, dataset_name)
                    if kb_context:
                        context_parts.append(kb_context)
            
            if context_parts:
                full_context = "\n\n".join(context_parts)
                # Prepend context to the last user message for the LLM prompt
                last_msg = messages.pop()
                messages.append({"role": "user", "content": f"{full_context}\n\nUser Query: {last_msg['content']}"})

            # 5. Stream Response
            full_response = ""
            async for chunk in llm_service.stream_chat(agent, messages):
                full_response += chunk
                yield chunk

            # 6. Save Assistant Message
            await self.chat_repo.add_message(session_id, "assistant", full_response)
            
            # 7. Log analytics with token usage
            token_usage = llm_service.get_last_token_usage()
            await self.analytics_repo.create_event(
                event_type="chat",
                user_id=agent.owner_id,
                agent_id=agent.id,
                event_data={
                    "session_id": session_id,
                    "message_length": len(message),
                    "response_length": len(full_response),
                    "tokens": token_usage
                },
                meta_data={
                    "model": agent.llm_config.model,
                    "has_kb": len(agent.knowledge_bases) > 0 if agent.knowledge_bases else False
                }
            )
            
        except Exception as e:
            print(f"Error in process_chat: {e}")
            yield f"Error: An internal error occurred: {str(e)}"
