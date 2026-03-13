import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
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
                "description": (
                    "Get the current date, time, and timezone information. "
                    "Optionally accepts a timezone name (e.g. 'Asia/Kolkata', 'America/New_York', 'Europe/London'). "
                    "Use this when the user asks for the current time, date, day of week, or wants to know "
                    "the time in a specific city or region."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": (
                                "IANA timezone name such as 'Asia/Kolkata', 'America/New_York', "
                                "'Europe/London', 'Asia/Dubai', 'Asia/Singapore', 'Australia/Sydney'. "
                                "Omit to use the user's local timezone."
                            )
                        }
                    },
                    "required": []
                }
            }
        }

    async def execute(self, timezone: str = None, **_) -> Any:
        try:
            if timezone:
                try:
                    tz = ZoneInfo(timezone)
                    now = datetime.datetime.now(tz)
                    tz_label = timezone
                except ZoneInfoNotFoundError:
                    now = datetime.datetime.now().astimezone()
                    tz_label = str(now.tzinfo)
            else:
                now = datetime.datetime.now().astimezone()
                tz_label = str(now.tzinfo)

            utc_offset = now.utcoffset()
            offset_seconds = utc_offset.total_seconds() if utc_offset else 0
            offset_hours = offset_seconds / 3600
            sign = "+" if offset_hours >= 0 else ""
            offset_str = f"UTC{sign}{offset_hours:g}"

            return {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "datetime_iso": now.isoformat(),
                "day_of_week": now.strftime("%A"),
                "month": now.strftime("%B"),
                "year": now.year,
                "hour_12": now.strftime("%I:%M %p"),
                "timezone": tz_label,
                "utc_offset": offset_str,
                "unix_timestamp": int(now.timestamp()),
                "formatted": now.strftime("%A, %d %B %Y at %I:%M %p (%Z)")
            }
        except Exception as e:
            return {"error": f"Failed to get datetime: {str(e)}"}
