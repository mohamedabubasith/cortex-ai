# Frontend RBAC UI - Manual Testing Guide

## Prerequisites

✅ Backend running on `http://localhost:8000`  
✅ Frontend running on `http://localhost:3000`  
✅ At least 2 test users created

## Test Scenario 1: Manage Team Modal

### Steps:

1. **Login to Dashboard**
   - Navigate to http://localhost:3000
   - Login with: `abubasith86@gmail.com` (or your admin email)
   - Should redirect to `/dashboard`

2. **Open Manage Team Modal**
   - Look in left sidebar for **"Manage Team"** button
   - It should be above "Light/Dark Mode" toggle
   - Click **"Manage Team"**

3. **Verify Modal Contents**
   - ✅ Modal title: "Tenant Members"
   - ✅ Subtitle: "Manage users in your tenant"
   - ✅ "Add Member" button (dashed border)
   - ✅ List of current members with:
     - User avatar icon (role-specific color)
     - Email address
     - Name
     - Role dropdown (owner/admin/member/viewer)
     - Trash icon to remove

4. **Test Add Member**
   - Click **"Add Member"** button
   - Form should expand with:
     - User email dropdown
     - Role dropdown (default: member)
     - Cancel & Add buttons
   - Select a user (e.g., `abubasith456@gmail.com`)
   - Choose role: `member`
   - Click **"Add"**
   - ✅ Member should appear in list
   - ✅ Success message (via alert)

5. **Test Update Role**
   - Find the newly added member in list
   - Click their role dropdown
   - Change to `admin`
   - ✅ Should update immediately
   - ✅ Icon color changes to NVIDIA green

6. **Test Remove Member**
   - Click trash icon next to member
   - ✅ Confirm dialog appears
   - Confirm deletion
   - ✅ Member removed from list

7. **Test Last Owner Protection**
   - Try to remove yourself (the owner)
   - ✅ Should see error: "Cannot remove the last owner"

**Expected UI**:
```
╔═══════════════════════════════════════════╗
║  👥 Tenant Members                    ✕  ║
╟───────────────────────────────────────────╢
║  Manage users in your tenant              ║
║                                           ║
║  ┌─────────────────────────────────────┐ ║
║  │  ➕ Add Member                      │ ║
║  └─────────────────────────────────────┘ ║
║                                           ║
║  ┌─────────────────────────────────────┐ ║
║  │ 👑 Abu                              │ ║
║  │    abubasith86@gmail.com            │ ║
║  │    [Owner ▼]                    🗑  │ ║
║  └─────────────────────────────────────┘ ║
║                                           ║
║                          [Done]           ║
╚═══════════════════════════════════════════╝
```

---

## Test Scenario 2: Share Resource Modal (Agents)

### Steps:

1. **Navigate to Agents**
   - Click **"Agents"** in sidebar
   - Should show list of agents

2. **Create Agent (if none exist)**
   - Click **"New Agent"** button
   - Fill in:
     - Name: "Test Share Agent"
     - Description: "Testing sharing"
   - Save agent

3. **Open Share Modal**
   - Find agent card with 3 buttons: Configure, Share, Delete
   - Click **Share** button (middle icon)
   - ✅ Modal opens: "Share Resource"

4. **Test User-Level Sharing**
   - Verify "Share with" toggle shows 2 options:
     - **Specific User** (UserPlus icon)
     - **Tenant Role** (Shield icon)
   - Click **"Specific User"** (should be selected by default)
   - Select user from dropdown
   - Choose permission level:
     - **Viewer** (Eye icon) - Read only
     - **Editor** (Edit icon) - Can edit
     - **Admin** (Settings icon) - Full control
   - Click **"Share"**
   - ✅ Success alert: "Agent shared successfully!"

5. **Test Role-Based Sharing**
   - Click Share button again
   - Click **"Tenant Role"** tab
   - Select role from dropdown:
     - owner
     - admin
     - member
     - viewer
   - ✅ Note appears: "All users with this role in your tenant will get access"
   - Choose permission level (viewer/editor/admin)
   - Click **"Share"**
   - ✅ Success alert

**Expected UI**:
```
╔═══════════════════════════════════════════════╗
║  👥 Share Resource                        ✕  ║
╟───────────────────────────────────────────────╢
║  Share "Test Share Agent" with users or roles║
║                                               ║
║  Share with:                                  ║
║  ┌──────────────┬──────────────┐             ║
║  │ 👤 Specific  │  🛡️ Tenant  │             ║
║  │    User      │     Role     │             ║
║  └──────────────┴──────────────┘             ║
║                                               ║
║  Select User:                                 ║
║  [user@example.com          ▼]               ║
║                                               ║
║  Permission Level:                            ║
║  ┌─────────┬─────────┬─────────┐            ║
║  │ 👁 View │ ✏️ Edit │ ⚙️ Admin│            ║
║  └─────────┴─────────┴─────────┘            ║
║                                               ║
║                  [Cancel] [Share]             ║
╚═══════════════════════════════════════════════╝
```

