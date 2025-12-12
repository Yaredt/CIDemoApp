"""
Data models for the multi-agent lead generation system
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict


class Industry(str, Enum):
    """Target industry categories"""
    BANKING = "banking"
    INSURANCE = "insurance"
    ENERGY = "energy"
    GOVERNMENT = "government"
    UNKNOWN = "unknown"


class LeadStatus(str, Enum):
    """Lead processing status"""
    NEW = "new"
    ENRICHING = "enriching"
    VALIDATING = "validating"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    CONTACTED = "contacted"


class TechnologyStack(str, Enum):
    """Technology indicators"""
    LEGACY_MAINFRAME = "legacy_mainframe"
    LEGACY_COBOL = "legacy_cobol"
    CLOUD_AZURE = "cloud_azure"
    CLOUD_AWS = "cloud_aws"
    CLOUD_GCP = "cloud_gcp"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"


class BuyingSignal(str, Enum):
    """Buying cycle signals"""
    JOB_POSTING = "job_posting"
    RECENT_FUNDING = "recent_funding"
    EXECUTIVE_CHANGE = "executive_change"
    REGULATORY_DEADLINE = "regulatory_deadline"
    PARTNERSHIP_ANNOUNCEMENT = "partnership_announcement"
    TECHNOLOGY_INITIATIVE = "technology_initiative"
    RFP_PUBLISHED = "rfp_published"


class Contact(BaseModel):
    """Contact information for a lead"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Smith",
                "title": "CTO",
                "email": "john.smith@company.com",
                "department": "Technology",
                "seniority_level": "C-Level"
            }
        }
    )

    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    department: Optional[str] = None
    seniority_level: Optional[str] = None  # C-Level, VP, Director, Manager


class TechnologyIndicator(BaseModel):
    """Technology modernization indicators"""
    stack: List[TechnologyStack] = Field(default_factory=list)
    legacy_systems: bool = False
    cloud_migration_signals: bool = False
    digital_transformation_initiatives: List[str] = Field(default_factory=list)
    partnerships: List[str] = Field(default_factory=list)
    recent_it_investments: Optional[str] = None
    technology_debt_score: Optional[float] = Field(None, ge=0, le=100)


class Company(BaseModel):
    """Company information"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "ABC Bank",
                "industry": "banking",
                "website": "https://abcbank.com",
                "size": "Enterprise",
                "revenue": "$1B+",
                "employee_count": 5000,
                "fdic_cert_number": "12345"
            }
        }
    )

    name: str
    industry: Industry
    website: Optional[HttpUrl] = None
    size: Optional[str] = None  # Small, Medium, Large, Enterprise
    revenue: Optional[str] = None
    location: Optional[str] = None
    headquarters: Optional[str] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None

    # Industry-specific identifiers
    fdic_cert_number: Optional[str] = None  # Banking
    naic_code: Optional[str] = None  # Insurance
    duns_number: Optional[str] = None  # Government
    sam_uei: Optional[str] = None  # Government (SAM.gov)

    # Technology indicators
    technology_indicators: Optional[TechnologyIndicator] = None

    # Social/Web presence
    linkedin_url: Optional[HttpUrl] = None
    twitter_handle: Optional[str] = None


class LeadScore(BaseModel):
    """Lead scoring information"""
    overall_score: float = Field(..., ge=0, le=100)
    fit_score: float = Field(..., ge=0, le=100)  # How well they match ICP
    intent_score: float = Field(..., ge=0, le=100)  # Buying signals
    timing_score: float = Field(..., ge=0, le=100)  # Urgency/timing

    # Score breakdown
    industry_fit: float = Field(default=0, ge=0, le=100)
    size_fit: float = Field(default=0, ge=0, le=100)
    technology_fit: float = Field(default=0, ge=0, le=100)
    budget_likelihood: float = Field(default=0, ge=0, le=100)

    # Reasoning
    scoring_factors: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('overall_score', mode='before')
    @classmethod
    def calculate_overall_score(cls, v, info):
        """Calculate overall score from components"""
        if v is not None:
            return v
        # Weighted average: 40% fit, 35% intent, 25% timing
        values = info.data
        fit = values.get('fit_score', 0)
        intent = values.get('intent_score', 0)
        timing = values.get('timing_score', 0)
        return round(0.4 * fit + 0.35 * intent + 0.25 * timing, 2)


class Lead(BaseModel):
    """Complete lead information"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "lead_abc123",
                "company": {
                    "name": "ABC Bank",
                    "industry": "banking",
                    "website": "https://abcbank.com"
                },
                "source_agent": "banking_agent",
                "status": "new",
                "buying_signals": ["job_posting", "technology_initiative"]
            }
        }
    )

    id: str
    company: Company
    contacts: List[Contact] = Field(default_factory=list)

    # Status and processing
    status: LeadStatus = LeadStatus.NEW
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Source information
    source_agent: str  # Which agent discovered this lead
    source_data: Dict[str, Any] = Field(default_factory=dict)
    data_sources: List[str] = Field(default_factory=list)

    # Buying signals
    buying_signals: List[BuyingSignal] = Field(default_factory=list)
    signal_details: Dict[str, Any] = Field(default_factory=dict)

    # Scoring
    score: Optional[LeadScore] = None

    # Validation
    is_validated: bool = False
    validation_notes: List[str] = Field(default_factory=list)

    # Enrichment
    is_enriched: bool = False
    enrichment_timestamp: Optional[datetime] = None

    # Notes and metadata
    notes: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionResult(BaseModel):
    """Result from an agent execution"""
    agent_name: str
    success: bool
    leads_found: List[Lead] = Field(default_factory=list)
    leads_processed: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
