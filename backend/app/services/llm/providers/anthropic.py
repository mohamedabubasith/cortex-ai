from typing import Dict, Any, Optional, AsyncGenerator, List
import json
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from .base import BaseLLMProvider

# Hardcoded fallback in case the API call fails
_ANTHROPIC_MODELS = [
    {"id": "claude-opus-4-6",            "name": "Claude Opus 4.6"},
    {"id": "claude-sonnet-4-6",          "name": "Claude Sonnet 4.6"},
    {"id": "claude-haiku-4-5-20251001",  "name": "Claude Haiku 4.5"},
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
    {"id": "claude-3-5-haiku-20241022",  "name": "Claude 3.5 Haiku"},
    {"id": "claude-3-opus-20240229",     "name": "Claude 3 Opus"},
]


def _convert_messages_for_anthropic(messages: list) -> tuple[str, list]:
    """Extract system prompt and convert OpenAI tool messages to Anthropic format."""
    system_prompt = ""
    converted = []

    for msg in messages:
        role = msg.get("role")

        if role == "system":
            system_prompt += msg["content"] + "\n"
            continue

        if role == "tool":
            # OpenAI: {"role": "tool", "tool_call_id": id, "content": result}
            # Anthropic: user message with tool_result content block
            tool_result = {
                "type": "tool_result",
                "tool_use_id": msg.get("tool_call_id", ""),
                "content": msg.get("content", ""),
            }
            # Merge consecutive tool results into one user message
            if converted and converted[-1]["role"] == "user" and isinstance(converted[-1]["content"], list):
                converted[-1]["content"].append(tool_result)
            else:
                converted.append({"role": "user", "content": [tool_result]})
            continue

        if role == "assistant" and msg.get("tool_calls"):
            # OpenAI: {"role": "assistant", "content": text, "tool_calls": [...]}
            # Anthropic: assistant message with text + tool_use content blocks
            content = []
            if msg.get("content"):
                content.append({"type": "text", "text": msg["content"]})
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                content.append({
                    "type": "tool_use",
                    "id": tc.get("id", ""),
                    "name": func.get("name", ""),
                    "input": args,
                })
            converted.append({"role": "assistant", "content": content})
            continue

        converted.append(msg)

    return system_prompt.strip(), converted


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Provider implementation."""

    def _client(self, api_key: str, base_url: Optional[str] = None, timeout: float = 30.0) -> AsyncAnthropic:
        kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            kwargs["base_url"] = base_url
        return AsyncAnthropic(**kwargs)

    async def list_models(self, api_key: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        try:
            client = self._client(api_key, base_url)
            response = await client.models.list()
            return [{"id": m.id, "name": getattr(m, "display_name", m.id)} for m in response.data]
        except Exception:
            return _ANTHROPIC_MODELS

    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    ):
        client = self._client(api_key, base_url, timeout)

        anthropic_tools = []
        if tools:
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    anthropic_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters") or {"type": "object", "properties": {}},
                    })

        system_prompt, filtered_messages = _convert_messages_for_anthropic(messages)

        kwargs = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": 4096,
            "stream": True,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        stream = await client.messages.create(**kwargs)
        # Return async generator (not itself a generator, so llm_service can `await` this method)
        return self._wrap_stream(stream)

    async def _wrap_stream(self, stream) -> AsyncGenerator:
        """Wrap Anthropic stream into OpenAI-compatible chunk objects."""
        async for chunk in stream:
            if chunk.type == "content_block_start":
                cb = chunk.content_block
                if cb.type == "tool_use":
                    yield self._tool_call_chunk(chunk.index, cb.id, cb.name, "")

            elif chunk.type == "content_block_delta":
                delta = chunk.delta
                if delta.type == "text_delta":
                    yield self._text_chunk(delta.text)
                elif delta.type == "input_json_delta":
                    yield self._tool_call_chunk(chunk.index, None, None, delta.partial_json)

    # ── Mock chunk builders ──────────────────────────────────────────────────

    def _text_chunk(self, text: str):
        class Delta:
            content = text
            tool_calls = None
            reasoning_content = None

        class Choice:
            delta = Delta()

        class Chunk:
            choices = [Choice()]

        return Chunk()

    def _tool_call_chunk(self, index: int, tool_id, name, arguments: str):
        class Function:
            pass

        fn = Function()
        fn.name = name
        fn.arguments = arguments

        class ToolCall:
            pass

        tc = ToolCall()
        tc.index = index
        tc.id = tool_id
        tc.function = fn

        class Delta:
            content = None
            reasoning_content = None
            tool_calls = [tc]

        class Choice:
            delta = Delta()

        class Chunk:
            choices = [Choice()]

        return Chunk()

    async def test_connection(self, api_key: str, model: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        try:
            client = self._client(api_key, base_url)
            response = await client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return {
                "status": "success",
                "message": f"Connection successful! Model '{model}' is accessible.",
                "test_response": response.content[0].text
            }
        except Exception as e:
            self._handle_error(e, model)

    def _handle_error(self, e: Exception, model: str):
        error_msg = str(e)
        if "401" in error_msg or "authentication_error" in error_msg:
            raise HTTPException(status_code=401, detail="API key is invalid or expired")
        elif "403" in error_msg or "permission_error" in error_msg:
            raise HTTPException(status_code=403, detail=f"API key doesn't have access to model '{model}'")
        elif "404" in error_msg or "not_found_error" in error_msg:
            raise HTTPException(status_code=404, detail=f"Model '{model}' not found")
        else:
            raise HTTPException(status_code=400, detail=f"Anthropic connection failed: {error_msg}")
