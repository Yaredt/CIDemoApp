"""
Base agent class and configuration for the multi-agent system
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from agents.models import Lead, AgentExecutionResult

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    model_config = ConfigDict(extra="allow")

    name: str
    description: str
    enabled: bool = True
    max_results: int = 50
    timeout_seconds: int = 300
    retry_attempts: int = 3
    rate_limit_per_minute: int = 60
    cache_ttl_seconds: int = 3600

    # Azure OpenAI configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"

    # Additional agent-specific config
    custom_config: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent lead generation system.

    All agents should inherit from this class and implement the execute() method.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the agent with configuration.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self._execution_count = 0
        self._last_execution: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Agent name"""
        return self.config.name

    @property
    def is_enabled(self) -> bool:
        """Check if agent is enabled"""
        return self.config.enabled

    @abstractmethod
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """
        Execute the agent's primary function.

        Args:
            context: Optional execution context with parameters

        Returns:
            AgentExecutionResult with leads found and execution metadata
        """
        pass

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Lead]:
        """
        Search for leads based on query and filters.

        Args:
            query: Search query
            filters: Optional filters to apply

        Returns:
            List of leads found
        """
        self.logger.info(f"Searching with query: {query}, filters: {filters}")
        # Default implementation - override in subclasses
        return []

    async def enrich(self, lead: Lead) -> Lead:
        """
        Enrich a lead with additional information.

        Args:
            lead: Lead to enrich

        Returns:
            Enriched lead
        """
        self.logger.info(f"Enriching lead: {lead.id}")
        # Default implementation - override in subclasses
        return lead

    async def validate(self, lead: Lead) -> bool:
        """
        Validate a lead.

        Args:
            lead: Lead to validate

        Returns:
            True if lead is valid, False otherwise
        """
        self.logger.info(f"Validating lead: {lead.id}")
        # Default implementation - override in subclasses
        return True

    async def score(self, lead: Lead) -> Lead:
        """
        Score a lead.

        Args:
            lead: Lead to score

        Returns:
            Lead with updated score
        """
        self.logger.info(f"Scoring lead: {lead.id}")
        # Default implementation - override in subclasses
        return lead

    def _record_execution(self, result: AgentExecutionResult) -> None:
        """
        Record execution metrics.

        Args:
            result: Execution result to record
        """
        self._execution_count += 1
        self._last_execution = datetime.utcnow()

        self.logger.info(
            f"Agent {self.name} execution #{self._execution_count}: "
            f"success={result.success}, leads_found={len(result.leads_found)}, "
            f"time={result.execution_time:.2f}s"
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the agent.

        Returns:
            Health status information
        """
        return {
            "agent_name": self.name,
            "enabled": self.is_enabled,
            "execution_count": self._execution_count,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None,
            "status": "healthy" if self.is_enabled else "disabled"
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, enabled={self.is_enabled})>"
