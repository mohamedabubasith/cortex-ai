# Cortex AI 🧠

**Production-ready AI Assistant with Knowledge Base (RAG) & SQL Agent Capabilities**

Cortex AI is a powerful, open-source AI platform that combines **RAG (Retrieval-Augmented Generation)** with **SQL Agent** capabilities. It allows users to chat with their documents (PDFs, text) AND their live databases (PostgreSQL, MySQL) in a single, unified interface.

Built with **FastAPI**, **Next.js**, **Cognee**, and **pgvector**.

---

## ✨ Key Features

- **📚 Knowledge Base (RAG)**: Upload and chat with PDF, DOCX, and TXT files. Powered by Cognee for advanced graph-based retrieval.
- **🗄️ SQL Agent**: Connect to live databases (PostgreSQL, MySQL, etc.) and ask questions about your data ("Show me the latest users", "Count orders by month").
- **🤖 Multi-LLM Support**: Compatible with OpenAI (GPT-4o, GPT-3.5) and any OpenAI-compatible API (LocalLLM, vLLM).
- **⚡ Real-time Streaming**: Smooth, typewriter-style chat responses.
- **🔐 Enterprise Security**: Role-based access control (RBAC), encrypted credentials, and secure session management.
- **🐳 Production Ready**: Fully containerized with Docker Compose, ready for deployment on AWS, GCP, or DigitalOcean.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, AsyncPG
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Framer Motion
- **AI/ML**: Cognee (Knowledge Graph + Vector Search), OpenAI API
- **Database**: PostgreSQL 16 + pgvector (Vector Embeddings + Relational Data)
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
POSTGRES_DB=cognee_db

# --- AI / LLM ---
OPENAI_API_KEY=sk-your-key-here

# --- Security ---
SECRET_KEY=change_this_to_a_secure_random_string

# --- Cognee & Vector DB ---
DB_PROVIDER=postgres
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

## 🏢 Organization & SaaS Setup

To configure Cortex AI for your own organization or as a SaaS offering:

### 1. Branding & Customization
- **App Name**: Update the application name in `frontend/app/layout.tsx` (metadata title) and `frontend/components/chat/Sidebar.tsx`.
- **Logo**: Replace the logo icon in `frontend/components/Logo.tsx` or `frontend/public/icon.png`.
- **Theme Colors**: The application uses a distinct green accent (`#76B900`). To apply your brand color:
  1. Update the `--nvidia-green` variable in `frontend/app/globals.css`.
  2. Perform a global search and replace for the hex code `#76B900` in the `frontend/` directory with your brand's primary color.

### 2. User Management & Access Control
Cortex AI comes with built-in authentication and role-based access control (RBAC).
- **Initial Admin**: The first user to register is just a standard user. You can manually promote users to superuser status in the database if needed for administrative features.
- **Private Instance**: To restrict access to only your employees, you can disable the "Register" endpoint in `backend/app/routers/auth.py` or put the entire application behind a corporate VPN or SSO proxy (like Cloudflare Access).

### 3. Production Database
For a robust SaaS setup, **do not** use the default local Docker volume for the database if you expect high traffic or need high availability.
- Connect the backend to a managed PostgreSQL instance (e.g., AWS RDS, Google Cloud SQL, Azure Database for PostgreSQL).
- Update `DB_HOST`, `DB_USER`, `DB_PASSWORD` in your `.env` file to point to your managed instance.
- **Requirement**: Ensure the managed database supports the `pgvector` extension (v0.5.0+).

### 4. LLM Provider Configuration
You can configure a global LLM provider for your organization or allow users to bring their own keys.
- **Global Key**: Set `OPENAI_API_KEY` (or Anthropic/Azure keys) in the backend `.env`. This key will be used for system operations (like RAG indexing) and default agents.
- **Multiple Models**: You can configure multiple models (GPT-4, Claude 3, Llama 3) in the "LLM Configurations" section of the dashboard, allowing different departments to use different models based on cost/performance needs.

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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by [Mohamed Abu Basith](https://github.com/mohamedabubasith)**
