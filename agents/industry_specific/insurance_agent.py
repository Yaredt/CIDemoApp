"""
Insurance Industry Search Agent

Searches for insurance carriers with modernization opportunities.
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


class InsuranceAgent(BaseAgent):
    """
    Agent specialized in finding insurance carrier leads.

    Data sources:
    - Insurance industry publications
    - Carrier websites and news
    - Technology modernization announcements
    - Industry conferences and events
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.web_search_tool = WebSearchTool(config.custom_config.get("serper_api_key"))

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute insurance lead search.

        Args:
            context: Optional context with search parameters

        Returns:
            AgentExecutionResult with discovered insurance leads
        """
        start_time = datetime.utcnow()
        leads = []

        try:
            self.logger.info("Starting insurance agent execution")

            # Search for insurance carriers with modernization signals
            search_queries = [
                "insurance carrier core system modernization",
                "insurance company legacy system replacement",
                "P&C insurance digital transformation",
                "life insurance cloud migration",
                "insurance carrier hiring CTO CIO technology"
            ]

            all_results = []
            for query in search_queries:
                results = await self.web_search_tool.search(query, num_results=10)
                all_results.extend(results)

            # Extract unique companies from search results
            companies = await self._extract_companies_from_results(all_results)

            # Create leads
            for company_data in companies[:self.config.max_results]:
                try:
                    lead = await self._create_lead_from_company(company_data)
                    await self._enrich_lead(lead)
                    leads.append(lead)
                except Exception as e:
                    self.logger.error(f"Error processing company: {e}")
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
                    "results_found": len(all_results),
                    "data_sources": ["web_search"]
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Insurance agent execution failed: {e}", exc_info=True)
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

    async def _extract_companies_from_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract unique companies from search results.

        Args:
            results: Search results

        Returns:
            List of company data
        """
        companies = {}

        for result in results:
            # Simple extraction - could be enhanced with NER/LLM
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")

            # Extract company name (simplified)
            for word in title.split():
                if word[0].isupper() and len(word) > 3:
                    if word not in companies:
                        companies[word] = {
                            "name": word,
                            "mentions": [],
                            "sources": []
                        }
                    companies[word]["mentions"].append(snippet)
                    companies[word]["sources"].append(link)

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
            industry=Industry.INSURANCE,
            technology_indicators=TechnologyIndicator()
        )

        lead_id = f"insurance_{company_data.get('name', '').lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

        lead = Lead(
            id=lead_id,
            company=company,
            source_agent=self.name,
            source_data=company_data,
            data_sources=["web_search"],
            status=LeadStatus.NEW,
            tags=["insurance"],
            buying_signals=[BuyingSignal.TECHNOLOGY_INITIATIVE]
        )

        return lead

    async def _enrich_lead(self, lead: Lead) -> None:
        """
        Enrich lead with additional signals.

        Args:
            lead: Lead to enrich
        """
        try:
            # Search for specific buying signals
            hiring_query = f"{lead.company.name} insurance hiring technology jobs"
            hiring_results = await self.web_search_tool.search(hiring_query, num_results=3)

            if hiring_results:
                lead.buying_signals.append(BuyingSignal.JOB_POSTING)
                lead.signal_details["hiring"] = hiring_results

        except Exception as e:
            self.logger.error(f"Error enriching lead: {e}")
