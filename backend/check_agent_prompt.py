import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.models import models
from sqlalchemy import select

import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.models import models
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from openai import AsyncOpenAI
from app.services.prompt_service import prompt_service

async def test_llm_refusal():
    async with AsyncSessionLocal() as session:
        # Load agent with LLM Config
        result = await session.execute(
            select(models.Agent)
            .options(selectinload(models.Agent.llm_config))
            .where(models.Agent.id == "325c0a2b-6519-415e-84af-2af15fa3e972")
        )
        agent = result.scalars().first()
        
        if not agent:
            print("Agent not found")
            return

        print(f"Agent: {agent.name}")
        print(f"Model: {agent.llm_config.model}")
        print(f"Wrapper Provider: {agent.llm_config.provider}")
        print(f"Base URL: {agent.llm_config.base_url}")
        
        from app.services.tools_service import tools_service
        from app.services.database_service import database_service # We need this for context, even if mock
        
        # Get connections (re-fetch with eager loading)
        result = await session.execute(
            select(models.Agent)
            .options(
                selectinload(models.Agent.llm_config),
                selectinload(models.Agent.database_connections),
                selectinload(models.Agent.mcp_connections)
            )
            .where(models.Agent.id == "325c0a2b-6519-415e-84af-2af15fa3e972")
        )
        agent = result.scalars().first()
        
        # Build Tools
        db_connections = agent.database_connections
        mcp_connections = agent.mcp_connections
        print(f"DB Connections: {len(db_connections)}")
        print(f"MCP Connections: {len(mcp_connections)}")
        
        for mcp in mcp_connections:
            print(f"MCP ID: {mcp.id}")
            print(f"MCP Metadata: {mcp.tools_metadata}")
        
        # Mock database service or just pass None if it's strictly for schema generation
        # (Though execute_tool might fail later, we just want to see if the LLM refuses)
        # Use new signature with filtering
        tools = tools_service.get_agent_specific_tools(db_connections, mcp_connections, search_enabled=False)
        
        print(f"Tools passed: {[t['function']['name'] for t in tools]}")
        
        # Build System Prompt (Toggle OFF)
        system_prompt = prompt_service.build_system_prompt(
            agent, 
            db_connections=agent.database_connections, 
            search_enabled=False, 
            kb_enabled=False
        )
        print("\n--- SYSTEM PROMPT ---\n")
        print(system_prompt)
        print("\n---------------------\n")
        
        # Create client
        client = AsyncOpenAI(
            api_key=agent.llm_config.api_key,
            base_url=agent.llm_config.base_url
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Tell me about minecraft"}
        ]
        
        print("Sending request with tools...")
        
        try:
            response = await client.chat.completions.create(
                model=agent.llm_config.model,
                messages=messages,
                tools=tools, # PASSING TOOLS NOW
                max_tokens=200
            )
            print("\n--- RESPONSE ---\n")
            print(response.choices[0].message.content)
            print("\n----------------\n")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_refusal())
