# Infrastructure Deployment

This directory contains Azure infrastructure as code (Bicep templates) for the Agentic SOC platform.

## Status

⚠️ **Phase 2A Infrastructure (Tasks T024-T033) - Not Yet Implemented**

The infrastructure templates are placeholders. Full implementation is pending and includes:

- Azure AI Foundry workspace and model deployments
- Cosmos DB with collections and indexes
- Event Hubs for event-driven architecture
- Container Apps for agent hosting
- Application Insights for monitoring
- Azure AI Search with threat intelligence indexes

## Directory Structure

```
infra/
├── main.bicep                 # Main orchestration template (placeholder)
├── modules/                   # Resource-specific modules (TODO)
│   ├── ai-foundry.bicep      # AI Foundry workspace (TODO)
│   ├── cosmos.bicep          # Cosmos DB (TODO)
│   ├── event-hubs.bicep      # Event Hubs (TODO)
│   ├── container-apps.bicep  # Container Apps (TODO)
│   ├── monitoring.bicep      # Application Insights (TODO)
│   └── ai-search.bicep       # Azure AI Search (TODO)
└── parameters/                # Environment-specific parameters
    ├── dev.parameters.json   # Development environment
    └── prod.parameters.json  # Production environment (TODO)
```

## TODO

See `specs/001-agentic-soc/tasks.md` Phase 2A (T024-T033) for implementation details.
