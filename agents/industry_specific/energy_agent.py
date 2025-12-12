"""
Energy Industry Search Agent

Searches for energy companies (utilities, smart grid) with modernization opportunities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig
from agents.models import (
    Lead, Company, Industry, LeadStatus,
    BuyingSignal, TechnologyIndicator, AgentExecutionResult
)
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class EnergyAgent(BaseAgent):
    """
    Agent specialized in finding energy sector leads.

    Focus areas:
    - Electric utilities
    - Smart grid initiatives
    - Energy management systems
    - Grid modernization projects
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.web_search_tool = WebSearchTool(config.custom_config.get("serper_api_key"))

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute energy sector lead search.

        Args:
            context: Optional context with search parameters

        Returns:
            AgentExecutionResult with discovered energy leads
        """
        start_time = datetime.utcnow()
        leads = []

        try:
            self.logger.info("Starting energy agent execution")

            # Search for energy companies with modernization initiatives
            search_queries = [
                "utility company smart grid modernization",
                "electric utility grid management system upgrade",
                "energy company digital transformation technology",
                "utility SCADA system replacement",
                "power company AMI smart meter deployment"
            ]

            all_results = []
            for query in search_queries:
                results = await self.web_search_tool.search(query, num_results=10)
                all_results.extend(results)

            # Extract companies
            companies = await self._extract_energy_companies(all_results)

            # Create leads
            for company_data in companies[:self.config.max_results]:
                try:
                    lead = await self._create_lead_from_company(company_data)
                    await self._detect_grid_modernization_signals(lead)
                    leads.append(lead)
                except Exception as e:
                    self.logger.error(f"Error processing energy company: {e}")
                    continue

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=True,
                leads_found=leads,
                leads_processed=len(leads),
                execution_time=execution_time,
                metadata={
                    "search_queries": len(search_queries),
                    "data_sources": ["web_search"]
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Energy agent execution failed: {e}", exc_info=True)
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

    async def _extract_energy_companies(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract energy companies from search results.

        Args:
            results: Search results

        Returns:
            List of company data
        """
        companies = {}

        for result in results:
            snippet = result.get("snippet", "")
            title = result.get("title", "")

            # Look for utility/energy company patterns
            keywords = ["utility", "power", "electric", "energy", "grid"]
            if any(kw in title.lower() or kw in snippet.lower() for kw in keywords):
                # Extract company name (simplified)
                for word in title.split():
                    if word[0].isupper() and len(word) > 3:
                        company_name = word
                        if company_name not in companies:
                            companies[company_name] = {
                                "name": company_name,
                                "initiatives": [],
                                "sources": []
                            }
                        companies[company_name]["initiatives"].append(snippet)
                        companies[company_name]["sources"].append(result.get("link", ""))

        return list(companies.values())

    async def _create_lead_from_company(self, company_data: Dict[str, Any]) -> Lead:
        """
        Create a lead from company data.

        Args:
            company_data: Company data

        Returns:
            Lead object
        """
        company = Company(
            name=company_data.get("name", "Unknown"),
            industry=Industry.ENERGY,
            technology_indicators=TechnologyIndicator(
                digital_transformation_initiatives=company_data.get("initiatives", [])
            )
        )

        lead_id = f"energy_{company_data.get('name', '').lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

        lead = Lead(
            id=lead_id,
            company=company,
            source_agent=self.name,
            source_data=company_data,
            data_sources=["web_search"],
            status=LeadStatus.NEW,
            tags=["energy", "utility"],
            buying_signals=[BuyingSignal.TECHNOLOGY_INITIATIVE]
        )

        return lead

    async def _detect_grid_modernization_signals(self, lead: Lead) -> None:
        """
        Detect grid modernization and smart grid signals.

        Args:
            lead: Lead to enrich
        """
        try:
            # Search for specific grid modernization signals
            queries = [
                f"{lead.company.name} smart grid project",
                f"{lead.company.name} grid modernization investment",
                f"{lead.company.name} AMI smart meter"
            ]

            for query in queries:
                results = await self.web_search_tool.search(query, num_results=3)
                if results:
                    if not lead.signal_details.get("grid_modernization"):
                        lead.signal_details["grid_modernization"] = []
                    lead.signal_details["grid_modernization"].extend(results)

        except Exception as e:
            self.logger.error(f"Error detecting grid modernization signals: {e}")
