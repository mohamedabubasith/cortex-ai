from pydantic_settings import BaseSettings
from typing import Optional

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

    # Embeddings
    EMBEDDING_PROVIDER: str = "fastembed"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector DB
    VECTOR_DB_PROVIDER: str = "pgvector"
    VECTOR_DB_URL: Optional[str] = None
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma_db"

    @property
    def constructed_database_url(self) -> str:
        """Constructs the application database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

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
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
