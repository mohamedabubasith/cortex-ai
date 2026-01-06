from cryptography.fernet import Fernet
from app.core.config import settings
from app.models import models
import asyncpg
# import aiomysql 
# import motor.motor_asyncio
import json

# Simple key generation for demo (In prod, use a persistent key from env)
# If settings.SECRET_KEY is long enough, we can derive or use it. 
# For now, we'll generate a key if not present, but this resets on restart.
# Better: Use a fixed key derived from SECRET_KEY
import base64
import hashlib

def get_fernet():
    # Derive a 32-byte key from the SECRET_KEY
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

class DatabaseService:
    def __init__(self):
        self.fernet = get_fernet()

    def encrypt_password(self, password: str) -> str:
        return self.fernet.encrypt(password.encode()).decode()

    def decrypt_password(self, encrypted_password: str) -> str:
        return self.fernet.decrypt(encrypted_password.encode()).decode()

    async def test_connection(self, connection: models.DatabaseConnection) -> bool:
        password = self.decrypt_password(connection.encrypted_password)
        
        if connection.type == "postgres":
            conn = await asyncpg.connect(
                user=connection.username,
                password=password,
                database=connection.database_name,
                host=connection.host,
                port=connection.port,
                timeout=5
            )
            await conn.close()
            return True
        else:
            raise ValueError(f"Unsupported database type: {connection.type}")


    async def execute_query(self, connection: models.DatabaseConnection, query: str):
        password = self.decrypt_password(connection.encrypted_password)
        
        try:
            if connection.type == "postgres":
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Connecting to Postgres: {connection.host}:{connection.port}/{connection.database_name}")
                conn = await asyncpg.connect(
                    user=connection.username,
                    password=password,
                    database=connection.database_name,
                    host=connection.host,
                    port=connection.port,
                    timeout=5
                )
                logger.info("Connected to Postgres successfully")
                try:
                    # Fetch results
                    logger.info(f"Executing query: {query}")
                    rows = await conn.fetch(query)
                    logger.info(f"Query returned {len(rows)} rows")
                    # Convert to list of dicts
                    results = [dict(row) for row in rows]
                    
                    # Handle non-serializable types (like datetime) if needed
                    # For now, we assume basic types or let FastAPI/Pydantic handle it
                    # But asyncpg returns Record objects, we converted to dict.
                    # We might need to stringify UUIDs, dates etc.
                    return results
                finally:
                    await conn.close()
            
            return {"error": "Unsupported database type"}
        except Exception as e:
            return {"error": str(e)}

database_service = DatabaseService()
