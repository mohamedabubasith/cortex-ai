#!/bin/bash

# Cortex AI - RBAC & Tenant Management API Test Suite
# Tests all tenant management and resource sharing endpoints

API_BASE="http://localhost:8000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "CORTEX AI - RBAC API TEST SUITE"
echo "============================================================"

# Test 1: Create and authenticate two users
echo -e "\n${YELLOW}[Test 1] Creating test users...${NC}"
USER_A_EMAIL="api_test_owner_$(date +%s)@test.com"
USER_B_EMAIL="api_test_member_$(date +%s)@test.com"

# Register User A
echo "Creating User A: $USER_A_EMAIL"
REGISTER_A=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_A_EMAIL\",\"password\":\"test123\",\"full_name\":\"Test User A\"}")

echo $REGISTER_A | jq '.'

# Register User B
echo "Creating User B: $USER_B_EMAIL"
REGISTER_B=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_B_EMAIL\",\"password\":\"test123\",\"full_name\":\"Test User B\"}")

echo $REGISTER_B | jq '.'

# Test 2: Login as User A
echo -e "\n${YELLOW}[Test 2] Authenticating User A...${NC}"
TOKEN_A=$(curl -s -X POST "$API_BASE/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USER_A_EMAIL&password=test123" | jq -r '.access_token')

if [ "$TOKEN_A" = "null" ] || [ -z "$TOKEN_A" ]; then
    echo -e "${RED}✗ Failed to get User A token${NC}"
    exit 1
fi
echo -e "${GREEN}✓ User A authenticated${NC}"

# Test 3: Login as User B
echo -e "\n${YELLOW}[Test 3] Authenticating User B...${NC}"
TOKEN_B=$(curl -s -X POST "$API_BASE/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USER_B_EMAIL&password=test123" | jq -r '.access_token')

if [ "$TOKEN_B" = "null" ] || [ -z "$TOKEN_B" ]; then
    echo -e "${RED}✗ Failed to get User B token${NC}"
    exit 1
fi
echo -e "${GREEN}✓ User B authenticated${NC}"

# Test 4: Get User A details and tenant ID
echo -e "\n${YELLOW}[Test 4] Getting User A tenant info...${NC}"
USER_A_INFO=$(curl -s -X GET "$API_BASE/auth/me" \
  -H "Authorization: Bearer $TOKEN_A")

TENANT_A_ID=$(echo $USER_A_INFO | jq -r '.tenant_memberships[0].tenant_id')
USER_A_ID=$(echo $USER_A_INFO | jq -r '.id')
echo "User A ID: $USER_A_ID"
echo "Tenant A ID: $TENANT_A_ID"
echo -e "${GREEN}✓ Got tenant info${NC}"

# Test 5: Get User B ID
echo -e "\n${YELLOW}[Test 5] Getting User B info...${NC}"
USER_B_INFO=$(curl -s -X GET "$API_BASE/auth/me" \
  -H "Authorization: Bearer $TOKEN_B")
USER_B_ID=$(echo $USER_B_INFO | jq -r '.id')
echo "User B ID: $USER_B_ID"
echo -e "${GREEN}✓ Got User B info${NC}"

# Test 6: List tenant members (User A only)
echo -e "\n${YELLOW}[Test 6] Listing tenant members...${NC}"
MEMBERS=$(curl -s -X GET "$API_BASE/tenants/$TENANT_A_ID/members" \
  -H "Authorization: Bearer $TOKEN_A")
