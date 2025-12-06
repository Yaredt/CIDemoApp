"""
Master Coordinator Agent

Orchestrates all agents and implements the lead ranking algorithm.
"""

import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from agents.base import BaseAgent, AgentConfig
from agents.models import (
    Lead, LeadScore, Industry, AgentExecutionResult
)
from agents.industry_specific import (
    BankingAgent, InsuranceAgent, EnergyAgent, GovernmentAgent
)
from agents.supporting import (
    EnrichmentAgent, ValidationAgent, TimingAgent
)

logger = logging.getLogger(__name__)


class MasterCoordinator(BaseAgent):
    """
    Master Coordinator Agent orchestrates the multi-agent lead generation workflow.

    Workflow:
    1. Parallel execution of industry-specific search agents
    2. Deduplication and consolidation of leads
    3. Enrichment of leads with additional data
    4. Validation of lead quality
    5. Timing analysis for urgency
    6. Scoring and ranking of all leads
    7. Production of prioritized lead list
    """

    def __init__(
        self,
        config: AgentConfig,
        industry_agents: Optional[List[BaseAgent]] = None,
        supporting_agents: Optional[Dict[str, BaseAgent]] = None
    ):
        super().__init__(config)

        # Initialize industry-specific search agents
        if industry_agents:
            self.industry_agents = industry_agents
        else:
            self.industry_agents = self._initialize_industry_agents()

        # Initialize supporting agents
        if supporting_agents:
            self.enrichment_agent = supporting_agents.get("enrichment")
            self.validation_agent = supporting_agents.get("validation")
            self.timing_agent = supporting_agents.get("timing")
        else:
            agents = self._initialize_supporting_agents()
            self.enrichment_agent = agents["enrichment"]
            self.validation_agent = agents["validation"]
            self.timing_agent = agents["timing"]

    def _initialize_industry_agents(self) -> List[BaseAgent]:
        """Initialize industry-specific search agents"""
        base_config = self.config.custom_config

        agents = [
            BankingAgent(AgentConfig(
                name="banking_agent",
                description="Banking industry search agent",
                custom_config=base_config
            )),
            InsuranceAgent(AgentConfig(
                name="insurance_agent",
                description="Insurance industry search agent",
                custom_config=base_config
            )),
            EnergyAgent(AgentConfig(
                name="energy_agent",
                description="Energy industry search agent",
                custom_config=base_config
            )),
            GovernmentAgent(AgentConfig(
                name="government_agent",
                description="Government sector search agent",
                custom_config=base_config
            )),
        ]

        return [a for a in agents if a.is_enabled]

    def _initialize_supporting_agents(self) -> Dict[str, BaseAgent]:
        """Initialize supporting agents"""
        base_config = self.config.custom_config

        return {
            "enrichment": EnrichmentAgent(AgentConfig(
                name="enrichment_agent",
                description="Lead enrichment agent",
                custom_config=base_config
            )),
            "validation": ValidationAgent(AgentConfig(
                name="validation_agent",
                description="Lead validation agent",
                custom_config=base_config
            )),
            "timing": TimingAgent(AgentConfig(
                name="timing_agent",
                description="Timing analysis agent",
                custom_config=base_config
            )),
        }

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute the complete multi-agent lead generation workflow.

        Args:
            context: Optional execution context

        Returns:
            AgentExecutionResult with final ranked leads
        """
        start_time = datetime.utcnow()

        try:
            self.logger.info("=" * 80)
            self.logger.info("Starting Master Coordinator Execution")
            self.logger.info("=" * 80)

            # Phase 1: Parallel search across all industries
            self.logger.info("Phase 1: Industry-specific lead search")
            raw_leads = await self._execute_industry_search(context)
            self.logger.info(f"Found {len(raw_leads)} total leads from industry agents")

            if not raw_leads:
                self.logger.warning("No leads found by industry agents")
                return AgentExecutionResult(
                    agent_name=self.name,
                    success=True,
                    leads_found=[],
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )

            # Phase 2: Deduplication
            self.logger.info("Phase 2: Deduplication")
            unique_leads = await self._deduplicate_leads(raw_leads)
            self.logger.info(f"After deduplication: {len(unique_leads)} unique leads")

            # Phase 3: Enrichment
            self.logger.info("Phase 3: Lead enrichment")
            enriched_leads = await self._enrich_leads(unique_leads)
            self.logger.info(f"Enriched {len(enriched_leads)} leads")

            # Phase 4: Validation
            self.logger.info("Phase 4: Lead validation")
            validated_leads = await self._validate_leads(enriched_leads)
            self.logger.info(f"Validated leads: {len(validated_leads)}")

            # Phase 5: Timing analysis
            self.logger.info("Phase 5: Timing analysis")
            timed_leads = await self._analyze_timing(validated_leads)
            self.logger.info(f"Analyzed timing for {len(timed_leads)} leads")

            # Phase 6: Scoring and ranking
            self.logger.info("Phase 6: Scoring and ranking")
            scored_leads = await self._score_and_rank_leads(timed_leads)
            self.logger.info(f"Scored and ranked {len(scored_leads)} leads")

            # Calculate execution metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.info("=" * 80)
            self.logger.info(f"Master Coordinator Execution Complete in {execution_time:.2f}s")
            self.logger.info(f"Final Output: {len(scored_leads)} ranked leads")
            self.logger.info("=" * 80)

            result = AgentExecutionResult(
                agent_name=self.name,
                success=True,
                leads_found=scored_leads,
                leads_processed=len(scored_leads),
                execution_time=execution_time,
                metadata={
                    "raw_leads": len(raw_leads),
                    "unique_leads": len(unique_leads),
                    "validated_leads": len(validated_leads),
                    "pipeline_stages": {
                        "search": len(raw_leads),
                        "deduplication": len(unique_leads),
                        "enrichment": len(enriched_leads),
                        "validation": len(validated_leads),
                        "timing": len(timed_leads),
                        "scoring": len(scored_leads)
                    }
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Master coordinator execution failed: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=False,
                leads_found=[],
                execution_time=execution_time,
                error=str(e)
            )

            self._record_execution(result)
            return result

    async def _execute_industry_search(
        self,
        context: Optional[Dict[str, Any]]
    ) -> List[Lead]:
        """
        Execute industry-specific agents in parallel.

        Args:
            context: Execution context

        Returns:
            All leads found by industry agents
        """
        # Execute all enabled industry agents in parallel
        tasks = [agent.execute(context) for agent in self.industry_agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_leads = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Industry agent {i} failed: {result}")
                continue

            if result.success:
                all_leads.extend(result.leads_found)
                self.logger.info(
                    f"Agent '{result.agent_name}' found {len(result.leads_found)} leads "
                    f"in {result.execution_time:.2f}s"
                )

        return all_leads

    async def _deduplicate_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Deduplicate leads based on company name and identifiers.

        Args:
            leads: List of leads to deduplicate

        Returns:
            Unique leads
        """
        unique_leads = {}

        for lead in leads:
            # Create dedup key based on company name and identifiers
            dedup_key = lead.company.name.lower().strip()

            # Use industry-specific IDs if available
            if lead.company.fdic_cert_number:
                dedup_key = f"fdic_{lead.company.fdic_cert_number}"
            elif lead.company.sam_uei:
                dedup_key = f"sam_{lead.company.sam_uei}"
            elif lead.company.duns_number:
                dedup_key = f"duns_{lead.company.duns_number}"

            if dedup_key in unique_leads:
                # Merge data from duplicate lead
                existing = unique_leads[dedup_key]
                existing.data_sources = list(set(existing.data_sources + lead.data_sources))
                existing.buying_signals = list(set(existing.buying_signals + lead.buying_signals))
                existing.tags = list(set(existing.tags + lead.tags))
            else:
                unique_leads[dedup_key] = lead

        return list(unique_leads.values())

    async def _enrich_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Enrich leads using the enrichment agent.

        Args:
            leads: Leads to enrich

        Returns:
            Enriched leads
        """
        if not self.enrichment_agent:
            return leads

        result = await self.enrichment_agent.execute({"leads": leads})
        return result.leads_found if result.success else leads

    async def _validate_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Validate leads using the validation agent.

        Args:
            leads: Leads to validate

        Returns:
            Validated leads
        """
        if not self.validation_agent:
            return leads

        result = await self.validation_agent.execute({"leads": leads})
        return result.leads_found if result.success else leads

    async def _analyze_timing(self, leads: List[Lead]) -> List[Lead]:
        """
        Analyze timing for leads using the timing agent.

        Args:
            leads: Leads to analyze

        Returns:
            Leads with timing analysis
        """
        if not self.timing_agent:
            return leads

        result = await self.timing_agent.execute({"leads": leads})
        return result.leads_found if result.success else leads

    async def _score_and_rank_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Score and rank all leads.

        Args:
            leads: Leads to score and rank

        Returns:
            Sorted list of leads by score (highest first)
        """
        for lead in leads:
            score = await self._calculate_lead_score(lead)
            lead.score = score

        # Sort by overall score (descending)
        ranked_leads = sorted(
            leads,
            key=lambda l: l.score.overall_score if l.score else 0,
            reverse=True
        )

        return ranked_leads

    async def _calculate_lead_score(self, lead: Lead) -> LeadScore:
        """
        Calculate comprehensive lead score.

        Scoring algorithm:
        - Fit Score (40%): Industry fit, size fit, technology fit
        - Intent Score (35%): Buying signals strength
        - Timing Score (25%): Urgency and timing signals

        Args:
            lead: Lead to score

        Returns:
            LeadScore object
        """
        # Calculate fit score components
        industry_fit = await self._score_industry_fit(lead)
        size_fit = await self._score_size_fit(lead)
        technology_fit = await self._score_technology_fit(lead)

        # Fit score is average of components
        fit_score = (industry_fit + size_fit + technology_fit) / 3

        # Calculate intent score based on buying signals
        intent_score = await self._score_intent(lead)

        # Get timing score from timing analysis
        timing_score = lead.metadata.get("timing_score", 50.0)

        # Calculate overall score (weighted average)
        overall_score = (
            0.40 * fit_score +
            0.35 * intent_score +
            0.25 * timing_score
        )

        return LeadScore(
            overall_score=round(overall_score, 2),
            fit_score=round(fit_score, 2),
            intent_score=round(intent_score, 2),
            timing_score=round(timing_score, 2),
            industry_fit=round(industry_fit, 2),
            size_fit=round(size_fit, 2),
            technology_fit=round(technology_fit, 2),
            budget_likelihood=round((size_fit + intent_score) / 2, 2),
            scoring_factors={
                "buying_signals_count": len(lead.buying_signals),
                "data_sources_count": len(lead.data_sources),
                "has_contacts": len(lead.contacts) > 0,
                "is_enriched": lead.is_enriched,
                "is_validated": lead.is_validated
            }
        )

    async def _score_industry_fit(self, lead: Lead) -> float:
        """Score how well the lead fits target industries"""
        target_industries = [Industry.BANKING, Industry.INSURANCE, Industry.ENERGY, Industry.GOVERNMENT]

        if lead.company.industry in target_industries:
            return 100.0
        elif lead.company.industry == Industry.UNKNOWN:
            return 50.0
        else:
            return 25.0

    async def _score_size_fit(self, lead: Lead) -> float:
        """Score company size fit"""
        if lead.company.employee_count:
            if lead.company.employee_count >= 5000:
                return 100.0
            elif lead.company.employee_count >= 1000:
                return 80.0
            elif lead.company.employee_count >= 500:
                return 60.0
            elif lead.company.employee_count >= 100:
                return 40.0
            else:
                return 20.0

        if lead.company.size:
            size_map = {
                "Enterprise": 100.0,
                "Large": 80.0,
                "Medium": 60.0,
                "Small": 30.0
            }
            return size_map.get(lead.company.size, 50.0)

        return 50.0  # Default if no size data

    async def _score_technology_fit(self, lead: Lead) -> float:
        """Score technology modernization opportunity"""
        score = 50.0  # Base score

        if not lead.company.technology_indicators:
            return score

        tech = lead.company.technology_indicators

        # Legacy systems indicate strong modernization opportunity
        if tech.legacy_systems:
            score += 30.0

        # Cloud migration signals
        if tech.cloud_migration_signals:
            score += 15.0

        # Digital transformation initiatives
        if tech.digital_transformation_initiatives:
            score += 10.0 * min(len(tech.digital_transformation_initiatives), 3)

        return min(score, 100.0)

    async def _score_intent(self, lead: Lead) -> float:
        """Score buying intent based on signals"""
        if not lead.buying_signals:
            return 30.0  # Low intent

        # Weight different signals
        signal_weights = {
            "RFP_PUBLISHED": 30,
            "REGULATORY_DEADLINE": 25,
            "JOB_POSTING": 20,
            "EXECUTIVE_CHANGE": 15,
            "RECENT_FUNDING": 15,
            "TECHNOLOGY_INITIATIVE": 10,
            "PARTNERSHIP_ANNOUNCEMENT": 10
        }

        total_score = 0.0
        for signal in lead.buying_signals:
            weight = signal_weights.get(signal.value.upper(), 5)
            total_score += weight

        # Bonus for multiple signals
        if len(lead.buying_signals) > 2:
            total_score *= 1.2

        return min(total_score, 100.0)
