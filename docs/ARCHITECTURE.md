# System Architecture

## Overview

The Multi-Agent Lead Generation System is built using a distributed multi-agent architecture where specialized agents collaborate to discover, enrich, validate, and rank leads.

## Core Components

### 1. Master Coordinator Agent

The central orchestrator that:
- Manages workflow execution
- Coordinates all sub-agents
- Implements the ranking algorithm
- Produces final prioritized lead list

**Key Responsibilities:**
- Parallel execution of industry agents
- Lead deduplication
- Final scoring and ranking
- Workflow state management

### 2. Industry-Specific Search Agents

Specialized agents for each target industry:

#### Banking Agent
- **Data Sources**: FDIC Institution Database, financial news
- **Signals**: Core banking system upgrades, digital transformation initiatives
- **Output**: Banking institutions meeting size/asset criteria

#### Insurance Agent
- **Data Sources**: Insurance publications, carrier databases
- **Signals**: Legacy system replacement, modernization projects
- **Output**: Insurance carriers with technology opportunities

#### Energy Agent
- **Data Sources**: Utility databases, smart grid initiatives
- **Signals**: Grid modernization, AMI deployments
- **Output**: Energy companies pursuing infrastructure upgrades

#### Government Agent
- **Data Sources**: SAM.gov, procurement portals, RFPs
- **Signals**: Technology modernization fund applications, RFPs
- **Output**: Government agencies with active IT initiatives

### 3. Supporting Agents

#### Enrichment Agent
- **Purpose**: Enhance lead data quality
- **Actions**:
  - Find decision-maker contacts
  - Enrich company information
  - Identify technology stack
- **Tools**: Hunter.io, Clearbit, web search

#### Validation Agent
- **Purpose**: Filter unqualified leads
- **Criteria**:
  - Industry fit
  - Company size fit
  - Technology opportunity presence
  - Legitimacy verification
- **Output**: Qualified/disqualified status

#### Timing Agent
- **Purpose**: Detect urgency signals
- **Signals Tracked**:
  - Job postings (hiring = active projects)
  - Executive changes
  - Regulatory deadlines
  - Recent announcements
- **Output**: Timing score (0-100)

## Data Flow

```
[Data Sources] → [Industry Agents] → [Deduplication] →
[Enrichment] → [Validation] → [Timing Analysis] →
[Scoring] → [Ranked Leads] → [Storage]
```

## Scoring Algorithm

### Multi-Factor Score Calculation

**Overall Score = (0.40 × Fit) + (0.35 × Intent) + (0.25 × Timing)**

#### Fit Score (40% weight)
- Industry fit: Target industry match
- Size fit: Employee count/revenue
- Technology fit: Modernization opportunity indicators

#### Intent Score (35% weight)
- Buying signal strength
- Number of signals detected
- Signal recency

#### Timing Score (25% weight)
- Urgency indicators
- Budget cycle alignment
- Project timeline signals

## Technology Stack

### Runtime
- **Language**: Python 3.10+
- **Framework**: Microsoft Agent Framework SDK
- **AI/ML**: Azure OpenAI (GPT-4o)

### Data Storage
- **Primary DB**: Azure Cosmos DB (lead storage)
- **Blob Storage**: Azure Blob Storage (file exports)
- **Cache**: In-memory TTL cache

### External APIs
- **FDIC API**: Free, no key required
- **SAM.gov API**: Free with registration
- **Serper.dev**: Web search (paid)
- **Hunter.io**: Email finding (freemium)
- **Clearbit**: Company enrichment (paid)

## Scalability Considerations

### Horizontal Scaling
- Agents execute independently
- Parallel execution of industry agents
- Async I/O throughout

### Performance Optimizations
- Response caching (1-hour TTL)
- Rate limiting per API
- Batch operations for storage
- Connection pooling

### Cost Management
- Cosmos DB serverless (pay-per-use)
- Azure OpenAI rate limiting
- Cached API responses
- Free tier API usage where possible

## Security

### Data Protection
- Secrets in Azure Key Vault
- Environment variable configuration
- No hardcoded credentials
- Encrypted at rest (Cosmos DB)
- TLS for all communications

### Access Control
- Azure RBAC for resources
- API key rotation
- Least privilege principle

## Monitoring & Observability

### Logging
- Structured logging (JSON)
- Azure Application Insights integration
- Agent execution metrics
- Error tracking

### Metrics
- Leads per execution
- Agent success rates
- API call latency
- Scoring distribution

## Future Enhancements

1. **Real-time Processing**: Stream processing for live signals
2. **ML-Enhanced Scoring**: Train custom models on historical conversions
3. **Multi-Region**: Deploy across regions for global coverage
4. **Auto-Scaling**: Azure Container Apps for elastic scaling
5. **Advanced Workflows**: Conditional branching based on lead attributes
