// ============================================================================
// Agentic SOC - Main Infrastructure Template
// ============================================================================
// Orchestrates deployment of all infrastructure components

targetScope = 'resourceGroup'

// ============================================================================
// Parameters
// ============================================================================

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Project name prefix for resource naming')
param projectName string = 'asoc'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'Agentic-SOC'
  ManagedBy: 'Bicep'
}

@description('Enable monitoring resources (Application Insights, Log Analytics)')
param enableMonitoring bool = true

@description('Enable Cosmos DB for agent state storage')
param enableCosmosDb bool = true

@description('Azure OpenAI deployment name')
param openAiDeploymentName string = 'gpt-4.1-mini'

// ============================================================================
// Variables
// ============================================================================

var resourcePrefix = '${projectName}-${environment}'
var commonTags = union(tags, {
  DeploymentTimestamp: utcNow()
})

// ============================================================================
// Module: Microsoft Foundry (AI Foundry)
// ============================================================================

module foundry 'modules/microsoft-foundry.bicep' = {
  name: '${deployment().name}-foundry'
  params: {
    location: location
    projectName: resourcePrefix
    openAiDeploymentName: openAiDeploymentName
    tags: commonTags
  }
}

// ============================================================================
// Module: Cosmos DB (Agent State Storage)
// ============================================================================

module cosmosDb 'modules/cosmos.bicep' = if (enableCosmosDb) {
  name: '${deployment().name}-cosmos'
  params: {
    location: location
    accountName: '${resourcePrefix}-cosmos'
    databaseName: 'agentic-soc'
    tags: commonTags
  }
}

// ============================================================================
// Module: Monitoring (Application Insights, Log Analytics)
// ============================================================================

module monitoring 'modules/monitoring.bicep' = if (enableMonitoring) {
  name: '${deployment().name}-monitoring'
  params: {
    location: location
    projectName: resourcePrefix
    tags: commonTags
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Microsoft Foundry project endpoint')
output foundryProjectEndpoint string = foundry.outputs.projectEndpoint

@description('Microsoft Foundry project name')
output foundryProjectName string = foundry.outputs.projectName

@description('Azure OpenAI endpoint')
output openAiEndpoint string = foundry.outputs.openAiEndpoint

@description('Cosmos DB endpoint')
output cosmosDbEndpoint string = enableCosmosDb ? cosmosDb.outputs.endpoint : ''

@description('Cosmos DB database name')
output cosmosDbDatabaseName string = enableCosmosDb ? cosmosDb.outputs.databaseName : ''

@description('Application Insights connection string')
output appInsightsConnectionString string = enableMonitoring ? monitoring.outputs.appInsightsConnectionString : ''

@description('Log Analytics workspace ID')
output logAnalyticsWorkspaceId string = enableMonitoring ? monitoring.outputs.workspaceId : ''
