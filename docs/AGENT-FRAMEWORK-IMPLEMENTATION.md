# Alert Triage Agent - Microsoft Agent Framework Implementation

## Overview

The Alert Triage Agent has been completely refactored to use the **Microsoft Agent Framework** and **Azure AI Foundry SDK**, replacing the custom implementation with proper framework integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Alert Triage Agent                        │
│          (Microsoft Agent Framework Integration)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      ChatAgent                               │
│               (agent-framework library)                      │
│                                                              │
│  • Manages conversation flow                                 │
│  • Routes to appropriate tools                               │
│  • Generates natural language responses                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Custom AI Function Tools                    │
│                (@ai_function decorators)                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ calculate_risk_score                               │     │
│  │ - Multi-factor risk calculation                    │     │
│  │ - Returns: risk_score, breakdown, explanation      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ find_correlated_alerts                             │     │
│  │ - Entity-based correlation detection               │     │
│  │ - Returns: correlated_alerts, shared_entities      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ make_triage_decision                               │     │
│  │ - Decision logic based on risk + correlation       │     │
│  │ - Returns: decision, priority, rationale           │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ get_mitre_context                                  │     │
│  │ - MITRE ATT&CK technique enrichment                │     │
│  │ - Returns: technique details from Attack dataset   │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Azure AI Foundry / OpenAI                      │
│                                                              │
│  • AzureAIAgentClient (when endpoint configured)            │
│  • OpenAIChatClient (fallback for local testing)            │
│  • Model: GPT-4.1-mini-mini or other deployed model               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Structured Output                         │
│                                                              │
│  TriageResult:                                               │
│    • risk_score: int (0-100)                                 │
│    • priority: TriagePriority enum                           │
│    • decision: TriageDecision enum                           │
│    • explanation: str (AI-generated)                         │
│    • correlated_alert_ids: List[UUID]                        │
│    • enrichment_data: Dict[str, Any]                         │
│    • processing_time_ms: int                                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Improvements

### 1. **Microsoft Agent Framework Integration**

**Before (Custom Implementation):**
```python
class AlertTriageAgent:
    def __init__(self):
        # Custom agent implementation
        self.agent_version = "0.1.0"
    
    async def triage_alert(self, alert):
        # Manual implementation of all logic
        risk_score = self._calculate_risk_score(alert)
        correlated = self._correlate_alerts(alert)
        decision = self._make_decision(risk_score, correlated)
        # ...
```

**After (Agent Framework):**
```python
from agent_framework import ChatAgent, ai_function
from agent_framework.azure import AzureAIAgentClient

class AlertTriageAgent:
    def __init__(self):
        self._agent = ChatAgent(
            chat_client=AzureAIAgentClient(...),
            instructions="You are an expert security analyst...",
            tools=[
                self.tools.calculate_risk_score,
                self.tools.find_correlated_alerts,
                self.tools.make_triage_decision,
                self.tools.get_mitre_context
            ]
        )
    
    async def triage_alert(self, alert):
        # Let the AI agent orchestrate tool calls
        response = await self._agent.run(query)
        # AI generates natural language explanation
        return triage_result
```

### 2. **AI Function Tools with @ai_function Decorator**

**Tool Definition:**
```python
@ai_function(description="Calculate risk score for a security alert")
async def calculate_risk_score(
    self,
    severity: Annotated[str, Field(description="Alert severity level")],
    entity_count: Annotated[int, Field(description="Number of entities")],
    mitre_techniques: Annotated[List[str], Field(description="MITRE technique IDs")],
    confidence_score: Annotated[int, Field(description="Detection confidence")]
) -> str:
    """Calculate a risk score and return JSON with score and explanation."""
    # Tool implementation
    return str(result)
```

**Benefits:**
- AI decides when to call tools
- Type annotations provide context to AI
- Field descriptions guide AI usage
- Tools are composable and reusable
- Standard pattern across Microsoft ecosystem

### 3. **Azure AI Foundry SDK Integration**

**Client Setup:**
```python
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential

# Initialize project client
self._credential = AzureCliCredential()
self._project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=self._credential
)

# Create agent with Azure AI
self._agent = ChatAgent(
    chat_client=AzureAIAgentClient(
        project_client=self._project_client,
        async_credential=self._credential,
        model_deployment_name=model_deployment_name,
        agent_name="AlertTriageAgent"
    ),
    instructions=instructions,
    tools=tools
)
```

**Benefits:**
- Proper authentication with Azure credentials
- Managed AI model deployments
- Enterprise-grade security
- Integrated logging and monitoring
- Cost tracking and quotas

### 4. **Natural Language Agent Instructions**

```python
instructions = """You are an expert security analyst specializing in alert triage.

Your role is to analyze security alerts and make intelligent triage decisions by:
1. Calculating risk scores based on multiple factors
2. Finding correlated alerts to detect campaigns
3. Making triage decisions with clear rationales
4. Providing actionable recommendations

Always use the provided tools to analyze alerts systematically."""
```

