# Agentic SOC Schema Documentation

This directory contains JSON Schema definitions for agent input/output contracts and event-driven messaging in the Agentic Security Operations Center (SOC) system.

## Overview

The Agentic SOC uses a combination of:
- **Agent Input/Output Schemas**: Define contracts for AI agents hosted in Azure AI Foundry
- **Event Schemas**: Define messages published to Azure Event Hubs for event-driven orchestration

## Directory Structure

```
schemas/
├── agents/          # Agent input/output contracts
│   ├── alert-triage-agent-input.schema.json
│   ├── alert-triage-agent-output.schema.json
│   ├── threat-hunting-agent-input.schema.json
│   ├── threat-hunting-agent-output.schema.json
│   ├── incident-response-agent-input.schema.json
│   ├── incident-response-agent-output.schema.json
│   ├── threat-intelligence-agent-input.schema.json
│   └── threat-intelligence-agent-output.schema.json
└── events/          # Event Hub message schemas
    ├── alert-ingestion-event.schema.json
    ├── triage-complete-event.schema.json
    ├── response-complete-event.schema.json
    └── hunt-trigger-event.schema.json
```

## Agent Schemas

### Alert Triage Agent
- **Input**: Security alerts in Microsoft Sentinel/Graph Security API format
- **Output**: Risk assessment, priority determination, enrichment data, and recommended actions
- **Purpose**: Analyze incoming alerts, assign priority, correlate related alerts, and enrich with context

### Threat Hunting Agent
- **Input**: Natural language queries or structured hunt parameters
- **Output**: Hunt findings, anomalies detected, evidence, and recommended follow-up actions
- **Purpose**: Proactively search for hidden threats across security telemetry

### Incident Response Agent
- **Input**: Incident details, selected playbook, and approval status
- **Output**: Actions executed, verification status, containment assessment, and incident state updates
- **Purpose**: Execute automated containment and response actions for confirmed incidents

### Threat Intelligence Agent
- **Input**: IOCs to enrich or requests for threat intelligence briefings
- **Output**: Enriched indicator data, threat briefings, vulnerability assessments, or emerging threat alerts
- **Purpose**: Provide threat intelligence context for alerts, incidents, and proactive awareness

## Event Schemas

### alert-ingestion-event
- **Trigger**: New security alert ingested from Microsoft Sentinel, Defender XDR, or other sources
- **Consumers**: Alert Triage Agent
- **Purpose**: Initiate alert triage workflow

### triage-complete-event
- **Trigger**: Alert Triage Agent completes analysis
- **Consumers**: Incident Response Agent, Threat Hunting Agent, Threat Intelligence Agent, Human Analysts
- **Purpose**: Trigger downstream processing based on triage results

### response-complete-event
- **Trigger**: Incident Response Agent completes containment actions
- **Consumers**: Threat Hunting Agent, Audit Logging Service, Post-Incident Review Service
- **Purpose**: Trigger follow-up activities after incident response

### hunt-trigger-event
- **Trigger**: Scheduled job, incident response, or analyst request
- **Consumers**: Threat Hunting Agent
- **Purpose**: Initiate automated or scheduled threat hunts

## Orchestration Invocation Patterns

### AI Foundry Agent Invocation

Agents hosted in Azure AI Foundry are invoked using the **Microsoft Agent Framework SDK**:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import ManagedIdentityCredential

# Initialize AI Foundry client with Managed Identity
credential = ManagedIdentityCredential()
project_client = AIProjectClient(
    credential=credential,
    project_url="https://<project-name>.api.azureml.ms"
)

# Invoke Alert Triage Agent
triage_input = {
    "alertId": "ALT-2025-001234",
    "source": "Sentinel",
    "severity": "High",
    # ... (see alert-triage-agent-input.schema.json)
}

response = await project_client.agents.invoke_agent(
    agent_id="alert-triage-agent",
    input_data=triage_input
)

# Validate output against schema
triage_output = response.output
# Process triage_output according to alert-triage-agent-output.schema.json
```

### Event-Driven Invocation

Agents can also be triggered via Event Hubs:

```python
from azure.eventhub import EventHubProducerClient, EventData
from azure.identity import ManagedIdentityCredential
import json

# Initialize Event Hub producer with Managed Identity
credential = ManagedIdentityCredential()
producer = EventHubProducerClient(
    fully_qualified_namespace="<namespace>.servicebus.windows.net",
    eventhub_name="agentic-soc-events",
    credential=credential
)

# Publish triage complete event
event_data = {
    "eventId": "550e8400-e29b-41d4-a716-446655440000",
    "eventType": "alert.triage.complete",
    "eventVersion": "1.0",
    "eventTimestamp": "2025-11-20T19:00:00.000Z",
    # ... (see triage-complete-event.schema.json)
}

