import httpx
from typing import Dict, Any, Optional
from .base_tool import BaseTool

class LocationTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_location"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Get the approximate location (latitude, longitude, city, country) based on the server's public IP.",
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
                response = await client.get("http://ip-api.com/json/", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return {
                            "status": "success",
                            "city": data.get("city"),
                            "country": data.get("country"), 
                            "lat": data.get("lat"),
                            "lon": data.get("lon"),
                            "timezone": data.get("timezone"),
                            "query": data.get("query") # IP
                        }
                    else:
                        return {"error": "Failed to determine location", "details": data}
                return {"error": "Failed to connect to location service"}
        except Exception as e:
            return {"error": f"Failed to retrieve location: {str(e)}"}
