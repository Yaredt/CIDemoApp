"""
Lead Generation Workflow Orchestration

Manages the complete lead generation workflow from search to ranking.
"""

import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base import AgentConfig
from agents.coordinator import MasterCoordinator
from agents.models import Lead, AgentExecutionResult
from config.settings import get_settings
from orchestration.storage import LeadStorage

logger = logging.getLogger(__name__)


class LeadGenerationWorkflow:
    """
    Orchestrates the complete lead generation workflow.

    Workflow Steps:
    1. Initialize agents with configuration
    2. Execute master coordinator
    3. Store results in Cosmos DB
    4. Export to various formats
    5. Generate reports
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize workflow.

        Args:
            config: Optional configuration overrides
        """
        self.settings = get_settings()
        self.config = config or {}
        self.storage = LeadStorage()

        # Initialize master coordinator
        self.coordinator = self._initialize_coordinator()

    def _initialize_coordinator(self) -> MasterCoordinator:
        """
        Initialize the master coordinator agent.

        Returns:
            MasterCoordinator instance
        """
        # Build agent configuration
        agent_config = AgentConfig(
            name="master_coordinator",
            description="Master coordinator for lead generation",
            enabled=True,
            max_results=self.settings.max_results_per_agent,
            azure_openai_endpoint=self.settings.azure_openai_endpoint,
            azure_openai_key=self.settings.azure_openai_key,
            azure_openai_deployment=self.settings.azure_openai_deployment,
            custom_config={
                "serper_api_key": self.settings.serper_api_key,
                "hunter_api_key": self.settings.hunter_api_key,
                "clearbit_api_key": self.settings.clearbit_api_key,
                "sam_api_key": self.settings.sam_gov_api_key,
                "min_employee_count": self.settings.min_employee_count,
                "target_industries": self.settings.target_industries,
            }
        )

        return MasterCoordinator(agent_config)

    async def execute(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentExecutionResult:
        """
        Execute the complete lead generation workflow.

        Args:
            context: Optional execution context

        Returns:
            AgentExecutionResult with ranked leads
        """
        logger.info("=" * 80)
        logger.info("Starting Lead Generation Workflow")
        logger.info("=" * 80)

        start_time = datetime.utcnow()

        try:
            # Execute master coordinator
            logger.info("Executing master coordinator...")
            result = await self.coordinator.execute(context)

            if not result.success:
                logger.error(f"Workflow execution failed: {result.error}")
                return result

            leads = result.leads_found

            logger.info(f"Master coordinator completed successfully")
            logger.info(f"Total leads found: {len(leads)}")

            # Store leads in database
            if leads:
                logger.info("Storing leads in Cosmos DB...")
                await self.storage.store_leads(leads)
                logger.info(f"Stored {len(leads)} leads successfully")

            # Generate summary
            summary = self._generate_summary(leads, result)

            logger.info("=" * 80)
            logger.info("Workflow Execution Summary")
            logger.info("=" * 80)
            logger.info(f"Total Execution Time: {result.execution_time:.2f}s")
            logger.info(f"Leads Found: {len(leads)}")
            logger.info(f"Top Lead Score: {summary['top_lead_score']}")
            logger.info(f"Average Score: {summary['average_score']:.2f}")
            logger.info("=" * 80)

            # Add summary to result metadata
            result.metadata["summary"] = summary

            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return AgentExecutionResult(
                agent_name="workflow",
                success=False,
                leads_found=[],
                execution_time=execution_time,
                error=str(e)
            )

    def _generate_summary(
        self,
        leads: List[Lead],
        result: AgentExecutionResult
    ) -> Dict[str, Any]:
        """
        Generate execution summary.

        Args:
            leads: List of leads found
            result: Execution result

        Returns:
            Summary dictionary
        """
        if not leads:
            return {
                "total_leads": 0,
                "top_lead_score": 0,
                "average_score": 0,
                "industry_breakdown": {},
                "signal_breakdown": {}
            }

        # Calculate scores
        scores = [lead.score.overall_score for lead in leads if lead.score]
        top_lead_score = max(scores) if scores else 0
        average_score = sum(scores) / len(scores) if scores else 0

        # Industry breakdown
        industry_breakdown = {}
        for lead in leads:
            industry = lead.company.industry.value
            industry_breakdown[industry] = industry_breakdown.get(industry, 0) + 1

        # Buying signal breakdown
        signal_breakdown = {}
        for lead in leads:
            for signal in lead.buying_signals:
                signal_name = signal.value
                signal_breakdown[signal_name] = signal_breakdown.get(signal_name, 0) + 1

        return {
            "total_leads": len(leads),
            "top_lead_score": top_lead_score,
            "average_score": average_score,
            "industry_breakdown": industry_breakdown,
            "signal_breakdown": signal_breakdown,
            "pipeline_stats": result.metadata.get("pipeline_stages", {}),
            "execution_time": result.execution_time
        }

    async def get_top_leads(self, limit: int = 10) -> List[Lead]:
        """
        Get top ranked leads from storage.

        Args:
            limit: Number of leads to return

        Returns:
            List of top leads
        """
        return await self.storage.get_top_leads(limit)

    async def export_leads(
        self,
        leads: List[Lead],
        format: str = "json",
        output_path: Optional[str] = None
    ) -> str:
        """
        Export leads to file.

        Args:
            leads: Leads to export
            format: Export format (json, csv, excel)
            output_path: Optional output file path

        Returns:
            Path to exported file
        """
        return await self.storage.export_leads(leads, format, output_path)