event = EventData(json.dumps(event_data))
await producer.send_batch([event])
```

### Context Sharing Between Agents

**Option 1: Inline Context** (for small payloads)
```python
# Pass triage results directly to response agent
response_input = {
    "incidentId": "INC-2025-001234",
    "context": {
        "triageRationale": triage_output["rationale"],
        "riskScore": triage_output["riskScore"]
    }
}
```

**Option 2: Cosmos DB Reference** (for large payloads)
```python
# Store triage results in Cosmos DB
cosmos_client.upsert_item({
    "id": "ALT-2025-001234",
    "type": "triage_result",
    "data": triage_output
})

# Pass reference to response agent
response_input = {
    "incidentId": "INC-2025-001234",
    "contextReference": {
        "type": "cosmos_db",
        "container": "agent_context",
        "id": "ALT-2025-001234"
    }
}
```

### Orchestration Flow Example

**End-to-End Alert Processing Flow**:

1. **Alert Ingestion** → Publish `alert-ingestion-event` to Event Hubs
2. **Event Hub Trigger** → Azure Function or AKS service receives event
3. **Orchestrator** → Validates event, invokes Alert Triage Agent via AI Foundry SDK
4. **Triage Agent** → Returns prioritized assessment
5. **Orchestrator** → Validates output against schema, publishes `triage-complete-event`
6. **Conditional Routing**:
   - If `requiresApproval == true` → Send approval request to Teams, wait for human response
   - If `priority == "Critical"` → Invoke Incident Response Agent
   - If `isFalsePositive == false` → Enrich with Threat Intelligence Agent
7. **Response Agent** → Executes containment actions, publishes `response-complete-event`
8. **Post-Response** → Trigger automated threat hunt via `hunt-trigger-event`

## Schema Validation

### Python Validation Example
```python
import json
import jsonschema

# Load schema
with open('schemas/agents/alert-triage-agent-output.schema.json') as f:
    schema = json.load(f)

# Validate agent output
try:
    jsonschema.validate(instance=triage_output, schema=schema)
    print("Output is valid")
except jsonschema.ValidationError as e:
    print(f"Validation error: {e.message}")
```

### TypeScript/JavaScript Validation Example
```typescript
import Ajv from 'ajv';
import schema from './schemas/agents/alert-triage-agent-output.schema.json';

const ajv = new Ajv();
const validate = ajv.compile(schema);

if (validate(triageOutput)) {
    console.log('Output is valid');
} else {
    console.error('Validation errors:', validate.errors);
}
```

## Response Handling

### Synchronous Invocation
For interactive analyst requests, use synchronous invocation:
```python
# Wait for agent to complete and return response
response = await project_client.agents.invoke_agent(
    agent_id="threat-hunting-agent",
    input_data=hunt_input,
    wait_for_completion=True,
    timeout_seconds=300  # 5 minutes for deep searches
)
```

### Asynchronous Invocation
For batch processing or long-running operations, use event-driven callbacks:
```python
# Publish event and continue
await event_hub_producer.send_event(hunt_trigger_event)

# Agent publishes results to another event when complete
# Orchestrator subscribes to hunt-complete-event
```

## Schema Versioning

Schemas follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes (incompatible field removals or type changes)
- **MINOR**: Backward-compatible additions (new optional fields)
- **PATCH**: Documentation updates or clarifications

All schemas currently at version 1.0. Future versions will be added as:
- `alert-triage-agent-input.v2.schema.json`
- Event schemas include `eventVersion` field for runtime version detection

## Best Practices

1. **Always Validate**: Validate inputs before agent invocation and outputs before publishing events
2. **Use Managed Identity**: Never embed credentials in code - use Azure Managed Identity for authentication
3. **Handle Failures Gracefully**: Implement retry logic with exponential backoff for transient failures
4. **Monitor Latency**: Track processing time against SLAs (FR-054 through FR-057)
5. **Correlate Events**: Use `correlationId` to track related events across the system
6. **Document Assumptions**: Update schemas when LLM output patterns change

## References

- [Functional Requirements](../specs/001-agentic-soc/spec.md#functional-requirements)
- [Architecture Document](../specs/001-agentic-soc/AgenticSOC_Architecture.md)
- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/azure/ai-foundry/agents/)
- [Azure Event Hubs SDK](https://learn.microsoft.com/azure/event-hubs/)
- [JSON Schema Specification](https://json-schema.org/draft-07/schema)

## Schema Update Process

When updating schemas:
1. Create new version file (e.g., `v2.schema.json`) if breaking changes
2. Update version in `eventVersion` field for event schemas
3. Update this README with migration notes
4. Test backward compatibility with existing agents
5. Update agent prompts to match new schema expectations
6. Document changes in changelog

---

**Last Updated**: 2025-11-20  
**Schema Version**: 1.0  
**Maintained By**: Agentic SOC Team
