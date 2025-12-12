"""
Tests for agent implementations
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from agents.base import AgentConfig
from agents.industry_specific.banking_agent import BankingAgent
from agents.supporting.enrichment_agent import EnrichmentAgent
from agents.coordinator import MasterCoordinator
from agents.models import Lead, Company, Industry, LeadStatus


class TestBankingAgent:
    """Test banking agent"""

    @pytest.fixture
    def agent_config(self):
        return AgentConfig(
            name="test_banking_agent",
            description="Test banking agent",
            custom_config={}
        )

    @pytest.fixture
    def banking_agent(self, agent_config):
        return BankingAgent(agent_config)

    @pytest.mark.asyncio
    async def test_execute(self, banking_agent):
        """Test banking agent execution"""
        with patch.object(banking_agent, '_search_fdic_database', return_value=[]):
            result = await banking_agent.execute()

            assert result is not None
            assert result.agent_name == "test_banking_agent"

    @pytest.mark.asyncio
    async def test_create_lead_from_bank(self, banking_agent):
        """Test lead creation from bank data"""
        bank_data = {
            "name": "Test Bank",
            "cert": "12345",
            "asset": 1000000000,
            "city": "New York",
            "state": "NY",
            "website": "https://testbank.com",
            "employees": 500
        }

        lead = await banking_agent._create_lead_from_bank(bank_data)

        assert lead.company.name == "Test Bank"
        assert lead.company.industry == Industry.BANKING
        assert lead.company.fdic_cert_number == "12345"
        assert lead.status == LeadStatus.NEW


class TestEnrichmentAgent:
    """Test enrichment agent"""

    @pytest.fixture
    def agent_config(self):
        return AgentConfig(
            name="test_enrichment_agent",
            description="Test enrichment agent",
            custom_config={}
        )

    @pytest.fixture
    def enrichment_agent(self, agent_config):
        return EnrichmentAgent(agent_config)

    @pytest.fixture
    def sample_lead(self):
        return Lead(
            id="test_lead_1",
            company=Company(
                name="Test Company",
                industry=Industry.BANKING,
                website="https://testcompany.com"
            ),
            source_agent="test_agent",
            status=LeadStatus.NEW
        )

    @pytest.mark.asyncio
    async def test_enrich_lead(self, enrichment_agent, sample_lead):
        """Test lead enrichment"""
        with patch.object(enrichment_agent, '_enrich_contacts', return_value=None):
            with patch.object(enrichment_agent, '_enrich_company_info', return_value=None):
                with patch.object(enrichment_agent, '_enrich_technology_stack', return_value=None):
                    enriched_lead = await enrichment_agent.enrich(sample_lead)

                    assert enriched_lead.is_enriched is True
                    assert enriched_lead.status == LeadStatus.ENRICHING


class TestMasterCoordinator:
    """Test master coordinator"""

    @pytest.fixture
    def coordinator_config(self):
        return AgentConfig(
            name="test_coordinator",
            description="Test coordinator",
            custom_config={}
        )

    @pytest.fixture
    def coordinator(self, coordinator_config):
        return MasterCoordinator(coordinator_config)

    @pytest.mark.asyncio
    async def test_deduplicate_leads(self, coordinator):
        """Test lead deduplication"""
        leads = [
            Lead(
                id="lead_1",
                company=Company(name="Test Bank", industry=Industry.BANKING),
                source_agent="agent_1"
            ),
            Lead(
                id="lead_2",
                company=Company(name="Test Bank", industry=Industry.BANKING),
                source_agent="agent_2"
            ),
            Lead(
                id="lead_3",
                company=Company(name="Another Bank", industry=Industry.BANKING),
                source_agent="agent_1"
            )
        ]

        unique_leads = await coordinator._deduplicate_leads(leads)

        assert len(unique_leads) == 2  # Deduped "Test Bank"

    @pytest.mark.asyncio
    async def test_score_industry_fit(self, coordinator):
        """Test industry fit scoring"""
        lead = Lead(
            id="test_lead",
            company=Company(name="Test", industry=Industry.BANKING),
            source_agent="test"
        )

        score = await coordinator._score_industry_fit(lead)

        assert score == 100.0  # Banking is in target industries
