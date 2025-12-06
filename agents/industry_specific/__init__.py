"""
Industry-specific search agents
"""

from agents.industry_specific.banking_agent import BankingAgent
from agents.industry_specific.insurance_agent import InsuranceAgent
from agents.industry_specific.energy_agent import EnergyAgent
from agents.industry_specific.government_agent import GovernmentAgent

__all__ = [
    "BankingAgent",
    "InsuranceAgent",
    "EnergyAgent",
    "GovernmentAgent",
]
