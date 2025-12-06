"""
SAM.gov API Tool

Integrates with SAM.gov (System for Award Management) API
to search for government contracting opportunities.

API Documentation: https://open.gsa.gov/api/get-opportunities-public-api/
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class SAMGovAPITool(BaseTool):
    """
    Tool for interacting with SAM.gov Opportunities API.

    Requires API key from https://open.gsa.gov/api/get-opportunities-public-api/
    """

    BASE_URL = "https://api.sam.gov/opportunities/v2/search"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="sam_gov_api",
            api_key=api_key,
            cache_ttl=3600,  # Cache for 1 hour
            rate_limit_per_minute=30  # SAM.gov has rate limits
        )

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search SAM.gov opportunities.

        Args:
            query: Search keyword
            **kwargs: Additional parameters

        Returns:
            List of opportunity data
        """
        return await self.search_opportunities(query, **kwargs)

    async def search_opportunities(
        self,
        keyword: str,
        limit: int = 10,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Search for contracting opportunities.

        Args:
            keyword: Search keyword
            limit: Maximum results to return
            **filters: Additional filter parameters

        Returns:
            List of opportunities
        """
        cache_key = f"sam_search_{keyword}_{limit}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self.api_key:
            self.logger.warning("SAM.gov API key not configured, returning empty results")
            return []

        try:
            await self._check_rate_limit()

            params = {
                "api_key": self.api_key,
                "keyword": keyword,
                "limit": limit,
                "offset": filters.get("offset", 0),
                "postedFrom": filters.get("posted_from", "01/01/2024"),  # Default to current year
                "postedTo": filters.get("posted_to", "12/31/2024")
            }

            # Add NAICS codes if specified
            if filters.get("naics_codes"):
                params["naics"] = ",".join(filters["naics_codes"])

            self.logger.info(f"Searching SAM.gov with keyword: {keyword}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()

                data = response.json()
                opportunities = data.get("opportunitiesData", [])

                # Transform to our format
                results = []
                for opp in opportunities:
                    results.append({
                        "opportunity_id": opp.get("noticeId"),
                        "title": opp.get("title"),
                        "agency_name": opp.get("fullParentPathName"),
                        "office_name": opp.get("officeAddress", {}).get("city"),
                        "type": opp.get("type"),
                        "posted_date": opp.get("postedDate"),
                        "response_deadline": opp.get("responseDeadLine"),
                        "naics_code": opp.get("naicsCode"),
                        "description": opp.get("description"),
                        "uei": opp.get("ueiSAM"),
                        "point_of_contact": opp.get("pointOfContact"),
                        "link": opp.get("uiLink")
                    })

                self.logger.info(f"Found {len(results)} opportunities from SAM.gov")

                # Cache results
                self._set_in_cache(cache_key, results)

                return results

        except httpx.HTTPStatusError as e:
            self.logger.error(f"SAM.gov API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            self.logger.error(f"SAM.gov API search failed: {e}", exc_info=True)
            return []

    async def get_entity_information(self, uei: str) -> Optional[Dict[str, Any]]:
        """
        Get entity information by UEI (Unique Entity Identifier).

        Args:
            uei: Unique Entity Identifier

        Returns:
            Entity data or None
        """
        if not self.api_key:
            self.logger.warning("SAM.gov API key not configured")
            return None

        cache_key = f"sam_entity_{uei}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            url = f"https://api.sam.gov/entity-information/v3/entities"
            params = {
                "api_key": self.api_key,
                "ueiSAM": uei
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                entity = data.get("entityData", [{}])[0] if data.get("entityData") else None

                if entity:
                    self._set_in_cache(cache_key, entity)

                return entity

        except Exception as e:
            self.logger.error(f"Failed to get entity {uei}: {e}")
            return None