**Benefits:**
- AI understands its role and responsibilities
- Clear guidance on tool usage
- Flexible - can be updated without code changes
- Enables sophisticated reasoning

## Usage

### Setup Environment Variables

```bash
# Required for Azure AI Foundry integration
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/project-id"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"

# Authenticate with Azure
az login
```

### Run the Demo

```bash
# With Azure AI Foundry (recommended)
python utils/demo_agent_framework.py

# Without Azure AI Foundry (uses OpenAI fallback)
# Just run without setting environment variables
python utils/demo_agent_framework.py
```

### Programmatic Usage

```python
from src.agents.alert_triage.agent_framework import get_triage_agent
from src.shared.schemas import SecurityAlert

# Initialize agent
agent = get_triage_agent(
    project_endpoint="https://...",
    model_deployment_name="gpt-4.1-mini"
)

# Triage an alert
alert = SecurityAlert(...)
result = await agent.triage_alert(alert)

print(f"Risk Score: {result.RiskScore}")
print(f"Decision: {result.TriageDecision}")
print(f"Explanation: {result.Explanation}")

# Clean up
await agent.close()
```

## Tool Details

### calculate_risk_score

**Purpose:** Calculate a comprehensive risk score (0-100) based on multiple factors.

**Inputs:**
- `severity`: Alert severity level
- `entity_count`: Number of entities involved
- `mitre_techniques`: List of MITRE ATT&CK techniques
- `confidence_score`: Detection confidence (0-100)

**Output:** JSON string with risk score, breakdown, and explanation.

**Example:**
```json
{
  "risk_score": 75,
  "breakdown": {
    "severity": 30,
    "entities": 6,
    "mitre_techniques": 15,
    "asset_criticality": 15,
    "user_risk": 5,
    "confidence": 8
  },
  "explanation": "Risk score of 75/100 calculated from High severity, 3 entities, 3 MITRE techniques, and 85% confidence."
}
```

### find_correlated_alerts

**Purpose:** Find related alerts by checking entity overlap.

**Inputs:**
- `alert_entities`: List of entities from current alert

**Output:** JSON string with correlated alerts and overlap details.

**Example:**
```json
{
  "correlated_count": 2,
  "correlated_alerts": [
    {
      "alert_id": "uuid-1",
      "alert_name": "Suspicious PowerShell",
      "shared_entities": ["host:WS-001", "user:jdoe"]
    }
  ],
  "has_correlation": true
}
```

### make_triage_decision

**Purpose:** Determine triage decision based on risk and correlation.

**Inputs:**
- `risk_score`: Calculated risk score (0-100)
- `has_correlation`: Whether alert correlates with others

**Output:** JSON string with decision, priority, and rationale.

**Example:**
```json
{
  "decision": "EscalateToIncident",
  "priority": "High",
  "rationale": "High risk score indicates potential significant threat requiring immediate incident response."
}
```

### get_mitre_context

**Purpose:** Retrieve MITRE ATT&CK technique details.

**Inputs:**
- `technique_ids`: List of MITRE technique IDs

**Output:** JSON string with technique information from Attack dataset.

## Comparison: Before vs After

| Aspect | Before (Custom) | After (Agent Framework) |
|--------|----------------|------------------------|
| **Architecture** | Custom implementation | Microsoft Agent Framework |
| **AI Integration** | None (rule-based) | GPT-4.1-mini via Azure AI Foundry |
| **Tool Pattern** | Manual methods | @ai_function decorators |
| **Decision Making** | Hardcoded logic | AI-powered reasoning |
| **Explanations** | Template strings | Natural language generation |
| **Extensibility** | Requires code changes | Add new @ai_function tools |
| **Testing** | Mock all components | Use OpenAI fallback |
| **Enterprise Ready** | Basic | Azure AD auth, managed deployments |

## Benefits of New Implementation

1. **AI-Powered Analysis**: Real AI reasoning instead of hardcoded rules
2. **Framework Best Practices**: Using Microsoft's official patterns
3. **Natural Language**: AI generates human-readable explanations
4. **Extensible**: Easy to add new tools without changing core logic
5. **Testable**: Can run with OpenAI fallback without Azure
6. **Enterprise Ready**: Proper Azure integration with security and monitoring
7. **Future-Proof**: Compatible with Microsoft's agent ecosystem

## Next Steps

1. **Deploy to Azure**: Set up Azure AI Foundry project and deploy model
2. **Add More Tools**: Create additional @ai_function tools for:
   - Threat intelligence lookups
   - User risk assessment
   - Asset criticality checks
3. **Enable Streaming**: Use streaming responses for real-time feedback
4. **Add Code Interpreter**: Enable code execution for complex analysis
5. **File Search Integration**: Add vector search for historical incidents

## Files

- `src/agents/alert_triage/agent_framework.py` - New agent implementation
- `utils/demo_agent_framework.py` - Demo script with framework
- `src/agents/alert_triage/agent.py` - Old custom implementation (deprecated)
- `utils/demo_alert_triage.py` - Old demo script (deprecated)

## References

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/)
- [Azure AI Projects SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
