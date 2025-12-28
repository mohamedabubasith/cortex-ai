"""LLM Service for Chat - Handles streaming chat completions"""
import logging
import asyncio
from typing import AsyncGenerator, Dict
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

from app.services.tools_service import tools_service
from app.core.utils import extract_usage_from_chunk
import json

class LLMService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def stream_chat(self, agent, messages: list) -> AsyncGenerator[str, None]:
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
            logger.info(f"Attempting LLM request - Model: {agent.llm_config.model}, Base URL: {agent.llm_config.base_url}")
            
            client_kwargs = {"api_key": agent.llm_config.api_key, "timeout": 300.0}
            if agent.llm_config.base_url:
                client_kwargs["base_url"] = agent.llm_config.base_url
            
            client = AsyncOpenAI(**client_kwargs)
            
            # Add system prompt
            full_messages = []
            
            # Get available tools (including agent-specific database tools)
            db_connections = agent.database_connections if hasattr(agent, 'database_connections') else []
            logger.info(f"LLM Service: Found {len(db_connections)} DB connections for agent {agent.id}")
            
            # Build System Prompt using PromptService
            from app.services.prompt_service import prompt_service
            system_prompt = prompt_service.build_system_prompt(agent, db_connections)
            
            full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            tools = tools_service.get_agent_specific_tools(db_connections)
            
            # Set agent context for tool execution (database service needs to be passed from chat_service)
            from app.services.database_service import database_service
            tools_service.set_agent_context(db_connections, database_service)
            
            # Loop for handling tool calls (max depth 3 to prevent infinite loops)
            for loop_index in range(3):
                logger.info(f"Sending request to {agent.llm_config.model} (Loop {loop_index})")
                
                # Create stream
                stream = await client.chat.completions.create(
                    model=agent.llm_config.model,
                    messages=full_messages,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                    stream=True,
                    stream_options={"include_usage": True}
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
                        # Add timeout to prevent hanging
                        tool_result = await asyncio.wait_for(tools_service.execute_tool(func_name, func_args), timeout=30.0)
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

llm_service = LLMService()
