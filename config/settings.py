"""
Application settings and configuration management
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All sensitive data (API keys, connection strings) should be stored
    in Azure Key Vault and loaded via environment variables.
    """

    # Application
    app_name: str = "Lead Generation Agents"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Azure OpenAI
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(..., env="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field(default="gpt-4o", env="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-02-01", env="AZURE_OPENAI_API_VERSION")

    # Azure Cosmos DB
    cosmos_endpoint: str = Field(..., env="COSMOS_ENDPOINT")
    cosmos_key: str = Field(..., env="COSMOS_KEY")
    cosmos_database: str = Field(default="leadgen", env="COSMOS_DATABASE")
    cosmos_container: str = Field(default="leads", env="COSMOS_CONTAINER")

    # Azure Blob Storage
    storage_connection_string: str = Field(..., env="STORAGE_CONNECTION_STRING")
    storage_container: str = Field(default="lead-data", env="STORAGE_CONTAINER")

    # Azure Key Vault (optional - for advanced secret management)
    key_vault_url: Optional[str] = Field(default=None, env="KEY_VAULT_URL")

    # Data Source API Keys
    serper_api_key: Optional[str] = Field(default=None, env="SERPER_API_KEY")
    hunter_api_key: Optional[str] = Field(default=None, env="HUNTER_API_KEY")
    clearbit_api_key: Optional[str] = Field(default=None, env="CLEARBIT_API_KEY")
    sam_gov_api_key: Optional[str] = Field(default=None, env="SAM_GOV_API_KEY")

    # Agent Configuration
    max_results_per_agent: int = Field(default=50, env="MAX_RESULTS_PER_AGENT")
    enable_banking_agent: bool = Field(default=True, env="ENABLE_BANKING_AGENT")
    enable_insurance_agent: bool = Field(default=True, env="ENABLE_INSURANCE_AGENT")
    enable_energy_agent: bool = Field(default=True, env="ENABLE_ENERGY_AGENT")
    enable_government_agent: bool = Field(default=True, env="ENABLE_GOVERNMENT_AGENT")

    # Validation Criteria
    min_employee_count: int = Field(default=100, env="MIN_EMPLOYEE_COUNT")
    target_industries: List[str] = Field(
        default=["banking", "insurance", "energy", "government"],
        env="TARGET_INDUSTRIES"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # Caching
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()