---

## Test Scenario 3: Cross-User Access

### Steps:

**As User A (Owner)**:
1. Login as `abubasith86@gmail.com`
2. Go to Agents
3. Create agent: "Shared Test Agent"
4. Click Share button
5. Share with `abubasith456@gmail.com` as **Viewer**
6. Logout

**As User B (Recipient)**:
1. Login as `abubasith456@gmail.com`
2. Go to Agents
3. ✅ Should see "Shared Test Agent"
4. Click on agent to view
5. ✅ Can see details
6. Try to click Delete
7. ✅ Should get error (viewers cannot delete)

**As User A (Owner)**:
1. Login back as `abubasith86@gmail.com`
2. Go to Manage Team
3. Add `abubasith456@gmail.com` as **Admin** to your tenant
4. Logout

**As User B (Now Admin)**:
1. Login as `abubasith456@gmail.com`
2. Go to Agents
3. ✅ Should now see ALL agents in User A's tenant
4. Try to delete an agent
5. ✅ Should succeed (admins can delete)

---

## Test Scenario 4: Theme & Responsive Design

### Dark Mode Test:
1. Click **"Dark Mode"** button in sidebar
2. ✅ All modals switch to dark theme
3. ✅ NVIDIA green (#76B900) still visible
4. ✅ Text readable (white on dark)
5. ✅ Borders visible (white/10 opacity)

### Light Mode Test:
1. Click **"Light Mode"** button
2. ✅ All modals switch to light theme
3. ✅ NVIDIA green still prominent
4. ✅ Text readable (dark on white)
5. ✅ Borders visible (gray-200)

### Mobile Test:
1. Resize browser to mobile width (< 768px)
2. ✅ Sidebar collapses
3. ✅ Hamburger menu appears
4. ✅ Modals remain centered
5. ✅ All buttons stack vertically

---

## Verification Checklist

### UI Components Created:
- [x] `ShareResourceModal.tsx`
- [x] `TenantMembersModal.tsx`
- [x] Share button on agent cards
- [x] "Manage Team" button in sidebar

### Integration Points:
- [x] Agents page (`/dashboard/agents/page.tsx`)
- [x] Dashboard layout (`/dashboard/layout.tsx`)
- [x] API calls to backend endpoints

### Backend Endpoints Used:
- [x] `GET /api/v1/tenants/{id}/members`
- [x] `POST /api/v1/tenants/{id}/members`
- [x] `PUT /api/v1/tenants/{id}/members/{user_id}`
- [x] `DELETE /api/v1/tenants/{id}/members/{user_id}`
- [x] `POST /api/v1/access/{type}/{id}/share`
- [x] `GET /api/v1/admin/users` (for user list)

---

## Expected Behavior Summary

| Action | Expected Result |
|--------|----------------|
| Open Manage Team | Modal appears with current members |
| Add member | User added to tenant, appears in list |
| Update role | Role changes, icon updates |
| Remove member | Member removed from list |
| Remove last owner | Error: "Cannot remove last owner" |
| Share with user | User gets access to resource |
| Share with role | All users with role get access |
| Viewer tries delete | 403 error or disabled button |
| Admin deletes | Success |
| Toggle theme | All modals update theme |

---

## Common Issues & Fixes

### Modal Not Appearing
- Check browser console for errors
- Verify `tenant_memberships[0]` exists in user object
- Check that backend is running on port 8000

### User Dropdown Empty
- Verify `/api/v1/admin/users` endpoint works
- Check network tab for 403 errors
- Ensure user has proper permissions

### Share Not Working
- Check `/api/v1/access/agent/{id}/share` endpoint
- Verify `user_id` or `tenant_role` is being sent
- Check backend logs for validation errors

### Styles Not Applied
- Verify Tailwind classes are compiling
- Check `isDark` prop is working
- Ensure `cn()` utility is imported

---

## Browser Console Commands

Test API calls directly:

```javascript
// Get current user
fetch('/api/v1/auth/me', {
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
}).then(r => r.json()).then(console.log)

// List tenant members
const tenantId = 'your-tenant-id'
fetch(`/api/v1/tenants/${tenantId}/members`, {
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
}).then(r => r.json()).then(console.log)

// Share agent
fetch(`/api/v1/access/agent/agent-id/share`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ user_id: 'user-id', access_level: 'viewer' })
}).then(r => r.json()).then(console.log)
```

---

**Testing Complete When**:
✅ All 4 scenarios pass  
✅ No console errors  
✅ UI looks good in dark & light themes  
✅ Responsive on mobile  
✅ Backend API calls succeed  

**Report Issues**: Note any errors, unexpected behavior, or missing features.
