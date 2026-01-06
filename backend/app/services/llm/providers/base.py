from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def test_connection(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test connection to the LLM provider.
        
        Args:
            api_key: The API key for authentication
            model: The model identifier
            base_url: Optional base URL for the API
            
        Returns:
            Dict containing status and message
        """
    
    @abstractmethod
    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ):
        """
        Stream chat completion.
        
        Args:
            api_key: API key
            model: Model name
            messages: Chat messages
            tools: Optional list of tools
            base_url: Optional base URL
            timeout: Request timeout
            
        Returns:
            AsyncGenerator yielding chunks
        """
        pass
