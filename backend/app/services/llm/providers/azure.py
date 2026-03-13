from typing import Dict, Any, Optional, List
from openai import AsyncAzureOpenAI
from fastapi import HTTPException
from .base import BaseLLMProvider

# Azure deployments can't be listed via API — return common deployment names as hints
_AZURE_COMMON_MODELS = [
    {"id": "gpt-4o",           "name": "GPT-4o"},
    {"id": "gpt-4o-mini",      "name": "GPT-4o Mini"},
    {"id": "gpt-4",            "name": "GPT-4"},
    {"id": "gpt-4-turbo",      "name": "GPT-4 Turbo"},
    {"id": "gpt-35-turbo",     "name": "GPT-3.5 Turbo"},
    {"id": "gpt-35-turbo-16k", "name": "GPT-3.5 Turbo 16k"},
]

_API_VERSION = "2024-02-15-preview"

class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI Provider implementation."""

    def _client(self, api_key: str, base_url: str, timeout: float = 30.0) -> AsyncAzureOpenAI:
        if not base_url:
            raise HTTPException(status_code=400, detail="Azure OpenAI requires a Base URL (your Azure Endpoint).")
        return AsyncAzureOpenAI(
            api_key=api_key,
            api_version=_API_VERSION,
            azure_endpoint=base_url,
            timeout=timeout
        )

    async def list_models(self, api_key: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        # Azure Management API requires a different auth flow; return common deployment names instead.
        # The user enters the deployment name as their "model" — these are just suggestions.
        return _AZURE_COMMON_MODELS

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
            if tools and ("tool_choice" in str(e) or "tool choice" in str(e).lower()):
                kwargs["tool_choice"] = None
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
                "message": f"Connection successful! Deployment '{model}' is accessible.",
                "test_response": response.choices[0].message.content if response.choices else None
            }
        except Exception as e:
            self._handle_error(e, model)

    def _handle_error(self, e: Exception, model: str):
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            raise HTTPException(status_code=401, detail="API key is invalid or expired")
        elif "404" in error_msg or "ResourceNotFound" in error_msg:
            raise HTTPException(status_code=404, detail=f"Deployment '{model}' or endpoint not found")
        else:
            raise HTTPException(status_code=400, detail=f"Azure OpenAI connection failed: {error_msg}")
