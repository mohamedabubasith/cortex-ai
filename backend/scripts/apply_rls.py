import asyncio
import os
from sqlalchemy import text
from app.core.database import engine
from app.models.models import Base

# RLS Policies Definition
# Using $$ for function bodies to avoid quoting hell
RLS_STMTS = [
    # 1. Helper Functions
    """
    CREATE OR REPLACE FUNCTION current_app_user() RETURNS text AS $$
      SELECT NULLIF(current_setting('app.current_user_id', true), '');
    $$ LANGUAGE sql STABLE;
    """,
    """
    CREATE OR REPLACE FUNCTION current_app_tenant() RETURNS text AS $$
      SELECT NULLIF(current_setting('app.current_tenant_id', true), '');
    $$ LANGUAGE sql STABLE;
    """,
    """
    CREATE OR REPLACE FUNCTION is_admin() RETURNS boolean AS $$
      SELECT current_setting('app.is_super_admin', true) = 'true' 
          OR current_setting('app.is_tenant_admin', true) = 'true';
    $$ LANGUAGE sql STABLE;
    """,
    
    # 2. Enable RLS
    "ALTER TABLE projects ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE database_connections ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE database_connections FORCE ROW LEVEL SECURITY;",
    "ALTER TABLE llm_configurations ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE resource_shares ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE resource_shares FORCE ROW LEVEL SECURITY;",
    
    # 3. Policies
    # Resource Shares
    "DROP POLICY IF EXISTS share_tenant_isolation ON resource_shares;",
    "CREATE POLICY share_tenant_isolation ON resource_shares USING (tenant_id = current_app_tenant());",
    
    # Projects
    "DROP POLICY IF EXISTS agent_select_policy ON projects;",
    """
    CREATE POLICY agent_select_policy ON projects
    FOR SELECT
    USING (
      tenant_id = current_app_tenant() 
      AND (
        is_admin() 
        OR owner_id = current_app_user()
        OR is_public = true
        OR EXISTS (
          SELECT 1 FROM resource_shares rs
          WHERE rs.resource_id = projects.id
          AND rs.resource_type = 'agent'
          AND rs.grantee_id = current_app_user()
        )
      )
    );
    """,
    
    # DB Connections
    "DROP POLICY IF EXISTS db_select_policy ON database_connections;",
    """
    CREATE POLICY db_select_policy ON database_connections
    FOR SELECT
    USING (
      tenant_id = current_app_tenant() 
      AND (
        is_admin() 
        OR user_id = current_app_user()
        OR EXISTS (
          SELECT 1 FROM resource_shares rs
          WHERE rs.resource_id = database_connections.id
          AND rs.resource_type = 'db_connection'
          AND rs.grantee_id = current_app_user()
        )
      )
    );
    """,
    
    # Knowledge Bases
    "DROP POLICY IF EXISTS kb_select_policy ON knowledge_bases;",
    """
    CREATE POLICY kb_select_policy ON knowledge_bases
    FOR SELECT
    USING (
      tenant_id = current_app_tenant() 
      AND (
        is_admin() 
        OR user_id = current_app_user()
        OR EXISTS (
          SELECT 1 FROM resource_shares rs
          WHERE rs.resource_id = knowledge_bases.id
          AND rs.resource_type = 'kb'
          AND rs.grantee_id = current_app_user()
        )
      )
    );
    """,
]

async def apply_rls():
    print("Applying RLS Policies...")
    async with engine.begin() as conn:
        for stmt in RLS_STMTS:
            print(f"Executing: {stmt.strip().splitlines()[0]}...") # Print first line only
            try:
                # Use begin_nested to act as a SAVEPOINT
                # This ensures one failure doesn't abort the entire transaction
                async with conn.begin_nested():
                    await conn.execute(text(stmt))
            except Exception as e:
                # Ignore idempotent errors
                err_str = str(e).lower()
                if "already exists" in err_str or "does not exist" in err_str:
                     print("  -> Skipped (Already exists/Not found)")
                else:
                     print(f"  -> ERROR: {e}")

    print("RLS Policies application finished.")

if __name__ == "__main__":
    asyncio.run(apply_rls())
