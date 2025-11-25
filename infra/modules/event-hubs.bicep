// Event Hubs module
// Deploys Event Hubs namespace with alert-ingestion hub

@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for resources')
param location string

@description('Base name for resources')
param baseName string

@description('Tags to apply to resources')
param tags object = {}

var namespaceName = '${baseName}-eventhubs-${environment}'
var hubName = 'alert-ingestion'

// Event Hubs namespace
resource eventHubsNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' = {
  name: namespaceName
  location: location
  tags: tags
  sku: {
    name: environment == 'prod' ? 'Standard' : 'Basic'
    tier: environment == 'prod' ? 'Standard' : 'Basic'
    capacity: environment == 'prod' ? 2 : 1
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled' // Change to 'Disabled' for private endpoints
    isAutoInflateEnabled: environment == 'prod'
    maximumThroughputUnits: environment == 'prod' ? 10 : 0
    zoneRedundant: environment == 'prod'
  }
}

// Alert ingestion event hub
resource alertIngestionHub 'Microsoft.EventHub/namespaces/eventhubs@2023-01-01-preview' = {
  parent: eventHubsNamespace
  name: hubName
  properties: {
    messageRetentionInDays: environment == 'prod' ? 7 : 1
    partitionCount: environment == 'prod' ? 4 : 2
    status: 'Active'
  }
}

// Consumer group for orchestrator
resource orchestratorConsumerGroup 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2023-01-01-preview' = {
  parent: alertIngestionHub
  name: 'orchestrator'
  properties: {}
}

// Consumer group for alert triage agent
resource triageConsumerGroup 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2023-01-01-preview' = {
  parent: alertIngestionHub
  name: 'alert-triage'
  properties: {}
}

// Authorization rule for sending
resource sendAuthRule 'Microsoft.EventHub/namespaces/eventhubs/authorizationRules@2023-01-01-preview' = {
  parent: alertIngestionHub
  name: 'SendRule'
  properties: {
    rights: [
      'Send'
    ]
  }
}

// Authorization rule for listening
resource listenAuthRule 'Microsoft.EventHub/namespaces/eventhubs/authorizationRules@2023-01-01-preview' = {
  parent: alertIngestionHub
  name: 'ListenRule'
  properties: {
    rights: [
      'Listen'
    ]
  }
}

// Output values for other modules
output namespaceId string = eventHubsNamespace.id
output namespaceName string = eventHubsNamespace.name
output principalId string = eventHubsNamespace.identity.principalId
output hubName string = alertIngestionHub.name
output sendConnectionString string = sendAuthRule.listKeys().primaryConnectionString
output listenConnectionString string = listenAuthRule.listKeys().primaryConnectionString
