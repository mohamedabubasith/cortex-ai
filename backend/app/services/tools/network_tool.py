import httpx
from typing import Dict, Any
from .base_tool import BaseTool


class NetworkTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_ip_and_network_info"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Get the public IP address, geolocation, ISP, and network info of the user. "
                    "Use this when the user asks about their IP address, server location, ISP, "
                    "network provider, ASN, or region details."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    async def execute(self, client_ip: str = None, **_) -> Any:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # ip-api.com returns IP + full geo + ISP in a single call (HTTPS on pro, but HTTP is fine for server-side)
                ip_param = client_ip if client_ip else ""
                url = f"http://ip-api.com/json/{ip_param}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,query"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return {
                            "ip_address": data.get("query"),
                            "isp": data.get("isp"),
                            "organization": data.get("org"),
                            "asn": data.get("as"),
                            "asn_name": data.get("asname"),
                            "location": {
                                "city": data.get("city"),
                                "region": data.get("regionName"),
                                "region_code": data.get("region"),
                                "country": data.get("country"),
                                "country_code": data.get("countryCode"),
                                "postal_code": data.get("zip"),
                                "latitude": data.get("lat"),
                                "longitude": data.get("lon"),
                                "timezone": data.get("timezone"),
                            }
                        }
                    return {"error": data.get("message", "Lookup failed")}
                return {"error": f"HTTP {response.status_code} from IP lookup service"}
        except Exception as e:
            return {"error": f"Network info lookup failed: {str(e)}"}
