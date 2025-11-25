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
var modelDeploymentResourceName = '${workspaceName}/deployment-${modelDeploymentName}'

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
// Note: Model deployments for AI Foundry workspaces are created via the AI Projects SDK
// or Azure Portal after workspace provisioning. This is a reference placeholder.
// Use Azure AI Projects SDK to create model deployments programmatically:
// https://learn.microsoft.com/azure/ai-studio/how-to/deploy-models-openai

// Output values for other modules
output workspaceId string = aiFoundryWorkspace.id
output workspaceName string = aiFoundryWorkspace.name
output endpoint string = aiFoundryWorkspace.properties.discoveryUrl
output principalId string = aiFoundryWorkspace.identity.principalId
output modelDeploymentName string = modelDeploymentName
