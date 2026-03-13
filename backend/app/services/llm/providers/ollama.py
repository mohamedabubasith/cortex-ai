from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from fastapi import HTTPException
from .base import BaseLLMProvider, flatten_system_messages
import httpx

class OllamaProvider(BaseLLMProvider):
    """Ollama Provider implementation (OpenAI compatible)."""

    def _endpoints(self, base_url: Optional[str]):
        openai_base = base_url if base_url else "http://localhost:11434/v1"
        ollama_base = openai_base.rstrip("/").removesuffix("/v1")
        return openai_base, ollama_base

    async def list_models(self, api_key: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        _, ollama_base = self._endpoints(base_url)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{ollama_base}/api/tags")
                response.raise_for_status()
                data = response.json()
            return [{"id": m["name"], "name": m["name"]} for m in data.get("models", [])]
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Could not connect to Ollama at {ollama_base}. Is it running?")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to list Ollama models: {str(e)}")

    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ):
        openai_base, _ = self._endpoints(base_url)
        client = AsyncOpenAI(
            api_key=api_key if api_key else "ollama",
            base_url=openai_base,
            timeout=timeout
        )
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
            # Retry without tool_choice for Ollama without --enable-auto-tool-choice
            if tools and ("tool_choice" in err or "tool choice" in err):
                kwargs["tool_choice"] = None
                try:
                    return await client.chat.completions.create(**kwargs)
                except Exception as e2:
                    err = str(e2).lower()
            # Retry without system role for models that don't support it
            if "system role" in err or ("system" in err and "not supported" in err):
                kwargs["messages"] = flatten_system_messages(kwargs["messages"])
                return await client.chat.completions.create(**kwargs)
            raise

    async def test_connection(self, api_key: str, model: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        try:
            openai_base, _ = self._endpoints(base_url)
            client = AsyncOpenAI(
                api_key=api_key if api_key else "ollama",
                base_url=openai_base
            )
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return {
                "status": "success",
                "message": f"Ollama connection successful! Model '{model}' is accessible.",
                "test_response": response.choices[0].message.content if response.choices else None
            }
        except Exception as e:
            self._handle_error(e, model, base_url)

    def _handle_error(self, e: Exception, model: str, base_url: Optional[str] = None):
        error_msg = str(e)
        if "Connection refused" in error_msg or "ConnectError" in error_msg:
            raise HTTPException(status_code=503, detail="Could not connect to Ollama. Is it running?")
        elif "404" in error_msg:
            raise HTTPException(status_code=404, detail=f"Model '{model}' not found. Try: ollama pull {model}")
        else:
            raise HTTPException(status_code=400, detail=f"Ollama connection failed: {error_msg}")
