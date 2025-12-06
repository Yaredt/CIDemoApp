"""
Web Search Tool

Uses Serper.dev API for Google search results.

API Documentation: https://serper.dev/
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    Tool for web search using Serper.dev API.

    Serper.dev provides Google search results through an API.
    Requires API key from https://serper.dev
    """

    BASE_URL = "https://google.serper.dev/search"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="web_search",
            api_key=api_key,
            cache_ttl=3600,  # Cache for 1 hour
            rate_limit_per_minute=100
        )

    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform web search.

        Args:
            query: Search query
            num_results: Number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        if not self.api_key:
            self.logger.warning("Serper API key not configured, returning empty results")
            return []

        cache_key = f"search_{query}_{num_results}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": query,
                "num": num_results,
                "gl": kwargs.get("country", "us"),  # Country
                "hl": kwargs.get("language", "en")  # Language
            }

            # Add optional parameters
            if kwargs.get("date_restrict"):
                payload["tbs"] = f"qdr:{kwargs['date_restrict']}"  # e.g., 'd' for past day, 'w' for week

            self.logger.info(f"Web searching for: {query}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()

                # Extract organic results
                organic_results = data.get("organic", [])

                # Transform to our format
                results = []
                for result in organic_results:
                    results.append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                        "position": result.get("position"),
                        "date": result.get("date")
                    })

                # Also include knowledge graph if available
                if data.get("knowledgeGraph"):
                    kg = data["knowledgeGraph"]
                    results.append({
                        "type": "knowledge_graph",
                        "title": kg.get("title"),
                        "description": kg.get("description"),
                        "website": kg.get("website"),
                        "attributes": kg.get("attributes", {})
                    })

                self.logger.info(f"Found {len(results)} search results for: {query}")

                # Cache results
                self._set_in_cache(cache_key, results)

                return results

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Serper API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            self.logger.error(f"Web search failed for query '{query}': {e}", exc_info=True)
            return []

    async def search_news(
        self,
        query: str,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of news results
        """
        if not self.api_key:
            self.logger.warning("Serper API key not configured")
            return []

        try:
            await self._check_rate_limit()

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": query,
                "num": num_results
            }

            url = "https://google.serper.dev/news"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()
                news_results = data.get("news", [])

                results = []
                for article in news_results:
                    results.append({
                        "title": article.get("title"),
                        "link": article.get("link"),
                        "snippet": article.get("snippet"),
                        "date": article.get("date"),
                        "source": article.get("source"),
                        "imageUrl": article.get("imageUrl")
                    })

                return results

        except Exception as e:
            self.logger.error(f"News search failed: {e}")
            return []
