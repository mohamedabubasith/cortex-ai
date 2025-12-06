# Chatbot Application - AI Assistant with Knowledge Base

Production-ready AI chatbot with chat interface, knowledge base, and LLM integration.

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd chatbot

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Deploy

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📦 Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js UI |
| Backend | 8000 | FastAPI Server |
| PostgreSQL | 5432 | Database |
| Nginx | 80/443 | Reverse Proxy (optional) |

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Security
SECRET_KEY=your_random_secret_key

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# CORS (update with your domain)
CORS_ORIGINS=https://yourdomain.com
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🌐 Production Deployment

### Option 1: Docker Compose (Recommended)

```bash
# With Nginx reverse proxy
docker-compose --profile production up -d

# SSL Setup
# 1. Place SSL certificates in nginx/ssl/
# 2. Update nginx.conf with your domain
# 3. Uncomment HTTPS server block
# 4. Restart nginx
docker-compose restart nginx
```

### Option 2: Cloud Platforms

#### AWS (EC2)
```bash
# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy
git clone <repo>
cd chatbot
cp .env.example .env
# Edit .env
docker-compose up -d
```

#### Google Cloud (Cloud Run)
```bash
# Build & Push images
gcloud builds submit --tag gcr.io/PROJECT_ID/chatbot-backend ./backend
gcloud builds submit --tag gcr.io/PROJECT_ID/chatbot-frontend ./frontend

# Deploy
gcloud run deploy chatbot-backend --image gcr.io/PROJECT_ID/chatbot-backend --platform managed
gcloud run deploy chatbot-frontend --image gcr.io/PROJECT_ID/chatbot-frontend --platform managed
```

#### Digital Ocean
```bash
# Use App Platform with docker-compose.yml
# Or deploy to Droplet following AWS EC2 steps
```

---

## 🧪 Testing

### Health Checks
```bash
# Backend
curl http://localhost:8000/health

# Frontend  
curl http://localhost:3000/api/health

# Database
docker-compose exec postgres pg_isready
```

### End-to-End Test
```bash
# Create test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Run automated tests
cd backend
python test_kb_e2e.py
```

---

## 📊 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Container Stats
```bash
docker stats
```

### Database Backup
```bash
docker-compose exec postgres pg_dump -U chatbot_user chatbot > backup.sql
```

---

## 🔒 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Change `POSTGRES_PASSWORD`
- [ ] Update `CORS_ORIGINS` with your domain
- [ ] Enable HTTPS/SSL in nginx
- [ ] Use strong database passwords
- [ ] Enable firewall (ports 22, 80, 443 only)
- [ ] Regular security updates
- [ ] Implement rate limiting
- [ ] Enable database backups

---

## 🛠️ Maintenance

### Update Application
```bash
git pull
docker-compose build
docker-compose up -d
```

### Database Migration
```bash
docker-compose exec backend alembic upgrade head
```

### Restart Services
```bash
docker-compose restart backend
docker-compose restart frontend
```

### Clean Up
```bash
# Stop all services
docker-compose down

# Remove volumes (⚠️ deletes data)
docker-compose down -v
```

---

## 📚 API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🏗️ Architecture

```
┌─────────────┐
│   Nginx     │  Port 80/443
│  (Optional) │
└──────┬──────┘
       │
   ┌───┴────────────────┐
   │                    │
┌──▼────────┐    ┌─────▼─────┐
│ Frontend  │    │  Backend  │
│ Next.js   │    │  FastAPI  │
│ Port 3000 │    │ Port 8000 │
└───────────┘    └─────┬─────┘
                       │
                ┌──────▼────────┐
                │  PostgreSQL   │
                │  Port 5432    │
                └───────────────┘
```

---

## 🎯 Features

✅ Chat Interface with streaming responses  
✅ Knowledge Base (PDF, DOCX, TXT upload)  
✅ LLM Integration (OpenAI, custom endpoints)  
✅ User Authentication & Authorization  
✅ Session Management  
✅ Database Persistence (PostgreSQL)  
✅ Production-ready Docker setup  
✅ Health checks & monitoring  
✅ Rate limiting & security headers  
✅ SSL/HTTPS support  

---

## 📝 License

[Your License]

---

## 🤝 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@yourdomain.com

---

## 🚦 Status

- **Backend**: ✅ Production Ready
- **Frontend**: ✅ Production Ready  
- **Database**: ✅ PostgreSQL
- **Docker**: ✅ Configured
- **Tests**: ✅ Automated Testing Available

**Ready for Cloud Deployment!** 🚀
