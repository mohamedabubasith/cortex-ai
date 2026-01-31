import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.services.llm.factory import LLMProviderFactory
from app.services.llm.providers.anthropic import AnthropicProvider
from app.services.llm.providers.azure import AzureOpenAIProvider

# --- Factory Tests ---

def test_factory_get_anthropic():
    provider = LLMProviderFactory.get_provider("anthropic")
    assert isinstance(provider, AnthropicProvider)

def test_factory_get_azure():
    provider = LLMProviderFactory.get_provider("azure")
    assert isinstance(provider, AzureOpenAIProvider)

def test_factory_invalid():
    with pytest.raises(ValueError):
        LLMProviderFactory.get_provider("invalid-provider")

# --- Anthropic Provider Tests ---

@pytest.mark.asyncio
async def test_anthropic_chat_success():
    provider = AnthropicProvider()
    
    with patch("app.services.llm.providers.anthropic.AsyncAnthropic") as MockAnthropic:
        # Define the async generator
        async def async_gen():
            chunks = [
                MagicMock(type="message_start"),
                MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="Hello from Claude")),
                MagicMock(type="message_delta")
            ]
            for c in chunks:
                yield c

        # Mock messages.create to be an AsyncMock that returns the generator
        # When awaited, it returns the async_gen identifier
        mock_create = AsyncMock(return_value=async_gen())
        MockAnthropic.return_value.messages.create = mock_create
        
        response_chunks = []
        async for chunk in provider.chat(
            api_key="test-key", 
            model="claude-3-opus", 
            messages=[{"role": "user", "content": "hi"}],
            timeout=10
        ):
            response_chunks.append(chunk)
            
        assert len(response_chunks) == 1
        assert response_chunks[0].choices[0].delta.content == "Hello from Claude"
        
        # Verify call
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "claude-3-opus"

@pytest.mark.asyncio
async def test_anthropic_connection_error():
    provider = AnthropicProvider()
    with patch("app.services.llm.providers.anthropic.AsyncAnthropic") as MockAnthropic:
        # test_connection does await client.messages.create(...)
        # So create needs to be AsyncMock
        mock_create = AsyncMock()
        mock_create.side_effect = Exception("authentication_error: Invalid key")
        MockAnthropic.return_value.messages.create = mock_create
        
        with pytest.raises(HTTPException) as exc:
            await provider.test_connection(api_key="bad-key", model="claude-3")
            
        assert exc.value.status_code == 401

# --- Azure Provider Tests ---

@pytest.mark.asyncio
async def test_azure_chat_success():
    provider = AzureOpenAIProvider()
    
    with patch("app.services.llm.providers.azure.AsyncAzureOpenAI") as MockAzure:
         # Mock chat.completions.create
         # It effectively needs to be an AsyncMock that returns the response
         mock_create = AsyncMock(return_value="mock_stream_response")
         MockAzure.return_value.chat.completions.create = mock_create
         
         result = await provider.chat(
             api_key="azure-key",
             model="my-deployment",
             base_url="https://azure.com",
             messages=[{"role": "user", "content": "hi"}]
         )
         
         assert result == "mock_stream_response"
         
         # Check kwargs
         assert "api_version" in MockAzure.call_args.kwargs
         assert MockAzure.call_args.kwargs["azure_endpoint"] == "https://azure.com"
         assert mock_create.call_args.kwargs["model"] == "my-deployment"

@pytest.mark.asyncio
async def test_azure_missing_base_url():
    provider = AzureOpenAIProvider()
    with pytest.raises(HTTPException) as exc:
        await provider.chat(api_key="key", model="model", messages=[], base_url=None)
    
    assert exc.value.status_code == 400
    assert "requires a 'base_url'" in exc.value.detail
