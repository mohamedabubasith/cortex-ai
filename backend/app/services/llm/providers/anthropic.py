from typing import Dict, Any, Optional, AsyncGenerator
import json
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from .base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Provider implementation."""
    
    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ) -> AsyncGenerator:
        # Anthropic doesn't use base_url typically, but we accept it
        client_kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        client = AsyncAnthropic(**client_kwargs)
        
        # Convert tools to Anthropic format if necessary
        # Anthropic uses a different tool format, we might need a converter
        # For now, assuming tools are passed in OpenAI format and might need conversion
        # or relying on libraries to handle it. 
        # But this basic implementation focuses on chat.
        
        anthropic_tools = []
        if tools:
            for tool in tools:
                # Basic conversion from OpenAI tool format to Anthropic
                # OpenAI: {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}
                # Anthropic: {"name": "...", "description": "...", "input_schema": {...}}
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    anthropic_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description"),
                        "input_schema": func.get("parameters")
                    })

        system_prompt = ""
        filtered_messages = []
        
        # Extract system prompt as Anthropic passes it separately
        for msg in messages:
            if msg["role"] == "system":
                system_prompt += msg["content"] + "\n"
            else:
                filtered_messages.append(msg)

        kwargs = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": 4096, # Required parameter for Anthropic
            "stream": True,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt.strip()
            
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        stream = await client.messages.create(**kwargs)

        # Yield in a format compatible with our LLMService (OpenAI-like chunks)
        # We need to wrap Anthropic chunks to look like OpenAI chunks for the service to consume
        async for chunk in stream:
            if chunk.type == "message_start":
                # Initial message metadata
                pass
            elif chunk.type == "content_block_start":
                # Start of a content block (text or tool_use)
                pass
            elif chunk.type == "content_block_delta":
                if chunk.delta.type == "text_delta":
                    # Emit text content
                     yield self._mock_openai_chunk(content=chunk.delta.text)
                elif chunk.delta.type == "input_json_delta":
                    # Emit partial tool arguments
                    # We might need to track the current tool use ID from content_block_start
                    # For simplicity in this streaming wrapper, getting exact parity is complex
                    # Just yielding partial args if we can, but LLMService expects typical structure
                    pass 
            elif chunk.type == "message_delta":
                # Usage, stop reason etc
                pass
            
            # FIXME: Full tool support in streaming for Anthropic requires more complex state management 
            # to reconstruct the 'tool_calls' structure expected by LLMService.
            # This is a basic text streaming implementation.
            
    def _mock_openai_chunk(self, content: str = None):
        """Helper to create an object that looks like an OpenAI chunk"""
        class Delta:
            def __init__(self, content):
                self.content = content
                self.tool_calls = None
                self.reasoning_content = None

        class Choice:
            def __init__(self, content):
                self.delta = Delta(content)

        class Chunk:
            def __init__(self, content):
                self.choices = [Choice(content)]

        return Chunk(content)

    async def test_connection(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            
            client = AsyncAnthropic(**client_kwargs)
            
            response = await client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            
            return {
                "status": "success", 
                "message": f"Connection successful! Model '{model}' is accessible.",
                "test_response": response.content[0].text
            }
            
        except Exception as e:
            self._handle_error(e, model)
            
    def _handle_error(self, e: Exception, model: str):
        error_msg = str(e)
        status_code = 400
        
        if "401" in error_msg or "authentication_error" in error_msg:
            detail = "API key is invalid or expired"
            status_code = 401
        elif "403" in error_msg or "permission_error" in error_msg:
            detail = f"API key doesn't have access to model '{model}'"
            status_code = 403
        elif "404" in error_msg or "not_found_error" in error_msg:
            detail = f"Model '{model}' not found"
            status_code = 404
        else:
            detail = f"Anthropic Connection failed: {error_msg}"
        
        raise HTTPException(status_code=status_code, detail=detail)
