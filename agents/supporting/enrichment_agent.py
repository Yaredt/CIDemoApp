"""
Enrichment Agent

Enriches leads with additional company information, contacts, and technology stack details.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig
from agents.models import (
    Lead, Contact, TechnologyIndicator, TechnologyStack,
    AgentExecutionResult, LeadStatus
)
from tools.hunter_io import HunterIOTool
from tools.clearbit import ClearbitTool
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class EnrichmentAgent(BaseAgent):
    """
    Agent specialized in enriching leads with additional data.

    Enrichment areas:
    - Contact information (emails, phone numbers)
    - Company details (size, revenue, description)
    - Technology stack information
    - Social media presence
    - Recent news and activities
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.hunter_tool = HunterIOTool(config.custom_config.get("hunter_api_key"))
        self.clearbit_tool = ClearbitTool(config.custom_config.get("clearbit_api_key"))
        self.web_search_tool = WebSearchTool(config.custom_config.get("serper_api_key"))

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute lead enrichment.

        Args:
            context: Context with leads to enrich

        Returns:
            AgentExecutionResult with enriched leads
        """
        start_time = datetime.utcnow()
        enriched_leads = []

        try:
            leads = context.get("leads", []) if context else []

            if not leads:
                self.logger.warning("No leads provided for enrichment")
                return AgentExecutionResult(
                    agent_name=self.name,
                    success=True,
                    leads_found=[],
                    execution_time=0.0
                )

            self.logger.info(f"Enriching {len(leads)} leads")

            for lead in leads:
                try:
                    enriched_lead = await self.enrich(lead)
                    enriched_leads.append(enriched_lead)
                except Exception as e:
                    self.logger.error(f"Error enriching lead {lead.id}: {e}")
                    enriched_leads.append(lead)  # Return original if enrichment fails

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=True,
                leads_found=enriched_leads,
                leads_processed=len(enriched_leads),
                execution_time=execution_time,
                metadata={
                    "enrichment_sources": ["hunter.io", "clearbit", "web_search"]
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Enrichment agent execution failed: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=False,
                leads_found=enriched_leads,
                execution_time=execution_time,
                error=str(e)
            )

            self._record_execution(result)
            return result

    async def enrich(self, lead: Lead) -> Lead:
        """
        Enrich a single lead with additional information.

        Args:
            lead: Lead to enrich

        Returns:
            Enriched lead
        """
        self.logger.info(f"Enriching lead: {lead.id}")

        # Update status
        lead.status = LeadStatus.ENRICHING

        # Enrich contacts
        await self._enrich_contacts(lead)

        # Enrich company information
        await self._enrich_company_info(lead)

        # Enrich technology stack
        await self._enrich_technology_stack(lead)

        # Mark as enriched
        lead.is_enriched = True
        lead.enrichment_timestamp = datetime.utcnow()
        lead.updated_at = datetime.utcnow()

        return lead

    async def _enrich_contacts(self, lead: Lead) -> None:
        """
        Find and enrich contact information.

        Args:
            lead: Lead to enrich
        """
        try:
            if not lead.company.website:
                return

            # Extract domain from website
            domain = str(lead.company.website).replace("http://", "").replace("https://", "").split("/")[0]

            # Search for email addresses
            contacts = await self.hunter_tool.find_emails(
                domain=domain,
                department="technology"  # Focus on IT decision makers
            )

            if contacts:
                lead.contacts.extend([
                    Contact(
                        name=c.get("name"),
                        email=c.get("email"),
                        title=c.get("position"),
                        department=c.get("department"),
                        seniority_level=c.get("seniority")
                    )
                    for c in contacts[:5]  # Limit to top 5
                ])

                lead.data_sources.append("hunter.io")
                self.logger.info(f"Found {len(contacts)} contacts for {lead.company.name}")

        except Exception as e:
            self.logger.error(f"Error enriching contacts: {e}")

    async def _enrich_company_info(self, lead: Lead) -> None:
        """
        Enrich company information using Clearbit.

        Args:
            lead: Lead to enrich
        """
        try:
            if not lead.company.website:
                return

            domain = str(lead.company.website).replace("http://", "").replace("https://", "").split("/")[0]

            # Get company data from Clearbit
            company_data = await self.clearbit_tool.enrich_company(domain)

            if company_data:
                # Update company information
                if company_data.get("description"):
                    lead.company.description = company_data["description"]

                if company_data.get("employeesRange"):
                    lead.company.size = company_data["employeesRange"]
                    lead.company.employee_count = company_data.get("metrics", {}).get("employees")

                if company_data.get("tags"):
                    lead.tags.extend(company_data["tags"])

                if company_data.get("tech"):
                    # Update technology stack
                    if not lead.company.technology_indicators:
                        lead.company.technology_indicators = TechnologyIndicator()

                    tech_list = company_data["tech"]
                    if any("cloud" in t.lower() for t in tech_list):
                        lead.company.technology_indicators.cloud_migration_signals = True

                lead.data_sources.append("clearbit")
                self.logger.info(f"Enriched company info for {lead.company.name}")

        except Exception as e:
            self.logger.error(f"Error enriching company info: {e}")

    async def _enrich_technology_stack(self, lead: Lead) -> None:
        """
        Enrich technology stack information.

        Args:
            lead: Lead to enrich
        """
        try:
            # Search for technology stack information
            tech_query = f"{lead.company.name} technology stack systems"
            results = await self.web_search_tool.search(tech_query, num_results=5)

            if results:
                if not lead.company.technology_indicators:
                    lead.company.technology_indicators = TechnologyIndicator()

                # Analyze results for technology mentions
                content = " ".join([r.get("snippet", "") for r in results])

                # Detect cloud providers
                if "azure" in content.lower():
                    lead.company.technology_indicators.stack.append(TechnologyStack.CLOUD_AZURE)
                if "aws" in content.lower():
                    lead.company.technology_indicators.stack.append(TechnologyStack.CLOUD_AWS)
                if "gcp" in content.lower() or "google cloud" in content.lower():
                    lead.company.technology_indicators.stack.append(TechnologyStack.CLOUD_GCP)

                # Detect legacy systems
                if any(kw in content.lower() for kw in ["mainframe", "as400", "cobol"]):
                    lead.company.technology_indicators.stack.append(TechnologyStack.LEGACY_MAINFRAME)
                    lead.company.technology_indicators.legacy_systems = True

                lead.signal_details["technology_research"] = results

        except Exception as e:
            self.logger.error(f"Error enriching technology stack: {e}")
