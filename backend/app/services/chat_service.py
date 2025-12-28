from typing import List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models import models
from app.repositories.chat_repository import ChatRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.llm_service import llm_service
from app.services.kb_service import KBService
from app.repositories.kb_repository import KBRepository
from app.repositories.agent_audit_repository import AgentAuditLogRepository
from app.services.agent_audit_service import AgentAuditService
import logging
import tiktoken
import time
from app.core.utils import count_tokens

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession):
        self.chat_repo = ChatRepository(models.ChatSession, db)
        self.agent_repo = AgentRepository(models.Agent, db)
        self.analytics_repo = AnalyticsRepository(db)
        # Initialize Agent Audit Service
        audit_repo = AgentAuditLogRepository(db)
        self.audit_service = AgentAuditService(audit_repo)
        self.db = db

    def _count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        return count_tokens(text, model)

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

    async def create_new_session(self, agent_id: str) -> str:
        """Create a new chat session and return its ID"""
        session_id = str(uuid.uuid4())
        await self.chat_repo.create_session(session_id, agent_id)
        return session_id

    async def get_session(self, session_id: str) -> models.ChatSession:
        """Get a chat session by ID"""
        return await self.chat_repo.get_session(session_id)

    async def process_chat(self, agent: models.Agent, message: str, session_id: str) -> AsyncGenerator[str, None]:
        try:
            # 0. Validate Agent Config
            if not agent.llm_config:
                yield "Error: This agent has no LLM configuration linked. Please configure an LLM for this agent."
                return

            # 1. Manage Session - Session ID must be provided by caller
            if not session_id:
                yield "Error: Session ID is required."
                return
            
            # Check if it's a new session (no messages yet) to add first message
            history = await self.chat_repo.get_history(session_id)
            is_new_session = len(history) == 0
            
            # Add first message to history if it's a new session
            if is_new_session and agent.first_message:
                await self.chat_repo.add_message(session_id, "assistant", agent.first_message)

            # 2. Save User Message
            await self.chat_repo.add_message(session_id, "user", message)

            # 3. Get History
            history = await self.chat_repo.get_history(session_id)
            messages = [{"role": m.role, "content": m.content} for m in history]

            # 3.5 Prune History based on Context Window
            context_window = getattr(agent.llm_config, 'context_window', 128000) or 128000
            # Reserve tokens for response (e.g. 4096)
            max_input_tokens = context_window - 4096
            
            system_prompt_tokens = 0
            if agent.system_prompt:
                system_prompt_tokens = self._count_tokens(agent.system_prompt, agent.llm_config.model)
            
            current_tokens = system_prompt_tokens
            kept_messages = []
            
            # Process from newest to oldest
            for msg in reversed(messages):
                msg_content = msg.get("content", "")
                msg_tokens = self._count_tokens(msg_content, agent.llm_config.model)
                
                if current_tokens + msg_tokens > max_input_tokens:
                    # If we can't fit this message, stop adding older messages
                    # But always ensure we have at least the last message (the user query)
                    if not kept_messages:
                         kept_messages.append(msg)
                    break
                
                current_tokens += msg_tokens
                kept_messages.append(msg)
            
            # Restore order
            messages = list(reversed(kept_messages))

            # 4. RAG: Retrieve Context
            context_parts = []
            
            # Debug: Log KB selection
            logger.info(f"RAG Check: Agent ID: {agent.id}, Name: {agent.name}")
            logger.info(f"RAG Check: Linked KBs: {len(agent.knowledge_bases) if agent.knowledge_bases else 0}")
            
            if agent.knowledge_bases and agent.llm_config:
                dataset_names = [f"doc_{kb.id}" for kb in agent.knowledge_bases]
                for kb in agent.knowledge_bases:
                    logger.info(f"RAG Check: Linked KB: {kb.id} - {kb.name} (Status: {kb.status})")
                
                logger.info(f"RAG Query: Datasets: {dataset_names}, Query: {message[:50]}...")
                
                # Initialize KB Service (lightweight)
                kb_repo = KBRepository(self.db)
                kb_service = KBService(kb_repo)
                
                try:
                    # Pass the agent owner's email for proper multi-tenant filtering
                    search_result = await kb_service.query_datasets(
                        dataset_names, 
                        message, 
                        agent.llm_config,
                        user_email=agent.owner.email if agent.owner else None  # Use owner email
                    )
                    if search_result and search_result.get("success") and search_result.get("data"):
                        logger.info(f"RAG Success: Found {len(search_result['data'])} results")
                        # Format results
                        for result in search_result["data"]:
                            # Assuming result is a string or dict with 'text'
                            text = result.get("text", str(result)) if isinstance(result, dict) else str(result)
                            context_parts.append(text)
                    else:
                        logger.info(f"RAG Info: No results found for query")
                except Exception as e:
                    logger.error(f"RAG Error: {e}")
            else:
                if not agent.knowledge_bases:
                    logger.info(f"RAG Skip: No KBs linked to this agent")
                if not agent.llm_config:
                    logger.info(f"RAG Skip: No LLM config for this agent")
            
            if context_parts:
                full_context = "\n\n".join(context_parts)
                # Prepend context to the last user message for the LLM prompt
                last_msg = messages.pop()
                messages.append({"role": "user", "content": f"{full_context}\n\nUser Query: {last_msg['content']}"})

            # 5. Stream Response
            full_response = ""
            full_thinking = ""
            is_thinking = False
            start_time = time.time()
            
            async for chunk in llm_service.stream_chat(agent, messages):
                if chunk == "<THINK>":
                    is_thinking = True
                    yield chunk
                elif chunk == "</THINK>":
                    is_thinking = False
                    yield chunk
                else:
                    if is_thinking:
                        full_thinking += chunk
                    else:
                        full_response += chunk
                    yield chunk

            latency_ms = int((time.time() - start_time) * 1000)

            # 6. Save Assistant Message
            await self.chat_repo.add_message(session_id, "assistant", full_response, thinking=full_thinking if full_thinking else None)
            
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

            # 8. Log Detailed Agent Audit
            try:
                await self.audit_service.log_interaction(
                    user_id=agent.owner_id,
                    agent_id=agent.id,
                    session_id=session_id,
                    model_name=agent.llm_config.model,
                    prompt_tokens=token_usage.get("prompt_tokens", 0),
                    completion_tokens=token_usage.get("completion_tokens", 0),
                    total_tokens=token_usage.get("total_tokens", 0),
                    latency_ms=latency_ms,
                    user_message=message,
                    llm_response=full_response,
                    rag_context={"context_parts": context_parts} if context_parts else None,
                    status="success"
                )
            except Exception as audit_err:
                logger.error(f"Failed to log agent audit: {audit_err}")
            
        except Exception as e:
            logger.error(f"Error in process_chat: {e}")
            # Log failure if we have enough info
            try:
                if agent and session_id:
                    await self.audit_service.log_interaction(
                        user_id=agent.owner_id,
                        agent_id=agent.id,
                        session_id=session_id,
                        model_name=agent.llm_config.model if agent.llm_config else "unknown",
                        user_message=message,
                        status="error",
                        error_message=str(e)
                    )
            except:
                pass
            yield f"Error: An internal error occurred: {str(e)}"
