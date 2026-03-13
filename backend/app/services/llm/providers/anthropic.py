from typing import Dict, Any, Optional, AsyncGenerator, List
import json
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from .base import BaseLLMProvider

# Hardcoded fallback in case the API call fails
_ANTHROPIC_MODELS = [
    {"id": "claude-opus-4-6",            "name": "Claude Opus 4.6"},
    {"id": "claude-sonnet-4-6",          "name": "Claude Sonnet 4.6"},
    {"id": "claude-haiku-4-5-20251001",  "name": "Claude Haiku 4.5"},
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
    {"id": "claude-3-5-haiku-20241022",  "name": "Claude 3.5 Haiku"},
    {"id": "claude-3-opus-20240229",     "name": "Claude 3 Opus"},
]

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Provider implementation."""

    def _client(self, api_key: str, base_url: Optional[str] = None, timeout: float = 30.0) -> AsyncAnthropic:
        kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            kwargs["base_url"] = base_url
        return AsyncAnthropic(**kwargs)

    async def list_models(self, api_key: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        try:
            client = self._client(api_key, base_url)
            response = await client.models.list()
            return [{"id": m.id, "name": getattr(m, "display_name", m.id)} for m in response.data]
        except Exception:
            # Anthropic SDK may not support list on all accounts — return known models
            return _ANTHROPIC_MODELS

    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ) -> AsyncGenerator:
        client = self._client(api_key, base_url, timeout)

        anthropic_tools = []
        if tools:
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    anthropic_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description"),
                        "input_schema": func.get("parameters")
                    })

        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt += msg["content"] + "\n"
            else:
                filtered_messages.append(msg)

        kwargs = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": 4096,
            "stream": True,
        }
        if system_prompt:
            kwargs["system"] = system_prompt.strip()
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        stream = await client.messages.create(**kwargs)

        async for chunk in stream:
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "text_delta":
                    yield self._mock_openai_chunk(content=chunk.delta.text)

    def _mock_openai_chunk(self, content: str = None):
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

    async def test_connection(self, api_key: str, model: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        try:
            client = self._client(api_key, base_url)
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
        if "401" in error_msg or "authentication_error" in error_msg:
            raise HTTPException(status_code=401, detail="API key is invalid or expired")
        elif "403" in error_msg or "permission_error" in error_msg:
            raise HTTPException(status_code=403, detail=f"API key doesn't have access to model '{model}'")
        elif "404" in error_msg or "not_found_error" in error_msg:
            raise HTTPException(status_code=404, detail=f"Model '{model}' not found")
        else:
            raise HTTPException(status_code=400, detail=f"Anthropic connection failed: {error_msg}")
