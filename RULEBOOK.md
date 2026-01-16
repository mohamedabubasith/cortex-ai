# Cortex AI - Open Source Rulebook

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Access Control & Security](#access-control--security)
- [API Reference](#api-reference)
- [Setup & Installation](#setup--installation)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Overview

**Cortex AI** is an enterprise-grade AI agent platform with multi-tenancy, role-based access control, and comprehensive knowledge base management.

### Key Features

- 🤖 **AI Agents**: Create custom AI agents with configurable LLMs, knowledge bases, and tools
- 📚 **Knowledge Base**: RAG-powered document search using LangChain and ChromaDB
- 🔌 **MCP Integration**: Model Context Protocol for external tool connections
- 🗄️ **Database Connections**: Query databases via natural language
- 🔐 **Enterprise RBAC**: Granular permissions with user and role-based sharing
- 🏢 **Multi-Tenancy**: Complete tenant isolation with cascade management
- 🔍 **Web Search**: Real-time web search integration
- 📊 **Analytics**: Usage tracking and audit logging

---

## Architecture

### Tech Stack

**Backend**:
- FastAPI (Python 3.12)
- PostgreSQL (pgvector enabled)
- ChromaDB (vector storage)
- LangChain (RAG framework)
- SQLAlchemy (ORM)

**Frontend**:
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS

**Authentication**:
- JWT tokens
- SSO support (Keycloak-ready)
- JIT user provisioning

### Directory Structure

```
cortex-ai/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration, database, utilities
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── repositories/  # Data access layer
│   │   ├── services/      # Business logic
│   │   ├── routers/       # API endpoints
│   │   └── middleware/    # CORS, audit, etc.
│   ├── tests/             # Test suites
│   └── data/              # Uploads, ChromaDB, models
├── frontend/
│   └── app/
│       ├── dashboard/     # Main UI
│       └── chat/          # Public chat interface
└── docs/                  # Documentation
```

---

## Access Control & Security

### Tenant Hierarchy

```
Superuser (admin)
  └── Tenant Owner
      └── Tenant Admin
          └── Tenant Member
              └── Tenant Viewer
```

### Resource Permissions

| Level | Read | Edit | Delete | Share |
|-------|------|------|--------|-------|
| **Viewer** | ✅ | ❌ | ❌ | ❌ |
| **Editor** | ✅ | ✅ | ❌ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ |

### Sharing Rules

1. **User-Level Sharing**: Share resources with specific users
2. **Role-Level Sharing**: Share with all users having a specific role in the tenant
3. **Default Visibility**: All resources are private (tenant-scoped)
4. **Ownership**: Resource owners always have full access

### Permission Matrix

| Action | Owner | Tenant Owner | Tenant Admin | Explicit Share | Public |
|--------|-------|--------------|--------------|----------------|--------|
| View own resources | ✅ | ✅ | ✅ | ✅ | ✅ |
| View tenant resources | ❌ | ✅ | ✅ | ❌ | ❌ |
| Share resources | ✅ | ✅ | ❌ | ⚠️ (if admin) | ❌ |
| Add tenant members | ❌ | ✅ | ❌ | ❌ | ❌ |
| Remove tenant members | ❌ | ✅ | ❌ | ❌ | ❌ |
| Delete tenant | ❌ | ❌ | ❌ | ❌ | ❌ (super admin only) |

---

## API Reference

### Base URL

```
Production: https://api.cortex-ai.com/api/v1
Development: http://localhost:8000/api/v1
```

### Authentication

All endpoints require `Authorization: Bearer <token>` header except public chat endpoints.

### Endpoints

#### Authentication

```http
POST   /auth/register          # Register new user
POST   /auth/token             # Login
GET    /auth/me                # Get current user
POST   /auth/forgot-password   # Request password reset
POST   /auth/reset-password    # Reset password
```

#### Agents

```http
POST   /agents                 # Create agent
GET    /agents                 # List agents (tenant-scoped)
GET    /agents/{id}            # Get agent details
PUT    /agents/{id}            # Update agent
DELETE /agents/{id}            # Delete agent
POST   /agents/{id}/regenerate-url  # Regenerate share token
```

#### Knowledge Base

```http
POST   /kb/upload              # Upload document
GET    /kb                     # List documents
GET    /kb/{id}/status         # Get processing status
POST   /kb/{id}/query          # Query document
DELETE /kb/{id}                # Delete document
```

#### LLM Configurations

```http
POST   /llm                    # Create LLM config
GET    /llm                    # List configs
GET    /llm/{id}               # Get config
PUT    /llm/{id}               # Update config
DELETE /llm/{id}               # Delete config
POST   /llm/test               # Test connection
```

#### Resources (DB & MCP)

```http
POST   /resources/databases    # Create DB connection
GET    /resources/databases    # List DB connections
POST   /resources/databases/test  # Test connection
DELETE /resources/databases/{id}  # Delete connection

POST   /resources/mcp          # Create MCP connection
GET    /resources/mcp          # List MCP connections
POST   /resources/mcp/{id}/sync  # Sync tools
DELETE /resources/mcp/{id}     # Delete connection

GET    /resources/mcp/hub      # Get MCP hub registry
```

#### Access Management

```http
POST   /access/{type}/{id}/share  # Share resource
DELETE /access/{access_id}        # Revoke access
```

**Share Request**:
```json
{
  "user_id": "uuid",           // Specific user (optional)
  "tenant_role": "admin",      // OR role-based (optional)
  "access_level": "viewer"     // viewer|editor|admin
}
```

#### Tenant Management

```http
POST   /tenants/{id}/members           # Add member
DELETE /tenants/{id}/members/{user_id} # Remove member
PUT    /tenants/{id}/members/{user_id} # Update role
GET    /tenants/{id}/members           # List members
DELETE /tenants/{id}                   # Delete tenant (super admin)
```

**Add Member Request**:
```json
{
  "user_id": "uuid",
  "role": "member"  // owner|admin|member|viewer
}
```

#### Chat

```http
GET    /chat/public/{token}           # Get public agent info
POST   /chat/public/{token}/chat      # Chat with public agent (SSE)
GET    /chat/public/{token}/sessions  # Get chat sessions
POST   /chat/test/{agent_id}/chat     # Test chat (authenticated)
```

#### Analytics

```http
GET    /analytics/events              # Get analytics events
GET    /analytics/api-hits            # API usage stats
GET    /analytics/token-usage         # LLM token usage
```

---

## Setup & Installation

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- Redis (optional, for caching)

### Backend Setup

```bash
# Clone repository
git clone https://github.com/your-org/cortex-ai.git
cd cortex-ai/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb cortex_ai
psql cortex_ai -c "CREATE EXTENSION vector;"

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local

# Start development server
npm run dev
```

### Docker Setup

```bash
# Full stack with docker-compose
docker-compose up -d

# Backend only
docker-compose up backend

# With hot reload
docker-compose -f docker-compose.dev.yml up
```

---

## Development Guidelines

### Code Style

**Python**:
- Follow PEP 8
- Use type hints
- Max line length: 120
- Docstrings for public methods

**TypeScript**:
- Use strict mode
- Functional components with hooks
- Props interfaces for all components

### Repository Pattern

All data access through repositories:

```python
class SomeRepository(BaseRepository[Model]):
    def __init__(self, db: AsyncSession):
        super().__init__(Model, db)
    
    async def custom_method(self, ...):
        # Business-specific queries
```

### Service Layer

Business logic in services:

```python
class SomeService:
    def __init__(self, db: AsyncSession):
        self.repo = SomeRepository(db)
        self.access_service = AccessControlService(db)
    
    async def perform_action(self, user: User, ...):
        # Check permissions
        if not await self.access_service.has_access(...):
            raise HTTPException(403)
        
        # Execute business logic
        return await self.repo.some_method(...)
```

### Adding New Resources

1. **Model** (`models/models.py`):
```python
class NewResource(Base):
    __tablename__ = "new_resources"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    owner_id = Column(String, ForeignKey("users.id"))
    # ... fields
```

2. **Repository** (`repositories/new_resource_repository.py`):
```python
class NewResourceRepository(BaseRepository[NewResource]):
    def __init__(self, db: AsyncSession):
        super().__init__(NewResource, db)
```

3. **Service** (`services/new_resource_service.py`):
```python
class NewResourceService:
    def __init__(self, db: AsyncSession):
        self.repo = NewResourceRepository(db)
        self.access_service = AccessControlService(db)
```

4. **Router** (`routers/new_resource.py`):
```python
@router.post("")
async def create_resource(
    data: Schema,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    service = NewResourceService(db)
    return await service.create(data, current_user, current_tenant.id)
```

5. **Register** (`main.py`):
```python
from app.routers import new_resource
app.include_router(new_resource.router, prefix=f"{settings.API_V1_STR}/new-resource")
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_rbac_sharing.py

# With coverage
pytest --cov=app --cov-report=html

# Integration tests
pytest tests/integration/
```

### Test Structure

```python
async def test_scenario():
    """Test description"""
    # Setup
    user = await create_test_user()
    
    # Execute
    result = await service.perform_action(user, ...)
    
    # Assert
    assert result.status == "success"
```

### RBAC Test Scenarios

Required tests for all new resources:
- ✅ Owner can create/read/update/delete
- ✅ Non-owner gets 403 on access
- ✅ Shared viewer can read only
- ✅ Shared editor cannot delete
- ✅ Shared admin can delete
- ✅ Tenant admin can access tenant resources
- ✅ Cross-tenant isolation

---

## Deployment

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/cortex_ai

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256

# CORS
ALLOWED_ORIGINS=https://cortex-ai.com,https://app.cortex-ai.com

# Storage
UPLOAD_DIR=/var/cortex/uploads
CHROMA_DB_PATH=/var/cortex/chroma

# LLM (optional defaults)
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o

# Search (optional)
BRAVE_SEARCH_API_KEY=your-key

# Auth (optional SSO)
AUTH_PROVIDER=keycloak
KEYCLOAK_SERVER_URL=https://auth.cortex-ai.com
KEYCLOAK_CLIENT_ID=cortex-ai
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure proper `ALLOWED_ORIGINS`
- [ ] Use strong `SECRET_KEY` (32+ chars)
- [ ] Enable HTTPS
- [ ] Setup PostgreSQL with pgvector
- [ ] Configure backup strategy
- [ ] Setup monitoring (Sentry, DataDog)
- [ ] Enable rate limiting
- [ ] Configure CDN for static assets
- [ ] Setup CI/CD pipeline
- [ ] Database migrations tested
- [ ] Load balancer configured
- [ ] Logging aggregation setup

### Scaling Considerations

**Horizontal Scaling**:
- Stateless backend (use Redis for sessions)
- Separate ChromaDB instance
- CDN for frontend
- Database read replicas

**Performance**:
- Connection pooling (SQLAlchemy)
- Query optimization
- Caching (Redis)
- Background tasks (Celery)

---

## Contributing

### Workflow

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### PR Requirements

- ✅ All tests passing
- ✅ Code coverage >80%
- ✅ Type hints added
- ✅ Documentation updated
- ✅ No linting errors
- ✅ RBAC tests for new resources

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Support

- 📧 Email: support@cortex-ai.com
- 💬 Discord: https://discord.gg/cortex-ai
- 📖 Docs: https://docs.cortex-ai.com
- 🐛 Issues: https://github.com/your-org/cortex-ai/issues

---

**Built with ❤️ by the Cortex AI Team**
