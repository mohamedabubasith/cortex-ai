import httpx
from typing import Dict, Any
from .base_tool import BaseTool

class NetworkTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_public_ip"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Get the public IP address of the server running this bot.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.ipify.org?format=json", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": "Failed to retrieve IP"}
        except Exception as e:
            return {"error": f"Failed to retrieve IP: {str(e)}"}