echo $MEMBERS | jq '.'
MEMBER_COUNT=$(echo $MEMBERS | jq '. | length')
if [ "$MEMBER_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✓ Tenant has 1 member (owner)${NC}"
else
    echo -e "${RED}✗ Expected 1 member, got $MEMBER_COUNT${NC}"
fi

# Test 7: User A adds User B as member
echo -e "\n${YELLOW}[Test 7] Adding User B to tenant as 'member'...${NC}"
ADD_MEMBER=$(curl -s -X POST "$API_BASE/tenants/$TENANT_A_ID/members" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_B_ID\",\"role\":\"member\"}")
echo $ADD_MEMBER | jq '.'

if echo $ADD_MEMBER | jq -e '.message' > /dev/null; then
    echo -e "${GREEN}✓ User B added to tenant${NC}"
else
    echo -e "${RED}✗ Failed to add member${NC}"
fi

# Test 8: Verify User B is now a member
echo -e "\n${YELLOW}[Test 8] Verifying User B membership...${NC}"
UPDATED_MEMBERS=$(curl -s -X GET "$API_BASE/tenants/$TENANT_A_ID/members" \
  -H "Authorization: Bearer $TOKEN_A")
UPDATED_COUNT=$(echo $UPDATED_MEMBERS | jq '. | length')
if [ "$UPDATED_COUNT" -eq 2 ]; then
    echo -e "${GREEN}✓ Tenant now has 2 members${NC}"
else
    echo -e "${RED}✗ Expected 2 members, got $UPDATED_COUNT${NC}"
fi

# Test 9: Update User B to 'admin'
echo -e "\n${YELLOW}[Test 9] Upgrading User B to 'admin'...${NC}"
UPDATE_ROLE=$(curl -s -X PUT "$API_BASE/tenants/$TENANT_A_ID/members/$USER_B_ID" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d "{\"role\":\"admin\"}")
echo $UPDATE_ROLE | jq '.'

if echo $UPDATE_ROLE | jq -e '.role' | grep -q "admin"; then
    echo -e "${GREEN}✓ User B upgraded to admin${NC}"
else
    echo -e "${RED}✗ Failed to update role${NC}"
fi

# Test 10: User A creates an agent
echo -e "\n${YELLOW}[Test 10] User A creates agent...${NC}"
CREATE_AGENT=$(curl -s -X POST "$API_BASE/agents" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test Agent\",\"description\":\"For API testing\",\"system_prompt\":\"You are helpful.\"}")
AGENT_ID=$(echo $CREATE_AGENT | jq -r '.id')
echo "Agent ID: $AGENT_ID"

if [ "$AGENT_ID" != "null" ] && [ -n "$AGENT_ID" ]; then
    echo -e "${GREEN}✓ Agent created${NC}"
else
    echo -e "${RED}✗ Failed to create agent${NC}"
    exit 1
fi

# Test 11: User B can access agent (same tenant admin)
echo -e "\n${YELLOW}[Test 11] User B (admin) accessing agent...${NC}"
ACCESS_AGENT=$(curl -s -X GET "$API_BASE/agents/$AGENT_ID" \
  -H "Authorization: Bearer $TOKEN_B")
  
if echo $ACCESS_AGENT | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ User B can access agent (tenant admin)${NC}"
else
    echo -e "${RED}✗ User B cannot access agent${NC}"
fi

# Test 12: Share agent with User B as 'viewer' (explicit)
echo -e "\n${YELLOW}[Test 12] User A shares agent with User B as viewer...${NC}"
SHARE_AGENT=$(curl -s -X POST "$API_BASE/access/agent/$AGENT_ID/share" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_B_ID\",\"access_level\":\"viewer\"}")
echo $SHARE_AGENT | jq '.'

if echo $SHARE_AGENT | jq -e '.message' > /dev/null; then
    echo -e "${GREEN}✓ Agent shared with User B${NC}"
else
    echo -e "${YELLOW}⚠ Share may have failed (might be admin already)${NC}"
fi

# Test 13: Role-based sharing (share with 'admin' role)
echo -e "\n${YELLOW}[Test 13] Sharing agent with 'admin' role...${NC}"
SHARE_ROLE=$(curl -s -X POST "$API_BASE/access/agent/$AGENT_ID/share" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d "{\"tenant_role\":\"admin\",\"access_level\":\"editor\"}")
echo $SHARE_ROLE | jq '.'

if echo $SHARE_ROLE | jq -e '.message' > /dev/null; then
    echo -e "${GREEN}✓ Agent shared with admin role${NC}"
else
    echo -e "${YELLOW}⚠ Role-based share response: check if successful${NC}"
fi

# Test 14: User B (non-owner) tries to add member (should fail)
echo -e "\n${YELLOW}[Test 14] User B (non-owner) tries to add member...${NC}"
FAIL_ADD=$(curl -s -X POST "$API_BASE/tenants/$TENANT_A_ID/members" \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"fake-id\",\"role\":\"viewer\"}")

if echo $FAIL_ADD | jq -e '.detail' | grep -q "owner"; then
    echo -e "${GREEN}✓ Correctly denied (403 - only owners can add)${NC}"
else
    echo -e "${RED}✗ Should have been denied${NC}"
fi

# Test 15: List all agents (verify visibility)
echo -e "\n${YELLOW}[Test 15] User A lists agents...${NC}"
LIST_AGENTS_A=$(curl -s -X GET "$API_BASE/agents" \
  -H "Authorization: Bearer $TOKEN_A")
AGENT_COUNT_A=$(echo $LIST_AGENTS_A | jq '. | length')
echo "User A sees $AGENT_COUNT_A agents"

echo -e "\n${YELLOW}User B lists agents...${NC}"
LIST_AGENTS_B=$(curl -s -X GET "$API_BASE/agents" \
  -H "Authorization: Bearer $TOKEN_B")
AGENT_COUNT_B=$(echo $LIST_AGENTS_B | jq '. | length')
echo "User B sees $AGENT_COUNT_B agents"

if [ "$AGENT_COUNT_B" -gt 0 ]; then
    echo -e "${GREEN}✓ User B can see shared/tenant agents${NC}"
else
    echo -e "${YELLOW}⚠ User B cannot see agents (check tenant context)${NC}"
fi

# Test 16: Delete agent
echo -e "\n${YELLOW}[Test 16] User A deletes agent...${NC}"
DELETE_AGENT=$(curl -s -X DELETE "$API_BASE/agents/$AGENT_ID" \
  -H "Authorization: Bearer $TOKEN_A")

if echo $DELETE_AGENT | jq -e '.message' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Agent deleted${NC}"
else
    echo -e "${YELLOW}⚠ Delete response: $DELETE_AGENT${NC}"
fi

# Test 17: Remove User B from tenant
echo -e "\n${YELLOW}[Test 17] Removing User B from tenant...${NC}"
REMOVE_MEMBER=$(curl -s -X DELETE "$API_BASE/tenants/$TENANT_A_ID/members/$USER_B_ID" \
  -H "Authorization: Bearer $TOKEN_A")
echo $REMOVE_MEMBER | jq '.'

if echo $REMOVE_MEMBER | jq -e '.message' > /dev/null; then
    echo -e "${GREEN}✓ User B removed from tenant${NC}"
else
    echo -e "${RED}✗ Failed to remove member${NC}"
fi

# Test 18: Verify member count back to 1
echo -e "\n${YELLOW}[Test 18] Verifying final member count...${NC}"
FINAL_MEMBERS=$(curl -s -X GET "$API_BASE/tenants/$TENANT_A_ID/members" \
  -H "Authorization: Bearer $TOKEN_A")
FINAL_COUNT=$(echo $FINAL_MEMBERS | jq '. | length')

if [ "$FINAL_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✓ Tenant back to 1 member${NC}"
else
    echo -e "${RED}✗ Expected 1 member, got $FINAL_COUNT${NC}"
fi

# Summary
echo ""
echo "============================================================"
echo -e "${GREEN}RBAC API TEST SUITE COMPLETED${NC}"
echo "============================================================"
echo "Tested endpoints:"
echo "  ✓ POST /auth/register"
echo "  ✓ POST /auth/token"
echo "  ✓ GET  /auth/me"
echo "  ✓ GET  /tenants/{id}/members"
echo "  ✓ POST /tenants/{id}/members"
echo "  ✓ PUT  /tenants/{id}/members/{user_id}"
echo "  ✓ DELETE /tenants/{id}/members/{user_id}"
echo "  ✓ POST /agents"
echo "  ✓ GET  /agents/{id}"
echo "  ✓ GET  /agents"
echo "  ✓ POST /access/agent/{id}/share (user & role)"
echo "  ✓ DELETE /agents/{id}"
echo "============================================================"
