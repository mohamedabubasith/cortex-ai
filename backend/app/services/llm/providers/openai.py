from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from fastapi import HTTPException
from .base import BaseLLMProvider, flatten_system_messages

# Chat-capable model name fragments (filters out embedding/audio/image models)
_CHAT_PREFIXES = ("gpt-", "o1", "o3", "o4", "chatgpt")

class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider implementation (also used for OpenAI-compatible APIs)."""

    def _client(self, api_key: str, base_url: Optional[str] = None, timeout: float = 30.0) -> AsyncOpenAI:
        kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            kwargs["base_url"] = base_url
        return AsyncOpenAI(**kwargs)

    async def list_models(self, api_key: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        try:
            client = self._client(api_key, base_url)
            response = await client.models.list()
            models = list(response.data)

            # For standard OpenAI, filter to chat-capable models only
            if not base_url:
                models = [m for m in models if any(m.id.startswith(p) for p in _CHAT_PREFIXES)]

            return sorted(
                [{"id": m.id, "name": m.id} for m in models],
                key=lambda x: x["id"]
            )
        except Exception as e:
            self._handle_error(e, "")

    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ):
        client = self._client(api_key, base_url, timeout)
        kwargs = dict(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            stream=True,
            stream_options={"include_usage": True}
        )
        try:
            return await client.chat.completions.create(**kwargs)
        except Exception as e:
            err = str(e).lower()
            # Retry without tool_choice for endpoints that don't support it
            if tools and ("tool_choice" in err or "tool choice" in err):
                kwargs["tool_choice"] = None
                try:
                    return await client.chat.completions.create(**kwargs)
                except Exception as e2:
                    err = str(e2).lower()
            # Retry without system role for models that don't support it
            if "system role" in err or "system" in err and "not supported" in err:
                kwargs["messages"] = flatten_system_messages(kwargs["messages"])
                return await client.chat.completions.create(**kwargs)
            raise

    async def test_connection(self, api_key: str, model: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        try:
            client = self._client(api_key, base_url)
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return {
                "status": "success",
                "message": f"Connection successful! Model '{model}' is accessible.",
                "test_response": response.choices[0].message.content if response.choices else None
            }
        except Exception as e:
            self._handle_error(e, model)

    def _handle_error(self, e: Exception, model: str):
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            raise HTTPException(status_code=401, detail="API key is invalid or expired")
        elif "403" in error_msg or "Forbidden" in error_msg:
            raise HTTPException(status_code=403, detail=f"API key doesn't have access to model '{model}'")
        elif "404" in error_msg:
            raise HTTPException(status_code=404, detail=f"Model '{model}' not found")
        else:
            raise HTTPException(status_code=400, detail=f"OpenAI connection failed: {error_msg}")
