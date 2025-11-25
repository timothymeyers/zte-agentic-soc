// Container Apps module
// Deploys Container Apps environment with agent services

@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for resources')
param location string

@description('Base name for resources')
param baseName string

@description('Log Analytics workspace ID')
param logAnalyticsWorkspaceId string

@description('Tags to apply to resources')
param tags object = {}

var environmentName = '${baseName}-containerenv-${environment}'

// Container Apps environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2022-10-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2022-10-01').primarySharedKey
      }
    }
    zoneRedundant: environment == 'prod'
  }
}

// Alert Triage Agent container app
resource alertTriageAgent 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${baseName}-alert-triage-${environment}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 8080
        transport: 'http'
      }
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'alert-triage-agent'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - replace with actual image
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

// Orchestrator container app
resource orchestrator 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${baseName}-orchestrator-${environment}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 8080
        transport: 'http'
      }
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'orchestrator'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - replace with actual image
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 5 : 2
      }
    }
  }
}

// API service container app
resource apiService 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${baseName}-api-${environment}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'api'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - replace with actual image
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Output values for other modules
output environmentId string = containerAppEnvironment.id
output environmentName string = containerAppEnvironment.name
output alertTriageAgentId string = alertTriageAgent.id
output alertTriageAgentPrincipalId string = alertTriageAgent.identity.principalId
output orchestratorId string = orchestrator.id
output orchestratorPrincipalId string = orchestrator.identity.principalId
output apiServiceId string = apiService.id
output apiServicePrincipalId string = apiService.identity.principalId
output apiServiceUrl string = apiService.properties.configuration.ingress.fqdn
