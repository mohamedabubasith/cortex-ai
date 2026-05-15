from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Basivo"
    API_V1_STR: str = "/api/v1"
    FRONTEND_URL: str = "https://chat.basivo.in"
    
    # Database (TimescaleDB / PostgreSQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "chat_db"
    DB_USERNAME: str = "admin"
    DB_PASSWORD: str = "admin"

    # Full connection URL — overrides DB_* vars above if set
    DATABASE_URL: Optional[str] = None

    TOKENIZERS_PARALLELISM: bool = True

    # Security
    # WARNING: Change this in production!
    SECRET_KEY: str = "development_secret_key_only_change_me_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Admin Security
    ADMIN_SECRET_KEY: str = "ec49d476-0757-46c5-a4de-9c0b5a87a20a" # Default secret, change in production
    
    # Default Admin User (created on first startup if no superuser exists)
    DEFAULT_ADMIN_EMAIL: str = "admin@gmail.com"
    DEFAULT_ADMIN_PASSWORD: str = "Apple@123"
    DEFAULT_ADMIN_NAME: str = "System Administrator"

    # Allow overriding with simpler env vars (ADMIN_EMAIL, ADMIN_PASSWORD)
    # These will take precedence if set in .env
    @property
    def admin_email(self) -> str:
        import os
        return os.getenv("ADMIN_EMAIL", self.DEFAULT_ADMIN_EMAIL)

    @property
    def admin_password(self) -> str:
        import os
        return os.getenv("ADMIN_PASSWORD", self.DEFAULT_ADMIN_PASSWORD)
    
    # Auth Provider
    # "local" = standard username/password
    # "keycloak" = SSO via Keycloak
    AUTH_PROVIDER: str = "local"
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Email
    EMAIL_PROVIDER: str = "smtp" # smtp, console, none
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = "no-reply@basivo.in"
    EMAILS_FROM_NAME: Optional[str] = "Basivo"
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 15

    # Embeddings (legacy app-wide defaults; knowledge base uses Ollama below)
    EMBEDDING_PROVIDER: str = "ollama"
    EMBEDDING_MODEL: str = "paraphrase-multilingual:latest"

    # Vector DB (application DB / legacy)
    VECTOR_DB_PROVIDER: str = "pgvector"
    VECTOR_DB_URL: Optional[str] = None

    # Knowledge base — Haystack + Unstructured + Ollama + Qdrant
    UNSTRUCTURED_API_URL: str = "http://127.0.0.1:8000"
    UNSTRUCTURED_GENERAL_PATH: str = "general/v0/general"
    # Optional API key for hosted / secured Unstructured deployments (sent as `unstructured-api-key` header).
    UNSTRUCTURED_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "paraphrase-multilingual:latest"
    # Prefer POST /api/embed (current Ollama); legacy /api/embeddings can 500 on some proxies/old builds.
    OLLAMA_PREFER_API_EMBED: bool = True
    # Pass through to Ollama embed API; avoids hard failures when a chunk is slightly over context.
    OLLAMA_EMBED_TRUNCATE: bool = True
    # Include an explicit port if Qdrant is not on 6333 (e.g. :80 behind a reverse proxy).
    QDRANT_URL: str = "http://127.0.0.1:6333"
    QDRANT_COLLECTION: str = "cortex_kb"
    # Optional; required when Qdrant is secured (Bearer / api-key header).
    QDRANT_API_KEY: Optional[str] = None
    # KB ingest: how many chunks to send per Ollama embed HTTP call (and per Qdrant upsert batch).
    # Higher = fewer HTTP round-trips (faster on remote Ollama); lower if you hit timeouts or OOM on the embed server.
    RAG_EMBEDDING_BATCH_SIZE: int = 64
    # Haystack → Qdrant client internal batch size for writes (see QdrantDocumentStore).
    RAG_QDRANT_WRITE_BATCH_SIZE: int = 128
    # KB chunk upper bound (characters) ≈ embedding max tokens × factor (Haystack splitter uses chars).
    # Set to the model's **context length in tokens** (same idea as GGUF ``bert.context_length``). Check with:
    #   ``ollama show paraphrase-multilingual:latest`` → use that context (e.g. 512 for your BERT embedder).
    # Only use a smaller value (e.g. 128) if your GGUF explicitly reports a 128-token context.
    KB_EMBEDDING_MAX_INPUT_TOKENS: int = 512
    KB_CHUNK_CHARS_PER_TOKEN: float = 4.0
    KB_MIN_CHUNK_CHARS: int = 256

    @property
    def kb_max_chunk_chars(self) -> int:
        est = int(self.KB_EMBEDDING_MAX_INPUT_TOKENS * self.KB_CHUNK_CHARS_PER_TOKEN)
        return max(self.KB_MIN_CHUNK_CHARS, est)

    @property
    def constructed_database_url(self) -> str:
        """Constructs the application database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # URL-encode user/password so @, #, :, /, etc. in passwords do not break the URL.
        user = quote_plus(self.DB_USERNAME)
        password = quote_plus(self.DB_PASSWORD or "")
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def validate_providers(self):
        if self.VECTOR_DB_PROVIDER != "pgvector":
            raise ValueError("VECTOR_DB_PROVIDER must be set to 'pgvector'.")

    # Logging
    LOG_LEVEL: str = "INFO"

    # Knowledge Graph (Neo4j)
    ENABLE_GRAPH: bool = False
    NEO4J_URI: Optional[str] = "bolt://neo4j:7687"
    NEO4J_USER: Optional[str] = "neo4j"
    NEO4J_PASSWORD: Optional[str] = "password"

    # ── External Cortex KB service ────────────────────────────────
    # Set both to enable external KB; leave blank to use local Haystack pipeline.
    CORTEX_KB_URL: str = ""       # e.g. https://knowledge.basivo.in
    CORTEX_KB_API_KEY: str = ""   # e.g. cortex_xxx
    
    class Config:
        env_file = (str(_REPO_ROOT / ".env"),)
        case_sensitive = True
        extra = "ignore"

settings = Settings()
