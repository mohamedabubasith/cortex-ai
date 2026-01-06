from typing import Dict, Any
from .base_tool import BaseTool
from app.services.search_service import search_service

class WebsiteReaderTool(BaseTool):
    @property
    def name(self) -> str:
        return "website_reader"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Read the full text content of a website from a given URL. Use this for deep research after finding relevant links via web_search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The full URL of the website to read."
                        }
                    },
                    "required": ["url"]
                }
            }
        }

    async def execute(self, url: str, **kwargs) -> Any:
        if not url:
            return {"error": "URL is required."}
        
        content = await search_service.fetch_page_content(url)
        
        if not content or content.startswith("Error"):
            return {"error": content if content else "Failed to fetch content."}
            
        return {
            "url": url,
            "content": content
        }
