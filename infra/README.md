# Infrastructure Deployment

This directory contains Azure infrastructure as code (Bicep templates) for the Agentic SOC platform.

## Status

✅ **Phase 2A Infrastructure (Tasks T024-T033) - COMPLETE**

Full Bicep implementation with production-ready configurations for all Azure resources.

## Architecture

The infrastructure deploys the following Azure resources:

1. **Azure AI Foundry Workspace** - AI agent runtime with GPT-4.1-mini model deployment
2. **Cosmos DB** - NoSQL database with 6 containers for alerts, incidents, triage results, response actions, agent state, and audit logs
3. **Event Hubs** - Event-driven architecture with alert-ingestion hub
4. **Container Apps** - Microservices hosting for alert triage agent, orchestrator, and API
5. **Application Insights** - Monitoring and observability with Log Analytics workspace
6. **Azure AI Search** - Threat intelligence knowledge base with 3 indexes

## Directory Structure

```
infra/
├── main.bicep                      # Main orchestration template
├── modules/                        # Resource-specific modules
│   ├── ai-foundry.bicep           # AI Foundry workspace + GPT-4.1-mini
│   ├── cosmos.bicep               # Cosmos DB with 6 containers
│   ├── event-hubs.bicep           # Event Hubs namespace
│   ├── container-apps.bicep       # Container Apps environment + 3 apps
│   ├── monitoring.bicep           # Application Insights + Log Analytics
│   └── ai-search.bicep            # Azure AI Search with indexes
├── parameters/                     # Environment-specific parameters
│   ├── dev.parameters.json        # Development environment
│   └── prod.parameters.json       # Production environment
└── outputs/                        # Deployment outputs (generated)
```

## Quick Start

### Prerequisites

- Azure CLI installed (`az --version`)
- Logged in to Azure (`az login`)
- Subscription with sufficient permissions to create resources

### Deploy to Azure

**Development Environment:**
```bash
./utils/deploy_infrastructure.sh dev
```

**Production Environment:**
```bash
./utils/deploy_infrastructure.sh prod
```

The script will:
1. Validate your Azure login
2. Create resource group if it doesn't exist
3. Validate the Bicep template
4. Deploy all infrastructure resources
5. Save outputs to `infra/outputs/<env>-outputs.json`

Deployment takes approximately 10-15 minutes.

## Resource Configuration

### Development Environment
- AI Foundry: GPT-4.1-mini with 100 TPM capacity
- Cosmos DB: Serverless with 6 containers (30-365 day TTL)
- Event Hubs: Basic tier, 2 partitions
- Container Apps: 1-3 replicas per service
- AI Search: Basic tier, 1 replica
- Monitoring: 30-day retention

### Production Environment
- AI Foundry: GPT-4.1-mini with 100 TPM capacity
- Cosmos DB: Provisioned throughput (6K RU/s total) with zone redundancy
- Event Hubs: Standard tier with auto-inflate, 4 partitions
- Container Apps: 2-10 replicas with autoscaling
- AI Search: Standard tier, 2 replicas, 2 partitions
- Monitoring: 90-day retention

## Security Features

- **Managed Identities**: All services use system-assigned managed identities
- **Network Security**: Optional private endpoints (configured in production)
- **Secrets Management**: Key Vault references for sensitive configuration
- **RBAC**: Role-based access control for service-to-service communication
- **TLS 1.2+**: All communications encrypted in transit

## Cost Estimates

**Development Environment**: ~$350/month
- AI Foundry: $190/month (estimated 10M tokens)
- Cosmos DB (Serverless): $25/month  
- Event Hubs (Basic): $25/month
- Container Apps: $20/month
- AI Search (Basic): $75/month
- Monitoring: $15/month

**Production Environment**: ~$800/month
- AI Foundry: $190/month (estimated 10M tokens)
- Cosmos DB (Provisioned): $150/month (6K RU/s)
- Event Hubs (Standard): $100/month
- Container Apps: $80/month (with scaling)
- AI Search (Standard): $250/month
- Monitoring: $30/month

## Post-Deployment Setup

After infrastructure deployment, complete these setup steps:

1. **Configure Environment Variables**
   ```bash
   # From infra/outputs/<env>-outputs.json
   export AZURE_AI_PROJECT_ENDPOINT=$(jq -r '.aiFoundryEndpoint.value' infra/outputs/dev-outputs.json)
   export AZURE_AI_MODEL_DEPLOYMENT_NAME=$(jq -r '.aiFoundryModelDeploymentName.value' infra/outputs/dev-outputs.json)
   export COSMOS_ENDPOINT=$(jq -r '.cosmosEndpoint.value' infra/outputs/dev-outputs.json)
   export EVENTHUB_NAMESPACE=$(jq -r '.eventHubsNamespace.value' infra/outputs/dev-outputs.json)
   export AI_SEARCH_ENDPOINT=$(jq -r '.aiSearchEndpoint.value' infra/outputs/dev-outputs.json)
   ```

2. **Create AI Search Indexes**
   ```bash
   python utils/setup_ai_search.py
   ```

3. **Verify Cosmos DB Collections**
   ```bash
   python utils/setup_cosmos_db.py
   ```

4. **Build and Deploy Container Images**
   ```bash
   # Build images
   docker build -t agentic-soc-alert-triage:latest -f Dockerfile.alert-triage .
   docker build -t agentic-soc-orchestrator:latest -f Dockerfile.orchestrator .
   docker build -t agentic-soc-api:latest -f Dockerfile.api .
   
   # Push to Azure Container Registry
   az acr login --name <your-acr-name>
   docker tag agentic-soc-alert-triage:latest <your-acr-name>.azurecr.io/alert-triage:latest
   docker push <your-acr-name>.azurecr.io/alert-triage:latest
   # ... repeat for other images
   ```

## Troubleshooting

### Deployment Failures

**Resource name conflicts:**
```bash
# Change baseName parameter to make resource names unique
# Edit infra/parameters/<env>.parameters.json
```

**Quota limitations:**
```bash
# Check quota usage
az vm list-usage --location eastus --output table

# Request quota increase if needed
```

**Permission errors:**
```bash
# Verify you have Owner or Contributor role
az role assignment list --assignee $(az account show --query user.name -o tsv)
```

### Validation Issues

```bash
# Validate template manually
az deployment group validate \
  --resource-group agentic-soc-rg-dev \
  --template-file infra/main.bicep \
  --parameters @infra/parameters/dev.parameters.json
```

## Maintenance

### Updating Resources

Modify parameters or templates and redeploy:
```bash
./utils/deploy_infrastructure.sh <env>
```

Bicep uses incremental deployment mode by default, only updating changed resources.

### Monitoring

View deployment status in Azure Portal:
```bash
# Get resource group URL
echo "https://portal.azure.com/#@/resource$(az group show --name agentic-soc-rg-dev --query id -o tsv)"
```

### Cleanup

Delete all resources:
```bash
# CAUTION: This deletes ALL resources in the resource group
az group delete --name agentic-soc-rg-dev --yes --no-wait
```

## Additional Resources

- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Cosmos DB Documentation](https://learn.microsoft.com/azure/cosmos-db/)

