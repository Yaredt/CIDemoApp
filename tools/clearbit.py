"""
Clearbit API Tool

Integrates with Clearbit for company enrichment data.

API Documentation: https://clearbit.com/docs
"""

import logging
from typing import Any, Dict, Optional
import httpx

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class ClearbitTool(BaseTool):
    """
    Tool for interacting with Clearbit Enrichment API.

    Requires API key from https://clearbit.com
    """

    BASE_URL = "https://company.clearbit.com/v2/companies/find"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="clearbit",
            api_key=api_key,
            cache_ttl=86400,  # Cache for 24 hours (company data doesn't change often)
            rate_limit_per_minute=60
        )

    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search for company by domain.

        Args:
            query: Company domain
            **kwargs: Additional parameters

        Returns:
            Company data
        """
        return await self.enrich_company(query)

    async def enrich_company(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Enrich company data using Clearbit.

        Args:
            domain: Company domain (e.g., "example.com")

        Returns:
            Company enrichment data or None
        """
        if not self.api_key:
            self.logger.warning("Clearbit API key not configured, returning None")
            return None

        cache_key = f"clearbit_company_{domain}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            params = {"domain": domain}

            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            self.logger.info(f"Enriching company data for domain: {domain}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers
                )

                if response.status_code == 404:
                    self.logger.info(f"No Clearbit data found for domain: {domain}")
                    return None

                response.raise_for_status()

                company_data = response.json()

                # Transform to our format
                result = {
                    "name": company_data.get("name"),
                    "domain": company_data.get("domain"),
                    "description": company_data.get("description"),
                    "logo": company_data.get("logo"),
                    "website": company_data.get("url"),
                    "founded_year": company_data.get("foundedYear"),
                    "industry": company_data.get("industry"),
                    "sector": company_data.get("sector"),
                    "tags": company_data.get("tags", []),
                    "location": company_data.get("location"),
                    "timezone": company_data.get("timeZone"),
                    "employeesRange": company_data.get("metrics", {}).get("employeesRange"),
                    "metrics": {
                        "employees": company_data.get("metrics", {}).get("employees"),
                        "estimated_revenue": company_data.get("metrics", {}).get("estimatedAnnualRevenue"),
                        "fiscal_year_end": company_data.get("metrics", {}).get("fiscalYearEnd")
                    },
                    "tech": company_data.get("tech", []),
                    "linkedin_url": company_data.get("linkedin", {}).get("handle"),
                    "twitter_handle": company_data.get("twitter", {}).get("handle"),
                    "facebook_handle": company_data.get("facebook", {}).get("handle"),
                    "phone": company_data.get("phone"),
                    "type": company_data.get("type"),  # public, private, etc.
                    "category": {
                        "sector": company_data.get("category", {}).get("sector"),
                        "industry_group": company_data.get("category", {}).get("industryGroup"),
                        "industry": company_data.get("category", {}).get("industry"),
                        "sub_industry": company_data.get("category", {}).get("subIndustry")
                    }
                }

                self.logger.info(f"Successfully enriched data for {domain}")

                # Cache results
                self._set_in_cache(cache_key, result)

                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                self.logger.error(f"Clearbit API HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            self.logger.error(f"Clearbit enrichment failed for {domain}: {e}", exc_info=True)
            return None

    async def enrich_person(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Enrich person data using Clearbit.

        Args:
            email: Person's email address

        Returns:
            Person enrichment data or None
        """
        if not self.api_key:
            self.logger.warning("Clearbit API key not configured")
            return None

        cache_key = f"clearbit_person_{email}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            url = "https://person.clearbit.com/v2/people/find"
            params = {"email": email}

            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                person_data = response.json()

                if person_data:
                    self._set_in_cache(cache_key, person_data)

                return person_data

        except Exception as e:
            self.logger.error(f"Person enrichment failed for {email}: {e}")
            return None
