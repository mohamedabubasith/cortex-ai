import logging
from typing import Dict, List, Any, Optional
from duckduckgo_search import DDGS
import asyncio
import httpx
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        # DuckDuckGo doesn't require an API key
        pass

    @property
    def is_available(self) -> bool:
        return True

    async def search(self, query: str, max_results: int = 5, timelimit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform a web search using DuckDuckGo.
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _do_search():
                with DDGS() as ddgs:
                    # Remove 'backend' as it can cause 202 Ratelimit issues in some environments
                    return list(ddgs.text(query, max_results=max_results, timelimit=timelimit))
            
            raw_results = await loop.run_in_executor(None, _do_search)
            
            # If no results and it might be a rate limit, try one more time after a tiny delay
            if not raw_results:
                await asyncio.sleep(0.5)
                raw_results = await loop.run_in_executor(None, _do_search)

            logger.info(f"DuckDuckGo raw results count: {len(raw_results) if raw_results else 0}")
            
            results = []
            if raw_results:
                for r in raw_results:
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "content": r.get("body")
                    })
            
            # Fallback to News if regular search is empty (news is sometimes less restricted)
            if not results:
                logger.info(f"Regular search empty for '{query}', falling back to news...")
                news_fallback = await self.news_search(query, max_results=max_results)
                if news_fallback:
                    results = news_fallback

            return results
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            if "Ratelimit" in str(e):
                # Try news search as a last resort
                return await self.news_search(query, max_results=max_results)
            return []

    async def news_search(self, query: str, max_results: int = 5, timelimit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform a news search using DuckDuckGo.
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _do_news():
                with DDGS() as ddgs:
                    return ddgs.news(query, max_results=max_results, timelimit=timelimit)
            
            raw_results = await loop.run_in_executor(None, _do_news)
            logger.info(f"DuckDuckGo News raw results count: {len(raw_results) if raw_results else 0}")
            
            results = []
            for r in raw_results:
                results.append({
                    "title": r.get("title"),
                    "url": r.get("url"), # News uses 'url' NOT 'href'
                    "content": r.get("body"), # News uses 'body'
                    "date": r.get("date"),
                    "source": r.get("source")
                })
            return results
        except Exception as e:
            logger.error(f"DuckDuckGo news search failed: {e}")
            return []

    async def get_search_context(self, query: str, max_results: int = 3, search_type: str = "text") -> str:
        """
        Get a concatenated string of search results optimized for LLM context.
        """
        if search_type == "news":
            results = await self.news_search(query=query, max_results=max_results)
        else:
            results = await self.search(query=query, max_results=max_results)
            
        if not results:
            return "No search results found."

        context_parts = []
        for r in results:
            source_info = f" (Source: {r.get('source')}, Date: {r.get('date')})" if search_type == "news" else ""
            context_parts.append(f"Title: {r['title']}{source_info}\nURL: {r['url']}\nContent: {r['content']}")
        
        return "\n\n---\n\n".join(context_parts)

    async def fetch_page_content(self, url: str) -> str:
        """
        Fetch the full text content of a webpage and clean it up.
        Uses a background thread for CPU-intensive parsing to avoid blocking the event loop.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html_content = response.text

            def _parse_and_clean(html):
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text(separator=' ')
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text[:10000]

            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, _parse_and_clean, html_content)
            return content
            
        except Exception as e:
            logger.error(f"Failed to fetch page content from {url}: {e}")
            return f"Error fetching page content: {str(e)}"

search_service = SearchService()
