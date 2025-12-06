"""
Base tool class for all data source integrations
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import asyncio
from datetime import datetime, timedelta
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Base class for all data source tools.

    Provides common functionality:
    - Rate limiting
    - Caching
    - Error handling
    - Logging
    """

    def __init__(
        self,
        name: str,
        api_key: Optional[str] = None,
        cache_ttl: int = 3600,
        rate_limit_per_minute: int = 60
    ):
        """
        Initialize base tool.

        Args:
            name: Tool name
            api_key: API key for the service
            cache_ttl: Cache TTL in seconds
            rate_limit_per_minute: Maximum requests per minute
        """
        self.name = name
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{name}")

        # Initialize cache
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)

        # Rate limiting
        self.rate_limit = rate_limit_per_minute
        self.request_times = []

    async def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting.
        """
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)

        # Remove old request times
        self.request_times = [t for t in self.request_times if t > one_minute_ago]

        # Check if we've hit the limit
        if len(self.request_times) >= self.rate_limit:
            # Calculate wait time
            oldest_request = min(self.request_times)
            wait_seconds = 60 - (now - oldest_request).total_seconds()

            if wait_seconds > 0:
                self.logger.warning(
                    f"Rate limit reached ({self.rate_limit}/min). "
                    f"Waiting {wait_seconds:.1f}s"
                )
                await asyncio.sleep(wait_seconds)

        # Record this request
        self.request_times.append(now)

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        value = self.cache.get(key)
        if value is not None:
            self.logger.debug(f"Cache hit for key: {key}")
        return value

    def _set_in_cache(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value
        self.logger.debug(f"Cached value for key: {key}")

    @abstractmethod
    async def search(self, query: str, **kwargs) -> Any:
        """
        Search using the tool.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            Search results
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the tool.

        Returns:
            Health status information
        """
        return {
            "tool_name": self.name,
            "status": "healthy",
            "cache_size": len(self.cache),
            "recent_requests": len(self.request_times),
            "has_api_key": self.api_key is not None
        }
