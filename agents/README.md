# Agentic SOC - Agent Definitions

This directory contains **declarative YAML agent definitions** for the Agentic SOC system. These agents are designed to work with **Microsoft Foundry Agent Service** and leverage native Foundry capabilities like knowledge bases, enterprise memory, and built-in tools.

## Agent Architecture

Agents in this directory follow the **Foundry Native Agent** pattern:

1. **Declarative Configuration**: Agents defined in YAML, not code
2. **Persistent Lifecycle**: Agents created once and reused across sessions
3. **Native Tooling**: Leverage MCP tools, Code Interpreter, File Search, Bing Grounding, A2A
4. **Enterprise Memory**: Long-term memory backed by Cosmos DB
5. **Knowledge Integration**: Direct access to Foundry IQ knowledge bases

## Available Agents

### Alert Triage Agent (`alert-triage-agent.yaml`)

**Purpose**: Analyzes security alerts, calculates risk scores, detects correlations, and provides actionable remediation steps.

**Model**: GPT-4.1-mini (temperature: 0.3)

**Tools**:
- MCP Tool: MITRE ATT&CK knowledge base
- Code Interpreter: Risk score calculations
- File Search: Historical incidents
- Bing Grounding: Real-time threat intelligence
- A2A: Agent-to-agent communication

**Key Features**:
- Autonomous response prioritization
- Multi-factor risk scoring
- Attack scenario prevalence analysis
- Specific remediation prescriptions
- Per-alert memory scope

## YAML Schema

All agent definitions follow the Microsoft Foundry agent schema:

```yaml
# yaml-language-server: $schema=https://aka.ms/ai-foundry/vsc/agent/1.0.0

version: 1.0.0
name: agent-name
description: Agent purpose and capabilities

metadata:
  authors: [...]
  tags: [...]
  version: '1.0.0'

model:
  id: 'model-deployment-name'
  options:
    temperature: 0.0-2.0
    top_p: 0.0-1.0
    max_tokens: int

instructions: |
  System prompt defining agent behavior...

tools:
  - type: mcp | code_interpreter | file_search | bing_grounding | a2a
    # Tool-specific configuration

memory:
  enabled: true/false
  scope_type: "alert" | "user" | "session"
  cosmos_connection_id: "${CONNECTION_ID}"

tool_resources:
  file_search:
    vector_stores: [...]
  code_interpreter:
    files: [...]
```

## Environment Variables

Agents use environment variable placeholders in the form `${VARIABLE_NAME}`. These must be configured before initializing agents:

### Required Variables

```bash
# Azure AI Foundry Project
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/project-id"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"

# Azure AI Search (Knowledge Base)
export AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"

# Project Connections
export PROJECT_CONNECTION_ID="/subscriptions/.../connections/attack-scenarios-kb-connection"
export BING_PROJECT_CONNECTION_ID="/subscriptions/.../connections/bing-connection"
export A2A_PROJECT_CONNECTION_ID="/subscriptions/.../connections/a2a-connection"
export COSMOS_PROJECT_CONNECTION_ID="/subscriptions/.../connections/cosmos-connection"

# Vector Stores
export HISTORICAL_INCIDENTS_VECTOR_STORE_ID="vs-12345..."
```

### Authentication

Agents use Azure DefaultAzureCredential for authentication:

```bash
# Login with Azure CLI
az login

# Or set service principal credentials
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
export AZURE_TENANT_ID="..."
```

## Usage

### Initialize Agent from YAML

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import PromptAgentDefinition
import yaml
import os

# Load YAML definition
with open('agents/alert-triage-agent.yaml', 'r') as f:
    agent_config = yaml.safe_load(f)

# Create project client
project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# Check if agent exists
existing_agents = project_client.agents.list_agents()
agent = next(
    (a for a in existing_agents if a.name == agent_config['name']),
    None
)

if not agent:
    # Create agent from YAML
    agent = project_client.agents.create_version(
        agent_name=agent_config['name'],
        definition=PromptAgentDefinition(
            model=agent_config['model']['id'],
            instructions=agent_config['instructions'],
            tools=[...]  # Build tools from config
        ),
        description=agent_config['description']
    )

print(f"Agent ready: {agent.name} (version {agent.version})")
```

### Run Agent with Query

```python
# Get OpenAI client for Responses API
openai_client = project_client.get_openai_client()

# Create conversation
response = openai_client.responses.create(
    input="Analyze this security alert: ...",
    extra_body={
        "agent": {
            "name": agent.name,
            "type": "agent_reference"
        }
    }
)

print(response.output_text)
```

### Persist Conversation Thread

```python
# Create conversation with thread ID
response = openai_client.responses.create(
    conversation_id="alert-12345",  # Persistent thread ID
    input="What was the risk score?",
    extra_body={
        "agent": {
            "name": agent.name,
            "type": "agent_reference"
        }
    }
)

# Agent remembers previous context in this thread
```

## Knowledge Base Setup

Agents rely on Foundry IQ knowledge bases. Set up knowledge sources before using agents:

### 1. Create Knowledge Source

```bash
az search knowledge-source create \
  --resource-group $RG \
  --service-name $SEARCH_SERVICE \
  --knowledge-base-name attack-scenarios-kb \
  --knowledge-source-name attack-scenarios \
  --type azure-search-index \
  --index-name attack-scenarios
