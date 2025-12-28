import tiktoken
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in a string using tiktoken"""
    if not text:
        return 0
    try:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except (KeyError, ValueError):
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Failed to count tokens with tiktoken: {e}")
        # Very rough fallback: ~4 chars per token
        return len(text) // 4

def extract_usage_from_chunk(chunk: Any) -> Optional[Dict[str, int]]:
    """
    Robustly extract token usage from a streaming chunk.
    Different providers and SDK versions put usage in different places.
    """
    try:
        # 1. Top level 'usage' attribute (OpenAI standard for last chunk)
        usage = getattr(chunk, 'usage', None)
        if not usage and hasattr(chunk, 'get'):
            usage = chunk.get('usage')
            
        if usage:
            # Handle object-like vs dict-like usage
            if hasattr(usage, 'prompt_tokens'):
                return {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            elif isinstance(usage, dict):
                return {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
        
        # 2. Choice-level usage (Older or some alternative providers)
        if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
            choice = chunk.choices[0]
            usage = getattr(choice, 'usage', None)
            if usage:
                if hasattr(usage, 'prompt_tokens'):
                    return {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    }
    except Exception as e:
        logger.debug(f"Failed to extract usage from chunk: {e}")
    
    return None

def estimate_token_usage(messages: List[Dict[str, str]], response_text: str, model: str = "gpt-4o") -> Dict[str, int]:
    """Estimate token usage for a chat interaction"""
    # Prompt tokens: sum of all messages
    prompt_text = ""
    for m in messages:
        content = m.get("content")
        if content:
            prompt_text += f"{content}\n"
    
    prompt_tokens = count_tokens(prompt_text, model)
    completion_tokens = count_tokens(response_text, model)
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }
