# Agent Deployment Verification Guide

This guide explains how to verify that agents can be successfully created in Microsoft Foundry using **azure-ai-projects 2.0.0b1+**.

## Prerequisites

1. **Azure Authentication**
   - Ensure you are logged into Azure CLI: `az login`
   - Verify your identity: `az account show`

2. **Environment Variables**
   Required environment variables:
   ```bash
   export AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://your-foundry.services.ai.azure.com/api/projects/your-project"
   export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"
   # OR
   export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1-mini"
   ```

3. **Python Dependencies**
   Install the project dependencies:
   ```bash
   pip install --pre 'azure-ai-projects>=2.0.0b1' azure-identity
   ```

## Verification Methods

### Method 1: Using the Test Script

Run the included test script to verify agent deployment with azure-ai-projects 2.0.0b1+:

```bash
python test_agent_api.py
```

**Expected Output:**
```
================================================================================
Testing azure-ai-projects 2.0.0b1+ Agent API
================================================================================

1. Checking environment variables...
✓ Endpoint: https://asoc-foundry.services.ai.azure.com/api/******/asoc
✓ Model: gpt-4.1-mini

2. Initializing AIProjectClient...
✓ AIProjectClient initialized successfully

3. Listing existing agents...
✓ Found 3 existing agents

  First few agents:
  - alert-triage-agent (version: N/A, id: alert-triage-agent...)
  - AlertTriageTim (version: N/A, id: AlertTriageTim...)
  - AlertTriageAgentNew (version: N/A, id: AlertTriageAgentNew...)

4. Testing get(agent_name=...)...
✓ Retrieved agent 'alert-triage-agent'
  - ID: alert-triage-agent
  - Kind: N/A
  - Created: N/A

5. Testing create_version (create or update agent)...
✓ Agent created/updated successfully
  - Name: test-api-agent
  - ID: test-api-agent:1
  - Version: 1
  - Kind: N/A
  - Created: 2025-12-19 14:40:27+00:00

================================================================================
✅ All API tests passed! Agent deployment is working correctly.
================================================================================
```

### Method 2: Using Python REPL

Test agent deployment interactively with azure-ai-projects 2.0.0b1+:

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
import os

# Initialize client
endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)

# List existing agents
agents = list(client.agents.list())
print(f"Found {len(agents)} agents")

# Get an existing agent by name
agent = client.agents.get(agent_name="alert-triage-agent")
print(f"Retrieved: {agent.name} (ID: {agent.id})")

# Create or update an agent
agent = client.agents.create_version(
    agent_name="test-agent",
    definition=PromptAgentDefinition(
        model="gpt-4.1-mini",
        instructions="You are a helpful assistant.",
    ),
    description="Test agent"
)
print(f"Created/Updated: {agent.name} (ID: {agent.id}, Version: {agent.version})")
```

### Method 3: Using the CLI

If you have the CLI installed, you can use:

```bash
# Deploy agents to Microsoft Foundry
asoc deploy

# List deployed agents
asoc list-agents

# Cleanup agents (use with caution)
asoc cleanup
```

Or run directly with Python:

```bash
python -m src.demo.cli deploy
python -m src.demo.cli list-agents
```

## Troubleshooting

### Common Issues

1. **CredentialUnavailableError**
   - **Solution**: Run `az login` to authenticate with Azure CLI
   - Verify: `az account show`

2. **AZURE_AI_FOUNDRY_PROJECT_ENDPOINT not set**
   - **Solution**: Set the environment variable:
     ```bash
     export AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://your-endpoint.services.ai.azure.com/api/projects/project-name"
     ```

3. **AZURE_AI_MODEL_DEPLOYMENT_NAME not set**
   - **Solution**: Set the model deployment name:
     ```bash
     export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"
     ```
   - Verify available models in your Foundry project

4. **403 Forbidden Error**
   - **Cause**: Insufficient RBAC permissions on the resource group
   - **Solution**: Ensure you have Contributor or Cognitive Services Contributor role on the resource group

5. **Agent already exists**
   - **Behavior**: The deployer will skip creation and return the existing agent
   - This is expected behavior to prevent duplicates

## SDK Details

### Using AIProjectClient (azure-ai-projects 2.0.0b1+)

The project uses `AIProjectClient` from the `azure-ai-projects` package (version 2.0.0b1 or higher):

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

# Initialize client
client = AIProjectClient(
    endpoint="https://your-foundry.services.ai.azure.com/api/projects/project-name",
    credential=DefaultAzureCredential()
)

# Create new agent
agent = client.agents.create(
    name="MyAgent",
    definition=PromptAgentDefinition(
        model="gpt-4.1-mini",
        instructions="You are a helpful assistant",
    ),
    description="My custom agent"
)

# Update existing agent (creates new version)
agent = client.agents.create_version(
    agent_name="MyAgent",
    definition=PromptAgentDefinition(
        model="gpt-4.1-mini",
        instructions="Updated instructions",
    ),
    description="Updated description"
)

# Get agent by name
agent = client.agents.get(agent_name="MyAgent")

# List all agents
agents = list(client.agents.list())

# Delete agent
client.agents.delete(agent_name="MyAgent")

# Interact with agent using OpenAI client
openai_client = client.get_openai_client()
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Hello!"}],
    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
)
print(response.output_text)
```

### Version Requirements

- **azure-ai-projects**: ≥2.0.0b1 (pre-release, install with `--pre` flag)
- **azure-identity**: ≥1.15.0
- **openai**: ≥1.0.0 (optional, for agent interaction testing)

## API Endpoints

The AIProjectClient.agents interface communicates with Microsoft Foundry v2 Agent API:
```
POST   /api/projects/{project}/agents              # Create agent
POST   /api/projects/{project}/agents/{name}       # Create version (update)
GET    /api/projects/{project}/agents              # List agents
GET    /api/projects/{project}/agents/{name}       # Get agent by name
DELETE /api/projects/{project}/agents/{name}       # Delete agent
```

## Next Steps

After verifying agent deployment:

1. **Deploy Additional Agents**: Add more agent definitions to `AGENT_DEFINITIONS` in `deploy_agents.py`
2. **Test Orchestration**: Run workflow orchestration with deployed agents
3. **Monitor Agent Usage**: Check Azure Foundry portal for agent metrics

## References

- [Azure AI Projects Python SDK](https://learn.microsoft.com/en-us/python/api/azure-ai-projects)
- [Microsoft Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry)
- [DefaultAzureCredential Authentication](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential)
