import asyncio
from typing import Dict, Any
from .base_tool import BaseTool
from app.services.search_service import search_service

class SearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Search the web for real-time information, news, or facts that are not in your internal knowledge base.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up on the internet."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of search results to return (default: 5).",
                            "default": 5
                        },
                        "timelimit": {
                            "type": "string",
                            "description": "Filter results by time: 'd' (day), 'w' (week), 'm' (month), 'y' (year).",
                            "enum": ["d", "w", "m", "y"]
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    async def execute(self, query: str, max_results: int = 5, timelimit: str = None, **kwargs) -> Any:
        if not search_service.is_available:
            return {"error": "Web search is currently unavailable."}
        
        # Smart Heuristic: If query is time-sensitive, try News search first
        is_time_sensitive = False
        time_words = ["today", "now", "latest", "rate", "current", "price", "news", "stock"]
        if any(word in query.lower() for word in time_words):
            is_time_sensitive = True
            if not timelimit:
                timelimit = "d"
        
        results = []
        news_results = []
        
        search_tasks = []
        # 1. Try News Search for time-sensitive queries
        if is_time_sensitive:
            search_tasks.append(search_service.news_search(query=query, max_results=max_results, timelimit=timelimit))
            
        # 2. Regular Web Search
        search_tasks.append(search_service.search(query=query, max_results=max_results, timelimit=timelimit))
        
        # Run in parallel
        if is_time_sensitive:
            news_results, results = await asyncio.gather(*search_tasks)
        else:
            results = (await asyncio.gather(*search_tasks))[0]
        
        # 3. Fallback: If 'd' returned nothing, try without timelimit
        if not results and not news_results and timelimit == "d":
            results = await search_service.search(query=query, max_results=max_results)
            
        if not results and not news_results:
            return {"message": "No search results found for the query."}
            
        return {
            "query": query,
            "timelimit_applied": timelimit,
            "news_results": news_results[:3], # Only top 3 news
            "web_results": results[:2]       # Only top 2 web
        }
