import datetime
from typing import Dict, Any
from .base_tool import BaseTool

class TimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_datetime"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Get the current date and time. Use this when the user asks for the time or date.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        now = datetime.datetime.now()
        return {
            "current_datetime": now.isoformat(),
            "day_of_week": now.strftime("%A"),
            "timezone": str(now.astimezone().tzinfo)
        }
