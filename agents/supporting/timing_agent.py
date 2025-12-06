"""
Timing Agent

Analyzes buying cycle signals to determine urgency and optimal timing for outreach.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig
from agents.models import (
    Lead, BuyingSignal, AgentExecutionResult
)
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class TimingAgent(BaseAgent):
    """
    Agent specialized in detecting timing and urgency signals.

    Timing signals:
    - Recent job postings (hiring indicates active projects)
    - Executive changes (new leadership = new initiatives)
    - Funding rounds (budget availability)
    - Regulatory deadlines (compliance drivers)
    - Fiscal year timing (budget cycles)
    - Technology announcements (active modernization)
    - RFP publications (active procurement)
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.web_search_tool = WebSearchTool(config.custom_config.get("serper_api_key"))

        # Timing weights for different signals
        self.signal_weights = {
            BuyingSignal.RFP_PUBLISHED: 30,  # Very high urgency
            BuyingSignal.JOB_POSTING: 20,  # High urgency
            BuyingSignal.EXECUTIVE_CHANGE: 15,  # Medium-high urgency
            BuyingSignal.REGULATORY_DEADLINE: 25,  # Very high urgency
            BuyingSignal.RECENT_FUNDING: 15,  # Medium-high urgency
            BuyingSignal.TECHNOLOGY_INITIATIVE: 10,  # Medium urgency
            BuyingSignal.PARTNERSHIP_ANNOUNCEMENT: 10,  # Medium urgency
        }

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute timing analysis.

        Args:
            context: Context with leads to analyze

        Returns:
            AgentExecutionResult with timing-analyzed leads
        """
        start_time = datetime.utcnow()
        analyzed_leads = []

        try:
            leads = context.get("leads", []) if context else []

            if not leads:
                self.logger.warning("No leads provided for timing analysis")
                return AgentExecutionResult(
                    agent_name=self.name,
                    success=True,
                    leads_found=[],
                    execution_time=0.0
                )

            self.logger.info(f"Analyzing timing for {len(leads)} leads")

            for lead in leads:
                try:
                    await self._analyze_timing(lead)
                    analyzed_leads.append(lead)
                except Exception as e:
                    self.logger.error(f"Error analyzing timing for lead {lead.id}: {e}")
                    analyzed_leads.append(lead)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=True,
                leads_found=analyzed_leads,
                leads_processed=len(analyzed_leads),
                execution_time=execution_time,
                metadata={
                    "signal_weights": self.signal_weights
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Timing agent execution failed: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=False,
                leads_found=analyzed_leads,
                execution_time=execution_time,
                error=str(e)
            )

            self._record_execution(result)
            return result

    async def _analyze_timing(self, lead: Lead) -> None:
        """
        Analyze timing signals for a lead.

        Args:
            lead: Lead to analyze
        """
        self.logger.info(f"Analyzing timing for lead: {lead.id}")

        # Search for recent timing signals
        await self._detect_job_postings(lead)
        await self._detect_executive_changes(lead)
        await self._detect_recent_announcements(lead)

        # Calculate timing score based on signals
        timing_score = await self._calculate_timing_score(lead)

        # Store timing score in metadata
        lead.metadata["timing_score"] = timing_score
        lead.metadata["timing_analysis"] = {
            "signals_detected": [s.value for s in lead.buying_signals],
            "urgency_level": self._get_urgency_level(timing_score),
            "recommended_action": self._get_recommended_action(timing_score)
        }

        lead.updated_at = datetime.utcnow()

    async def _detect_job_postings(self, lead: Lead) -> None:
        """
        Detect recent job postings indicating hiring.

        Args:
            lead: Lead to check
        """
        try:
            # Search for job postings
            job_titles = ["CTO", "CIO", "VP Technology", "Director IT", "Chief Digital Officer"]

            for title in job_titles:
                query = f"{lead.company.name} hiring {title} site:linkedin.com OR site:indeed.com"
                results = await self.web_search_tool.search(query, num_results=3)

                if results:
                    if BuyingSignal.JOB_POSTING not in lead.buying_signals:
                        lead.buying_signals.append(BuyingSignal.JOB_POSTING)

                    if "job_postings" not in lead.signal_details:
                        lead.signal_details["job_postings"] = []
                    lead.signal_details["job_postings"].extend(results)

                    break  # Found job postings, no need to search more

        except Exception as e:
            self.logger.error(f"Error detecting job postings: {e}")

    async def _detect_executive_changes(self, lead: Lead) -> None:
        """
        Detect recent executive changes.

        Args:
            lead: Lead to check
        """
        try:
            # Search for executive changes in past 6 months
            query = f"{lead.company.name} new CTO OR CIO OR 'Chief Technology Officer' OR 'Chief Information Officer'"
            results = await self.web_search_tool.search(query, num_results=5)

            if results:
                # Check if announcements are recent (simple heuristic)
                recent_results = [
                    r for r in results
                    if any(kw in r.get("snippet", "").lower() for kw in ["joins", "appointed", "names", "announces"])
                ]

                if recent_results:
                    if BuyingSignal.EXECUTIVE_CHANGE not in lead.buying_signals:
                        lead.buying_signals.append(BuyingSignal.EXECUTIVE_CHANGE)

                    lead.signal_details["executive_changes"] = recent_results

        except Exception as e:
            self.logger.error(f"Error detecting executive changes: {e}")

    async def _detect_recent_announcements(self, lead: Lead) -> None:
        """
        Detect recent technology announcements.

        Args:
            lead: Lead to check
        """
        try:
            query = f"{lead.company.name} announces technology modernization digital transformation"
            results = await self.web_search_tool.search(query, num_results=5)

            if results:
                lead.signal_details["recent_announcements"] = results

        except Exception as e:
            self.logger.error(f"Error detecting announcements: {e}")

    async def _calculate_timing_score(self, lead: Lead) -> float:
        """
        Calculate timing score based on detected signals.

        Args:
            lead: Lead to score

        Returns:
            Timing score (0-100)
        """
        total_score = 0.0

        # Add weights for each signal detected
        for signal in lead.buying_signals:
            weight = self.signal_weights.get(signal, 5)
            total_score += weight

        # Boost score for multiple signals
        if len(lead.buying_signals) > 3:
            total_score *= 1.2

        # Cap at 100
        return min(total_score, 100.0)

    def _get_urgency_level(self, timing_score: float) -> str:
        """
        Get urgency level from timing score.

        Args:
            timing_score: Timing score

        Returns:
            Urgency level string
        """
        if timing_score >= 70:
            return "VERY HIGH"
        elif timing_score >= 50:
            return "HIGH"
        elif timing_score >= 30:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommended_action(self, timing_score: float) -> str:
        """
        Get recommended action based on timing score.

        Args:
            timing_score: Timing score

        Returns:
            Recommended action
        """
        if timing_score >= 70:
            return "IMMEDIATE OUTREACH - High urgency signals detected"
        elif timing_score >= 50:
            return "PRIORITIZE - Strong buying signals present"
        elif timing_score >= 30:
            return "ENGAGE - Moderate opportunity window"
        else:
            return "NURTURE - Monitor for stronger signals"
