from app.services.database_service import database_service  # Reuse for encryption
from app.services.llm_service import llm_service
from typing import List, Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class MCPService:
    def __init__(self):
        pass

    async def connect_and_fetch_tools(self, server_url: str, auth_headers: dict = None, protocol: str = "sse") -> list:
        """
        Connects to the MCP server via fastmcp and fetches available tools.
        """
        try:
            from fastmcp import Client
            
            # Helper to convert tool objects to dicts
            def tool_to_dict(tool):
                if isinstance(tool, dict):
                    return {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "inputSchema": tool.get("inputSchema")
                    }
                else:
                    return {
                        "name": getattr(tool, "name", None),
                        "description": getattr(tool, "description", None),
                        "inputSchema": getattr(tool, "inputSchema", None)
                    }

            # Prepare auth if present
            # fastmcp Client auth parameter typically accepts a token string or None
            # We try to extract a token from Authorization header if present
            auth = None
            if auth_headers and "Authorization" in auth_headers:
                 auth = auth_headers["Authorization"]

            # Use fastmcp Client context manager
            async with Client(server_url, auth=auth) as client:
                tools_result = await client.list_tools()
                # tools_result is usually a list of tools directly in fastmcp >= 0.3.0
                # but if it returns a wrapper, we check.
                # Based on docstring: returns list[mcp.types.Tool]
                
                return [tool_to_dict(t) for t in tools_result]
                
        except Exception as e:
            logger.error(f"Failed to fetch tools from {server_url} via fastmcp: {e}")
            raise e

    async def summarize_tools(self, tools_list: list, llm_config) -> str:
        """
        Uses the provided LLM config to summarize the capabilities of the provided tools.
        """
        if not tools_list:
            return "No tools available."

        tools_json = json.dumps(tools_list, indent=2)
        prompt = f"""
        You are an expert system integrator. I will provide a list of tools available from a Model Context Protocol (MCP) server.
        Your task is to generate a concise, 1-paragraph summary of what these tools allow an AI agent to do.
        Focus on the capabilities and the data they can access.
        
        Tools included:
        {tools_json}
        
        Summary:
        """
        
        try:
            return await llm_service.generate_text(prompt, llm_config)
        except Exception as e:
            logger.error(f"Failed to summarize tools: {e}")
            return "Error generating summary."

    async def call_mcp_tool(self, server_url: str, tool_name: str, arguments: dict, auth_headers: dict = None) -> Any:
        """
        Calls a tool on a remote MCP server.
        """
        try:
            from fastmcp import Client
            
            auth = None
            if auth_headers and "Authorization" in auth_headers:
                 auth = auth_headers["Authorization"]

            async with Client(server_url, auth=auth) as client:
                result = await client.call_tool(name=tool_name, arguments=arguments)
                return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_url}: {e}")
            return {"error": str(e)}

mcp_service = MCPService()
