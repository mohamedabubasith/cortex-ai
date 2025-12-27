from typing import List, Optional
from app.models import models

class PromptService:
    def build_system_prompt(self, agent: models.Agent, db_connections: Optional[List[models.DatabaseConnection]] = None) -> str:
        """
        Constructs a comprehensive system prompt that clearly distinguishes between
        general instructions, database capabilities, and document context.
        """
        # 1. Base Identity
        base_prompt = agent.system_prompt if agent.system_prompt else "You are a helpful AI assistant."
        
        # 2. Database Capabilities
        db_section = ""
        if db_connections and len(db_connections) > 0:
            db_names = ", ".join([f'"{db.name}"' for db in db_connections])
            db_section = (
                f"\n\n### LIVE DATABASE ACCESS\n"
                f"You have ACTIVE, READ-ONLY access to the following connected databases: {db_names}.\n"
                f"You have a tool named 'query_database' to execute SQL queries on them.\n"
                f"**CRITICAL INSTRUCTIONS:**\n"
                f"1. **Prioritize DB Tools**: If the user asks about 'tables', 'columns', 'schema', 'rows', or 'database records', you MUST use the 'query_database' tool. Do not rely on document context for this.\n"
                f"2. **Schema Discovery**: If asked for 'all tables' or 'schema', query `information_schema.tables` first.\n"
                f"3. **Data Retrieval**: If asked for data (e.g., 'show me users'), write and execute the SQL query.\n"
                f"4. **Separation**: Do not confuse data in the database with data in uploaded documents (RAG). They are separate sources.\n"
            )
        
        # 3. Context Handling Instructions
        context_section = (
            f"\n\n### DOCUMENT CONTEXT (RAG)\n"
            f"You may also receive snippets of text from uploaded documents (Knowledge Base).\n"
            f"- Use this context to answer questions about specific documents, files, or unstructured text.\n"
            f"- If the user asks about 'the document' or 'the file', look here.\n"
            f"- If the RAG context contradicts the Live Database, trust the Live Database for current data, but mention the discrepancy if relevant.\n"
        )
        
        # 4. General Guidelines
        guidelines = (
            f"\n\n### GUIDELINES\n"
            f"- Be concise and direct.\n"
            f"- If using a tool, do not narrate 'I am using a tool'. Just do it.\n"
            f"- If the user asks for a list, provide a clean list.\n"
        )
        
        return f"{base_prompt}{db_section}{context_section}{guidelines}"

prompt_service = PromptService()
