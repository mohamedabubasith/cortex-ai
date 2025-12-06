"""LLM Service for Chat - Handles streaming chat completions"""
import logging
import asyncio
from typing import AsyncGenerator, Dict
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

from app.services.tools_service import tools_service
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
            if agent.system_prompt:
                full_messages.append({"role": "system", "content": agent.system_prompt})
            full_messages.extend(messages)
            
            # Get available tools
            tools = tools_service.get_tool_definitions()
            
            # Loop for handling tool calls (max depth 5)
            for _ in range(5):
                # Count input tokens (approximation)
                input_text = " ".join([str(m.get("content", "")) for m in full_messages])
                input_tokens = int(len(input_text.split()) * 1.3)
                
                logger.info(f"Sending request to {agent.llm_config.model} with {len(tools)} tools")
                
                # Create stream
                stream = await client.chat.completions.create(
                    model=agent.llm_config.model,
                    messages=full_messages,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                    stream=True
                )
                
                tool_calls = []
                output_text = ""
                
                async for chunk in stream:
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
                    
                    # Handle Content
                    if delta.content:
                        content = delta.content
                        output_text += content
                        yield content
                        
                        # Tiny backpressure
                        if chunk_count % 100 == 0:
                            await asyncio.sleep(0.001)
                
                # If no tool calls, we are done
                if not tool_calls:
                    # Calculate output tokens
                    output_tokens = int(len(output_text.split()) * 1.3)
                    self.last_token_usage = {
                        "prompt_tokens": input_tokens,
                        "completion_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens
                    }
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
                    
                    # Optional: notify user about tool execution?
                    # yield f"\n\n[Using tool: {func_name}]" 
                    
                    tool_result = await tools_service.execute_tool(func_name, func_args)
                    
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
