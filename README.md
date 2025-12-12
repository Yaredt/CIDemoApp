# Multi-Agent Lead Generation System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Azure](https://img.shields.io/badge/Azure-Powered-0078D4.svg)](https://azure.microsoft.com/)

An enterprise-grade multi-agent system for automated lead generation and qualification in regulated industries (Banking, Insurance, Energy, Government).

## 🎯 Overview

This system leverages Microsoft Agent Framework SDK and Azure AI to automatically:

- **Search** multiple data sources for prospects in target industries
- **Enrich** leads with company information, contacts, and technology stack data
- **Validate** lead quality against ideal customer profile criteria
- **Analyze** buying signals and timing indicators
- **Score & Rank** leads using a sophisticated multi-factor algorithm

### Key Features

✨ **Multi-Agent Architecture** - Specialized agents for different industries and tasks
🔍 **Intelligent Search** - Integrates with FDIC, SAM.gov, Hunter.io, Clearbit, and more
🤖 **AI-Powered** - Uses Azure OpenAI GPT-4o for analysis and enrichment
📊 **Smart Scoring** - Ranks leads by fit, intent, and timing signals
☁️ **Cloud-Native** - Built for Azure with Cosmos DB and Blob Storage
🔐 **Enterprise-Ready** - Secure, scalable, and production-tested

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Master Coordinator Agent                    │
│           Orchestrates workflow & ranks leads                │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴──────────────┬─────────────────┐
         │                            │                 │
┌────────▼────────┐         ┌─────────▼────────┐       │
│ Industry Agents │         │Supporting Agents │       │
├─────────────────┤         ├──────────────────┤       │
│ • Banking       │         │ • Enrichment     │       │
│ • Insurance     │         │ • Validation     │       │
│ • Energy        │         │ • Timing         │       │
│ • Government    │         └──────────────────┘       │
└─────────────────┘                                     │
         │                                              │
         └──────────────────┬───────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │   Tool Layer    │
                   ├─────────────────┤
                   │ • FDIC API      │
                   │ • SAM.gov API   │
                   │ • Hunter.io     │
                   │ • Clearbit      │
                   │ • Web Search    │
                   └─────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Yaredt/CIDemoApp.git
cd CIDemoApp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Run the system
python -m orchestration.main run
```

## 📦 Prerequisites

- Python 3.10+
- Azure OpenAI Service (GPT-4o)
- Azure Cosmos DB
- Azure Blob Storage

### Optional API Keys
- Serper.dev (Web search)
- Hunter.io (Email finding)
- Clearbit (Company enrichment)
- SAM.gov (Government contracts)

## 💻 Usage

### Run Complete Workflow
```bash
python -m orchestration.main run --max-results 100
```

### View Top Leads
```bash
python -m orchestration.main top --limit 20
```

### Export Leads
```bash
python -m orchestration.main run --export-format csv --output leads.csv
```

## 🐳 Docker Deployment

```bash
cd deployment/docker
docker-compose up -d
```

## 📊 Output Example

```json
{
  "company": "ABC Bank",
  "industry": "banking",
  "score": 85.5,
  "buying_signals": ["job_posting", "technology_initiative"],
  "contacts": [{"name": "John Smith", "title": "CTO"}]
}
```

## 🧪 Testing

```bash
pytest --cov=agents --cov=tools --cov=orchestration
```

## 📚 Documentation

- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## 📝 License

MIT License - see [LICENSE](LICENSE)

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Built with Microsoft Agent Framework SDK and Azure AI**