-- Enable RLS and Create Policies for Multi-Tenant Resource Isolation

-- 1. Helper Functions
CREATE OR REPLACE FUNCTION current_app_user() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION current_app_tenant() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::uuid;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION is_admin() RETURNS boolean AS $$
  SELECT current_setting('app.is_super_admin', true) = 'true' 
      OR current_setting('app.is_tenant_admin', true) = 'true';
$$ LANGUAGE sql STABLE;

-- 2. Enable RLS on Tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE database_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_shares ENABLE ROW LEVEL SECURITY;

-- 3. Policy: Resource Shares (The Gatekeeper)
-- SELECT: Visible if you can see the resource... 
-- Actually, easier: Visible if in same tenant. (Simpler for now)
CREATE POLICY share_tenant_isolation ON resource_shares
    USING (tenant_id = current_app_tenant());

-- 4. Policy: Projects (Agents)
-- SELECT
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
      WHERE rs.resource_id = id
      AND rs.resource_type = 'agent'
      AND rs.grantee_id = current_app_user()
    )
  )
);

-- INSERT
CREATE POLICY agent_insert_policy ON projects
FOR INSERT
WITH CHECK (
  tenant_id = current_app_tenant()
  AND owner_id = current_app_user()
);

-- UPDATE
CREATE POLICY agent_update_policy ON projects
FOR UPDATE
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR owner_id = current_app_user()
    OR EXISTS (
      SELECT 1 FROM resource_shares rs
      WHERE rs.resource_id = id
      AND rs.resource_type = 'agent'
      AND rs.grantee_id = current_app_user()
      AND rs.permission IN ('write', 'admin')
    )
  )
);

-- DELETE
CREATE POLICY agent_delete_policy ON projects
FOR DELETE
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR owner_id = current_app_user()
  )
);

-- 5. Policy: Knowledge Bases
-- SELECT
CREATE POLICY kb_select_policy ON knowledge_bases
FOR SELECT
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR user_id = current_app_user() -- Note: user_id is owner
    OR EXISTS (
      SELECT 1 FROM resource_shares rs
      WHERE rs.resource_id = id
      AND rs.resource_type = 'kb'
      AND rs.grantee_id = current_app_user()
    )
     -- Compatibility with the specific 'knowledge_base_members' table if we keep it:
    OR EXISTS (
       SELECT 1 FROM knowledge_base_members kbm
       WHERE kbm.kb_id = id
       AND kbm.user_id = current_app_user()
    )
  )
);

-- INSERT
CREATE POLICY kb_insert_policy ON knowledge_bases
FOR INSERT
WITH CHECK (
  tenant_id = current_app_tenant()
  AND user_id = current_app_user()
);

-- UPDATE
CREATE POLICY kb_update_policy ON knowledge_bases
FOR UPDATE
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR user_id = current_app_user()
    OR EXISTS (
      SELECT 1 FROM resource_shares rs
      WHERE rs.resource_id = id
      AND rs.resource_type = 'kb'
      AND rs.grantee_id = current_app_user()
      AND rs.permission IN ('write', 'admin')
    )
  )
);

-- DELETE
CREATE POLICY kb_delete_policy ON knowledge_bases
FOR DELETE
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR user_id = current_app_user()
  )
);

-- 6. Policy: Database Connections
-- SELECT
CREATE POLICY db_select_policy ON database_connections
FOR SELECT
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR user_id = current_app_user()
    OR EXISTS (
      SELECT 1 FROM resource_shares rs
      WHERE rs.resource_id = id
      AND rs.resource_type = 'db_connection'
      AND rs.grantee_id = current_app_user()
    )
  )
);

-- INSERT
CREATE POLICY db_insert_policy ON database_connections
FOR INSERT
WITH CHECK (
  tenant_id = current_app_tenant()
  AND user_id = current_app_user()
);

-- UPDATE
CREATE POLICY db_update_policy ON database_connections
FOR UPDATE
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR user_id = current_app_user()
    OR EXISTS (
      SELECT 1 FROM resource_shares rs
      WHERE rs.resource_id = id
      AND rs.resource_type = 'db_connection'
      AND rs.grantee_id = current_app_user()
      AND rs.permission IN ('write', 'admin')
    )
  )
);

-- DELETE
CREATE POLICY db_delete_policy ON database_connections
FOR DELETE
USING (
  tenant_id = current_app_tenant() 
  AND (
    is_admin() 
    OR user_id = current_app_user()
  )
);
