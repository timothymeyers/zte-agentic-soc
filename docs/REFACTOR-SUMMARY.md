# Foundry Native Agents Refactor - Implementation Summary

**Date**: November 25, 2024  
**Status**: Analysis Complete - Ready for Review  
**Goal**: Migrate from programmatic agent creation to declarative YAML-based Foundry native agents

---

## Quick Links

- **📋 Full Refactor Plan**: [docs/FOUNDRY-NATIVE-AGENTS-REFACTOR-PLAN.md](./FOUNDRY-NATIVE-AGENTS-REFACTOR-PLAN.md)
- **🤖 Agent Definitions**: [agents/](../agents/)
- **📖 Agent Configuration Guide**: [agents/README.md](../agents/README.md)
- **🔧 Example YAML**: [agents/alert-triage-agent.yaml](../agents/alert-triage-agent.yaml)

---

## Executive Summary

This refactor plan outlines migration from the current Microsoft Agent Framework implementation (programmatic, custom tools) to **Microsoft Foundry native agents** (declarative YAML, native tools).

### Current State
```python
# Create agent programmatically on every run
agent = ChatAgent(
    chat_client=AzureAIAgentClient(...),
    instructions="...",  # Hardcoded
    tools=[
        calculate_risk_score,      # Custom @ai_function
        find_correlated_alerts,    # Custom @ai_function
        get_mitre_context          # Custom AI Search query
    ]
)
```

### Target State
```yaml
# Define agent in YAML (version controlled)
name: alert-triage-agent
model:
  id: 'gpt-4.1-mini'
instructions: |
  You are an autonomous security analyst...
tools:
  - type: mcp              # Foundry IQ knowledge base
  - type: code_interpreter # Native Python execution
  - type: file_search      # Historical incident RAG
  - type: bing_grounding   # Real-time threat intel
memory:
  enabled: true            # Enterprise memory (Cosmos DB)
```

---

## Key Changes

### 1. Agent Definition
- **FROM**: Code-based agent creation
- **TO**: YAML declarative definitions
- **BENEFIT**: Version control, no code changes needed

### 2. Agent Lifecycle
- **FROM**: Create agent on every request
- **TO**: Create once at startup, reuse forever
- **BENEFIT**: Efficiency, resource optimization

### 3. Knowledge Integration
- **FROM**: Custom AI Search queries in @ai_function
- **TO**: MCP tool with Foundry IQ knowledge bases
- **BENEFIT**: Semantic search, query planning, automatic citations

### 4. Tool Ecosystem
- **FROM**: Custom @ai_function tools for everything
- **TO**: Native Foundry tools (Code Interpreter, File Search, Bing, A2A)
- **BENEFIT**: No custom code, richer capabilities

### 5. Memory Management
- **FROM**: In-memory lists (lost on restart)
- **TO**: Enterprise memory backed by Cosmos DB
- **BENEFIT**: Persistent across sessions, never lose context

---

## Tool Migration Map

| Current Custom Tool | Native Foundry Tool | Why |
|---------------------|---------------------|-----|
| `get_mitre_context` | MCP Tool (Knowledge Base) | Semantic search, citations, query planning |
| `calculate_risk_score` | Code Interpreter | Flexible Python execution, agent-generated logic |
| `find_correlated_alerts` | File Search + Memory | RAG over historical alerts, persistent state |
| `record_triage_decision` | (Not needed) | Agent naturally records in thread |

---

## Implementation Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1: Infrastructure** | 1-2 weeks | Set up knowledge bases, enterprise memory, connections |
| **Phase 2: Agent Definitions** | 1 week | Create YAML definitions, wrapper class |
| **Phase 3: Lifecycle Management** | 1 week | Startup initialization, thread persistence |
| **Phase 4: Testing & Docs** | 1 week | Integration tests, validation, documentation |

**Total**: 4-5 weeks

---

## Architecture Comparison

### Current Architecture
```
Alert → Create New Agent → Custom Tools (@ai_function) → Azure AI Foundry → Response
                ↓
           (Agent discarded)
```

### Target Architecture
```
Startup → Create Persistent Agent (from YAML)
                ↓
Alert → Reuse Agent → Native Foundry Tools → Knowledge Bases → Response
                          ↓                       ↓
                   Code Interpreter        Foundry IQ (MCP)
                   File Search             Enterprise Memory
                   Bing Grounding          (Cosmos DB)
                   Agent-to-Agent (A2A)
```

---

## Example: Before vs After

### Before (Programmatic)
```python
# src/agents/alert_triage_agent.py

@ai_function(description="Get MITRE context")
def get_mitre_context(technique_ids: List[str]) -> str:
    # Manual AI Search query construction
    search_client = SearchClient(endpoint=..., index="attack-scenarios")
    results = await search_client.search(
        search_text=technique_ids[0],
        filter="",
        top=3
    )
    # Manual result parsing
    return json.dumps(results)

# Create agent programmatically
agent = ChatAgent(
    chat_client=AzureAIAgentClient(...),
    instructions="You are a security analyst...",
    tools=[get_mitre_context, calculate_risk_score, ...]
)
```

### After (Declarative)
```yaml
# agents/alert-triage-agent.yaml

name: alert-triage-agent
instructions: |
  You are an autonomous security analyst...
  Use the knowledge base tool to retrieve MITRE context.

tools:
  - type: mcp
    mcp:
      server_label: "attack-scenarios-kb"
      server_url: "${AZURE_SEARCH_ENDPOINT}/knowledgebases/attack-scenarios-kb/mcp"
      allowed_tools:
        - knowledge_base_retrieve
      description: >-
        Knowledge base with 14K+ MITRE attack scenarios
```

