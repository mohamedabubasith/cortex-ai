from typing import Dict, Any, Optional
from openai import AsyncAzureOpenAI
from fastapi import HTTPException
from .base import BaseLLMProvider

class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI Provider implementation."""
    
    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ):
        # Azure requires azure_endpoint, api_version, and api_key
        # We map base_url -> azure_endpoint
        # We use a default api_version if not configurable (could be improved)
        
        client_kwargs = {
            "api_key": api_key, 
            "timeout": timeout,
            "api_version": "2024-02-15-preview", # Default stable-ish version
            "azure_endpoint": base_url 
        }
        
        if not base_url:
             raise HTTPException(status_code=400, detail="Azure OpenAI requires a 'base_url' (your Azure Endpoint).")

        client = AsyncAzureOpenAI(**client_kwargs)
        
        # In Azure, 'model' param usually refers to the deployment name
        return await client.chat.completions.create(
            model=model, # This is the deployment name
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
            if not base_url:
                 raise ValueError("Azure OpenAI requires a 'base_url' (your Azure Endpoint).")

            client_kwargs = {
                "api_key": api_key,
                "api_version": "2024-02-15-preview",
                "azure_endpoint": base_url
            }
            
            client = AsyncAzureOpenAI(**client_kwargs)
            
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
        status_code = 400
        
        if "401" in error_msg or "Unauthorized" in error_msg:
            detail = "API key is invalid or expired"
            status_code = 401
        elif "404" in error_msg or "ResourceNotFound" in error_msg:
            detail = f"Deployment '{model}' or Endpoint not found"
            status_code = 404
        else:
            detail = f"Azure OpenAI Connection failed: {error_msg}"
        
        raise HTTPException(status_code=status_code, detail=detail)
