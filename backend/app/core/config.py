from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cortex AI"
    API_V1_STR: str = "/api/v1"
    
    # Database
    # Default to PostgreSQL for production grade
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/chatbot"
    
    # Security
    # WARNING: Change this in production!
    SECRET_KEY: str = "development_secret_key_only_change_me_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Keycloak (Example config)
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = "chatbot-app"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
