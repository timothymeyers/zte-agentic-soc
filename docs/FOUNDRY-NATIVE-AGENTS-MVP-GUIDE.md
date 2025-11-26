# Foundry Native Agents - MVP Implementation Guide

This document describes the MVP implementation of Microsoft Foundry Native Agents for the Agentic SOC project. This is part of the refactor from programmatic agent creation to declarative YAML-based agent definitions.

## What's New

The MVP implementation introduces:

1. **FoundryNativeAgent wrapper class** - Loads agents from YAML definitions
2. **Global agent management** - Agents initialized once at startup and reused
3. **Environment variable resolution** - Dynamic configuration via `${VAR}` placeholders
4. **Persistent agent lifecycle** - No need to recreate agents for each operation
5. **Backward compatibility** - Existing code continues to work

## Quick Start

### 1. Initialize Agents at Startup

```python
import asyncio
from src.agents import initialize_agents, get_alert_triage_agent

async def main():
    # Initialize all agents once at startup
    await initialize_agents()
    
    # Get the alert triage agent instance
    triage_agent = get_alert_triage_agent()
    
    print(f"Agent ready: {triage_agent.name} v{triage_agent.version}")
    
    # Use agent for multiple operations
    for alert in alerts:
        result = await triage_agent.run(query=build_query(alert))
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Configuration

Set environment variables for Azure resources:

```bash
# Required for production
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/project-id"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"

# Optional for enhanced functionality
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export PROJECT_CONNECTION_ID="/subscriptions/.../connections/attack-scenarios-kb"

# Authentication
az login
```

### 3. Run Without Azure (Development Mode)

For development and testing without Azure infrastructure:

```python
# The agent will initialize with warnings but work in limited mode
await initialize_agents()
agent = get_alert_triage_agent()

# Basic operations work without Azure endpoint
print(f"Agent: {agent.name} v{agent.version}")
```

## Architecture

### Before (Programmatic)

```python
# Create agent programmatically on every run
agent = ChatAgent(
    chat_client=AzureAIAgentClient(...),
    instructions="...",  # Hardcoded
    tools=[custom_function_1, custom_function_2]  # Custom @ai_function
)

# Use agent
result = await agent.run(query)

# Agent discarded after use
```

### After (Declarative YAML + Wrapper)

```python
# Initialize agent ONCE at startup from YAML
await initialize_agents()
agent = get_alert_triage_agent()

# Reuse agent for all operations
for item in items:
    result = await agent.run(query)
```

## File Structure

```
agents/
├── alert-triage-agent.yaml       # Declarative agent definition
└── README.md                      # Agent configuration guide

src/agents/
├── __init__.py                    # Global agent management
├── foundry_native_agent.py        # YAML wrapper class
└── alert_triage_agent.py          # Legacy implementation (backward compat)

tests/unit/
└── test_foundry_native_agent.py   # Unit tests for new implementation
```

## Key Classes and Functions

### FoundryNativeAgent

The core wrapper class that loads agents from YAML:

```python
class FoundryNativeAgent:
    """Wrapper for Foundry native agents with persistent lifecycle."""
    
    def __init__(self, agent_yaml_path: str):
        """Load agent from YAML file."""
        pass
    
    async def initialize(self) -> None:
        """Initialize agent from YAML definition."""
        pass
    
    async def run(self, query: str, thread_id: Optional[str] = None):
        """Run agent with query."""
        pass
    
    async def close(self) -> None:
        """Clean up agent resources."""
        pass
```

### Global Agent Management

Centralized agent lifecycle management:

```python
# Initialize all agents at startup
await initialize_agents()

# Get agent instances
agent = get_alert_triage_agent()

# Clean up at shutdown
await cleanup_agents()
```

## Environment Variable Resolution

YAML files support environment variable placeholders:

```yaml
# In agent YAML
tools:
  - type: mcp
    mcp:
      server_url: "${AZURE_SEARCH_ENDPOINT}/knowledgebases/kb1"
      project_connection_id: "${PROJECT_CONNECTION_ID}"
```

At runtime, `${VAR}` is replaced with the actual environment variable value.

## Migration Guide

### For Existing Code

The new implementation maintains backward compatibility:

```python
# Old way (still works)
from src.agents.alert_triage_agent import AlertTriageAgent

agent = AlertTriageAgent(
    project_endpoint=endpoint,
    model_deployment_name=model
)
result = await agent.triage_alert(alert)

# New way (recommended)
from src.agents import initialize_agents, get_alert_triage_agent

