"""
Hunter.io API Tool

Integrates with Hunter.io to find email addresses and contacts.

API Documentation: https://hunter.io/api-documentation
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class HunterIOTool(BaseTool):
    """
    Tool for interacting with Hunter.io Email Finder API.

    Requires API key from https://hunter.io
    """

    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="hunter_io",
            api_key=api_key,
            cache_ttl=86400,  # Cache for 24 hours
            rate_limit_per_minute=50  # Adjusted for typical plan limits
        )

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for email addresses.

        Args:
            query: Domain name to search
            **kwargs: Additional parameters

        Returns:
            List of email data
        """
        domain = query
        return await self.find_emails(domain=domain, **kwargs)

    async def find_emails(
        self,
        domain: str,
        department: Optional[str] = None,
        type: str = "personal"
    ) -> List[Dict[str, Any]]:
        """
        Find email addresses for a domain.

        Args:
            domain: Company domain (e.g., "example.com")
            department: Department filter (e.g., "engineering", "sales")
            type: Email type ("personal" or "generic")

        Returns:
            List of email contacts
        """
        if not self.api_key:
            self.logger.warning("Hunter.io API key not configured, returning empty results")
            return []

        cache_key = f"hunter_domain_{domain}_{department}_{type}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            params = {
                "api_key": self.api_key,
                "domain": domain,
                "type": type,
                "limit": 10
            }

            if department:
                params["department"] = department

            url = f"{self.BASE_URL}/domain-search"

            self.logger.info(f"Searching Hunter.io for domain: {domain}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("errors"):
                    self.logger.error(f"Hunter.io API errors: {data['errors']}")
                    return []

                domain_data = data.get("data", {})
                emails = domain_data.get("emails", [])

                # Transform to our format
                results = []
                for email_data in emails:
                    results.append({
                        "email": email_data.get("value"),
                        "name": f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                        "position": email_data.get("position"),
                        "department": email_data.get("department"),
                        "seniority": email_data.get("seniority"),
                        "phone": email_data.get("phone_number"),
                        "linkedin_url": email_data.get("linkedin"),
                        "twitter": email_data.get("twitter"),
                        "confidence": email_data.get("confidence")
                    })

                self.logger.info(f"Found {len(results)} email contacts for {domain}")

                # Cache results
                self._set_in_cache(cache_key, results)

                return results

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Hunter.io API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            self.logger.error(f"Hunter.io API search failed: {e}", exc_info=True)
            return []

    async def verify_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Verify an email address.

        Args:
            email: Email address to verify

        Returns:
            Verification result or None
        """
        if not self.api_key:
            self.logger.warning("Hunter.io API key not configured")
            return None

        cache_key = f"hunter_verify_{email}"

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            await self._check_rate_limit()

            params = {
                "api_key": self.api_key,
                "email": email
            }

            url = f"{self.BASE_URL}/email-verifier"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                result = data.get("data", {})

                if result:
                    self._set_in_cache(cache_key, result)

                return result

        except Exception as e:
            self.logger.error(f"Email verification failed for {email}: {e}")
            return None

    async def find_email_by_name(
        self,
        domain: str,
        first_name: str,
        last_name: str
    ) -> Optional[str]:
        """
        Find email address for a specific person.

        Args:
            domain: Company domain
            first_name: Person's first name
            last_name: Person's last name

        Returns:
            Email address or None
        """
        if not self.api_key:
            self.logger.warning("Hunter.io API key not configured")
            return None

        try:
            await self._check_rate_limit()

            params = {
                "api_key": self.api_key,
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name
            }

            url = f"{self.BASE_URL}/email-finder"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                email = data.get("data", {}).get("email")

                return email

        except Exception as e:
            self.logger.error(f"Email finder failed for {first_name} {last_name} @ {domain}: {e}")
            return None
