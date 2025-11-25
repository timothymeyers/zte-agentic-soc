// Azure AI Search module
// Deploys Azure AI Search service with 3 indexes for threat intelligence

@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for resources')
param location string

@description('Base name for resources')
param baseName string

@description('Tags to apply to resources')
param tags object = {}

var searchServiceName = '${baseName}-search-${environment}'

// Azure AI Search service
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: environment == 'prod' ? 'standard' : 'basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: environment == 'prod' ? 2 : 1
    partitionCount: environment == 'prod' ? 2 : 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled' // Change to 'disabled' for private endpoints
    networkRuleSet: {
      ipRules: []
    }
    semanticSearch: 'free' // Enable semantic search
  }
}

// Note: Indexes are created via utils/setup_ai_search.py script
// The following are index definitions for reference:
//
// Index 1: attack-scenarios
// - Fields: id, scenario_name, description, mitre_techniques, attack_pattern, severity, embedding (vector)
// - Vector search enabled for similarity matching
// - Partition key: scenario_id
//
// Index 2: historical-incidents  
// - Fields: id, incident_id, description, alerts, entities, resolution, embedding (vector)
// - Vector search enabled for RAG retrieval
// - Partition key: incident_date
//
// Index 3: threat-intelligence
// - Fields: id, ioc_type, ioc_value, reputation_score, first_seen, last_seen, sources
// - Faceting enabled on ioc_type and reputation_score
// - Partition key: ioc_type

// Output values for other modules
output searchServiceId string = searchService.id
output searchServiceName string = searchService.name
output endpoint string = 'https://${searchService.name}.search.windows.net'
output principalId string = searchService.identity.principalId
output adminKey string = searchService.listAdminKeys().primaryKey
