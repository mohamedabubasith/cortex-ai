from typing import List, Optional
from app.models import models

class PromptService:
    def build_system_prompt(self, agent: models.Agent, db_connections: Optional[List[models.DatabaseConnection]] = None) -> str:
        """
        Constructs a comprehensive system prompt that clearly distinguishes between
        general instructions, database capabilities, and document context.
        """
        # 1. Base Identity & Time Awareness
        import datetime
        now = datetime.datetime.now()
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        day_of_week = now.strftime("%A")
        
        base_prompt = agent.system_prompt if agent.system_prompt else "You are a helpful AI assistant."
        base_prompt += f"\n\n**CURRENT CONTEXT:** Today is {day_of_week}, {current_time_str}. Use this as your reference for 'today', 'now', or current events."
        
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
            f"You will receive snippets of text from uploaded documents (Knowledge Base) when relevant.\n"
            f"- Use this context to answer questions about specific documents, files, or unstructured text.\n"
            f"- **CITATIONS**: When you use information from the provided document context, you MUST cite the source. "
            f"Each snippet will be clearly labeled with its source. In your response, use the format [Filename] (e.g., [research_paper.pdf]) to credit the source.\n"
            f"- If the user asks about 'the document' or 'the file', look here.\n"
            f"- If the RAG context contradicts the Live Database, trust the Live Database for current data, but mention the discrepancy if relevant.\n"
        )
        
        # 4. Web Search & Deep Research Section
        search_section = (
            f"\n\n### WEB SEARCH & DEEP RESEARCH\n"
            f"You have access to the internet via 'web_search' and 'website_reader' tools.\n"
            f"- **web_search**: Use this to find relevant links, news, and snippets. It supports filtering by time (e.g., 'd' for last 24h).\n"
            f"- **website_reader**: After finding a promising URL via search, use this tool to read the FULL text of the page. This is essential for deep research, detailed specifications, or long-form analysis.\n"
            f"- **Workflow**: For complex queries, first 'web_search' to find the best source, then 'website_reader' to extract the full details.\n"
            f"- **CRITICAL:** Always check the date of the search results against the CURRENT CONTEXT defined above. If a search result is older than today, look for more recent ones.\n"
            f"- **CITATIONS**: You MUST cite your sources using Markdown links: [Source Name](URL). Place citations immediately after the supported facts.\n"
        )

        # 5. General Guidelines
        guidelines = (
            f"\n\n### GUIDELINES\n"
            f"- Be concise and direct.\n"
            f"- If using a tool, do not narrate 'I am using a tool'. Just do it.\n"
            f"- If the user asks for a list, provide a clean list.\n"
        )
        
        return f"{base_prompt}{db_section}{context_section}{search_section}{guidelines}"

prompt_service = PromptService()
