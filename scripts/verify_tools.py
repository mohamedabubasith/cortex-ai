import sys
import os
import asyncio
import logging

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

# Mock objects
class MockDB:
    def __init__(self, name, type, host):
        self.name = name
        self.type = type
        self.host = host

class MockDatabaseService:
    async def execute_query(self, db_conn, query):
        if "users" in query:
            return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        return []

async def test_tools():
    print("Testing Tools Service...")
    
    try:
        from app.services.tools_service import tools_service
        
        # 1. Test Default Tools Registration
        definitions = tools_service.get_tool_definitions()
        print(f"Registered tools: {[t['function']['name'] for t in definitions]}")
        
        expected_tools = ["get_current_datetime", "get_public_ip", "get_current_weather", "get_current_location"]
        for tool in expected_tools:
            if not any(t['function']['name'] == tool for t in definitions):
                print(f"ERROR: Tool {tool} not found in definitions")
            else:
                print(f"Verified {tool} exists")

        # 2. Test Time Tool
        print("\nTesting get_current_datetime...")
        result = await tools_service.execute_tool("get_current_datetime", "{}")
        print(f"Result: {result}")
        if "current_datetime" in result:
             print("SUCCESS: Time tool returned datetime")
        else:
             print("FAILURE: Time tool missing data")

        # 3. Test Network Tool (Public IP) - might fail if no internet, but test the call
        print("\nTesting get_public_ip...")
        result = await tools_service.execute_tool("get_public_ip", "{}")
        print(f"Result: {result}")
        
        # 4. Test Weather Tool (Real API)
        print("\nTesting get_current_weather...")
        # Tokyo coordinates
        args = '{"latitude": 35.6895, "longitude": 139.6917}' 
        result = await tools_service.execute_tool("get_current_weather", args)
        print(f"Result: {result}")
        if "current" in result and "temperature" in result:
            print("SUCCESS: Weather tool returned data")
        
        # 5. Test Location Tool
        print("\nTesting get_current_location...")
        result = await tools_service.execute_tool("get_current_location", "{}")
        print(f"Result: {result}")

        # 6. Test Database Tool (Context)
        print("\nTesting query_database...")
        mock_dbs = [MockDB("test_db", "postgres", "localhost")]
        mock_service = MockDatabaseService()
        
        # Set context
        tools_service.set_agent_context(mock_dbs, mock_service)
        
        # Check dynamic schema
        agent_tools = tools_service.get_agent_specific_tools(mock_dbs)
        if any(t['function']['name'] == "query_database" for t in agent_tools):
            print("Verified query_database tool added to agent tools")
        else:
            print("FAILURE: query_database tool NOT found in agent tools")
            
        # Execute query
        args = '{"database_name": "test_db", "query": "SELECT * FROM users"}'
        result = await tools_service.execute_tool("query_database", args)
        print(f"Result: {result}")
        if "Alice" in result:
            print("SUCCESS: Database query returned mock data")
        else:
            print("FAILURE: Database query failed")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tools())
