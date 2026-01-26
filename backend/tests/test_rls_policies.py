import pytest
import asyncio
import uuid
import httpx
from sqlalchemy import text
from app.main import app
from app.core.database import engine
import pytest_asyncio
import os

from app.models.models import Base

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True)
async def setup_rls_schema():
    """Manually apply RLS migration for testing"""
    async with engine.begin() as conn:
        # Create all tables first
        await conn.run_sync(Base.metadata.create_all)
        
        # CLEANUP: Drop potential debug policies from previous failed runs
        try:
            await conn.execute(text("DROP POLICY IF EXISTS debug_bypass_test ON database_connections"))
            await conn.execute(text("DROP POLICY IF EXISTS db_select_policy ON database_connections"))
            await conn.execute(text("DROP POLICY IF EXISTS db_insert_policy ON database_connections"))
            await conn.execute(text("DROP POLICY IF EXISTS share_tenant_isolation ON resource_shares"))
        except Exception:
            pass

        # Define RLS Policies Manually
        rls_stmts = [
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
            "CREATE POLICY share_tenant_isolation ON resource_shares USING (tenant_id = current_app_tenant());",
            
            # DB Connections
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
            """
            CREATE POLICY db_insert_policy ON database_connections
            FOR INSERT
            WITH CHECK (
              tenant_id = current_app_tenant()
              AND user_id = current_app_user()
            );
            """
        ]
        
        # Execute RLS Statements
        for stmt in rls_stmts:
             try:
                 await conn.execute(text(stmt))
             except Exception as e:
                 # Ignore if already exists or other non-fatal setup errors in dev
                 print(f"DEBUG SETUP WARNING: {e}")
        
        # Verify RLS is enabled on database_connections
        result = await conn.execute(text("SELECT relrowsecurity FROM pg_class WHERE relname = 'database_connections'"))
        rls_enabled = result.scalar()
        print(f"DEBUG: database_connections RLS Enabled? {rls_enabled}")
        
    yield
    
    # Teardown
    async with engine.begin() as conn:
         pass

