"""
FDIC API Tool

Integrates with the FDIC (Federal Deposit Insurance Corporation) API
to search for banking institutions.

API Documentation: https://banks.data.fdic.gov/docs/
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class FDICAPITool(BaseTool):
    """
    Tool for interacting with FDIC Institution API.

    The FDIC API is free and doesn't require an API key.
    """

    BASE_URL = "https://banks.data.fdic.gov/api/institutions"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="fdic_api",
            api_key=api_key,  # Not required for FDIC
            cache_ttl=86400,  # Cache for 24 hours (data doesn't change frequently)
            rate_limit_per_minute=60
        )

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search FDIC institution database.

        Args:
            query: Search query (institution name)
            **kwargs: Additional filter parameters

        Returns:
            List of institution data
        """
        # FDIC API uses specific parameter names
        filters = kwargs.get("filters", {})
        return await self.search_institutions(filters)

    async def search_institutions(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for banking institutions.

        Args:
            filters: Filter criteria
                - asset_min: Minimum asset size
                - asset_max: Maximum asset size
                - states: List of state codes
                - city: City name
                - active: Active institutions only (default: True)

        Returns:
            List of institution data
        """
        filters = filters or {}

        # Build cache key
        cache_key = f"fdic_search_{str(filters)}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            # Build query parameters
            params = {
                "limit": filters.get("limit", 100),
                "offset": filters.get("offset", 0),
                "format": "json",
                "sort_by": "ASSET",
                "sort_order": "DESC"
            }

            # Add filters
            filter_conditions = []

            if filters.get("asset_min"):
                filter_conditions.append(f"ASSET>={filters['asset_min']}")

            if filters.get("asset_max"):
                filter_conditions.append(f"ASSET<={filters['asset_max']}")

            if filters.get("states"):
                states = filters["states"]
                if isinstance(states, list):
                    state_filter = " OR ".join([f"STNAME:'{s}'" for s in states])
                    filter_conditions.append(f"({state_filter})")

            if filters.get("city"):
                filter_conditions.append(f"CITY:'{filters['city']}'")

            # Active institutions only (default)
            if filters.get("active", True):
                filter_conditions.append("ACTIVE:1")

            if filter_conditions:
                params["filters"] = " AND ".join(filter_conditions)

            self.logger.info(f"Searching FDIC API with params: {params}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()

                data = response.json()
                institutions = data.get("data", [])

                # Transform to our format
                results = []
                for inst in institutions:
                    results.append({
                        "name": inst.get("NAME"),
                        "cert": inst.get("CERT"),
                        "asset": inst.get("ASSET"),
                        "city": inst.get("CITY"),
                        "state": inst.get("STNAME"),
                        "zip": inst.get("ZIP"),
                        "website": inst.get("WEBADDR"),
                        "established": inst.get("DATEUPDT"),
                        "employees": inst.get("ENDEFYMD"),
                        "address": inst.get("ADDRESS"),
                        "charter_class": inst.get("CHARTER"),
                        "fdic_region": inst.get("FDICDBS"),
                        "insured": inst.get("INSURED")
                    })

                self.logger.info(f"Found {len(results)} institutions from FDIC")

                # Cache results
                self._set_in_cache(cache_key, results)

                return results

        except httpx.HTTPStatusError as e:
            self.logger.error(f"FDIC API HTTP error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            self.logger.error(f"FDIC API search failed: {e}", exc_info=True)
            return []

    async def get_institution_by_cert(self, cert_number: str) -> Optional[Dict[str, Any]]:
        """
        Get institution details by FDIC certificate number.

        Args:
            cert_number: FDIC certificate number

        Returns:
            Institution data or None
        """
        cache_key = f"fdic_cert_{cert_number}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            url = f"{self.BASE_URL}/{cert_number}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                institution = data.get("data", [{}])[0]

                if institution:
                    self._set_in_cache(cache_key, institution)

                return institution

        except Exception as e:
            self.logger.error(f"Failed to get institution {cert_number}: {e}")
            return None
