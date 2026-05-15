from app.services.database_service import database_service  # Reuse for encryption
from app.services.llm_service import llm_service
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

# MCP tool call hard timeout — must be well under the HTTP request timeout (typically 60–120s)
# so the tool error is returned to the LLM with time to respond before the stream dies.
MCP_TOOL_TIMEOUT = 20      # seconds per tool call
MCP_CONNECT_TIMEOUT = 10   # seconds to establish connection / list tools


class MCPService:
    def __init__(self):
        pass

    def _extract_auth(self, auth_headers: dict) -> Optional[str]:
        if not auth_headers:
            return None
        return auth_headers.get("Authorization") or None

    async def connect_and_fetch_tools(self, server_url: str, auth_headers: dict = None, protocol: str = "sse") -> list:
        """Connect to MCP server and return available tools list."""
        try:
            from fastmcp import Client

            def tool_to_dict(tool):
                if isinstance(tool, dict):
                    return {"name": tool.get("name"), "description": tool.get("description"), "inputSchema": tool.get("inputSchema")}
                return {"name": getattr(tool, "name", None), "description": getattr(tool, "description", None), "inputSchema": getattr(tool, "inputSchema", None)}

            auth = self._extract_auth(auth_headers)

            async with Client(server_url, auth=auth) as client:
                tools_result = await asyncio.wait_for(client.list_tools(), timeout=MCP_CONNECT_TIMEOUT)
                return [tool_to_dict(t) for t in tools_result]

        except asyncio.TimeoutError:
            logger.error(f"Timeout connecting to MCP server {server_url} ({MCP_CONNECT_TIMEOUT}s)")
            raise TimeoutError(f"MCP server did not respond within {MCP_CONNECT_TIMEOUT}s")
        except Exception as e:
            logger.error(f"Failed to fetch tools from {server_url}: {e}")
            raise

    async def summarize_tools(self, tools_list: list, llm_config) -> str:
        """Use LLM to summarize MCP server capabilities."""
        if not tools_list:
            return "No tools available."

        tools_json = json.dumps(tools_list, indent=2)
        prompt = f"""You are an expert system integrator. I will provide a list of tools available from a Model Context Protocol (MCP) server.
Generate a concise 1-paragraph summary of what these tools allow an AI agent to do. Focus on capabilities and data access.

Tools:
{tools_json}

Summary:"""

        try:
            return await llm_service.generate_text(prompt, llm_config)
        except Exception as e:
            logger.error(f"Failed to summarize tools: {e}")
            return "Error generating summary."

    async def call_mcp_tool(self, server_url: str, tool_name: str, arguments: dict, auth_headers: dict = None) -> Any:
        """Call a tool on a remote MCP server with a hard timeout."""
        auth = self._extract_auth(auth_headers)
        try:
            from fastmcp import Client

            async with Client(server_url, auth=auth) as client:
                result = await asyncio.wait_for(
                    client.call_tool(name=tool_name, arguments=arguments),
                    timeout=MCP_TOOL_TIMEOUT,
                )
                return result

        except asyncio.TimeoutError:
            msg = f"MCP tool '{tool_name}' timed out after {MCP_TOOL_TIMEOUT}s"
            logger.error(msg)
            return {"error": msg, "tool": tool_name, "server": server_url}
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_url}: {e}")
            return {"error": str(e), "tool": tool_name, "server": server_url}


mcp_service = MCPService()
