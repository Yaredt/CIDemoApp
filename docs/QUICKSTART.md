# Quick Start Guide

Get started with the Multi-Agent Lead Generation System in 15 minutes.

## Prerequisites Checklist

- [ ] Python 3.10 or higher installed
- [ ] Azure subscription active
- [ ] Git installed

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/Yaredt/CIDemoApp.git
cd CIDemoApp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Azure Setup (5 minutes)

### Create Azure Resources

```bash
# Login to Azure
az login

# Create resource group
az group create --name leadgen-rg --location eastus

# Deploy infrastructure using Bicep template
az deployment group create \
  --resource-group leadgen-rg \
  --template-file deployment/azure/deploy.bicep \
  --parameters environment=dev
```

This creates:
- Azure OpenAI with GPT-4o deployment
- Cosmos DB (serverless)
- Blob Storage
- Key Vault
- Application Insights

## Step 3: Configure Environment (3 minutes)

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env` with your Azure details (from deployment output):

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://leadgen-openai-xxxxx.openai.azure.com/
AZURE_OPENAI_KEY=your-key-from-deployment
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Azure Cosmos DB
COSMOS_ENDPOINT=https://leadgen-cosmos-xxxxx.documents.azure.com:443/
COSMOS_KEY=your-key-from-deployment
COSMOS_DATABASE=leadgen
COSMOS_CONTAINER=leads

# Azure Blob Storage
STORAGE_CONNECTION_STRING=your-connection-string-from-deployment
```

### Optional: Add Free API Keys (5 minutes)

Sign up for free tiers:

1. **Serper.dev** (https://serper.dev)
   - Free tier: 2,500 searches/month
   - Add to `.env`: `SERPER_API_KEY=your-key`

2. **Hunter.io** (https://hunter.io)
   - Free tier: 25 searches/month
   - Add to `.env`: `HUNTER_API_KEY=your-key`

3. **SAM.gov** (https://sam.gov/content/api)
   - Free with registration
   - Add to `.env`: `SAM_GOV_API_KEY=your-key`

## Step 4: Run Your First Search (2 minutes)

```bash
# Run the lead generation workflow
python -m orchestration.main run --max-results 10

# You should see output like:
# 🚀 Starting Lead Generation System
# Phase 1: Industry-specific lead search
# Found 45 total leads from industry agents
# ...
# ✅ Workflow completed successfully!
```

## Step 5: View Results (1 minute)

```bash
# View top leads
python -m orchestration.main top --limit 10

# View specific lead details
python -m orchestration.main show <lead-id>

# Export to CSV
python -m orchestration.main run --export-format csv --output leads.csv
```

## Common Issues & Solutions

### Issue: "Azure OpenAI quota not available"

**Solution**: Request quota increase in Azure Portal
1. Go to Azure OpenAI resource
2. Navigate to "Quotas"
3. Request increase for GPT-4o

### Issue: "Module not found"

**Solution**: Ensure virtual environment is activated
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Issue: "Cosmos DB connection failed"

**Solution**: Check endpoint and key in `.env`
```bash
# Test connection
python -c "from config.settings import get_settings; print(get_settings().cosmos_endpoint)"
```

## Next Steps

1. **Customize Agents**: Edit agent configurations in `config/settings.py`
2. **Add Data Sources**: Integrate additional APIs in `tools/`
3. **Tune Scoring**: Adjust weights in `agents/coordinator.py`
4. **Set up Monitoring**: Configure Application Insights dashboard
5. **Schedule Runs**: Set up Azure Functions or GitHub Actions

## Cost Optimization Tips

1. **Start with free APIs**: Use FDIC (free) and SAM.gov (free)
2. **Use Cosmos DB serverless**: Only pay for what you use
3. **Limit max results**: Set `--max-results 25` for development
4. **Cache aggressively**: Default 1-hour cache reduces API calls

## Getting Help

- **Issues**: https://github.com/Yaredt/CIDemoApp/issues
- **Documentation**: See `docs/` folder
- **Examples**: Check `examples/` folder (coming soon)

## What's Next?

- [ ] Review [Architecture](ARCHITECTURE.md) to understand the system
- [ ] Read [Implementation Guide](IMPLEMENTATION_GUIDE.md) for deep dive
- [ ] Explore [Contributing](CONTRIBUTING.md) to add features
- [ ] Set up [Deployment](DEPLOYMENT.md) for production

Congratulations! You've successfully set up the Multi-Agent Lead Generation System! 🎉
