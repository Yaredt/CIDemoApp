"""
Banking Industry Search Agent

Searches for banking prospects using FDIC data, financial news, and regulatory filings.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio

from agents.base import BaseAgent, AgentConfig
from agents.models import (
    Lead, Company, Industry, LeadStatus,
    BuyingSignal, TechnologyIndicator, AgentExecutionResult
)
from tools.fdic_api import FDICAPITool
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class BankingAgent(BaseAgent):
    """
    Agent specialized in finding banking leads with technology modernization opportunities.

    Data sources:
    - FDIC Institution Database
    - Financial news and press releases
    - Banking technology publications
    - Regulatory filings (if available)
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.fdic_tool = FDICAPITool()
        self.web_search_tool = WebSearchTool(config.custom_config.get("serper_api_key"))

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute banking lead search.

        Args:
            context: Optional context with search parameters

        Returns:
            AgentExecutionResult with discovered banking leads
        """
        start_time = datetime.utcnow()
        leads = []

        try:
            self.logger.info("Starting banking agent execution")

            # Search parameters from context or defaults
            search_params = context or {}
            asset_min = search_params.get("asset_min", 1000000000)  # $1B+ assets
            states = search_params.get("states", None)

            # Phase 1: Search FDIC database for target banks
            self.logger.info(f"Searching FDIC database (min assets: ${asset_min})")
            banks = await self._search_fdic_database(asset_min, states)

            # Phase 2: Enrich with technology signals
            for bank_data in banks[:self.config.max_results]:
                try:
                    lead = await self._create_lead_from_bank(bank_data)

                    # Search for technology modernization signals
                    await self._detect_technology_signals(lead)

                    # Search for buying signals
                    await self._detect_buying_signals(lead)

                    leads.append(lead)

                except Exception as e:
                    self.logger.error(f"Error processing bank {bank_data.get('name')}: {e}")
                    continue

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=True,
                leads_found=leads,
                leads_processed=len(leads),
                execution_time=execution_time,
                metadata={
                    "banks_searched": len(banks),
                    "asset_threshold": asset_min,
                    "data_sources": ["fdic", "web_search"]
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Banking agent execution failed: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=False,
                leads_found=leads,
                leads_processed=len(leads),
                execution_time=execution_time,
                error=str(e)
            )

            self._record_execution(result)
            return result

    async def _search_fdic_database(
        self,
        asset_min: int,
        states: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search FDIC database for banks matching criteria.

        Args:
            asset_min: Minimum asset threshold
            states: Optional list of state codes to filter by

        Returns:
            List of bank data from FDIC
        """
        try:
            filters = {"asset_min": asset_min}
            if states:
                filters["states"] = states

            banks = await self.fdic_tool.search_institutions(filters)
            self.logger.info(f"Found {len(banks)} banks from FDIC database")
            return banks

        except Exception as e:
            self.logger.error(f"FDIC database search failed: {e}")
            return []

    async def _create_lead_from_bank(self, bank_data: Dict[str, Any]) -> Lead:
        """
        Create a lead from FDIC bank data.

        Args:
            bank_data: Bank data from FDIC API

        Returns:
            Lead object
        """
        company = Company(
            name=bank_data.get("name", "Unknown"),
            industry=Industry.BANKING,
            website=bank_data.get("website"),
            location=f"{bank_data.get('city')}, {bank_data.get('state')}",
            headquarters=f"{bank_data.get('city')}, {bank_data.get('state')}",
            fdic_cert_number=str(bank_data.get("cert", "")),
            employee_count=bank_data.get("employees"),
            revenue=f"${bank_data.get('asset', 0) / 1000000:.0f}M Assets"
        )

        lead_id = f"bank_{bank_data.get('cert', datetime.utcnow().timestamp())}"

        lead = Lead(
            id=lead_id,
            company=company,
            source_agent=self.name,
            source_data=bank_data,
            data_sources=["fdic"],
            status=LeadStatus.NEW,
            tags=["banking", "fdic"]
        )

        return lead

    async def _detect_technology_signals(self, lead: Lead) -> None:
        """
        Detect technology modernization signals for a bank.

        Args:
            lead: Lead to enrich with technology signals
        """
        try:
            # Search for technology-related news
            search_queries = [
                f"{lead.company.name} core banking system upgrade",
                f"{lead.company.name} digital transformation",
                f"{lead.company.name} cloud migration",
                f"{lead.company.name} legacy modernization"
            ]

            tech_signals = []
            for query in search_queries:
                results = await self.web_search_tool.search(query, num_results=3)
                tech_signals.extend(results)

            if tech_signals:
                # Extract technology indicators
                if not lead.company.technology_indicators:
                    lead.company.technology_indicators = TechnologyIndicator()

                # Simple keyword matching (could be enhanced with LLM analysis)
                content = " ".join([r.get("snippet", "") for r in tech_signals])

                if any(kw in content.lower() for kw in ["mainframe", "as400", "legacy"]):
                    lead.company.technology_indicators.legacy_systems = True

                if any(kw in content.lower() for kw in ["cloud", "azure", "aws", "migration"]):
                    lead.company.technology_indicators.cloud_migration_signals = True

                lead.data_sources.append("web_search")
                lead.signal_details["technology_search"] = tech_signals

        except Exception as e:
            self.logger.error(f"Error detecting technology signals: {e}")

    async def _detect_buying_signals(self, lead: Lead) -> None:
        """
        Detect buying signals for a bank.

        Args:
            lead: Lead to enrich with buying signals
        """
        try:
            # Search for hiring signals
            job_search_query = f"{lead.company.name} hiring CTO CIO technology jobs"
            job_results = await self.web_search_tool.search(job_search_query, num_results=5)

            if job_results:
                lead.buying_signals.append(BuyingSignal.JOB_POSTING)
                lead.signal_details["job_postings"] = job_results

            # Search for partnership/vendor announcements
            partnership_query = f"{lead.company.name} partnership technology vendor announcement"
            partnership_results = await self.web_search_tool.search(partnership_query, num_results=5)

            if partnership_results:
                lead.buying_signals.append(BuyingSignal.PARTNERSHIP_ANNOUNCEMENT)
                lead.signal_details["partnerships"] = partnership_results

        except Exception as e:
            self.logger.error(f"Error detecting buying signals: {e}")
