from typing import Dict, Type
from .providers.base import BaseLLMProvider
from .providers.openai import OpenAIProvider
from .providers.ollama import OllamaProvider
from .providers.anthropic import AnthropicProvider
from .providers.azure import AzureOpenAIProvider

class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "azure": AzureOpenAIProvider,
        "anthropic": AnthropicProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_id: str) -> BaseLLMProvider:
        """
        Get a provider instance by ID.
        
        Args:
            provider_id: The provider identifier (e.g., 'openai', 'ollama')
            
        Returns:
            An instance of the requested provider
            
        Raises:
            ValueError: If the provider is not supported
        """
        provider_class = cls._providers.get(provider_id.lower())
        
        if not provider_class:
            # Fallback to OpenAI if unknown, or raise error?
            # For robustness, let's default to OpenAI compatible if unsure, 
            # or raise meaningful error.
            raise ValueError(f"Unsupported provider: {provider_id}")
            
        return provider_class()
