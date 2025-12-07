from app.core.database import SessionLocal
from app.models import models
from sqlalchemy import select
import asyncio

async def check_llm():
    async with SessionLocal() as db:
        result = await db.execute(select(models.LLMConfiguration))
        configs = result.scalars().all()
        print(f"LLM Configs: {len(configs)}")
        for c in configs:
            print(f" - {c.name} ({c.model})")

if __name__ == "__main__":
    asyncio.run(check_llm())
