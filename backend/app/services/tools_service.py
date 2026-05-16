import json
import logging
import asyncio
import datetime
import uuid
import decimal
from typing import List, Dict, Any, Optional

from app.services.tools.time_tool import TimeTool
from app.services.tools.network_tool import NetworkTool
from app.services.tools.weather_tool import WeatherTool
from app.services.tools.database_tool import DatabaseTool
from app.services.tools.search_tool import SearchTool
from app.services.tools.website_reader_tool import WebsiteReaderTool
from app.services.tools.image_tool import ImageGenerationTool

logger = logging.getLogger(__name__)


class ToolsService:
    def __init__(self):
        self.tools_registry: Dict[str, Any] = {}
        self.register_default_tools()
        # Agent-specific context set before each request
        self.current_agent_db_connections: List[Any] = []
        self.current_agent_mcp_connections: List[Any] = []
        self.database_service: Optional[Any] = None
        self.current_llm_config: Optional[Any] = None
        self.client_ip: Optional[str] = None
        self.client_timezone: Optional[str] = None

    def set_agent_context(
        self,
        db_connections: List[Any],
        mcp_connections: List[Any],
        database_service: Any,
        llm_config: Optional[Any] = None,
        client_ip: Optional[str] = None,
        client_timezone: Optional[str] = None,
    ) -> None:
        self.current_agent_db_connections = db_connections
        self.current_agent_mcp_connections = mcp_connections
        self.database_service = database_service
        self.current_llm_config = llm_config
        self.client_ip = client_ip
        self.client_timezone = client_timezone

    def register_tool(self, tool_instance: Any) -> None:
        self.tools_registry[tool_instance.name] = tool_instance

    def register_default_tools(self) -> None:
        self.register_tool(TimeTool())
        self.register_tool(NetworkTool())
        self.register_tool(WeatherTool())
        self.register_tool(SearchTool())
        self.register_tool(WebsiteReaderTool())

    def get_agent_specific_tools(
        self,
        db_connections: List[Any],
        mcp_connections: List[Any],
        search_enabled: bool = True,
        db_enabled: bool = True,
        image_enabled: bool = True,
    ) -> List[Dict[str, Any]]:
        tools_schemas = self.get_tool_definitions(search_enabled=search_enabled)

        # Image generation — only for OpenAI-compatible providers (DALL-E)
        if image_enabled and self.current_llm_config:
            provider = getattr(self.current_llm_config, "provider", "openai")
            if provider in ("openai", "azure"):
                img_tool = ImageGenerationTool(
                    api_key=self.current_llm_config.api_key,
                    base_url=getattr(self.current_llm_config, "base_url", None),
                )
                tools_schemas.append(img_tool.schema)

        # Database tool
        if db_connections and db_enabled:
            db_tool = DatabaseTool(db_connections, self.database_service)
            tools_schemas.append(db_tool.schema)

        # MCP tools
        if mcp_connections:
            for mcp in mcp_connections:
                if mcp.tools_metadata:
                    for tool in mcp.tools_metadata:
                        tools_schemas.append({
                            "type": "function",
                            "function": {
                                "name": f"mcp_{mcp.id}_{tool['name']}",
                                "description": tool.get("description", ""),
                                "parameters": tool.get("inputSchema") or {}
                            }
                        })

        return tools_schemas

    def get_tool_definitions(self, search_enabled: bool = True) -> List[Dict[str, Any]]:
        schemas = []
        for name, tool in self.tools_registry.items():
            if not search_enabled and name in ("web_search", "website_reader"):
                continue
            schemas.append(tool.schema)
        return schemas

    async def execute_tool(self, name: str, arguments: str) -> str:
        # --- Image generation ---
        if name == "generate_image":
            if self.current_llm_config:
                img_tool = ImageGenerationTool(
                    api_key=self.current_llm_config.api_key,
                    base_url=getattr(self.current_llm_config, "base_url", None),
                )
                kwargs = json.loads(arguments) if arguments else {}
                result = await img_tool.execute(**kwargs)
                return json.dumps(result, default=self._json_serializer)
            return json.dumps({"error": "No LLM config available for image generation"})

        # --- Database query ---
        if name == "query_database":
            if self.current_agent_db_connections and self.database_service:
                db_tool = DatabaseTool(self.current_agent_db_connections, self.database_service)
                kwargs = json.loads(arguments) if arguments else {}
                result = await db_tool.execute(**kwargs)
                return json.dumps(result, default=self._json_serializer)
            return json.dumps({"error": "Database context not initialized"})

        # --- MCP tools ---
        if name.startswith("mcp_"):
            try:
                parts = name.split("_", 2)
                if len(parts) >= 3:
                    mcp_id = parts[1]
                    original_tool_name = parts[2]
                    mcp_conn = next(
                        (c for c in self.current_agent_mcp_connections if str(c.id) == mcp_id),
                        None
                    )
                    if mcp_conn:
                        from app.services.mcp_service import mcp_service
                        kwargs = json.loads(arguments) if arguments else {}
                        auth_headers: Dict[str, str] = {}
                        if mcp_conn.auth_headers:
                            try:
                                auth_headers = json.loads(mcp_conn.auth_headers)
                            except Exception:
                                pass
                        result = await mcp_service.call_mcp_tool(
                            server_url=mcp_conn.server_url,
                            tool_name=original_tool_name,
                            arguments=kwargs,
                            auth_headers=auth_headers,
                        )
                        return json.dumps(result, default=self._json_serializer)
                    return json.dumps({"error": f"MCP connection {mcp_id} not found"})
            except Exception as e:
                logger.error(f"MCP tool execution failed: {e}")
                return json.dumps({"error": f"MCP execution error: {str(e)}"})

        # --- Registry tools ---
        if name not in self.tools_registry:
            return json.dumps({"error": f"Tool '{name}' not found"})

        try:
            tool = self.tools_registry[name]
            kwargs = json.loads(arguments) if arguments else {}
            # Inject client context for location/time tools
            if name == "get_ip_and_network_info" and self.client_ip:
                kwargs["client_ip"] = self.client_ip
            if name == "get_current_datetime" and self.client_timezone and "timezone" not in kwargs:
                kwargs["timezone"] = self.client_timezone
            result = await tool.execute(**kwargs)
            return json.dumps(result, default=self._json_serializer)
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return json.dumps({"error": str(e)})

    def _json_serializer(self, obj: Any) -> Any:
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return str(obj)


tools_service = ToolsService()
