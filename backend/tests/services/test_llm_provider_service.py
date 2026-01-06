import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.services.llm_provider_service import LLMProviderService

@pytest.fixture
def provider_service():
    return LLMProviderService()

@pytest.mark.asyncio
async def test_connection_openai_success(provider_service):
    # Mock the specific provider instance created by the factory
    with patch("app.services.llm.providers.openai.AsyncOpenAI") as MockOpenAI:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test Response"))]
        MockOpenAI.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await provider_service.test_connection(
            provider="openai",
            api_key="valid-key",
            model="gpt-4"
        )
        
        assert result["status"] == "success"
        assert result["test_response"] == "Test Response"

@pytest.mark.asyncio
async def test_connection_unknown_provider(provider_service):
    with pytest.raises(HTTPException) as exc_info:
        await provider_service.test_connection(
            provider="invalid-provider",
            api_key="key",
            model="model"
        )
    assert exc_info.value.status_code == 400
    assert "Unsupported provider" in exc_info.value.detail

@pytest.mark.asyncio
async def test_connection_ollama_success(provider_service):
    # Test Ollama specific logic
    with patch("app.services.llm.providers.ollama.AsyncOpenAI") as MockOpenAI:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Ollama Response"))]
        MockOpenAI.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await provider_service.test_connection(
            provider="ollama",
            api_key="none", # Ollama often ignores this
            model="llama2"
        )
        
        assert result["status"] == "success"
        assert "Ollama" in result["message"]

