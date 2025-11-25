// Main Bicep template for Agentic SOC infrastructure
// This template orchestrates the deployment of all Azure resources

targetScope = 'resourceGroup'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string = 'agentic-soc'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'Agentic SOC'
  ManagedBy: 'Bicep'
}

// Deploy monitoring first (needed by Container Apps)
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: tags
  }
}

// Deploy AI Foundry workspace
module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'ai-foundry-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: tags
  }
}

// Deploy Cosmos DB
module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: tags
  }
}

// Deploy Event Hubs
module eventHubs 'modules/event-hubs.bicep' = {
  name: 'event-hubs-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: tags
  }
}

// Deploy Azure AI Search
module aiSearch 'modules/ai-search.bicep' = {
  name: 'ai-search-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: tags
  }
}

// Deploy Container Apps (depends on monitoring)
module containerApps 'modules/container-apps.bicep' = {
  name: 'container-apps-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    tags: tags
  }
  dependsOn: [
    monitoring
  ]
}

// Outputs
output resourceGroupName string = resourceGroup().name
output environment string = environment
output location string = location

// AI Foundry outputs
output aiFoundryWorkspaceId string = aiFoundry.outputs.workspaceId
output aiFoundryEndpoint string = aiFoundry.outputs.endpoint
output aiFoundryModelDeploymentName string = aiFoundry.outputs.modelDeploymentName

// Cosmos DB outputs
output cosmosAccountName string = cosmos.outputs.accountName
output cosmosEndpoint string = cosmos.outputs.endpoint
output cosmosDatabaseName string = cosmos.outputs.databaseName

// Event Hubs outputs
output eventHubsNamespace string = eventHubs.outputs.namespaceName
output alertIngestionHubName string = eventHubs.outputs.hubName

// Azure AI Search outputs
output aiSearchServiceName string = aiSearch.outputs.searchServiceName
output aiSearchEndpoint string = aiSearch.outputs.endpoint

// Container Apps outputs
output containerAppEnvironmentName string = containerApps.outputs.environmentName
output apiServiceUrl string = containerApps.outputs.apiServiceUrl

// Monitoring outputs
output appInsightsName string = monitoring.outputs.appInsightsName
output appInsightsConnectionString string = monitoring.outputs.connectionString
output logAnalyticsWorkspaceName string = monitoring.outputs.workspaceName
