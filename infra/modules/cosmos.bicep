// ============================================================================
// Azure Cosmos DB Module
// ============================================================================
// Deploys Cosmos DB account, database, and containers for agent state

targetScope = 'resourceGroup'

// ============================================================================
// Parameters
// ============================================================================

@description('Location for Cosmos DB')
param location string

@description('Cosmos DB account name')
param accountName string

@description('Database name')
param databaseName string

@description('Tags for resources')
param tags object = {}

@description('Consistency level')
@allowed([
  'Eventual'
  'ConsistentPrefix'
  'Session'
  'BoundedStaleness'
  'Strong'
])
param consistencyLevel string = 'Session'

// ============================================================================
// Variables
// ============================================================================

var locations = [
  {
    locationName: location
    failoverPriority: 0
    isZoneRedundant: false
  }
]

// Container definitions
var containers = [
  {
    name: 'alerts'
    partitionKey: '/Severity'
    defaultTtl: 432000 // 5 days
  }
  {
    name: 'incidents'
    partitionKey: '/Severity'
    defaultTtl: 432000 // 5 days
  }
  {
    name: 'agent-state'
    partitionKey: '/AgentName'
    defaultTtl: -1 // No TTL (persist indefinitely)
  }
  {
    name: 'audit-logs'
    partitionKey: '/Actor'
    defaultTtl: 2592000 // 30 days
  }
  {
    name: 'triage-results'
    partitionKey: '/Priority'
    defaultTtl: 432000 // 5 days
  }
]

// ============================================================================
// Resources
// ============================================================================

// Cosmos DB Account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: consistencyLevel
    }
    locations: locations
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    capabilities: [
      {
        name: 'EnableServerless' // Serverless for MVP cost optimization
      }
    ]
  }
}

// Cosmos DB Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// Cosmos DB Containers
resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = [for item in containers: {
  parent: database
  name: item.name
  properties: {
    resource: {
      id: item.name
      partitionKey: {
        paths: [
          item.partitionKey
        ]
        kind: 'Hash'
      }
      defaultTtl: item.defaultTtl
    }
  }
}]

// ============================================================================
// Outputs
// ============================================================================

@description('Cosmos DB account endpoint')
output endpoint string = cosmosAccount.properties.documentEndpoint

@description('Cosmos DB account ID')
output accountId string = cosmosAccount.id

@description('Cosmos DB account name')
output accountName string = cosmosAccount.name

@description('Database name')
output databaseName string = databaseName

@description('Container names')
output containerNames array = [for item in containers: item.name]
