from typing import List, AsyncGenerator
import re
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

    async def process_chat(self, agent: models.Agent, message: str, session_id: str, search_enabled: bool = True, kb_enabled: bool = True, db_enabled: bool = True) -> AsyncGenerator[str, None]:
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

            # 4. RAG & Web Search: Retrieve Context
            context_parts = []
            
            # --- WEB SEARCH (PRE-SEARCH ARCHITECTURE) ---
            web_search_context = ""
            if search_enabled:
                # 4.1 Intent Detection
                # Check for URLs first
                url_patterns = [r'https?://[^\s<>"]+|www\.[^\s<>"]+']
                urls = []
                for pattern in url_patterns:
                    urls.extend(re.findall(pattern, message))
                
                if urls:
                    # Intent: Read specific URL
                    yield f"<READING>{urls[0][:30]}...</READING>"
                    try:
                        from app.services.search_service import search_service
                        page_content = await search_service.fetch_page_content(urls[0])
                        web_search_context = f"\n\n### WEBPAGE CONTENT ({urls[0]})\n{page_content[:5000]}"
                        logger.info(f"Pre-Read Success: Fetched {urls[0]}")
                    except Exception as e:
                        logger.error(f"Pre-Read Error: {e}")
                else:
                    # Intent: General Search
                    search_keywords = [
                        "search", "web", "internet", "current", "today", "latest", "news", 
                        "price", "rate", "stock", "weather", "who is", "what is", "how is",
                        "status", "live", "real-time", "now", "recent"
                    ]
                    needs_search = any(word in message.lower() for word in search_keywords) or len(message.split()) > 3
                    
                    if needs_search:
                        yield f"<SEARCHING>{message[:30]}...</SEARCHING>"
                        try:
                            from app.services.search_service import search_service
                            search_results = await search_service.search(message, max_results=3)
                            if search_results:
                                search_context_items = []
                                for res in search_results:
                                    search_context_items.append(f"SOURCE: {res['url']}\nTITLE: {res['title']}\nCONTENT: {res['content']}")
                                
                                web_search_context = "\n\n### WEB SEARCH RESULTS\n" + "\n---\n".join(search_context_items)
                                logger.info(f"Pre-Search Success: Found {len(search_results)} results")
                            else:
                                logger.warning(f"Pre-Search returned no results for: {message}")
                                web_search_context = "\n\n### WEB SEARCH STATUS\nSearch was attempted but returned no results. The service may be rate-limited or the query was too specific."
                        except Exception as e:
                            logger.error(f"Pre-Search Error: {e}")
                            web_search_context = f"\n\n### WEB SEARCH STATUS\nSearch failed due to an error: {str(e)}"

            # --- KNOWLEDGE BASE RAG ---
            if kb_enabled and agent.knowledge_bases and agent.llm_config:
                # ... existing KB logic ...
                kb_map = {f"doc_{kb.id}": kb.filename for kb in agent.knowledge_bases}
                dataset_names = list(kb_map.keys())
                
                kb_repo = KBRepository(self.db)
                kb_service = KBService(kb_repo)
                
                try:
                    yield f"<KB_QUERY>{message[:50]}...</KB_QUERY>"
                    search_result = await kb_service.query_datasets(
                        dataset_names, 
                        message, 
                        agent.llm_config,
                        user_email=agent.owner.email if agent.owner else None
                    )
                    if search_result and search_result.get("success") and search_result.get("data"):
                        for result in search_result["data"]:
                            # Robustly extract text and source dataset
                            # Cognee results can be dicts or objects with attributes
                            text = ""
                            source_dataset = "unknown"
                            
                            if isinstance(result, dict):
                                text = result.get("text") or result.get("content") or str(result)
                                source_dataset = result.get("belongs_to_set") or result.get("dataset_name") or "unknown"
                            else:
                                # Try attribute access for objects
                                text = getattr(result, "text", getattr(result, "content", str(result)))
                                source_dataset = getattr(result, "belongs_to_set", getattr(result, "dataset_name", "unknown"))
                            
                            filename = kb_map.get(source_dataset, "Unknown File")
                            
                            # Fallback: if we still have "Unknown File", check if the text itself contains a hint or if we only have one KB
                            if filename == "Unknown File" and len(kb_map) == 1:
                                filename = list(kb_map.values())[0]
                                
                            context_parts.append(f"SOURCE: [{filename}]\nCONTENT: {text}")
                except Exception as e:
                    logger.error(f"RAG Error: {e}")

            # --- CONTEXT INJECTION ---
            full_context = ""
            if context_parts:
                full_context += "\n\n### KNOWLEDGE BASE CONTEXT\n" + "\n\n".join(context_parts)
            
            if web_search_context:
                full_context += web_search_context

            if full_context:
                # Prepend context to the last user message
                last_msg = messages.pop()
                messages.append({
                    "role": "user", 
                    "content": f"CONTEXT INFORMATION:\n{full_context}\n\n---\nUSER QUERY: {last_msg['content']}\n\nInstruction: Use the provided context to answer the user query. If the context contains web search results, cite the URLs clearly."
                })

            # 5. Stream Response
            full_response = ""
            full_thinking = ""
            is_thinking = False
            start_time = time.time()
            # Stream from LLM
            async for chunk in llm_service.stream_chat(
                agent, 
                messages, 
                search_enabled=search_enabled,
                kb_enabled=kb_enabled,
                db_enabled=db_enabled
            ):
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
