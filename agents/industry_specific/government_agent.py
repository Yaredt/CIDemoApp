"""
Government Agency Search Agent

Searches for government agencies with technology modernization opportunities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig
from agents.models import (
    Lead, Company, Industry, LeadStatus,
    BuyingSignal, TechnologyIndicator, AgentExecutionResult
)
from tools.sam_gov_api import SAMGovAPITool
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class GovernmentAgent(BaseAgent):
    """
    Agent specialized in finding government agency leads.

    Data sources:
    - SAM.gov (System for Award Management)
    - Government procurement portals
    - Federal, state, and local RFPs
    - Technology modernization initiatives (TMF, etc.)
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.sam_tool = SAMGovAPITool(config.custom_config.get("sam_api_key"))
        self.web_search_tool = WebSearchTool(config.custom_config.get("serper_api_key"))

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute government lead search.

        Args:
            context: Optional context with search parameters

        Returns:
            AgentExecutionResult with discovered government leads
        """
        start_time = datetime.utcnow()
        leads = []

        try:
            self.logger.info("Starting government agent execution")

            # Phase 1: Search SAM.gov for opportunities
            opportunities = await self._search_sam_opportunities()

            # Phase 2: Search for agency modernization initiatives
            modernization_leads = await self._search_modernization_initiatives()

            # Combine and create leads
            all_agencies = opportunities + modernization_leads

            for agency_data in all_agencies[:self.config.max_results]:
                try:
                    lead = await self._create_lead_from_agency(agency_data)
                    leads.append(lead)
                except Exception as e:
                    self.logger.error(f"Error processing agency: {e}")
                    continue

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=True,
                leads_found=leads,
                leads_processed=len(leads),
                execution_time=execution_time,
                metadata={
                    "sam_opportunities": len(opportunities),
                    "modernization_initiatives": len(modernization_leads),
                    "data_sources": ["sam.gov", "web_search"]
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Government agent execution failed: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=False,
                leads_found=leads,
                execution_time=execution_time,
                error=str(e)
            )

            self._record_execution(result)
            return result

    async def _search_sam_opportunities(self) -> List[Dict[str, Any]]:
        """
        Search SAM.gov for technology modernization opportunities.

        Returns:
            List of opportunities
        """
        try:
            # Search for IT modernization RFPs
            keywords = [
                "legacy modernization",
                "system replacement",
                "cloud migration",
                "digital transformation"
            ]

            opportunities = []
            for keyword in keywords:
                results = await self.sam_tool.search_opportunities(keyword)
                opportunities.extend(results)

            self.logger.info(f"Found {len(opportunities)} SAM.gov opportunities")
            return opportunities

        except Exception as e:
            self.logger.error(f"SAM.gov search failed: {e}")
            return []

    async def _search_modernization_initiatives(self) -> List[Dict[str, Any]]:
        """
        Search for government modernization initiatives.

        Returns:
            List of agencies with initiatives
        """
        try:
            search_queries = [
                "federal agency IT modernization",
                "state government legacy system replacement",
                "government digital transformation initiative",
                "TMF technology modernization fund"
            ]

            all_results = []
            for query in search_queries:
                results = await self.web_search_tool.search(query, num_results=10)
                all_results.extend(results)

            # Extract agencies
            agencies = await self._extract_agencies_from_results(all_results)
            return agencies

        except Exception as e:
            self.logger.error(f"Modernization initiative search failed: {e}")
            return []

    async def _extract_agencies_from_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract government agencies from search results.

        Args:
            results: Search results

        Returns:
            List of agency data
        """
        agencies = {}

        # Common government agency patterns
        agency_patterns = ["Department", "Agency", "Bureau", "Office", "Administration"]

        for result in results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            for pattern in agency_patterns:
                if pattern in title:
                    # Extract agency name
                    parts = title.split(pattern)
                    if len(parts) > 1:
                        agency_name = parts[0].strip() + " " + pattern
                        if agency_name not in agencies:
                            agencies[agency_name] = {
                                "name": agency_name,
                                "initiatives": [],
                                "sources": []
                            }
                        agencies[agency_name]["initiatives"].append(snippet)
                        agencies[agency_name]["sources"].append(result.get("link", ""))

        return list(agencies.values())

    async def _create_lead_from_agency(self, agency_data: Dict[str, Any]) -> Lead:
        """
        Create a lead from agency data.

        Args:
            agency_data: Agency data

        Returns:
            Lead object
        """
        company = Company(
            name=agency_data.get("name", agency_data.get("agency_name", "Unknown")),
            industry=Industry.GOVERNMENT,
            sam_uei=agency_data.get("uei"),
            technology_indicators=TechnologyIndicator(
                digital_transformation_initiatives=agency_data.get("initiatives", [])
            )
        )

        lead_id = f"gov_{company.name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

        # Determine buying signals
        buying_signals = []
        if agency_data.get("rfp_id"):
            buying_signals.append(BuyingSignal.RFP_PUBLISHED)
        if agency_data.get("initiatives"):
            buying_signals.append(BuyingSignal.TECHNOLOGY_INITIATIVE)

        lead = Lead(
            id=lead_id,
            company=company,
            source_agent=self.name,
            source_data=agency_data,
            data_sources=["sam.gov", "web_search"] if agency_data.get("uei") else ["web_search"],
            status=LeadStatus.NEW,
            tags=["government", "public_sector"],
            buying_signals=buying_signals
        )

        return lead