```python
# src/agents/__init__.py

async def initialize_agents():
    """Initialize agents once at startup from YAML."""
    agent = FoundryNativeAgent('agents/alert-triage-agent.yaml')
    await agent.initialize()
    return agent

# Reuse agent for all alerts
agent = get_alert_triage_agent()
for alert in alerts:
    result = await agent.run(query=build_query(alert))
```

---

## Benefits Summary

### For Development
- ✅ No custom tool code to maintain
- ✅ Agent behavior changes without code deployment
- ✅ Version control for agent definitions
- ✅ Easier testing and validation

### For Operations
- ✅ Managed agent lifecycle
- ✅ Built-in scaling and reliability
- ✅ Native monitoring and logging
- ✅ Role-based access control

### For Features
- ✅ Richer knowledge integration (semantic search, citations)
- ✅ Persistent memory across sessions
- ✅ Real-time threat intelligence (Bing)
- ✅ Agent-to-agent communication (A2A)

---

## Required Setup

### Environment Variables
```bash
# Foundry Project
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/..."
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"

# Knowledge Base
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export PROJECT_CONNECTION_ID="/subscriptions/.../connections/attack-kb"

# Memory
export COSMOS_PROJECT_CONNECTION_ID="/subscriptions/.../connections/cosmos"

# Tools
export BING_PROJECT_CONNECTION_ID="/subscriptions/.../connections/bing"
export A2A_PROJECT_CONNECTION_ID="/subscriptions/.../connections/a2a"

# Vector Stores
export HISTORICAL_INCIDENTS_VECTOR_STORE_ID="vs-12345..."
```

### Dependencies
```txt
# requirements.txt
azure-ai-projects>=2.0.0b1   # NEW: Latest preview
azure-identity>=1.15.0
azure-search-documents>=11.4.0
azure-cosmos>=4.5.0
pyyaml>=6.0                   # NEW: For YAML parsing
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking changes in preview SDK | Pin to specific version, monitor releases |
| Knowledge base setup complexity | Detailed scripts and documentation |
| Agent behavior changes | Comprehensive testing, gradual rollout |
| Performance degradation | Benchmark before/after |
| Team learning curve | Training, detailed docs |

**Rollback Strategy**: Keep old implementation temporarily, feature flag toggle

---

## Success Criteria

### Functional
- [ ] Agents defined in YAML files
- [ ] Agents created once at startup, reused
- [ ] MCP tool queries knowledge base successfully
- [ ] Code Interpreter executes risk calculations
- [ ] File Search retrieves historical alerts
- [ ] Enterprise memory persists across sessions
- [ ] Triage decisions include remediation steps

### Performance
- [ ] Agent initialization < 5 seconds
- [ ] Triage response < 30 seconds
- [ ] Knowledge base query < 5 seconds
- [ ] Memory persistence 100% reliable

### Quality
- [ ] All integration tests passing
- [ ] Documentation complete
- [ ] Code review approved

---

## Future Agents

The same pattern extends to other agents:

### Threat Hunting Agent
```yaml
name: threat-hunting-agent
model:
  id: 'gpt-4o'  # More capable model
tools:
  - type: mcp              # Historical incidents KB
  - type: code_interpreter # Complex analytics
  - type: bing_grounding   # Emerging threats
```

### Incident Response Agent
```yaml
name: incident-response-agent
model:
  id: 'gpt-4o'
tools:
  - type: a2a              # Coordinate with other agents
  - type: azure_functions  # Execute response actions
  - type: mcp              # Playbook knowledge base
```

### Threat Intelligence Agent
```yaml
name: threat-intel-agent
model:
  id: 'gpt-4.1-mini'
tools:
  - type: bing_grounding  # Real-time feeds
  - type: mcp             # Threat intel KB
  - type: file_search     # Historical reports
```

---

## Next Steps

1. **Review**: Present this plan to stakeholders for approval
2. **Validate**: Confirm approach with Microsoft Foundry team
3. **Setup**: Create development environment (Foundry project, knowledge bases)
4. **Implement**: Begin Phase 1 (infrastructure setup)
5. **Test**: Build integration tests as we migrate
6. **Document**: Keep documentation up to date
7. **Deploy**: Gradual rollout with monitoring

---

## Questions to Resolve

1. **Knowledge Base**: Which Azure region supports Foundry IQ? (Check regional availability)
2. **Pricing**: What's the cost impact of enterprise memory (Cosmos DB)?
3. **Limits**: What are the rate limits for MCP tool calls?
4. **Migration**: Should we migrate all 4 agents at once or one at a time?
5. **Testing**: How do we test agents in preview (staging environment)?

---

## References

### Microsoft Documentation
- [Azure AI Foundry Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview)
- [Declarative Agent Definitions](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-types/azure-ai-agent#declarative-spec)
- [Foundry IQ Knowledge Bases](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/knowledge-retrieval)
- [Enterprise Memory](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/agent-memory)
- [Azure AI Projects SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)

### Code Examples
- [Azure AI Projects Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples)
- [Foundry Samples](https://github.com/azure-ai-foundry/foundry-samples)
- [Agentic Retrieval Example](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-foundry/samples/agentic-retrieval-pipeline-example)

### Project Documentation
- [Full Refactor Plan](./FOUNDRY-NATIVE-AGENTS-REFACTOR-PLAN.md)
- [Agent Configuration Guide](../agents/README.md)
- [Current Implementation Guide](./AGENT-FRAMEWORK-IMPLEMENTATION.md)

---

**Document Version**: 1.0  
**Last Updated**: November 25, 2024  
**Status**: Ready for Review