@pytest_asyncio.fixture(scope="session")
async def async_client():
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_rls_db_connection_isolation(async_client):
    """Verify RLS on database_connections table"""
    async with engine.begin() as conn:
        # Check if current user is superuser
        is_superuser = await conn.execute(text("SELECT usesuper FROM pg_user WHERE usename = current_user"))
        if is_superuser.scalar():
            print("WARNING: Running as superuser. RLS might be bypassed. creating temporary role.")
            
        # Create a specific role for implementation of RLS checks
        # Because superusers bypass RLS
        role_name = "rls_tester"
        await conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{role_name}') THEN
                    CREATE ROLE {role_name} WITH NOLOGIN NOBYPASSRLS;
                END IF;
            END
            $$;
        """))
            
        # Grant permissions to this role
        await conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {role_name}"))
        await conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role_name}"))
        
        # 1. Setup Data (As Superuser/Owner)
        tenant_id = str(uuid.uuid4())
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4()) # Same tenant
        user_x = str(uuid.uuid4()) # Diff tenant
        tenant_x = str(uuid.uuid4())
        
        await conn.execute(text(f"INSERT INTO tenants (id, name, slug) VALUES ('{tenant_id}', 'T1', '{tenant_id}')"))
        await conn.execute(text(f"INSERT INTO tenants (id, name, slug) VALUES ('{tenant_x}', 'TX', '{tenant_x}')"))
        
        await conn.execute(text(f"INSERT INTO users (id, email) VALUES ('{user_a}', 'a-{user_a}@t1.com')"))
        await conn.execute(text(f"INSERT INTO users (id, email) VALUES ('{user_b}', 'b-{user_b}@t1.com')"))
        await conn.execute(text(f"INSERT INTO users (id, email) VALUES ('{user_x}', 'x-{user_x}@tx.com')"))
        
        # Create Resource (DB Conn) by User A
        res_id = str(uuid.uuid4())
        await conn.execute(text(f"""
            INSERT INTO database_connections (id, user_id, tenant_id, name, type, host, port, username, database_name)
            VALUES ('{res_id}', '{user_a}', '{tenant_id}', 'DB-A', 'postgres', 'localhost', 5432, 'u', 'd')
        """))
        
        # SWITCH TO RESTRICTED ROLE
        await conn.execute(text(f"SET ROLE {role_name}"))
        
        # Verify Role
        role_check = await conn.execute(text("SELECT current_user, session_user"))
        print(f"DEBUG: Current Context: {role_check.fetchone()}")
        
        try:
            # 2. Test User B Access (Should be BLOCKED initially if not shared)
            # Set Session for B
            await conn.execute(text(f"set app.current_user_id = '{user_b}'"))
            await conn.execute(text(f"set app.current_tenant_id = '{tenant_id}'"))
            await conn.execute(text("set app.is_tenant_admin = 'false'"))
            await conn.execute(text("set app.is_super_admin = 'false'"))
            
            # Verify Role again
            role_check = await conn.execute(text("SELECT current_user, session_user, current_setting('app.current_user_id', true), current_setting('app.is_super_admin', true)"))
            print(f"DEBUG: Context at Check: {role_check.fetchone()}")

            # DEBUG: Why can B see it?
            # Check row data
            row_check = await conn.execute(text(f"SELECT id, user_id, tenant_id FROM database_connections WHERE id = '{res_id}'"))
            row = row_check.fetchone()
            print(f"DEBUG: Row Visible to B: {row}")
            
            # Check Policy Conditions manually
            policy_check = await conn.execute(text(f"""
                SELECT 
                    ('{tenant_id}' = current_app_tenant()) as tenant_match,
                    (is_admin()) as is_admin,
                    ('{user_a}' = current_app_user()) as user_match
            """))
            print(f"DEBUG: Policy Logic Check: {policy_check.fetchone()}")

            result = await conn.execute(text(f"SELECT count(*) FROM database_connections WHERE id = '{res_id}'"))
            count = result.scalar()
            print(f"DEBUG: Count result: {count}")
            assert count == 0, "User B should NOT see User A's resource yet"
            
            # 3. Share with User B
            # We need to switch back to Owner/Admin to insert the share?
            # Or can User A do it? User A is owner.
            # Let's switch to User A
            await conn.execute(text(f"set app.current_user_id = '{user_a}'"))
            await conn.execute(text(f"set app.current_tenant_id = '{tenant_id}'"))
            
            share_id = str(uuid.uuid4())
            await conn.execute(text(f"""
                INSERT INTO resource_shares (id, tenant_id, resource_id, resource_type, grantee_id, permission)
                VALUES ('{share_id}', '{tenant_id}', '{res_id}', 'db_connection', '{user_b}', 'read')
            """))
            
            # 4. Test User B Access (Should be ALLOWED now)
            await conn.execute(text(f"set app.current_user_id = '{user_b}'"))
            await conn.execute(text(f"set app.current_tenant_id = '{tenant_id}'"))
            
            # DEBUG SHARES
            # shares_check = await conn.execute(text("SELECT * FROM resource_shares"))
            # print(f"DEBUG: Shares visible to B: {shares_check.fetchall()}")

            result = await conn.execute(text(f"SELECT count(*) FROM database_connections WHERE id = '{res_id}'"))
            count = result.scalar()
            assert count == 1, "User B SHOULD see resource after sharing"
            
            # 5. Test User X (Diff Tenant) - Should NEVER see it
            await conn.execute(text(f"set app.current_user_id = '{user_x}'"))
            await conn.execute(text(f"set app.current_tenant_id = '{tenant_x}'"))
            
            result = await conn.execute(text(f"SELECT count(*) FROM database_connections WHERE id = '{res_id}'"))
            assert result.scalar() == 0, "User X (Diff Tenant) must NOT see resource"
            
        finally:
            # Revert Role
            await conn.execute(text("RESET ROLE"))
