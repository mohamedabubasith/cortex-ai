from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from fastapi import HTTPException
from .base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider implementation."""
    
    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ):
        client_kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        client = AsyncOpenAI(**client_kwargs)
        
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
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            
            client = AsyncOpenAI(**client_kwargs)
            
            # OpenAI specific test
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
        status_code = 400
        
        if "401" in error_msg or "Unauthorized" in error_msg:
            detail = "API key is invalid or expired"
            status_code = 401
        elif "403" in error_msg or "Forbidden" in error_msg:
            detail = f"API key doesn't have access to model '{model}'"
            status_code = 403
        elif "404" in error_msg:
            detail = f"Model '{model}' not found"
            status_code = 404
        else:
            detail = f"OpenAI Connection failed: {error_msg}"
        
        raise HTTPException(status_code=status_code, detail=detail)
