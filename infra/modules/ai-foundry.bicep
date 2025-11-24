// Azure AI Foundry workspace module
// Deploys AI Foundry workspace with GPT-4.1-mini model deployment

@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for resources')
param location string

@description('Base name for resources')
param baseName string

@description('Tags to apply to resources')
param tags object = {}

var workspaceName = '${baseName}-ai-foundry-${environment}'
var modelDeploymentName = 'gpt-4.1-mini'

// AI Foundry workspace (Hub)
resource aiFoundryWorkspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: workspaceName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Agentic SOC AI Foundry Workspace'
    description: 'AI Foundry workspace for Agentic SOC agents'
    publicNetworkAccess: 'Enabled' // Change to 'Disabled' for private endpoints in production
  }
  kind: 'Hub' // AI Foundry uses Hub kind
}

// Model deployment: GPT-4.1-mini
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  name: '${workspaceName}/${modelDeploymentName}'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2024-07-18' // Latest version as of plan creation
    }
    raiPolicyName: 'Microsoft.Default'
  }
  sku: {
    name: 'Standard'
    capacity: 100 // TPM (Tokens Per Minute)
  }
  dependsOn: [
    aiFoundryWorkspace
  ]
}

// Output values for other modules
output workspaceId string = aiFoundryWorkspace.id
output workspaceName string = aiFoundryWorkspace.name
output endpoint string = aiFoundryWorkspace.properties.discoveryUrl
output principalId string = aiFoundryWorkspace.identity.principalId
output modelDeploymentName string = modelDeploymentName
