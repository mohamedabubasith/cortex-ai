from typing import List, Optional
from app.models import models

class PromptService:
    def build_system_prompt(self, agent: models.Agent, db_connections: Optional[List[models.DatabaseConnection]] = None, search_enabled: bool = True, kb_enabled: bool = True, db_enabled: bool = True) -> str:
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
        if db_connections and len(db_connections) > 0 and db_enabled:
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
        elif db_connections and len(db_connections) > 0 and not db_enabled:
            db_section = (
                f"\n\n### DATABASE ACCESS DISABLED\n"
                f"Access to the Live Database tools is currently DISABLED for this conversation.\n"
                f"Do not attempt to run tools like 'query_database'.\n"
            )
        
        # 3. Context Handling Instructions
        context_section = ""
        if kb_enabled:
            context_section = (
                f"\n\n### DOCUMENT CONTEXT (RAG)\n"
                f"You will receive snippets of text from uploaded documents (Knowledge Base) when relevant.\n"
                f"- Use this context to answer questions about specific documents, files, or unstructured text.\n"
                f"- **CITATIONS**: When you use information from the provided document context, you MUST cite the source. "
                f"Each snippet will be clearly labeled with its source. In your response, use the format [Filename] (e.g., [research_paper.pdf]) to credit the source.\n"
                f"- If the user asks about 'the document' or 'the file', look here.\n"
                f"- If the RAG context contradicts the Live Database, trust the Live Database for current data, but mention the discrepancy if relevant.\n"
            )
        else:
            context_section = (
                f"\n\n### DOCUMENT ACCESS DISABLED\n"
                f"Access to the Knowledge Base (uploaded documents) is currently DISABLED for this conversation.\n"
                f"Do not attempt to search for or reference any document context. Rely only on your internal knowledge and live database if available.\n"
            )
        
        # 4. Web Search & Deep Research Section
        search_section = ""
        if search_enabled:
            search_section = (
                f"\n\n### WEB SEARCH & RESEARCH\n"
                f"You may be provided with search results directly in the conversation context (PRE-SEARCH results).\n"
                f"- **If context is provided**: Use it to answer the user's question immediately with citations.\n"
                f"- **If extra info is still needed**: Use the 'web_search' or 'website_reader' tools.\n"
                f"- **CITATIONS**: Use Markdown links: [Source Name](URL). Place citations immediately after the facts you are stating.\n"
            )
        else:
            search_section = (
                f"\n\n### WEB SEARCH DISABLED\n"
                f"Web search and internet access are currently DISABLED for this conversation.\n"
                f"Rely only on your internal knowledge and provided document context.\n"
            )

        # 5. Source Integration (if both enabled)
        integration_section = ""
        if kb_enabled and search_enabled:
            integration_section = (
                f"\n\n### SOURCE SYNTHESIS\n"
                f"You have access to BOTH uploaded documents (Knowledge Base) and Web Search.\n"
                f"- **COMBINE SOURCES**: Do not rely on just one. If the documents lack info, check the search results, and vice-versa.\n"
                f"- **CONFLICTS**: If document context conflicts with web search, prioritize the uploaded documents (internal truth) but mention the web finding.\n"
            )
        
        # 6. General Guidelines
        guidelines = (
            f"\n\n### GUIDELINES\n"
            f"- Be concise and direct.\n"
            f"- If using a tool, do not narrate 'I am using a tool'. Just do it.\n"
            f"- If the user asks for a list, provide a clean list.\n"
        )
        
        return f"{base_prompt}{db_section}{context_section}{search_section}{integration_section}{guidelines}"

prompt_service = PromptService()
