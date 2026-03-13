import logging
from typing import Dict, Any, Optional
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class ImageGenerationTool(BaseTool):
    """Generates images via DALL-E using the agent's configured LLM API key."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self._api_key = api_key
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "generate_image"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Generate an image from a text description using DALL-E. "
                    "Use this when the user asks to create, draw, generate, design, or visualize an image or artwork. "
                    "Returns a URL to the generated image."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "A detailed description of the image to generate. Be specific about style, colors, composition, and subject."
                        },
                        "size": {
                            "type": "string",
                            "description": "Image dimensions. Use 'landscape' for wide images, 'portrait' for tall, 'square' for 1:1.",
                            "enum": ["square", "landscape", "portrait"],
                            "default": "square"
                        },
                        "quality": {
                            "type": "string",
                            "description": "Image quality: 'standard' is faster, 'hd' produces more detailed images.",
                            "enum": ["standard", "hd"],
                            "default": "standard"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        }

    async def execute(self, prompt: str, size: str = "square", quality: str = "standard", **_) -> Any:
        size_map = {
            "square": "1024x1024",
            "landscape": "1792x1024",
            "portrait": "1024x1792"
        }
        dall_e_size = size_map.get(size, "1024x1024")

        try:
            from openai import AsyncOpenAI
            client_kwargs: Dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url

            client = AsyncOpenAI(**client_kwargs)
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=dall_e_size,
                quality=quality,
                n=1
            )

            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt or prompt

            return {
                "success": True,
                "image_url": image_url,
                "prompt": prompt,
                "revised_prompt": revised_prompt,
                "size": dall_e_size
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Image generation failed: {error_msg}")

            if "401" in error_msg or "Unauthorized" in error_msg:
                return {"error": "API key is invalid or does not have image generation access."}
            if "billing" in error_msg.lower() or "quota" in error_msg.lower():
                return {"error": "Image generation quota exceeded or billing issue."}
            if "content_policy" in error_msg.lower() or "safety" in error_msg.lower():
                return {"error": "The image request was rejected by the content policy. Please revise your prompt."}

            return {"error": f"Image generation failed: {error_msg}"}
