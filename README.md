# Basivo 🧠

An intelligent, agentic AI platform for your data — built and operated by [Mohamed Abu Basith](https://chat.basivo.in).

Basivo combines **RAG (Retrieval-Augmented Generation)** with **SQL Agent** capabilities, letting you chat with your documents (PDF, DOCX, PPTX) and live databases (PostgreSQL, MySQL) in a single unified interface. Live at [chat.basivo.in](https://chat.basivo.in).

Built with **FastAPI**, **Next.js**, **Haystack**, **Unstructured**, **Ollama**, **Qdrant**, and **PostgreSQL**.

---

## ✨ Key Features

- **📚 Knowledge Base (RAG)**: Upload PDF, DOCX, PPTX, TXT, and Markdown. Ingestion uses Unstructured (fast or high-resolution), Haystack chunking, Ollama embeddings, and Qdrant vector search with citation-friendly metadata.
- **🗄️ SQL Agent**: Connect to live databases (PostgreSQL, MySQL, etc.) and ask questions about your data ("Show me the latest users", "Count orders by month").
- **🤖 Multi-LLM Support**: Compatible with OpenAI (GPT-4o, GPT-3.5) and any OpenAI-compatible API (LocalLLM, vLLM).
- **⚡ Real-time Streaming**: Smooth, typewriter-style chat responses.
- **🔐 Enterprise Security**: Role-based access control (RBAC), encrypted credentials, and secure session management.
- **🐳 Production Ready**: Fully containerized with Docker Compose, ready for deployment on AWS, GCP, or DigitalOcean.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, AsyncPG
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Framer Motion
- **AI/ML**: Haystack pipelines, Unstructured parsing, Ollama embeddings, Qdrant, OpenAI API
- **Database**: PostgreSQL 16 (application data); knowledge-base vectors stored in **Qdrant**
- **Infrastructure**: Docker, Docker Compose, Nginx (Optional)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/mohamedabubasith/cortex-ai.git
cd cortex-ai
```

### 2. Configure Environment
Create a `.env` file in the `backend` directory (or root, depending on setup):

```bash
cp .env.example .env
```

**Minimal `.env` Configuration:**
```ini
# --- Database ---
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=chat_db

# --- AI / LLM ---
OPENAI_API_KEY=sk-your-key-here

# --- Security ---
SECRET_KEY=change_this_to_a_secure_random_string

# --- Knowledge base (Haystack + Unstructured + Ollama + Qdrant) ---
UNSTRUCTURED_API_URL=https://your-unstructured-host/
OLLAMA_BASE_URL=https://your-ollama-host/
OLLAMA_MODEL=paraphrase-multilingual:latest
QDRANT_URL=https://your-qdrant-host/
QDRANT_COLLECTION=cortex_kb
QDRANT_API_KEY=   # if Qdrant requires API key / Bearer

VECTOR_DB_PROVIDER=pgvector
ENABLE_BACKEND_ACCESS_CONTROL=true
REQUIRE_AUTHENTICATION=true
```

### 3. Deploy with One Command
We provide a production-ready deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
1. Pull the latest code.
2. Build the Docker containers (Frontend, Backend, Database).
3. Start the services.

### 4. Access the App
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌐 Production Deployment (Google Cloud / AWS)

For deploying to a cloud server (e.g., Google Compute Engine, AWS EC2):

1. **Provision a VM** (Ubuntu 22.04 recommended) with Docker installed.
2. **Clone the repo** and set up your `.env` file.
3. **Set Public URL**:
   In your `.env`, set `NEXT_PUBLIC_API_URL` to your server's public IP or domain:
   ```ini
   NEXT_PUBLIC_API_URL=http://<YOUR_STATIC_IP>:8000
   ```
4. **Run Deployment**:
   ```bash
   ./deploy.sh
   ```

---


## 📧 Email Configuration (SMTP)

To enable "Forgot Password" emails, you need an SMTP provider.

### Recommendations (Free Tier)
1.  **Gmail (Recommended for NO DOMAIN)**:
    -   Best if you don't have a custom domain but need to send emails to **anyone**.
    -   Go to **Google Account** > **Security** > **2-Step Verification**.
    -   Scroll to bottom > **App passwords**.
    -   Create one named "Basivo".
    -   Use `smtp.gmail.com`, `587`, your full email (User), and the 16-char App Password.

2.  **Brevo / Resend**:
    -   **REQUIRES Verified Domain** (e.g., `your-site.com`) to send to anyone.
    -   Without a domain, you can only send to your *own* email (Testing mode).

### Update your `.env`
```ini
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_login_email@example.com
SMTP_PASSWORD=xsmtpsib-...key...
EMAILS_FROM_EMAIL=no-reply@yourdomain.com
```

---

## 🛠️ Deployment & Customization

### 1. Docker Configuration
The project is fully containerized. To customize the deployment for your environment:

- **Database**: By default, `docker-compose.yml` uses a local `pgvector` container. For production, connect to an external managed database (AWS RDS, Google Cloud SQL) by updating `DB_HOST`, `DB_USER`, and `DB_PASSWORD` in `.env`.
- **Ports**: If ports `3000` (Frontend) or `8000` (Backend) are occupied, map them to different ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "8080:3000" # Access frontend at localhost:8080
  ```

### 2. Branding
- **App Name**: Update `frontend/app/layout.tsx` and `frontend/components/chat/Sidebar.tsx`.
- **Theme**: The primary color is defined as `--nvidia-green` in `frontend/app/globals.css`.

### 3. Authentication & Access
- The app includes built-in JWT authentication.
- To disable public registration (for private internal tools), modify `backend/app/routers/auth.py` or restrict access at the network level (VPN/Firewall).

---

## 🧪 Development

To run the project locally for development (with hot-reloading):

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by [Mohamed Abu Basith](https://github.com/mohamedabubasith)**
