// Main Bicep template for Agentic SOC infrastructure
// This template orchestrates the deployment of all Azure resources

// TODO: Implement Bicep infrastructure deployment
// This is a placeholder for Phase 2A infrastructure tasks (T024-T033)

targetScope = 'resourceGroup'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string = 'agentic-soc'

// TODO: Add parameters for:
// - AI Foundry workspace
// - Cosmos DB configuration
// - Event Hubs configuration
// - Container Apps configuration
// - Application Insights configuration
// - Azure AI Search configuration

// TODO: Reference modules:
// - modules/ai-foundry.bicep
// - modules/cosmos.bicep
// - modules/event-hubs.bicep
// - modules/container-apps.bicep
// - modules/monitoring.bicep
// - modules/ai-search.bicep

output resourceGroupName string = resourceGroup().name
output environment string = environment
