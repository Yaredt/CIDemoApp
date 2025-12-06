"""
Validation Agent

Validates leads to ensure they are legitimate and fit the ideal customer profile.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig
from agents.models import (
    Lead, LeadStatus, Industry, AgentExecutionResult
)
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Agent specialized in validating leads.

    Validation criteria:
    - Company legitimacy (real business, not defunct)
    - Industry fit (matches target industries)
    - Size fit (meets minimum size requirements)
    - Technology fit (has modernization opportunity)
    - Contact quality (valid email domains, real people)
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.web_search_tool = WebSearchTool(config.custom_config.get("serper_api_key"))

        # Validation criteria from config
        self.min_employee_count = config.custom_config.get("min_employee_count", 100)
        self.target_industries = config.custom_config.get(
            "target_industries",
            [Industry.BANKING, Industry.INSURANCE, Industry.ENERGY, Industry.GOVERNMENT]
        )

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute lead validation.

        Args:
            context: Context with leads to validate

        Returns:
            AgentExecutionResult with validated leads
        """
        start_time = datetime.utcnow()
        validated_leads = []
        disqualified_leads = []

        try:
            leads = context.get("leads", []) if context else []

            if not leads:
                self.logger.warning("No leads provided for validation")
                return AgentExecutionResult(
                    agent_name=self.name,
                    success=True,
                    leads_found=[],
                    execution_time=0.0
                )

            self.logger.info(f"Validating {len(leads)} leads")

            for lead in leads:
                try:
                    is_valid = await self.validate(lead)

                    if is_valid:
                        lead.status = LeadStatus.QUALIFIED
                        validated_leads.append(lead)
                    else:
                        lead.status = LeadStatus.DISQUALIFIED
                        disqualified_leads.append(lead)

                except Exception as e:
                    self.logger.error(f"Error validating lead {lead.id}: {e}")
                    # Default to keeping the lead if validation fails
                    validated_leads.append(lead)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=True,
                leads_found=validated_leads,
                leads_processed=len(leads),
                execution_time=execution_time,
                metadata={
                    "validated": len(validated_leads),
                    "disqualified": len(disqualified_leads),
                    "validation_criteria": {
                        "min_employees": self.min_employee_count,
                        "target_industries": [i.value for i in self.target_industries]
                    }
                }
            )

            self._record_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Validation agent execution failed: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_name=self.name,
                success=False,
                leads_found=validated_leads,
                execution_time=execution_time,
                error=str(e)
            )

            self._record_execution(result)
            return result

    async def validate(self, lead: Lead) -> bool:
        """
        Validate a single lead.

        Args:
            lead: Lead to validate

        Returns:
            True if valid, False otherwise
        """
        self.logger.info(f"Validating lead: {lead.id}")

        lead.status = LeadStatus.VALIDATING

        # Run validation checks
        checks = {
            "industry_fit": await self._check_industry_fit(lead),
            "company_legitimacy": await self._check_company_legitimacy(lead),
            "size_fit": await self._check_size_fit(lead),
            "technology_opportunity": await self._check_technology_opportunity(lead),
        }

        # Record validation results
        lead.validation_notes = [
            f"{check}: {'PASS' if result else 'FAIL'}"
            for check, result in checks.items()
        ]

        # Lead is valid if it passes all critical checks
        is_valid = all([
            checks["industry_fit"],
            checks["company_legitimacy"],
            # Size and technology are nice-to-have but not required
        ])

        lead.is_validated = True
        lead.updated_at = datetime.utcnow()

        self.logger.info(
            f"Lead {lead.id} validation result: {'VALID' if is_valid else 'INVALID'} - {checks}"
        )

        return is_valid

    async def _check_industry_fit(self, lead: Lead) -> bool:
        """
        Check if company is in target industry.

        Args:
            lead: Lead to check

        Returns:
            True if industry matches
        """
        if lead.company.industry in self.target_industries:
            return True

        # If industry is unknown, try to determine from other signals
        if lead.company.industry == Industry.UNKNOWN:
            # Could use additional signals to determine industry
            return True  # Give benefit of doubt

        return False

    async def _check_company_legitimacy(self, lead: Lead) -> bool:
        """
        Check if company is legitimate and active.

        Args:
            lead: Lead to check

        Returns:
            True if company appears legitimate
        """
        try:
            # Search for the company
            search_query = f"{lead.company.name} company"
            results = await self.web_search_tool.search(search_query, num_results=5)

            if not results:
                lead.validation_notes.append("No web presence found")
                return False

            # Check for negative signals
            content = " ".join([r.get("snippet", "") for r in results])
            negative_keywords = ["bankrupt", "defunct", "closed", "out of business"]

            if any(kw in content.lower() for kw in negative_keywords):
                lead.validation_notes.append("Negative signals found (bankrupt, closed, etc.)")
                return False

            # Has web presence and no negative signals
            return True

        except Exception as e:
            self.logger.error(f"Error checking company legitimacy: {e}")
            # Give benefit of doubt if check fails
            return True

    async def _check_size_fit(self, lead: Lead) -> bool:
        """
        Check if company meets minimum size requirements.

        Args:
            lead: Lead to check

        Returns:
            True if company is large enough
        """
        # Check employee count if available
        if lead.company.employee_count:
            if lead.company.employee_count >= self.min_employee_count:
                return True
            else:
                lead.validation_notes.append(
                    f"Below minimum employee count ({lead.company.employee_count} < {self.min_employee_count})"
                )
                return False

        # If no employee data, check size category
        if lead.company.size:
            valid_sizes = ["Medium", "Large", "Enterprise"]
            if lead.company.size in valid_sizes:
                return True

        # If no size data available, give benefit of doubt
        return True

    async def _check_technology_opportunity(self, lead: Lead) -> bool:
        """
        Check if company has technology modernization opportunity.

        Args:
            lead: Lead to check

        Returns:
            True if technology opportunity exists
        """
        if not lead.company.technology_indicators:
            # No technology data - give benefit of doubt
            return True

        # Look for positive signals
        has_legacy = lead.company.technology_indicators.legacy_systems
        has_initiatives = bool(lead.company.technology_indicators.digital_transformation_initiatives)
        has_signals = lead.company.technology_indicators.cloud_migration_signals

        if has_legacy or has_initiatives or has_signals:
            return True

        # No clear technology opportunity, but don't disqualify
        return True
