// Cosmos DB module
// Deploys Cosmos DB account with NoSQL database and collections

@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for resources')
param location string

@description('Base name for resources')
param baseName string

@description('Tags to apply to resources')
param tags object = {}

var accountName = '${baseName}-cosmos-${environment}'
var databaseName = 'agentic-soc'

// Cosmos DB account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: environment == 'prod'
      }
    ]
    enableAutomaticFailover: environment == 'prod'
    enableMultipleWriteLocations: false
    publicNetworkAccess: 'Enabled' // Change to 'Disabled' for private endpoints
    capabilities: [
      {
        name: 'EnableServerless' // Use serverless for dev, provisioned for prod
      }
    ]
  }
}

// NoSQL database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// Collection: alerts
resource alertsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'alerts'
  properties: {
    resource: {
      id: 'alerts'
      partitionKey: {
        paths: ['/alert_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
      defaultTtl: 2592000 // 30 days in seconds
    }
    options: environment == 'prod' ? {
      throughput: 1000
    } : {}
  }
}

// Collection: incidents
resource incidentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'incidents'
  properties: {
    resource: {
      id: 'incidents'
      partitionKey: {
        paths: ['/incident_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
      defaultTtl: 7776000 // 90 days in seconds
    }
    options: environment == 'prod' ? {
      throughput: 1000
    } : {}
  }
}

// Collection: triage_results
resource triageResultsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'triage_results'
  properties: {
    resource: {
      id: 'triage_results'
      partitionKey: {
        paths: ['/alert_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
      defaultTtl: 2592000 // 30 days in seconds
    }
    options: environment == 'prod' ? {
      throughput: 1000
    } : {}
  }
}

// Collection: response_actions
resource responseActionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'response_actions'
  properties: {
    resource: {
      id: 'response_actions'
      partitionKey: {
        paths: ['/incident_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
      defaultTtl: 7776000 // 90 days in seconds
    }
    options: environment == 'prod' ? {
      throughput: 1000
    } : {}
  }
}

// Collection: agent_state
resource agentStateContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'agent_state'
  properties: {
    resource: {
      id: 'agent_state'
      partitionKey: {
        paths: ['/agent_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
      defaultTtl: -1 // No TTL - keep agent state indefinitely
    }
    options: environment == 'prod' ? {
      throughput: 400
    } : {}
  }
}

// Collection: audit_logs
resource auditLogsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'audit_logs'
  properties: {
    resource: {
      id: 'audit_logs'
      partitionKey: {
        paths: ['/timestamp']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
      defaultTtl: 31536000 // 365 days in seconds (1 year retention)
    }
    options: environment == 'prod' ? {
      throughput: 1000
    } : {}
  }
}

// Output values for other modules
output accountId string = cosmosAccount.id
output accountName string = cosmosAccount.name
output endpoint string = cosmosAccount.properties.documentEndpoint
output principalId string = cosmosAccount.identity.principalId
output databaseName string = databaseName
output connectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
