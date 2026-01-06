from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.services.llm.factory import LLMProviderFactory

class LLMProviderService:
    async def test_connection(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test connection to an LLM provider.
        
        Args:
            provider: The provider ID (e.g., 'openai', 'ollama')
            api_key: The API key for authentication
            model: The model identifier
            base_url: Optional base URL for the API
            
        Returns:
            Dict containing status and message
            
        Raises:
            HTTPException: If connection fails
        """
        try:
            # Get specific provider implementation
            llm_provider = LLMProviderFactory.get_provider(provider)
            
            return await llm_provider.test_connection(
                api_key=api_key,
                model=model,
                base_url=base_url
            )
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            # Catch-all for unexpected service level errors
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
