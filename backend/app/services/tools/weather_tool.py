import httpx
from typing import Dict, Any
from .base_tool import BaseTool

class WeatherTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_weather"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Get current weather information for a specific location (latitude/longitude). Use 'get_current_location' to get coordinates if not provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "description": "Latitude of the location"},
                        "longitude": {"type": "number", "description": "Longitude of the location"}
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        
        if lat is None or lon is None:
            return {"error": "Latitude and longitude are required"}

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "timezone": "auto"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    current = data.get("current", {})
                    units = data.get("current_units", {})
                    daily = data.get("daily", {})
                    
                    return {
                        "location": {"lat": lat, "lon": lon},
                        "current": {
                            "temperature": f"{current.get('temperature_2m')} {units.get('temperature_2m')}",
                            "humidity": f"{current.get('relative_humidity_2m')} {units.get('relative_humidity_2m')}",
                            "feel_like": f"{current.get('apparent_temperature')} {units.get('apparent_temperature')}",
                            "condition_code": current.get('weather_code'),
                            "wind_speed": f"{current.get('wind_speed_10m')} {units.get('wind_speed_10m')}",
                            "time": current.get('time')
                        },
                        "forecast_today": {
                             "max_temp": f"{daily.get('temperature_2m_max', [])[0]} {data.get('daily_units', {}).get('temperature_2m_max')}",
                             "min_temp": f"{daily.get('temperature_2m_min', [])[0]} {data.get('daily_units', {}).get('temperature_2m_min')}",
                        }
                    }
                return {"error": "Failed to retrieve weather data"}
        except Exception as e:
            return {"error": f"Failed to retrieve weather: {str(e)}"}
