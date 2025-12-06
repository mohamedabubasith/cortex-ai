from app.models import models
import httpx

class MCPService:
    def __init__(self):
        pass

    async def test_connection(self, server_url: str) -> bool:
        """
        Tests connection to an MCP server.
        """
        try:
            async with httpx.AsyncClient() as client:
                # Assuming MCP server has a health check or similar
                response = await client.get(f"{server_url}/health", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False

mcp_service = MCPService()
