from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


def flatten_system_messages(messages: list) -> list:
    """Convert system role messages into a prefixed user message.

    Some models (certain Ollama / vLLM variants) reject the 'system' role.
    This merges all system content into the first user message so the intent
    is preserved without using the unsupported role.
    """
    system_parts = [m["content"] for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]
    if not system_parts:
        return messages
    prefix = "\n\n".join(system_parts)
    if rest and rest[0].get("role") == "user":
        rest[0] = {**rest[0], "content": f"{prefix}\n\n---\n\n{rest[0]['content']}"}
    else:
        rest.insert(0, {"role": "user", "content": prefix})
    return rest


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def list_models(
        self,
        api_key: str,
        base_url: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        List available models for this provider.
        Returns a list of dicts with 'id' and 'name' keys.
        """

    @abstractmethod
    async def test_connection(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test connection to the LLM provider.
        Returns dict containing status and message.
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
        """Stream chat completion."""
        pass
