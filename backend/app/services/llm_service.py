"""LLM Service for Chat - Handles streaming chat completions"""
import logging
import asyncio
from typing import AsyncGenerator, Dict
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

from app.models.models import LLMConfiguration
from app.services.tools_service import tools_service
from app.core.utils import extract_usage_from_chunk
import json

class LLMService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def stream_chat(self, agent, messages: list, search_enabled: bool = True, kb_enabled: bool = True, db_enabled: bool = True) -> AsyncGenerator[str, None]:
        """Stream chat completion from LLM with token tracking, robust error handling, and tool support"""
        chunk_count = 0
        
        try:
            # Validate agent configuration
            if not agent.llm_config:
                logger.error("No LLM configuration found for agent")
                yield "Error: Agent has no LLM configuration"
                return
            
            if not agent.llm_config.api_key:
                logger.error("No API key configured")
                yield "Error: No API key configured for this agent"
                return
            
            # Log configuration (without revealing full key)
            logger.info(f"Attempting LLM request - Model: {agent.llm_config.model}, Provider: {agent.llm_config.provider}")
            
            # --- MODULAR PROVIDER USAGE ---
            from app.services.llm.factory import LLMProviderFactory
            
            # Get provider from config (default to openai if missing)
            provider_type = getattr(agent.llm_config, 'provider', 'openai')
            provider = LLMProviderFactory.get_provider(provider_type)
            
            # Add system prompt
            full_messages = []
            
            # Get available tools (including agent-specific database tools and MCP tools)
            db_connections = agent.database_connections if hasattr(agent, 'database_connections') else []
            mcp_connections = agent.mcp_connections if hasattr(agent, 'mcp_connections') else []
            
            logger.info(f"LLM Service: Found {len(db_connections)} DB connections and {len(mcp_connections)} MCP connections for agent {agent.id}")
            
            # Build System Prompt using PromptService
            from app.services.prompt_service import prompt_service
            system_prompt = prompt_service.build_system_prompt(agent, db_connections, search_enabled=search_enabled, kb_enabled=kb_enabled, db_enabled=db_enabled)
            logger.info(f"LLM Service: search_enabled={search_enabled} for agent {agent.id}")
            
            full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            tools = tools_service.get_agent_specific_tools(db_connections, mcp_connections, search_enabled=search_enabled, db_enabled=db_enabled)
            
            # Set agent context for tool execution (database service needs to be passed from chat_service)
            from app.services.database_service import database_service
            tools_service.set_agent_context(db_connections, mcp_connections, database_service)
            
            # Loop for handling tool calls (max depth 10 to allow complex chains)
            MAX_LOOPS = 10
            for loop_index in range(MAX_LOOPS):
                logger.info(f"Sending request to {agent.llm_config.model} (Loop {loop_index})")
                
                # Create stream via Provider
                stream = await provider.chat(
                    api_key=agent.llm_config.api_key,
                    model=agent.llm_config.model,
                    messages=full_messages,
                    tools=tools if tools else None,
                    base_url=agent.llm_config.base_url
                )
                
                tool_calls = []
                output_text = ""
                has_started_thinking = False
                
                async for chunk in stream:
                    # Capture Usage data if available (robust extraction)
                    usage_data = extract_usage_from_chunk(chunk)
                    if usage_data:
                        self.last_token_usage = usage_data
                        continue

                    if not hasattr(chunk, 'choices') or not chunk.choices:
                        continue

                    chunk_count += 1
                    delta = chunk.choices[0].delta
                    
                    # Handle Tool Calls
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            if tc.index is not None:
                                if len(tool_calls) <= tc.index:
                                    tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                
                                if tc.id:
                                    tool_calls[tc.index]["id"] += tc.id
                                if tc.function:
                                    if tc.function.name:
                                        tool_calls[tc.index]["function"]["name"] += tc.function.name
                                    if tc.function.arguments:
                                        tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments
                    
                    # Handle Reasoning/Thinking
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        if not has_started_thinking:
                            yield "<THINK>"
                            has_started_thinking = True
                        yield delta.reasoning_content

                    # Handle Content
                    if delta.content:
                        if has_started_thinking:
                            yield "</THINK>"
                            has_started_thinking = False
                        
                        content = delta.content
                        output_text += content
                        yield content
                        
                        # Tiny backpressure
                        if chunk_count % 100 == 0:
                            await asyncio.sleep(0.001)
                
                # Final check to close thinking tag
                if has_started_thinking:
                    yield "</THINK>"
                
                # If no tool calls, we are done
                if not tool_calls:
                    break
                
                # If we have tool calls, execute them and continue loop
                
                # 1. Append assistant message with tool calls
                full_messages.append({
                    "role": "assistant",
                    "content": output_text if output_text else None,
                    "tool_calls": tool_calls
                })
                
                # 2. Execute tools and append results
                for tc in tool_calls:
                    func_name = tc["function"]["name"]
                    func_args = tc["function"]["arguments"]
                    
                    logger.info(f"Executing tool: {func_name} with args: {func_args}")
                    
                    # Execute tool (No visible output to user)
                    try:
                        logger.info(f"Calling tools_service.execute_tool for {func_name}...")
                        
                        # Yield status markers for web tools
                        if func_name in ["web_search", "website_reader"]:
                            if not search_enabled:
                                logger.warning(f"Model tried to call {func_name} but search is DISABLED. Blocking.")
                                tool_result = json.dumps({"error": f"Tool '{func_name}' is currently disabled for this chat. Please enable Web Search if you need internet access."})
                                full_messages.append({
                                    "tool_call_id": tc["id"],
                                    "role": "tool",
                                    "name": func_name,
                                    "content": tool_result
                                })
                                continue

                        if func_name == "web_search":
                            # Extract query if possible from arguments
                            try:
                                args = json.loads(func_args)
                                yield f"<SEARCHING>{args.get('query', 'web')}...</SEARCHING>"
                            except:
                                yield "<SEARCHING>web...</SEARCHING>"
                        elif func_name == "website_reader":
                            try:
                                args = json.loads(func_args)
                                yield f"<READING>{args.get('url', 'page')}...</READING>"
                            except:
                                yield "<READING>page...</READING>"

                        # Add timeout to prevent hanging
                        tool_result = await asyncio.wait_for(tools_service.execute_tool(func_name, func_args), timeout=30.0)
                        logger.info(f"Tool {func_name} execution completed. Result length: {len(tool_result)}")
                    except asyncio.TimeoutError:
                        logger.error(f"Tool {func_name} timed out")
                        tool_result = json.dumps({"error": "Tool execution timed out (30s limit)."})
                    except Exception as e:
                        logger.error(f"Tool {func_name} failed: {e}")
                        tool_result = json.dumps({"error": f"Tool execution failed: {str(e)}"})
                    
                    full_messages.append({
                        "tool_call_id": tc["id"],
                        "role": "tool",
                        "name": func_name,
                        "content": tool_result
                    })
                
                # Loop continues to send tool results back to LLM
            
            # Check if we exited due to max loops
            if loop_index == MAX_LOOPS - 1:
                logger.warning(f"LLM reached max loop depth ({MAX_LOOPS}). Terminating chain.")
                yield f"\n\n[System Note: Agent stopped after {MAX_LOOPS} steps to prevent infinite loops. The task might be too complex or the agent got stuck.]"
                    
        except asyncio.TimeoutError:
            error_msg = "Request timed out - response took too long"
            logger.error(f"LLM timeout: {error_msg}")
            yield f"\n\nError: {error_msg}"
            self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM streaming error: {error_msg}")
            
            if "401" in error_msg or "Unauthorized" in error_msg:
                yield "\n\nError: Authentication failed. Please check your API key."
            elif "403" in error_msg or "Forbidden" in error_msg:
                yield f"\n\nError: Access denied to model '{agent.llm_config.model}'."
            elif "404" in error_msg:
                yield "\n\nError: Model not found."
            elif "429" in error_msg:
                yield "\n\nError: Rate limit exceeded."
            else:
                yield f"\n\nError: {error_msg}"
            
            self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def get_last_token_usage(self) -> Dict[str, int]:
        """Get token usage from last request"""
        return getattr(self, 'last_token_usage', {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

    async def reformulate_query(self, query: str, llm_config: LLMConfiguration) -> str:
        """
        Rewrite query for better RAG retrieval.
        """
        try:
            prompt = f"""You are an AI search optimizer. Rewrite the following user query to be more effective for vector database retrieval.
            - Remove conversational filler ("hello", "please").
            - Focus on identifying key entities and technical terms.
            - If it's a question, phrase it as a statement or a keyword-rich query.
            - Output ONLY the rewritten query, nothing else.

            User Query: {query}
            Rewritten Query:"""
            
            rewritten = await self.generate_text(prompt, llm_config)
            cleaned = rewritten.strip().replace('"', '').replace("'", "")
            logger.info(f"Query Reformulation: '{query}' -> '{cleaned}'")
            return cleaned
        except Exception as e:
            logger.warning(f"Query reformulation failed: {e}. Using original query.")
            return query

    async def generate_text(self, prompt: str, llm_config: LLMConfiguration) -> str:
        """Generate a single text response (non-streaming usage)"""
        try:
            from app.services.llm.factory import LLMProviderFactory
            
            provider_type = getattr(llm_config, 'provider', 'openai')
            provider = LLMProviderFactory.get_provider(provider_type)
            
            messages = [{"role": "user", "content": prompt}]
            
            # Using stream method and collecting result for simplicity as providers implement stream
            stream = await provider.chat(
                api_key=llm_config.api_key,
                model=llm_config.model,
                messages=messages,
                base_url=llm_config.base_url
            )
            
            response_text = ""
            async for chunk in stream:
                 # Check for choices and delta in standard OpenAI format or similar
                 if hasattr(chunk, 'choices') and chunk.choices:
                     delta = chunk.choices[0].delta
                     if delta.content:
                         response_text += delta.content
            
            return response_text
        except Exception as e:
            logger.error(f"Generate text failed: {e}")
            raise e

llm_service = LLMService()
