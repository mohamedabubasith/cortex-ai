import datetime
import httpx
import json
from typing import List, Dict, Any, Callable, Optional

class ToolsService:
    def __init__(self):
        self.tools_registry = {}
        self.register_default_tools()
        # Agent-specific context
        self.current_agent_db_connections = []
        self.database_service = None

    def set_agent_context(self, db_connections: List[Any], database_service: Any):
        """Set the current agent's database connections for this tool execution context"""
        self.current_agent_db_connections = db_connections
        self.database_service = database_service

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

    def get_agent_specific_tools(self, db_connections: List[Any]) -> List[Dict[str, Any]]:
        """Get tool definitions including database tools for the specific agent"""
        tools = self.get_tool_definitions()
        
        # Add database query tool if agent has database connections
        if db_connections and len(db_connections) > 0:
            # Build description with available databases
            db_list = ", ".join([f'"{db.name}" ({db.type} database at {db.host})' for db in db_connections])
            
            tools.append({
                "type": "function",
                "function": {
                    "name": "query_database",
                    "description": f"Execute SQL SELECT queries to retrieve data from databases. Available databases: {db_list}. Use this tool whenever the user asks about tables, columns, data, records, or wants to query/search database information. You MUST use this tool to get actual data - do not make up or guess data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "database_name": {
                                "type": "string",
                                "description": f"The name of the database to query. Must be one of: {', '.join([db.name for db in db_connections])}",
                                "enum": [db.name for db in db_connections]
                            },
                            "query": {
                                "type": "string",
                                "description": "The SQL SELECT query to execute. Must start with 'SELECT'. Examples: 'SELECT * FROM information_schema.tables', 'SELECT column_name FROM information_schema.columns WHERE table_name = \\'users\\'', 'SELECT * FROM products LIMIT 10'"
                            }
                        },
                        "required": ["database_name", "query"]
                    }
                }
            })
        
        return tools

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [tool["schema"] for tool in self.tools_registry.values()]

    async def execute_tool(self, name: str, arguments: str) -> str:
        # Handle database query tool specially
        if name == "query_database":
            return await self.query_database_tool(arguments)
        
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

    async def query_database_tool(self, arguments: str) -> str:
        """Execute a database query tool call"""
        try:
            args = json.loads(arguments) if arguments else {}
            database_name = args.get("database_name")
            query = args.get("query", "").strip()
            
            if not database_name or not query:
                return json.dumps({"error": "Both database_name and query are required"})
            
            # Validate it's a SELECT query for safety
            if not query.lower().strip().startswith("select"):
                return json.dumps({"error": "Only SELECT queries are allowed for safety"})
            
            # Find the database connection
            db_conn = None
            for conn in self.current_agent_db_connections:
                if conn.name == database_name:
                    db_conn = conn
                    break
            
            if not db_conn:
                available = ", ".join([db.name for db in self.current_agent_db_connections])
                return json.dumps({"error": f"Database '{database_name}' not found. Available: {available}"})
            
            # Execute the query
            if self.database_service:
                results = await self.database_service.execute_query(db_conn, query)
                
                if isinstance(results, dict) and "error" in results:
                    return json.dumps(results)
                
                # Format results nicely
                return json.dumps({
                    "success": True,
                    "rows": results,
                    "row_count": len(results) if isinstance(results, list) else 0
                })
            else:
                return json.dumps({"error": "Database service not available"})
                
        except Exception as e:
            return json.dumps({"error": f"Database query failed: {str(e)}"})

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
