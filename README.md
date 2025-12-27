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