```

### 2. Load Data

```python
# Use utils/setup_ai_search.py to load Attack dataset
python utils/setup_ai_search.py --load-attack-scenarios
```

### 3. Create Project Connection

```python
from azure.ai.projects import AIProjectClient

connection = project_client.project_connections.create(
    connection_name="attack-scenarios-kb-connection",
    connection_type="RemoteTool",
    endpoint=f"{search_endpoint}/knowledgebases/attack-scenarios-kb/mcp",
    authentication={
        "type": "managed_identity",
        "managed_identity": {
            "resource_id": project_managed_identity_id
        }
    }
)
```

## Enterprise Memory Setup

Agents use Foundry enterprise memory for persistent state:

### 1. Enable BYO Thread Storage

In Foundry project settings, enable "Bring Your Own Thread Storage" with Cosmos DB.

### 2. Create Cosmos Containers

```python
# Containers are auto-created by Foundry:
# - thread-message-store
# - system-thread-message-store
# - agent-entity-store
```

### 3. Create Project Connection

```python
cosmos_connection = project_client.project_connections.create(
    connection_name="enterprise-memory-cosmos",
    connection_type="AzureCosmosDB",
    endpoint=cosmos_endpoint,
    database_name="enterprise_memory",
    authentication={...}
)
```

## Tool Configuration

### MCP Tool (Knowledge Base)

```yaml
- type: mcp
  mcp:
    server_label: "attack-scenarios-kb"
    server_url: "${AZURE_SEARCH_ENDPOINT}/knowledgebases/attack-scenarios-kb/mcp?api-version=2025-11-01-preview"
    require_approval: "never"
    allowed_tools:
      - knowledge_base_retrieve
    project_connection_id: "${PROJECT_CONNECTION_ID}"
```

### Code Interpreter

```yaml
- type: code_interpreter
  code_interpreter:
    container:
      type: automatic
```

### File Search

```yaml
- type: file_search
  file_search:
    vector_store_ids:
      - "${HISTORICAL_INCIDENTS_VECTOR_STORE_ID}"
```

### Bing Grounding

```yaml
- type: bing_grounding
  bing_grounding:
    search_configurations:
      - project_connection_id: "${BING_PROJECT_CONNECTION_ID}"
```

### Agent-to-Agent (A2A)

```yaml
- type: a2a
  a2a:
    project_connection_id: "${A2A_PROJECT_CONNECTION_ID}"
```

## Best Practices

### 1. Version Control

- Track all agent definition changes in Git
- Use semantic versioning for agent versions
- Document breaking changes in commit messages

### 2. Environment-Specific Configs

Create separate environment variable files:
- `.env.dev` - Development environment
- `.env.staging` - Staging environment
- `.env.prod` - Production environment

### 3. Testing

Test agents with known inputs:

```python
# Test knowledge base retrieval
response = agent.run("Retrieve MITRE ATT&CK context for technique T1059.001")
assert "PowerShell" in response.output_text

# Test risk calculation
response = agent.run("Calculate risk score for High severity alert with 3 entities")
assert "risk score" in response.output_text.lower()
```

### 4. Monitoring

Enable logging and monitoring:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitor tool invocations, response times, errors
```

### 5. Security

- Use managed identities for authentication (not API keys)
- Restrict tool approval requirements for sensitive operations
- Implement least-privilege access for project connections
- Audit agent actions and decisions

## Troubleshooting

### Agent Creation Fails

**Error**: "Model deployment not found"

**Solution**: Verify model deployment name matches exactly:
```bash
az ml online-deployment list --resource-group $RG --workspace-name $WORKSPACE
```

### Knowledge Base Not Working

**Error**: "MCP tool invocation failed"

**Solution**: Verify project connection and permissions:
```bash
# Check connection exists
az search knowledge-base list --service-name $SEARCH_SERVICE

# Verify managed identity has Search Index Data Reader role
az role assignment list --scope $SEARCH_RESOURCE_ID
```

### Enterprise Memory Not Persisting

**Error**: "Thread not found"

**Solution**: Verify Cosmos DB connection and containers:
```python
# Check containers exist
cosmos_client = CosmosClient(endpoint, credential)
database = cosmos_client.get_database_client("enterprise_memory")
containers = list(database.list_containers())
print(containers)  # Should include thread-message-store, etc.
```

## Future Agents

Upcoming agent definitions:

- `threat-hunting-agent.yaml` - Proactive threat hunting
- `incident-response-agent.yaml` - Automated incident response
- `threat-intel-agent.yaml` - Threat intelligence aggregation

## References

- [Microsoft Foundry Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview)
- [Declarative Agent Definitions](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-types/azure-ai-agent#declarative-spec)
- [Foundry IQ Knowledge Bases](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/knowledge-retrieval)
- [Azure AI Projects SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- [Refactor Plan](../docs/FOUNDRY-NATIVE-AGENTS-REFACTOR-PLAN.md)
