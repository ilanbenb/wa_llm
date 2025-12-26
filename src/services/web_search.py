from typing import List, Dict, Any, Optional
import logging
from tavily import TavilyClient
from src.config import get_settings

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.tavily_api_key
        if self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("Tavily API key not found. Web search will be disabled.")

    async def search(self, query: str, search_depth: str = "basic", max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a web search using Tavily to get up-to-date information or information not present in the knowledge base.
        
        Args:
            query: The search query string.
            search_depth: The depth of the search. Can be "basic" or "advanced". Default is "basic".
            max_results: The maximum number of search results to return. Default is 5.
            
        Returns:
            A list of dictionaries containing search results (url, content, title, etc.).
        """
        if not self.client:
            logger.warning("Attempted to search without Tavily API key.")
            return [{"error": "Tavily API key not configured"}]

        logger.info(f"Performing web search for query: '{query}'")

        # Tavily's python client is synchronous, but we can wrap it or just use it if it's fast enough.
        # For now, let's use it directly.
        try:
            response = self.client.search(query=query, search_depth=search_depth, max_results=max_results)
            results = response.get("results", [])
            logger.info(f"Web search returned {len(results)} results.")
            return results
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return [{"error": str(e)}]

web_search_service = WebSearchService()
