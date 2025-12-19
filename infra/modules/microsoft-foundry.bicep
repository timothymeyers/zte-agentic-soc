// ============================================================================
// Microsoft Foundry (AI Foundry) Module
// ============================================================================
// Deploys Microsoft Foundry workspace and project configuration

targetScope = 'resourceGroup'

// ============================================================================
// Parameters
// ============================================================================

@description('Location for resources')
param location string

@description('Project name prefix')
param projectName string

@description('Azure OpenAI deployment name')
param openAiDeploymentName string = 'gpt-4.1-mini'

@description('Tags for resources')
param tags object = {}

// ============================================================================
// Variables
// ============================================================================

var workspaceName = '${projectName}-foundry'
var aiProjectName = 'asoc'

// ============================================================================
// Outputs (Placeholder - requires actual Microsoft Foundry resource types)
// ============================================================================

// NOTE: This is a placeholder template. Microsoft Foundry resource types
// may not be available in ARM/Bicep templates yet. Deployment may need to be
// done via Azure Portal, Azure CLI, or azure-ai-projects SDK.
//
// Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/

@description('Microsoft Foundry project endpoint')
output projectEndpoint string = 'https://${workspaceName}.services.ai.azure.com/api/projects/${aiProjectName}'

@description('Microsoft Foundry project name')
output projectName string = aiProjectName

@description('Azure OpenAI endpoint')
output openAiEndpoint string = 'https://${workspaceName}.openai.azure.com/openai/v1/'

@description('OpenAI deployment name')
output openAiDeploymentName string = openAiDeploymentName

// ============================================================================
// TODO: Implement actual Microsoft Foundry resources
// ============================================================================
// When Bicep support for Microsoft Foundry is available, implement:
// 1. Microsoft Foundry workspace
// 2. Microsoft Foundry project
// 3. Model deployments (GPT-4.1-mini, text-embedding-3-large)
// 4. Networking configuration (private endpoints if needed)
// 5. RBAC role assignments for managed identity
