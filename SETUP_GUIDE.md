# Cortex AI - Initial Setup & Admin User Guide

## First-Time Installation

When deploying Cortex AI for a new customer/company, follow these steps:

### 1. Database Setup

```bash
# Create database
createdb cortex_ai

# Enable pgvector extension
psql cortex_ai -c "CREATE EXTENSION vector;"

# Run migrations
cd backend
alembic upgrade head
```

### 2. Create Admin User

**Option A: Using Admin Script (Recommended)**

```bash
cd backend
python -m scripts.create_admin
```

Follow the prompts:
```
Email: admin@yourcompany.com
Password: (enter secure password)
Full Name: Company Administrator
```

The script will:
- ✅ Create the user account
- ✅ Create a personal tenant/workspace
- ✅ Set the user as tenant owner
- ✅ Grant superuser privileges
- ✅ Display user and tenant IDs

**Option B: Using Registration UI**

1. Go to `http://localhost:3000/register`
2. Register with admin email
3. User is auto-created with personal tenant as owner
4. Manually grant superuser via database:

```sql
-- Make user a superuser
UPDATE users SET is_superuser = true WHERE email = 'admin@company.com';
```

**Option C: Direct Database Insert**

```sql
-- Insert user (hash your password first)
INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser)
VALUES (
  gen_random_uuid(),
  'admin@company.com',
  '$2b$12$...',  -- bcrypt hash
  'Admin User',
  true,
  true
);

-- Create tenant
INSERT INTO tenants (id, name, slug)
VALUES (gen_random_uuid(), 'Company Workspace', 'company-workspace');

-- Link user to tenant as owner
INSERT INTO tenant_members (tenant_id, user_id, role)
VALUES (
  (SELECT id FROM tenants WHERE slug = 'company-workspace'),
  (SELECT id FROM users WHERE email = 'admin@company.com'),
  'owner'
);
```

### 3. Verify Admin Setup

```bash
# List all users
python -m scripts.create_admin
# Select option 2: "List All Users"
```

Expected output:
```
Email                         Name                  Superuser    Active
admin@company.com            Admin User            Yes          Yes
```

## Testing the UI

### Access the Application

1. **Start Backend**:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start Frontend**:
```bash
cd frontend
npm run dev
```

3. **Open Browser**: http://localhost:3000

### Test RBAC Features

#### 1. Login Flow
- Navigate to login page
- Enter admin credentials
- Should redirect to dashboard

#### 2. Manage Team (Tenant Members)
- Click **"Manage Team"** button in sidebar
- Should open Tenant Members modal
- Features to test:
  - ✅ View existing members
  - ✅ Click "Add Member" button
  - ✅ Select user from dropdown
  - ✅ Choose role (owner/admin/member/viewer)
  - ✅ Add member
  - ✅ Update member role via dropdown
  - ✅ Remove member via trash icon

**Expected Behavior**:
- Owners can add/remove/update members
- Cannot remove last owner (protected)
- Non-owners get 403 error

#### 3. Resource Sharing (Agents)
- Go to **Agents** page
- Create a test agent if none exist
- Click **Share** button (Share2 icon) on agent card
- Modal opens with two tabs:
  
  **Tab 1: Specific User**
  - Select user from dropdown
  - Choose permission: Viewer | Editor | Admin
  - Click "Share"
  
  **Tab 2: Tenant Role**
  - Select role: owner | admin | member | viewer
  - Choose permission level
  - Click "Share"

**Expected Behavior**:
- User-level sharing: Only that user gets access
- Role-level sharing: All users with that role get access
- Permission enforcement: viewer < editor < admin

#### 4. Cross-User Access Testing

Create two users for testing:

```bash
# User A (Owner)
Email: usera@test.com
Password: test123

# User B (Regular user)
Email: userb@test.com
Password: test123
```

**Test Scenario**:
1. Login as User A
2. Create agent (name: "Test Agent")
3. Logout
4. Login as User B
5. Go to Agents page
6. **Expected**: Should NOT see "Test Agent" (403)
7. Logout
8. Login as User A
9. Click Share on "Test Agent"
10. Share with User B as "viewer"
11. Logout
12. Login as User B
13. **Expected**: Can now see "Test Agent"
14. Try to delete agent
15. **Expected**: Gets 403 (viewer cannot delete)

### Test API Endpoints

```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin@company.com&password=yourpassword" | jq -r .access_token)

# List tenant members
curl http://localhost:8000/api/v1/tenants/{tenant_id}/members \
  -H "Authorization: Bearer $TOKEN"

# Add member
curl -X POST http://localhost:8000/api/v1/tenants/{tenant_id}/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid", "role": "member"}'

# Share agent
curl -X POST http://localhost:8000/api/v1/access/agent/{agent_id}/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid", "access_level": "viewer"}'
```

## Multi-Company Setup

For hosting multiple companies:

### Option 1: Separate Databases (Recommended)
```bash
# Company A
createdb cortex_company_a
python manage.py migrate --database=company_a

# Company B
createdb cortex_company_b
python manage.py migrate --database=company_b
```

### Option 2: Shared Database with Tenant Isolation
All data is already isolated by `tenant_id`:
- Create admin user for each company
- Each gets their own tenant
- Data is automatically isolated
- No cross-tenant access

## Post-Setup Checklist

- [ ] Admin user created with superuser flag
- [ ] Admin can login successfully
- [ ] "Manage Team" button visible in sidebar
- [ ] Can add/remove tenant members
- [ ] Can share resources (agents, KB, etc.)
- [ ] Permission levels work (viewer/editor/admin)
- [ ] Cross-user access control verified
- [ ] Role-based sharing functional
- [ ] Environment variables configured
- [ ] Database backups scheduled
- [ ] HTTPS enabled (production)
- [ ] CORS origins restricted (production)

## Troubleshooting

### User Cannot Login
```bash
# Check user exists and is active
python -m scripts.create_admin  # Option 2

# Verify password
psql cortex_ai -c "SELECT email, is_active, is_superuser FROM users WHERE email='user@example.com';"
```

### "Manage Team" Button Missing
- Ensure user has `tenant_memberships` loaded
- Check `user.tenant_memberships[0].tenant_id` exists
- Verify frontend is fetching `/auth/me` correctly

### Share Button Not Working
- Check browser console for errors
- Verify `/admin/users` endpoint returns user list
- Ensure backend running on port 8000

### 403 Errors on Resource Access
- Verify resource has correct `tenant_id`
- Check `ResourceAccess` table for sharing records
- Confirm user's tenant membership

## Production Deployment

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/cortex_prod"
export SECRET_KEY="your-super-secret-key-min-32-chars"
export ALLOWED_ORIGINS="https://app.yourcompany.com"

# Create admin
python -m scripts.create_admin

# Start with proper workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

**Support**: For issues, check logs in `backend/logs/` or contact support.
