from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from fastapi import HTTPException
from .base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    """Ollama Provider implementation (OpenAI compatible)."""
    
    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ):
        # Ollama defaults
        actual_api_key = api_key if api_key else "ollama"
        actual_base_url = base_url if base_url else "http://localhost:11434/v1"
        
        client = AsyncOpenAI(
            api_key=actual_api_key,
            base_url=actual_base_url,
            timeout=timeout
        )
        
        return await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            stream=True,
            stream_options={"include_usage": True}
        )

    async def test_connection(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # Ollama usually runs locally, often without an API key, 
            # but the OpenAI client requires one. We can use a dummy key if none provided.
            actual_api_key = api_key if api_key else "ollama"
            
            # Default Ollama URL if not provided
            actual_base_url = base_url if base_url else "http://localhost:11434/v1"
            
            client = AsyncOpenAI(
                api_key=actual_api_key,
                base_url=actual_base_url
            )
            
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            return {
                "status": "success", 
                "message": f"Ollama Connection successful! Model '{model}' is accessible.",
                "test_response": response.choices[0].message.content if response.choices else None
            }
            
        except Exception as e:
            self._handle_error(e, model)

    def _handle_error(self, e: Exception, model: str):
        error_msg = str(e)
        status_code = 400
        
        if "Connection refused" in error_msg:
            detail = "Could not connect to Ollama. Is it running?"
            status_code = 503
        elif "404" in error_msg:
            detail = f"Model '{model}' not found in Ollama. Try 'ollama pull {model}'."
            status_code = 404
        else:
            detail = f"Ollama Connection failed: {error_msg}"
        
        raise HTTPException(status_code=status_code, detail=detail)
