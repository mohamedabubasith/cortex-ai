import datetime
import httpx
import json
from typing import List, Dict, Any, Callable

class ToolsService:
    def __init__(self):
        self.tools_registry = {}
        self.register_default_tools()

    def register_tool(self, name: str, func: Callable, schema: Dict[str, Any]):
        self.tools_registry[name] = {
            "func": func,
            "schema": schema
        }

    def register_default_tools(self):
        # 1. Current Date and Time
        self.register_tool(
            "get_current_datetime",
            self.get_current_datetime,
            {
                "type": "function",
                "function": {
                    "name": "get_current_datetime",
                    "description": "Get the current date and time. Use this when the user asks for the time or date.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        )

        # 2. Get Public IP
        self.register_tool(
            "get_public_ip",
            self.get_public_ip,
            {
                "type": "function",
                "function": {
                    "name": "get_public_ip",
                    "description": "Get the public IP address of the server running this bot.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        )

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [tool["schema"] for tool in self.tools_registry.values()]

    async def execute_tool(self, name: str, arguments: str) -> str:
        if name not in self.tools_registry:
            return json.dumps({"error": f"Tool {name} not found"})
        
        try:
            func = self.tools_registry[name]["func"]
            # Parse arguments if they are JSON string
            kwargs = json.loads(arguments) if arguments else {}
            
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    # Tool Implementations
    def get_current_datetime(self):
        now = datetime.datetime.now()
        return {
            "current_datetime": now.isoformat(),
            "day_of_week": now.strftime("%A"),
            "timezone": str(now.astimezone().tzinfo)
        }

    async def get_public_ip(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.ipify.org?format=json", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": "Failed to retrieve IP"}
        except Exception as e:
            return {"error": f"Failed to retrieve IP: {str(e)}"}

import asyncio
tools_service = ToolsService()
