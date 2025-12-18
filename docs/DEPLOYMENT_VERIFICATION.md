# Agent Deployment Verification Guide

This guide explains how to verify that agents can be successfully created in Microsoft Foundry.

## Prerequisites

1. **Azure Authentication**
   - Ensure you are logged into Azure CLI: `az login`
   - Verify your identity: `az account show`

2. **Environment Variables**
   Required environment variables:
   ```bash
   export AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://your-foundry.services.ai.azure.com/api/projects/your-project"
   export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"
   ```

3. **Python Dependencies**
   Install the project dependencies:
   ```bash
   pip install azure-ai-agents azure-ai-projects azure-identity structlog
   ```

## Verification Methods

### Method 1: Using the Test Script

Run the included test script to verify agent deployment:

```bash
python test_agent_deployment.py
```

**Expected Output:**
```
================================================================================
Testing Agent Deployment to Microsoft Foundry
================================================================================

1. Checking environment variables...
✓ Endpoint: https://asoc-foundry.services.ai.azure.com/api/projects/asoc
✓ Model: gpt-4.1-mini

2. Initializing AgentDeployer...
✓ AgentDeployer initialized successfully

3. Listing existing agents...
✓ Found 19 existing agents
  - alert-triage-agent (id: asst_D8t6dYxJcjXfs7yi4CwXfhBH)
  - AlertTriageAgent (id: asst_iCaYIHWv3snQUuuX9rP5haiR)
  ...

4. Deploying SOC_Manager agent...
✓ Agent deployed successfully!
  - Name: SOC_Manager
  - ID: asst_8gCfxoJmrj0h1fdMH2Te6r8Z
  - Model: gpt-4.1-mini
  - Created: 2025-12-18 21:08:18+00:00

================================================================================
✅ All tests passed! Agent deployment is working correctly.
================================================================================
```

### Method 2: Using Python REPL

Test agent deployment interactively:

```python
from src.deployment.deploy_agents import AgentDeployer, AGENT_DEFINITIONS

# Initialize deployer
deployer = AgentDeployer()

# List existing agents
agents = deployer.list_agents()
print(f"Found {len(agents)} agents")

# Deploy manager agent
manager_def = AGENT_DEFINITIONS["manager"]
agent = deployer.deploy_agent(
    name=manager_def["name"],
    instructions_file=manager_def["instructions_file"],
    description=manager_def["description"],
)

print(f"✓ Agent deployed: {agent.name} (ID: {agent.id})")
```

### Method 3: Using the CLI

If you have the CLI installed, you can use:

```bash
# Deploy agents
python -m src.demo.cli deploy

# List deployed agents
python -m src.demo.cli list-agents

# Cleanup agents
python -m src.demo.cli cleanup
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

### Using AgentsClient (azure-ai-agents 1.1.0)

The project uses `AgentsClient` from the `azure-ai-agents` package:

```python
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

# Initialize client
client = AgentsClient(
    endpoint="https://your-endpoint.services.ai.azure.com/api/projects/project-name",
    credential=DefaultAzureCredential()
)

# Create agent
agent = client.create_agent(
    model="gpt-4.1-mini",
    name="MyAgent",
    instructions="You are a helpful assistant",
    description="My custom agent"
)

# List agents
agents = client.list_agents()

# Get agent by ID
agent = client.get_agent(agent_id="asst_12345...")

# Delete agent
client.delete_agent(agent_id="asst_12345...")
```

### Version Requirements

- **azure-ai-agents**: ≥1.1.0
- **azure-ai-projects**: ==1.0.0b3
- **azure-identity**: ≥1.15.0

## API Endpoints

The AgentsClient communicates with:
```
POST   /api/projects/{project}/assistants          # Create agent
GET    /api/projects/{project}/assistants          # List agents
GET    /api/projects/{project}/assistants/{id}     # Get agent
DELETE /api/projects/{project}/assistants/{id}     # Delete agent
```

## Next Steps

After verifying agent deployment:

1. **Deploy Additional Agents**: Add more agent definitions to `AGENT_DEFINITIONS` in `deploy_agents.py`
2. **Test Orchestration**: Run workflow orchestration with deployed agents
3. **Monitor Agent Usage**: Check Azure Foundry portal for agent metrics

## References

- [Azure AI Agents Python SDK](https://learn.microsoft.com/en-us/python/api/azure-ai-agents)
- [Azure AI Projects SDK](https://learn.microsoft.com/en-us/python/api/azure-ai-projects)
- [Microsoft Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry)
