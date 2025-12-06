import openai
import asyncio
from typing import AsyncGenerator
from app.models import models

class LLMService:
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1  # seconds

    async def stream_chat(self, agent: models.Agent, messages: list, retry_count: int = 0) -> AsyncGenerator[str, None]:
        """
        Streams chat response from the configured LLM provider with retry logic.
        """
        client = openai.AsyncOpenAI(
            base_url=agent.llm_config.base_url if agent.llm_config else None,
            api_key=agent.llm_config.api_key if agent.llm_config else None
        )
        
        # Convert messages to OpenAI format
        formatted_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        
        try:
            stream = await client.chat.completions.create(
                model=agent.llm_config.model if agent.llm_config else "gpt-3.5-turbo",
                messages=formatted_messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except openai.APIError as e:
            # Handle API errors with retry logic
            if retry_count < self.max_retries:
                delay = self.base_delay * (2 ** retry_count)  # Exponential backoff
                print(f"LLM API Error (attempt {retry_count + 1}/{self.max_retries}): {str(e)}. Retrying in {delay}s...")
                yield f"\n\n⚠️ Temporary error, retrying in {delay}s...\n\n"
                await asyncio.sleep(delay)
                # Retry by recursively calling with incremented retry count
                async for chunk in self.stream_chat(agent, messages, retry_count + 1):
                    yield chunk
            else:
                yield f"\n\n❌ Error after {self.max_retries} retries: {str(e)}\n\nPlease try again or check your LLM configuration."
                
        except openai.APIConnectionError as e:
            if retry_count < self.max_retries:
                delay = self.base_delay * (2 ** retry_count)
                print(f"LLM Connection Error (attempt {retry_count + 1}/{self.max_retries}): {str(e)}. Retrying in {delay}s...")
                yield f"\n\n⚠️ Connection error, retrying in {delay}s...\n\n"
                await asyncio.sleep(delay)
                async for chunk in self.stream_chat(agent, messages, retry_count + 1):
                    yield chunk
            else:
                yield f"\n\n❌ Connection failed after {self.max_retries} retries: {str(e)}\n\nPlease check your network connection."
                
        except Exception as e:
            print(f"Unexpected LLM error: {str(e)}")
            yield f"\n\n❌ Unexpected error: {str(e)}\n\nPlease try sending your message again."

llm_service = LLMService()
