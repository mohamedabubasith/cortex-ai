from app.core.database import SessionLocal
from app.models import models
from sqlalchemy import select
import asyncio

async def check_data():
    async with SessionLocal() as db:
        # Users
        result = await db.execute(select(models.User))
        users = result.scalars().all()
        print(f"Users: {len(users)}")
        for u in users:
            print(f" - {u.email} (ID: {u.id})")

        # LLM Configs
        result = await db.execute(select(models.LLMConfiguration))
        configs = result.scalars().all()
        print(f"LLM Configs: {len(configs)}")
        for c in configs:
            print(f" - {c.name} (User: {c.user_id})")

if __name__ == "__main__":
    asyncio.run(check_data())
