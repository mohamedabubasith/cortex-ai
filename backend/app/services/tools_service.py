import json
import logging
import asyncio
from typing import List, Dict, Any, Callable

# Import new tools
from app.services.tools.time_tool import TimeTool
from app.services.tools.network_tool import NetworkTool
from app.services.tools.weather_tool import WeatherTool
from app.services.tools.location_tool import LocationTool
from app.services.tools.database_tool import DatabaseTool
from app.services.tools.search_tool import SearchTool
from app.services.tools.website_reader_tool import WebsiteReaderTool

logger = logging.getLogger(__name__)

class ToolsService:
    def __init__(self):
        self.tools_registry = {}
        self.register_default_tools()
        # Agent-specific context
        self.current_agent_db_connections = []
        self.current_agent_mcp_connections = []
        self.database_service = None

    def set_agent_context(self, db_connections: List[Any], mcp_connections: List[Any], database_service: Any):
        """Set the current agent's context for this tool execution context"""
        self.current_agent_db_connections = db_connections
        self.current_agent_mcp_connections = mcp_connections
        self.database_service = database_service

    def register_tool(self, tool_instance):
        """Register a tool instance"""
        self.tools_registry[tool_instance.name] = tool_instance

    def register_default_tools(self):
        # Register standard tools
        self.register_tool(TimeTool())
        self.register_tool(NetworkTool())
        self.register_tool(WeatherTool())
        self.register_tool(LocationTool())
        self.register_tool(SearchTool())
        self.register_tool(WebsiteReaderTool())

    def get_agent_specific_tools(self, db_connections: List[Any], mcp_connections: List[Any]) -> List[Dict[str, Any]]:
        """Get tool definitions including database tools and MCP tools for the specific agent"""
        # Get standard tools schemas
        tools_schemas = self.get_tool_definitions()
        
        # Add database query tool if agent has database connections
        if db_connections and len(db_connections) > 0:
            db_tool = DatabaseTool(db_connections, self.database_service)
            tools_schemas.append(db_tool.schema)
            
        # Add MCP tools
        if mcp_connections:
            for mcp in mcp_connections:
                if mcp.tools_metadata:
                    for tool in mcp.tools_metadata:
                        # Prefix tool name to ensure uniqueness and routing
                        # We modify the local copy of the schema
                        tooled_schema = {
                            "type": "function",
                            "function": {
                                "name": f"mcp_{mcp.id}_{tool['name']}",
                                "description": tool.get("description", ""),
                                "parameters": tool.get("inputSchema", {})
                            }
                        }
                        tools_schemas.append(tooled_schema)
        
        return tools_schemas

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [tool.schema for tool in self.tools_registry.values()]

    async def execute_tool(self, name: str, arguments: str) -> str:
        # Handle database query tool specially as it relies on context not in registry
        if name == "query_database":
            # Re-create the tool used for schema generation context (or use context if stored)
            if self.current_agent_db_connections and self.database_service:
                db_tool = DatabaseTool(self.current_agent_db_connections, self.database_service)
                kwargs = json.loads(arguments) if arguments else {}
                result = await db_tool.execute(**kwargs)
                return json.dumps(result, default=self.json_serializer)
            else:
                return json.dumps({"error": "Database context not initialized"})

        # Handle MCP Tools
        if name.startswith("mcp_"):
            try:
                # Format: mcp_{connection_id}_{tool_name}
                parts = name.split("_", 2) # Limit split to 2 to keep tool name intact if it has underscores
                if len(parts) >= 3:
                    mcp_id = parts[1]
                    original_tool_name = parts[2]
                    
                    # Find the connection
                    mcp_conn = next((c for c in self.current_agent_mcp_connections if str(c.id) == mcp_id), None)
                    
                    if mcp_conn:
                        from app.services.mcp_service import mcp_service
                        kwargs = json.loads(arguments) if arguments else {}
                        
                        # Decrypt headers if needed (reuse logic or assume helper exists)
                        auth_headers = {}
                        if mcp_conn.auth_headers:
                            # TODO: Decrypt logic. For now assuming plain text or handled inside call
                             try:
                                auth_headers = json.loads(mcp_conn.auth_headers)
                             except:
                                pass # Or handle encryption properly
                                
                        result = await mcp_service.call_mcp_tool(
                            server_url=mcp_conn.server_url,
                            tool_name=original_tool_name,
                            arguments=kwargs,
                            auth_headers=auth_headers
                        )
                        return json.dumps(result, default=self.json_serializer)
                    else:
                        return json.dumps({"error": f"MCP Connection {mcp_id} not active"})
            except Exception as e:
                logger.error(f"MCP Tool execution failed: {e}")
                return json.dumps({"error": f"MCP execution error: {str(e)}"})
        
        if name not in self.tools_registry:
            return json.dumps({"error": f"Tool {name} not found"})
        
        try:
            tool = self.tools_registry[name]
            # Parse arguments if they are JSON string
            kwargs = json.loads(arguments) if arguments else {}
            
            result = await tool.execute(**kwargs)
            
            return json.dumps(result, default=self.json_serializer)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return json.dumps({"error": str(e)})

    def json_serializer(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        import datetime
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        import uuid
        if isinstance(obj, uuid.UUID):
            return str(obj)
        import decimal
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return str(obj)

tools_service = ToolsService()
