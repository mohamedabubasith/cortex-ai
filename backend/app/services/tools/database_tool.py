import json
from typing import Dict, Any, List
from .base_tool import BaseTool

class DatabaseTool(BaseTool):
    def __init__(self, db_connections: List[Any], database_service: Any):
        self.db_connections = db_connections
        self.database_service = database_service

    @property
    def name(self) -> str:
        return "query_database"

    @property
    def schema(self) -> Dict[str, Any]:
        if not self.db_connections:
            return {}
            
        db_list = ", ".join([f'"{db.name}" ({db.type} database at {db.host})' for db in self.db_connections])
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": f"Execute SQL SELECT queries to retrieve data from databases. Available databases: {db_list}. Use this tool whenever the user asks about tables, columns, data, records, or wants to query/search database information. You MUST use this tool to get actual data - do not make up or guess data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database_name": {
                            "type": "string",
                            "description": f"The name of the database to query. Must be one of: {', '.join([db.name for db in self.db_connections])}",
                            "enum": [db.name for db in self.db_connections]
                        },
                        "query": {
                            "type": "string",
                            "description": "The SQL SELECT query to execute. Must start with 'SELECT'. Examples: 'SELECT * FROM information_schema.tables', 'SELECT column_name FROM information_schema.columns WHERE table_name = \\'users\\'', 'SELECT * FROM products LIMIT 10'"
                        }
                    },
                    "required": ["database_name", "query"]
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        database_name = kwargs.get("database_name")
        query = kwargs.get("query", "").strip()
        
        if not database_name or not query:
            return {"error": "Both database_name and query are required"}
        
        if not query.lower().strip().startswith("select"):
            return {"error": "Only SELECT queries are allowed for safety"}
        
        db_conn = next((conn for conn in self.db_connections if conn.name == database_name), None)
        
        if not db_conn:
            available = ", ".join([db.name for db in self.db_connections])
            return {"error": f"Database '{database_name}' not found. Available: {available}"}
        
        if self.database_service:
            try:
                results = await self.database_service.execute_query(db_conn, query)
                if isinstance(results, dict) and "error" in results:
                    return results

                MAX_ROWS = 50
                truncated = False
                if isinstance(results, list) and len(results) > MAX_ROWS:
                    results = results[:MAX_ROWS]
                    truncated = True
                
                return {
                    "success": True,
                    "rows": results,
                    "row_count": len(results),
                    "truncated": truncated,
                    "note": "Results truncated to 50 rows for performance" if truncated else ""
                }
            except Exception as e:
                return {"error": f"Database query failed: {str(e)}"}
        else:
            return {"error": "Database service not available"}