await initialize_agents()
agent = get_alert_triage_agent()
result = await agent.run(query=build_query(alert))
```

### Gradual Migration Strategy

1. **Phase 1**: Keep existing code working (✅ Done)
2. **Phase 2**: Add new FoundryNativeAgent alongside existing code (✅ Done)
3. **Phase 3**: Update new code to use FoundryNativeAgent
4. **Phase 4**: Migrate existing code module by module
5. **Phase 5**: Remove legacy implementation (future)

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
# Test FoundryNativeAgent wrapper
pytest tests/unit/test_foundry_native_agent.py -v

# All unit tests
pytest tests/unit/ -v
```

### Integration Testing

```python
import pytest
from src.agents import initialize_agents, get_alert_triage_agent

@pytest.mark.asyncio
async def test_agent_lifecycle():
    """Test complete agent lifecycle."""
    # Initialize
    await initialize_agents()
    
    # Get agent
    agent = get_alert_triage_agent()
    assert agent is not None
    assert agent.is_initialized
    
    # Use agent
    result = await agent.run(query="Test query")
    assert result is not None
    
    # Cleanup
    await agent.close()
```

## Benefits

### For Development
- ✅ No custom tool code to maintain (tools defined in YAML)
- ✅ Agent behavior changes without code deployment
- ✅ Version control for agent definitions
- ✅ Easier testing and validation
- ✅ Clear separation of configuration and code

### For Operations
- ✅ Single agent initialization at startup
- ✅ Resource efficiency (no agent recreation overhead)
- ✅ Consistent agent state across operations
- ✅ Graceful shutdown and cleanup

### For Features (Future)
- 🔜 Native Foundry tools (MCP, Code Interpreter, File Search)
- 🔜 Enterprise memory backed by Cosmos DB
- 🔜 Real-time threat intelligence (Bing Grounding)
- 🔜 Agent-to-agent communication (A2A)

## Limitations (MVP)

This MVP implementation focuses on the wrapper infrastructure:

- ✅ YAML agent loading
- ✅ Environment variable resolution
- ✅ Persistent agent lifecycle
- ✅ Global agent management
- ⏳ Native Foundry tools (requires Azure infrastructure)
- ⏳ MCP tool integration (requires knowledge bases)
- ⏳ Code Interpreter integration
- ⏳ Enterprise memory (requires Cosmos DB)
- ⏳ Thread persistence (requires Responses API)

Full tool integration requires Azure infrastructure setup (knowledge bases, vector stores, Cosmos DB) that is beyond the scope of this MVP.

## Next Steps

### For Developers

1. **Use the new pattern** in new code:
   ```python
   await initialize_agents()
   agent = get_alert_triage_agent()
   ```

2. **Review YAML definitions** in `agents/` directory

3. **Add environment variables** for your Azure resources

4. **Run tests** to validate your setup

### For Production Deployment

1. **Set up Azure infrastructure**:
   - Azure AI Foundry project
   - Knowledge bases (Foundry IQ)
   - Vector stores for File Search
   - Cosmos DB for enterprise memory

2. **Configure project connections**:
   - MCP tool connections
   - Bing Grounding connections
   - A2A connections
   - Cosmos DB connections

3. **Deploy with proper secrets management**:
   - Use Azure Key Vault for secrets
   - Use Managed Identities for authentication
   - Configure RBAC appropriately

4. **Monitor and optimize**:
   - Enable Application Insights
   - Set up alerts for failures
   - Monitor agent performance
   - Tune model parameters

## Troubleshooting

### Agent initialization fails

**Problem**: `RuntimeError: Agent not initialized`

**Solution**: Call `initialize_agents()` before getting agent instances:
```python
await initialize_agents()
agent = get_alert_triage_agent()
```

### Environment variables not resolved

**Problem**: YAML contains `${VAR}` placeholders in output

**Solution**: Verify environment variables are set:
```bash
export AZURE_AI_PROJECT_ENDPOINT="your-endpoint"
echo $AZURE_AI_PROJECT_ENDPOINT  # Should print value
```

### YAML file not found

**Problem**: `FileNotFoundError` when loading agent

**Solution**: Verify YAML file exists:
```bash
ls agents/alert-triage-agent.yaml
```

Path should be relative to project root.

## References

- [Refactor Plan](./FOUNDRY-NATIVE-AGENTS-REFACTOR-PLAN.md) - Complete refactor strategy
- [Refactor Summary](./REFACTOR-SUMMARY.md) - Executive summary
- [Agent Configuration Guide](../agents/README.md) - YAML schema and examples
- [Microsoft Foundry Agents](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview) - Official documentation

## Support

For questions or issues:
1. Check the documentation in `docs/` and `agents/README.md`
2. Review test examples in `tests/unit/test_foundry_native_agent.py`
3. Open an issue on GitHub
4. Consult the Microsoft Foundry documentation

---

**Status**: MVP Implementation Complete ✅  
**Last Updated**: November 26, 2024  
**Version**: 1.0.0
