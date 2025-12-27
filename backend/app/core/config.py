from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cortex AI"
    API_V1_STR: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Database Configuration
    
    # 1. Cognee Database (Standard DB_ prefix)
    # These match the standard environment variables Cognee expects.
    DB_PROVIDER: str = "postgres"
    DB_HOST: str = "cognee-postgres"
    DB_PORT: int = 5432
    DB_NAME: str = "cognee_db"
    DB_USERNAME: str = "admin"
    DB_PASSWORD: str = "admin"
    
    # 2. Application Database (APP_ prefix)
    # These are specific to the Cortex AI application.
    APP_DB_HOST: str = "cognee-postgres"
    APP_DB_PORT: int = 5432
    APP_DB_NAME: str = "chat_db"
    APP_DB_USERNAME: str = "admin"
    APP_DB_PASSWORD: str = "admin"
    
    # Main App DB URL (can be constructed or overridden)
    DATABASE_URL: Optional[str] = None

    TOKENIZERS_PARALLELISM: bool = True

    # Security
    # WARNING: Change this in production!
    SECRET_KEY: str = "development_secret_key_only_change_me_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Keycloak (Example config)
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = "chatbot-app"

    # Email
    EMAIL_PROVIDER: str = "console" # smtp, console, none
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = "info@example.com"
    EMAILS_FROM_NAME: Optional[str] = "Cortex AI"
    RESET_PASSWORD_TOKEN_EXPIRE_HOURS: int = 1

    # Embeddings
    EMBEDDING_PROVIDER: str = "fastembed"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS: int = 384

    # Vector DB
    VECTOR_DB_PROVIDER: str = "pgvector"
    VECTOR_DB_URL: Optional[str] = None

    @property
    def constructed_database_url(self) -> str:
        """Constructs the main application database URL (using APP_ vars)."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.APP_DB_USERNAME}:{self.APP_DB_PASSWORD}@{self.APP_DB_HOST}:{self.APP_DB_PORT}/{self.APP_DB_NAME}"

    @property
    def constructed_vector_db_url(self) -> str:
        """Constructs the vector database URL for Cognee (using DB_ vars)."""
        if self.VECTOR_DB_URL:
            return self.VECTOR_DB_URL
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def validate_providers(self):
        if self.DB_PROVIDER != "postgres":
            raise ValueError("DB_PROVIDER must be set to 'postgres'. SQLite is not supported.")
        if self.VECTOR_DB_PROVIDER != "pgvector":
            raise ValueError("VECTOR_DB_PROVIDER must be set to 'pgvector'. LanceDB/Qdrant are not supported in this configuration.")

    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
