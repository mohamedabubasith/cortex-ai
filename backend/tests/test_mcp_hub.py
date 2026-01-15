import sys
import os
from typing import List, Dict

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.routers.resources import MCP_HUB_REGISTRY
from app.schemas.schemas import MCPConnectionCreate

class TestFailed(Exception):
    pass

def assert_true(condition, message):
    if not condition:
        raise TestFailed(message)

def test_mcp_hub_registry_integrity():
    """Verify the integrity of the MCP Hub Registry."""
    assert_true(isinstance(MCP_HUB_REGISTRY, list), "Registry must be a list")
    assert_true(len(MCP_HUB_REGISTRY) > 0, "Registry cannot be empty")
    
    for item in MCP_HUB_REGISTRY:
        # Check required fields
        assert_true("id" in item, f"Missing id in {item}")
        assert_true("name" in item, f"Missing name in {item}")
        assert_true("server_url" in item, f"Missing server_url in {item}")
        assert_true("protocol" in item, f"Missing protocol in {item}")
        assert_true("env_vars" in item, f"Missing env_vars in {item}")
        
        # Check env_vars structure
        if item["env_vars"]:
            for env_var in item["env_vars"]:
                assert_true("name" in env_var, f"Missing name in env_var of {item['id']}")
                assert_true("label" in env_var, f"Missing label in env_var of {item['id']}")
                assert_true("type" in env_var, f"Missing type in env_var of {item['id']}")
                assert_true("required" in env_var, f"Missing required in env_var of {item['id']}")

def test_mcp_hub_to_schema_conversion():
    """Verify that Hub items can be converted to MCPConnectionCreate schemas."""
    
    for item in MCP_HUB_REGISTRY:
        # Simulate user providing values for env_vars
        simulated_inputs = {}
        for env_var in item["env_vars"]:
            simulated_inputs[env_var["name"]] = "test_value"
            
        # Create connection schema (simulating frontend logic)
        try:
            connection_data = {
                "name": item["name"],
                "server_url": item["server_url"],
                "protocol": item["protocol"],
                "auth_headers": simulated_inputs if simulated_inputs else None
            }
            
            # This should not raise validation error
            schema = MCPConnectionCreate(**connection_data)
            
            assert_true(schema.name == item["name"], "Name mismatch")
            assert_true(schema.server_url == item["server_url"], "Server URL mismatch")
            assert_true(schema.protocol == item["protocol"], "Protocol mismatch")
            if simulated_inputs:
                assert_true(schema.auth_headers == simulated_inputs, "Auth headers mismatch")
                
        except Exception as e:
            raise TestFailed(f"Failed to create schema for {item['id']}: {str(e)}")

def test_specific_plugin_configs():
    """Verify specific plugin configurations match expectations."""
    
    registry_map = {item["id"]: item for item in MCP_HUB_REGISTRY}
    
    # Check GitHub
    if "github" in registry_map:
        github = registry_map["github"]
        env_names = [e["name"] for e in github["env_vars"]]
        assert_true("GITHUB_PERSONAL_ACCESS_TOKEN" in env_names, "Missing GITHUB_PERSONAL_ACCESS_TOKEN")
        
    # Check Brave
    if "brave" in registry_map:
        brave = registry_map["brave"]
        env_names = [e["name"] for e in brave["env_vars"]]
        assert_true("BRAVE_API_KEY" in env_names, "Missing BRAVE_API_KEY")
        
    # Check Postgres
    if "postgres" in registry_map:
        pg = registry_map["postgres"]
        env_names = [e["name"] for e in pg["env_vars"]]
        assert_true("POSTGRES_URL" in env_names, "Missing POSTGRES_URL")
        
    # Check Filesystem
    if "filesystem" in registry_map:
        fs = registry_map["filesystem"]
        assert_true(fs["env_vars"] == [], "Filesystem should have empty env_vars")

if __name__ == "__main__":
    print("Running MCP Hub Registry Checks...")
    try:
        test_mcp_hub_registry_integrity()
        print("✓ Registry Integrity Check Passed")
        
        test_mcp_hub_to_schema_conversion()
        print("✓ Schema Conversion Check Passed")
        
        test_specific_plugin_configs()
        print("✓ Specific Plugin Configs Check Passed")
        
        print("\nAll code-level checks passed successfully!")
    except TestFailed as e:
        print(f"\n❌ Check Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        sys.exit(1)
