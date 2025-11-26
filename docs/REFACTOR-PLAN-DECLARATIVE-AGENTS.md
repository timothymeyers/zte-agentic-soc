# Refactoring Plan: Microsoft Foundry Declarative Agents

## Executive Summary

This document outlines a plan to refactor the current Agentic SOC MVP implementation from programmatic agent creation via the Microsoft Agent Framework (`agent-framework` library) to **declarative YAML-based agent definitions** with **native Microsoft Foundry Agent Service** capabilities.

The goal is to leverage:
1. **Declarative Agent YAML definitions** for agent configuration and deployment
2. **Native Microsoft Foundry tooling** (AI Search, Enterprise Memory, File Search)
3. **Persistent Foundry Agents** that are created once and reused across sessions
4. **Azure AI Projects SDK v2** (`azure-ai-projects>=2.0.0b2` + `azure-ai-agents`)

---

## Current State Analysis

### Current Implementation

The Alert Triage Agent (`src/agents/alert_triage_agent.py`) currently uses:

```python
# Current approach - Programmatic agent creation
from agent_framework import ChatAgent, ai_function
from agent_framework.azure import AzureAIAgentClient
from azure.ai.projects.aio import AIProjectClient

class AlertTriageAgent:
    async def _get_agent(self) -> ChatAgent:
        self._agent = ChatAgent(
            chat_client=AzureAIAgentClient(...),
            instructions=instructions,
            tools=[
                self.tools.calculate_risk_score,
                self.tools.find_correlated_alerts,
                self.tools.record_triage_decision,
                self.tools.get_mitre_context
            ]
        )
```

**Current Architecture:**
- Agent created programmatically at runtime
- Custom `@ai_function` decorated tools
- Azure AI Search integration via custom code
- In-memory correlation storage
- GPT-4.1-mini model via Azure AI Foundry

**Current Limitations:**
1. Agent recreated each time application starts
2. No persistent conversation history or memory
3. Custom AI Search integration (not native)
4. No declarative configuration (requires code changes)
5. Limited observability into agent decisions

---

## Target State: Microsoft Foundry Native Agents

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    agent.yaml (Declarative Definition)          │
│                                                                  │
│  name: alert-triage-agent                                        │
│  model: gpt-4o                                                   │
│  instructions: <system prompt>                                   │
│  tools:                                                          │
│    - type: azure_ai_search                                       │
│    - type: file_search                                           │
│    - type: function (custom)                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Microsoft Foundry Agent Service                     │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Persistent      │  │ Enterprise      │  │ Native Tools    │  │
│  │ Agent Instance  │  │ Memory Store    │  │ (AI Search,     │  │
│  │                 │  │                 │  │ File Search)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                              │                                   │
│              Conversation History & Context                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Python Application                            │
│                                                                  │
│  from azure.ai.projects import AIProjectClient                   │
│  from azure.ai.agents import PersistentAgentsClient              │
│                                                                  │
│  # Get existing agent (created via YAML or startup)              │
│  agent = agents_client.get_agent(agent_id)                       │
│                                                                  │
│  # Run with thread for conversation continuity                   │
│  response = agents_client.runs.create_and_process(               │
│      thread_id=thread.id,                                        │
│      agent_id=agent.id                                           │
│  )                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Benefits of Declarative Agents

| Aspect | Current (Programmatic) | Target (Declarative) |
|--------|------------------------|----------------------|
| **Configuration** | Python code | YAML files |
| **Agent Lifecycle** | Created per request | Persistent, reused |
| **Memory** | None | Enterprise Memory Store |
| **Knowledge Base** | Custom AI Search | Native File Search + AI Search |
| **Tools** | @ai_function decorators | Native + Function calling |
| **Observability** | Custom logging | Native tracing & App Insights |
| **Deployment** | Code changes | YAML updates + azd deploy |

---

## Detailed Refactoring Plan

### Phase 1: Dependencies and SDK Migration

**Objective:** Update to the latest Azure AI SDKs that support declarative agents

**Tasks:**

1. **Update `requirements.txt`**
   ```diff
   - agent-framework #>=0.1.0
   - agent-framework-azure-ai #>=0.1.0
   - azure-ai-projects>=1.0.0
   + azure-ai-projects>=2.0.0b2
   + azure-ai-agents>=1.0.0b1
   # Note: agent-framework-declarative is optional - YAML parsing can be done with PyYAML
   # Include if using the Microsoft Agent Framework's declarative loader
   ```

2. **Install Pre-release Packages**
   ```bash
   pip install --pre azure-ai-projects>=2.0.0b2
   pip install azure-ai-agents
   ```

3. **Update Authentication Pattern**
   - Continue using `DefaultAzureCredential` or `AzureCliCredential`
   - Ensure proper RBAC roles on Foundry project

**Estimated Effort:** 0.5 days

---

### Phase 2: Create Declarative Agent YAML Definitions

**Objective:** Define the Alert Triage Agent as a declarative YAML file

**Tasks:**

1. **Create Agent YAML Definition**

   Create file: `src/agents/definitions/alert_triage_agent.yaml`

   ```yaml
   # yaml-language-server: $schema=https://aka.ms/ai-foundry-vsc/agent/1.0.0
   version: 1.0.0
   name: alert-triage-agent
   description: AI-powered security alert triage agent for SOC operations
   
   metadata:
     authors:
       - security-operations@contoso.com
     tags:
       - security
       - soc
       - alert-triage
       - agentic-soc
   
   model:
     # Use gpt-4o or your preferred deployed model
     # Note: gpt-4.1-mini used in current implementation can be used if deployed
     # gpt-4o is recommended for improved reasoning in declarative agents
     id: gpt-4o
     options:
       temperature: 0.3
       top_p: 0.9
   
   instructions: |
     You are an autonomous security analyst agent specializing in alert triage and automated response.
     
     PRIMARY GOAL: Provide actionable remediation steps to enable automated response. 
     Avoid human escalation except for the most critical, ambiguous scenarios.
     
     Your role is to analyze security alerts, make intelligent triage decisions, 
     and prescribe specific next actions for automated systems or other agents to execute.
     
     Analysis Process:
     1. Search the MITRE ATT&CK knowledge base for technique context
     2. Check for correlated alerts to identify potential attack campaigns
     3. Calculate risk score using all available alert factors
     4. Synthesize all information to determine the appropriate triage decision
     5. Prescribe specific, actionable remediation steps
     
     Triage Decisions:
     - EscalateToIncident: High risk, multiple correlations, critical threat
     - CorrelateWithExisting: Moderate risk, needs monitoring
     - MarkAsFalsePositive: Clear benign activity, low risk
     - RequireHumanReview: Ambiguous, requires expert judgment (USE SPARINGLY)
   
   tools:
     # Native Azure AI Search for MITRE ATT&CK knowledge base
     - type: azure_ai_search
       name: mitre-attack-search
       config:
         index_name: attack-scenarios
         connection_id: ${AZURE_SEARCH_CONNECTION_ID}
     
     # File Search for attack documentation
     - type: file_search
       name: threat-intelligence
       config:
         vector_store_id: ${VECTOR_STORE_ID}
     
     # Custom function tools
     - type: function
       name: calculate_risk_score
       description: Calculate risk score for a security alert
       parameters:
         type: object
         properties:
           severity:
             type: string
             description: Alert severity (High, Medium, Low, Informational)
           entity_count:
             type: integer
             description: Number of entities involved
           mitre_techniques:
             type: array
             items:
               type: string
             description: MITRE ATT&CK technique IDs
           confidence_score:
             type: integer
             description: Detection confidence (0-100)
         required:
           - severity
           - entity_count
           - confidence_score
     
     - type: function
       name: find_correlated_alerts
       description: Find related alerts by entity overlap
       parameters:
         type: object
         properties:
           alert_entities:
             type: array
             items:
               type: object
               properties:
                 type:
                   type: string
                 value:
                   type: string
             description: Entities from the current alert
         required:
           - alert_entities
     
     - type: function
       name: record_triage_decision
       description: Record the final triage decision
       parameters:
         type: object
         properties:
           decision:
             type: string
             enum: [EscalateToIncident, CorrelateWithExisting, MarkAsFalsePositive, RequireHumanReview]
           priority:
             type: string
             enum: [Critical, High, Medium, Low]
           rationale:
             type: string
             description: Detailed explanation of decision logic
         required:
           - decision
           - priority
           - rationale
   ```

2. **Create Agent Schema Validation**
   - Use VS Code Microsoft Foundry extension for YAML validation
   - Validate against `https://aka.ms/ai-foundry-vsc/agent/1.0.0` schema

**Estimated Effort:** 1 day

---

### Phase 3: Implement Agent Initialization Service

**Objective:** Create a service that creates/retrieves persistent agents on startup

**Tasks:**

1. **Create Agent Manager Module**

   Create file: `src/agents/agent_manager.py`

   ```python
   """
   Agent Manager for Microsoft Foundry Declarative Agents.
   
   Handles agent lifecycle: creation, retrieval, and reuse of persistent agents.
   """
   
   import os
   import yaml
   from pathlib import Path
   from typing import Optional
   
   from azure.ai.projects import AIProjectClient
   from azure.ai.agents import PersistentAgentsClient
   from azure.ai.agents.models import (
       CreateAgentOptions,
       FileSearchToolDefinition,
       AzureAISearchToolDefinition,
       FunctionTool,
       PersistentAgent,
   )
   from azure.identity import DefaultAzureCredential
   
   from src.shared.logging import get_logger
   
   logger = get_logger(__name__)
   
   
   class AgentManager:
       """Manages persistent Foundry agents."""
       
       def __init__(
           self,
           project_endpoint: Optional[str] = None,
       ):
           self.project_endpoint = project_endpoint or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
           self._credential = DefaultAzureCredential()
           self._project_client = AIProjectClient(
               endpoint=self.project_endpoint,
               credential=self._credential
           )
           self._agents_client = PersistentAgentsClient(
               endpoint=self.project_endpoint,
               credential=self._credential
           )
           self._agents_cache: dict[str, PersistentAgent] = {}
       
       def load_agent_definition(self, yaml_path: str) -> dict:
           """Load agent definition from YAML file."""
           with open(yaml_path, 'r') as f:
               return yaml.safe_load(f)
       
       async def get_or_create_agent(
           self,
           agent_name: str,
           yaml_path: Optional[str] = None,
           force_create: bool = False
       ) -> PersistentAgent:
           """Get existing agent or create new one from YAML definition."""
           
           # Check cache first
           if agent_name in self._agents_cache and not force_create:
               logger.info(f"Using cached agent: {agent_name}")
               return self._agents_cache[agent_name]
           
           # Try to find existing agent by name
           if not force_create:
               existing = await self._find_agent_by_name(agent_name)
               if existing:
                   self._agents_cache[agent_name] = existing
                   logger.info(f"Found existing agent: {agent_name} (ID: {existing.id})")
                   return existing
           
           # Create new agent from YAML
           if not yaml_path:
               yaml_path = f"src/agents/definitions/{agent_name}.yaml"
           
           definition = self.load_agent_definition(yaml_path)
           agent = await self._create_agent_from_definition(definition)
           self._agents_cache[agent_name] = agent
           logger.info(f"Created new agent: {agent_name} (ID: {agent.id})")
           return agent
       
       async def _find_agent_by_name(self, name: str) -> Optional[PersistentAgent]:
           """Find existing agent by name."""
           try:
               agents = self._agents_client.administration.list_agents()
               for agent in agents:
                   if agent.name == name:
                       return agent
           except Exception as e:
               logger.warning(f"Could not list agents: {e}")
           return None
       
       async def _create_agent_from_definition(self, definition: dict) -> PersistentAgent:
           """Create agent from YAML definition."""
           tools = self._build_tools(definition.get('tools', []))
           
           options = CreateAgentOptions(
               model=definition['model']['id'],
               name=definition['name'],
               instructions=definition['instructions'],
               tools=tools,
               metadata={
                   'version': definition.get('version', '1.0.0'),
                   'description': definition.get('description', ''),
               }
           )
           
           return self._agents_client.administration.create_agent(options)
       
       def _build_tools(self, tool_definitions: list) -> list:
           """Build tool instances from YAML definitions."""
           tools = []
           for tool_def in tool_definitions:
               tool_type = tool_def.get('type')
               
               if tool_type == 'azure_ai_search':
                   tools.append(self._build_ai_search_tool(tool_def))
               elif tool_type == 'file_search':
                   tools.append(FileSearchToolDefinition())
               elif tool_type == 'function':
                   tools.append(self._build_function_tool(tool_def))
           
           return tools
       
       def _build_ai_search_tool(self, tool_def: dict) -> AzureAISearchToolDefinition:
           """Build Azure AI Search tool from definition."""
           config = tool_def.get('config', {})
           connection_id = os.path.expandvars(config.get('connection_id', ''))
           
           return AzureAISearchToolDefinition(
               index_name=config.get('index_name'),
               connection_id=connection_id
           )
       
       def _build_function_tool(self, tool_def: dict) -> dict:
           """Build function tool definition."""
           return {
               'type': 'function',
               'function': {
                   'name': tool_def['name'],
                   'description': tool_def['description'],
                   'parameters': tool_def['parameters']
               }
           }
       
       async def delete_agent(self, agent_id: str) -> None:
           """Delete a persistent agent."""
           await self._agents_client.administration.delete_agent(agent_id)
           # Clear from cache
           for name, agent in list(self._agents_cache.items()):
               if agent.id == agent_id:
                   del self._agents_cache[name]
   ```

2. **Create Startup Initialization Script**

   Create file: `utils/initialize_agents.py`

   ```python
   """
   Initialize Foundry Agents on application startup.
   
   This script creates or retrieves persistent agents defined in YAML files.
   Run once at demo startup or deployment to ensure agents are ready.
   """
   
   import asyncio
   from src.agents.agent_manager import AgentManager
   from src.shared.logging import configure_logging, get_logger
   
   logger = get_logger(__name__)
   
   
   async def initialize_agents():
       """Initialize all persistent agents for the Agentic SOC."""
       
       logger.info("Initializing Foundry Agents...")
       
       manager = AgentManager()
       
       # Initialize Alert Triage Agent
       triage_agent = await manager.get_or_create_agent(
           agent_name="alert-triage-agent",
           yaml_path="src/agents/definitions/alert_triage_agent.yaml"
       )
       logger.info(f"Alert Triage Agent ready: {triage_agent.id}")
       
       # Future: Initialize other agents
       # hunting_agent = await manager.get_or_create_agent("threat-hunting-agent")
       # response_agent = await manager.get_or_create_agent("incident-response-agent")
       
       return {
           "alert_triage": triage_agent,
       }
   
   
   if __name__ == "__main__":
       configure_logging(log_level="INFO")
       agents = asyncio.run(initialize_agents())
       print(f"Initialized {len(agents)} agents")
   ```

**Estimated Effort:** 2 days

---

### Phase 4: Integrate Enterprise Memory

**Objective:** Add native Microsoft Foundry Enterprise Memory for conversation continuity

**Tasks:**

1. **Create Memory Store**
   ```python
   from azure.ai.projects import AIProjectClient
   
   # Create memory store for the triage agent
   memory_store = project_client.memory_stores.create(
       name="soc-triage-memory",
       description="Memory store for alert triage agent",
       chat_model_deployment="gpt-4o",
       embedding_model_deployment="text-embedding-3-small"
   )
   ```

2. **Integrate Memory in Agent Runs**
   ```python
   # Add memories from conversation
   project_client.memory_stores.update_memories(
       name="soc-triage-memory",
       scope=f"user:{user_id}",
       content=[
           {"role": "user", "content": "Analyzed alert XYZ..."},
           {"role": "assistant", "content": "Decision: Escalate..."}
       ]
   )
   
   # Search memories before responding
   memories = project_client.memory_stores.search_memories(
       name="soc-triage-memory",
       scope=f"user:{user_id}",
       query="similar alerts from host WS-001"
   )
   ```

3. **Add Memory Configuration to Agent YAML**
   ```yaml
   memory:
     store_name: soc-triage-memory
     scope_prefix: soc-analyst
     profile_details: |
       Track alert patterns, escalation history, and analyst preferences.
       Avoid storing sensitive PII.
   ```

**Estimated Effort:** 1.5 days

---

### Phase 5: Native AI Search Integration

**Objective:** Replace custom AI Search code with native Foundry tool

**Tasks:**

1. **Configure Azure AI Search Connection in Foundry Portal**
   - Create connection to existing `attack-scenarios` index
   - Note connection ID for agent YAML

2. **Update Agent YAML with AI Search Tool**
   ```yaml
   tools:
     - type: azure_ai_search
       name: mitre-attack-knowledge
       config:
         connection_id: /subscriptions/{sub}/resourceGroups/{rg}/...
         index_name: attack-scenarios
         query_type: semantic  # or vector, hybrid
   ```

3. **Remove Custom AI Search Code**
   - Delete `get_mitre_context` tool implementation
   - Remove `_search_client_config` module-level state
   - Remove Azure Search SDK imports from agent

**Estimated Effort:** 1 day

---

### Phase 6: Refactor Alert Triage Agent

**Objective:** Update the agent class to use persistent Foundry agents

**Tasks:**

1. **Create New Agent Implementation**

   Create file: `src/agents/alert_triage_agent_v2.py`

   ```python
   """
   Alert Triage Agent v2 - Using Microsoft Foundry Persistent Agents.
   
   This agent uses declarative YAML definitions and native Foundry tools.
   """
   
   import asyncio
   import json
   import os
   import random
   import time
   from typing import Optional, Dict, Any, List
   from uuid import UUID, uuid4
   from datetime import datetime
   
   from azure.ai.projects import AIProjectClient
   from azure.ai.agents import PersistentAgentsClient
   from azure.ai.agents.models import (
       PersistentAgent,
       ThreadRun,
       MessageRole,
   )
   from azure.identity import DefaultAzureCredential
   
   from src.agents.agent_manager import AgentManager
   from src.shared.schemas import (
       SecurityAlert,
       TriageResult,
       TriagePriority,
       TriageDecision,
   )
   from src.shared.logging import get_logger
   from src.shared.audit import get_audit_service, AuditResult
   from src.shared.metrics import counter
   
   logger = get_logger(__name__)
   
   
   class AlertTriageAgentV2:
       """
       Alert Triage Agent using Microsoft Foundry Persistent Agents.
       
       Key differences from v1:
       - Uses persistent agent (created once, reused)
       - Native AI Search tool for MITRE context
       - Enterprise Memory for conversation history
       - Declarative YAML configuration
       """
       
       AGENT_NAME = "alert-triage-agent"
       AGENT_VERSION = "2.0.0"
       
       def __init__(
           self,
           project_endpoint: Optional[str] = None,
       ):
           self.project_endpoint = project_endpoint or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
           self._credential = DefaultAzureCredential()
           self._project_client = AIProjectClient(
               endpoint=self.project_endpoint,
               credential=self._credential
           )
           self._agents_client = PersistentAgentsClient(
               endpoint=self.project_endpoint,
               credential=self._credential
           )
           self._agent_manager = AgentManager(project_endpoint)
           self._agent: Optional[PersistentAgent] = None
           self.audit_service = get_audit_service()
       
       async def initialize(self) -> None:
           """Initialize the persistent agent."""
           self._agent = await self._agent_manager.get_or_create_agent(
               agent_name=self.AGENT_NAME,
               yaml_path="src/agents/definitions/alert_triage_agent.yaml"
           )
           logger.info(f"Agent initialized: {self._agent.id}")
       
       async def triage_alert(
           self,
           alert: SecurityAlert,
           thread_id: Optional[str] = None
       ) -> TriageResult:
           """
           Triage a security alert using the persistent Foundry agent.
           
           Args:
               alert: Security alert to triage
               thread_id: Optional thread ID for conversation continuity
           
           Returns:
               TriageResult with triage analysis
           """
           start_time = time.time()
           
           if not self._agent:
               await self.initialize()
           
           # Create or use existing thread
           if thread_id:
               thread = self._agents_client.threads.get(thread_id)
           else:
               thread = self._agents_client.threads.create()
           
           # Build triage query
           query = self._build_triage_query(alert)
           
           # Add message to thread
           self._agents_client.messages.create(
               thread_id=thread.id,
               role=MessageRole.USER,
               content=query
           )
           
           # Run the agent
           run = self._agents_client.runs.create_and_process(
               thread_id=thread.id,
               agent_id=self._agent.id,
               additional_instructions=self._get_alert_context(alert)
           )
           
           # Handle function calls if needed
           while run.status == "requires_action":
               run = await self._handle_function_calls(run, thread.id, alert)
           
           # Extract result from messages
           messages = self._agents_client.messages.list(thread_id=thread.id)
           triage_result = self._parse_agent_response(messages, alert, start_time)
           
           # Log to audit trail
           await self.audit_service.log_agent_action(
               agent_name=self.AGENT_NAME,
               action="TriagedAlert",
               target_entity_type="SecurityAlert",
               target_entity_id=str(alert.SystemAlertId),
               result=AuditResult.SUCCESS,
               details={
                   "risk_score": triage_result.RiskScore,
                   "decision": str(triage_result.TriageDecision),
                   "thread_id": thread.id,
                   "foundry_native": True
               }
           )
           
           counter("alerts_triaged_total").inc()
           
           return triage_result
       
       def _build_triage_query(self, alert: SecurityAlert) -> str:
           """Build the triage query for the agent."""
           entities_list = self._extract_entities(alert)
           mitre_techniques = alert.ExtendedProperties.get("MitreTechniques", [])
           
           return f"""Analyze this security alert and provide a triage decision:

   Alert Name: {alert.AlertName}
   Alert Type: {alert.AlertType}
   Severity: {alert.Severity}
   Description: {alert.Description}
   MITRE Techniques: {', '.join(mitre_techniques) if mitre_techniques else 'None'}
   Confidence Score: {alert.ExtendedProperties.get('ConfidenceScore', 75)}%

   Entities involved:
   {chr(10).join([f"- {e['type']}: {e['value']}" for e in entities_list])}

   Use your tools to:
   1. Search the MITRE ATT&CK knowledge base for technique context
   2. Calculate the risk score
   3. Make and record your triage decision with remediation steps"""
       
       def _extract_entities(self, alert: SecurityAlert) -> List[Dict[str, str]]:
           """Extract entities from alert."""
           entities = []
           for entity in alert.Entities:
               if "HostName" in entity.Properties:
                   entities.append({"type": "host", "value": entity.Properties["HostName"]})
               if "UserName" in entity.Properties:
                   entities.append({"type": "user", "value": entity.Properties["UserName"]})
               if "IPAddress" in entity.Properties:
                   entities.append({"type": "ip", "value": entity.Properties["IPAddress"]})
           return entities
       
       async def _handle_function_calls(
           self,
           run: ThreadRun,
           thread_id: str,
           alert: SecurityAlert
       ) -> ThreadRun:
           """Handle function calls from the agent."""
           tool_calls = run.required_action.submit_tool_outputs.tool_calls
           tool_outputs = []
           
           for call in tool_calls:
               func_name = call.function.name
               args = json.loads(call.function.arguments)
               
               if func_name == "calculate_risk_score":
                   output = self._calculate_risk_score(**args)
               elif func_name == "find_correlated_alerts":
                   output = self._find_correlated_alerts(**args)
               elif func_name == "record_triage_decision":
                   output = json.dumps(args)  # Just echo back the decision
               else:
                   output = json.dumps({"error": f"Unknown function: {func_name}"})
               
               tool_outputs.append({
                   "tool_call_id": call.id,
                   "output": output
               })
           
           # Submit outputs
           self._agents_client.runs.submit_tool_outputs(
               thread_id=thread_id,
               run_id=run.id,
               tool_outputs=tool_outputs
           )
           
           # Continue processing
           return self._agents_client.runs.get(thread_id=thread_id, run_id=run.id)
       
       def _calculate_risk_score(
           self,
           severity: str,
           entity_count: int,
           mitre_techniques: List[str] = None,
           confidence_score: int = 75
       ) -> str:
           """Calculate risk score (same logic as v1)."""
           # Note: random is imported at module level
           
           score = 0
           severity_scores = {"High": 30, "Medium": 20, "Low": 10, "Informational": 5}
           score += severity_scores.get(severity, 10)
           score += min(entity_count * 2, 10)
           score += min(len(mitre_techniques or []) * 5, 25)
           score += random.randint(5, 20)  # Asset criticality placeholder
           score += random.randint(2, 10)  # User risk placeholder
           score += int(confidence_score / 10)
           
           return json.dumps({
               "risk_score": min(score, 100),
               "explanation": f"Risk score of {min(score, 100)}/100"
           })
       
       def _find_correlated_alerts(self, alert_entities: List[Dict]) -> str:
           """Find correlated alerts (placeholder for v2)."""
           # TODO: Query Enterprise Memory or database for correlations
           return json.dumps({
               "correlated_count": 0,
               "has_correlation": False,
               "note": "Use Enterprise Memory for correlation in production"
           })
       
       def _parse_agent_response(
           self,
           messages,
           alert: SecurityAlert,
           start_time: float
       ) -> TriageResult:
           """Parse agent response into TriageResult."""
           # Get last assistant message
           response_text = ""
           for msg in messages:
               if msg.role == "assistant":
                   for content in msg.content:
                       if hasattr(content, 'text'):
                           response_text = content.text.value
           
           # Parse decision from response
           decision = TriageDecision.REQUIRE_HUMAN_REVIEW
           priority = TriagePriority.MEDIUM
           risk_score = 50
           
           response_lower = response_text.lower()
           if "escalate" in response_lower and "incident" in response_lower:
               decision = TriageDecision.ESCALATE_TO_INCIDENT
               priority = TriagePriority.HIGH
           elif "correlate" in response_lower:
               decision = TriageDecision.CORRELATE_WITH_EXISTING
               priority = TriagePriority.MEDIUM
           elif "false positive" in response_lower:
               decision = TriageDecision.MARK_AS_FALSE_POSITIVE
               priority = TriagePriority.LOW
           
           return TriageResult(
               AlertId=alert.SystemAlertId,
               TriageId=uuid4(),
               Timestamp=datetime.utcnow(),
               RiskScore=risk_score,
               Priority=priority,
               TriageDecision=decision,
               Explanation=response_text,
               CorrelatedAlertIds=[],
               EnrichmentData={},
               ProcessingTimeMs=int((time.time() - start_time) * 1000),
               AgentVersion=self.AGENT_VERSION
           )
       
       async def close(self) -> None:
           """Clean up resources."""
           await self._credential.close()
   ```

**Estimated Effort:** 2 days

---

### Phase 7: Update Demo and Testing

**Objective:** Update demo script and tests for the new implementation

**Tasks:**

1. **Create New Demo Script**
   ```bash
   # utils/demo_foundry_agents.py
   - Load persistent agent
   - Process sample alerts
   - Show Enterprise Memory integration
   ```

2. **Update Tests**
   - Add tests for AgentManager
   - Add tests for YAML loading
   - Mock Foundry SDK calls

3. **Update README.md**
   - Document new architecture
   - Add setup instructions for Foundry
   - Update environment variables

**Estimated Effort:** 1.5 days

---

## Implementation Timeline

| Phase | Description | Duration | Dependencies |
|-------|-------------|----------|--------------|
| 1 | Dependencies & SDK Migration | 0.5 days | None |
| 2 | Declarative Agent YAML | 1 day | Phase 1 |
| 3 | Agent Initialization Service | 2 days | Phase 2 |
| 4 | Enterprise Memory Integration | 1.5 days | Phase 3 |
| 5 | Native AI Search Integration | 1 day | Phase 3 |
| 6 | Refactor Alert Triage Agent | 2 days | Phases 4, 5 |
| 7 | Demo & Testing Updates | 1.5 days | Phase 6 |

**Total Estimated Effort: ~9.5 days**

---

## Environment Setup Requirements

### Required Environment Variables

```bash
# Azure AI Foundry Project
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/your-project-id"

# Model Deployment
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o"

# AI Search Connection ID (from Foundry portal -> Connected Resources -> AI Search)
# Full format: /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.CognitiveServices/accounts/{ai-services-name}/projects/{project-name}/connections/{connection-name}
export AZURE_SEARCH_CONNECTION_ID="/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.CognitiveServices/accounts/{ai-services-name}/projects/{project-name}/connections/{your-search-connection-name}"

# Optional: Memory Store
export MEMORY_STORE_NAME="soc-triage-memory"
```

### Azure RBAC Requirements

| Role | Scope | Purpose |
|------|-------|---------|
| Azure AI User | Foundry Project | Agent operations |
| Azure AI Developer | Foundry Project | Create/delete agents |
| Storage Blob Data Contributor | Storage Account | File uploads |

---

## Backward Compatibility

### Migration Path

1. **Parallel Running**: Run v1 and v2 agents side-by-side initially
2. **Feature Flag**: Use environment variable to switch between versions
3. **Deprecation**: Mark v1 agent as deprecated after validation
4. **Removal**: Remove v1 code after full migration

### Breaking Changes

1. **Tool Signatures**: Function tool signatures may change
2. **Response Format**: Agent responses will include thread context
3. **Dependencies**: Requires newer SDK versions

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| SDK in preview (`2.0.0b2`) | Pin versions, test thoroughly |
| YAML schema changes | Use schema validation, version pin |
| Foundry service availability | Implement fallback to v1 agent |
| Performance differences | Benchmark both versions |

---

## Success Criteria

1. ✅ Alert Triage Agent defined in YAML
2. ✅ Agent persisted in Foundry (not recreated)
3. ✅ Native AI Search tool for MITRE context
4. ✅ Enterprise Memory for conversation history
5. ✅ Demo runs successfully with new architecture
6. ✅ All existing tests pass
7. ✅ Documentation updated

---

## Appendix: Reference Links

- [Microsoft Foundry Agent Service Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview)
- [Declarative Agents in VS Code](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/vs-code-agents)
- [Foundry Agent Memory](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/agent-memory)
- [Azure AI Projects SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Foundry Samples](https://github.com/azure-ai-foundry/foundry-samples)
- [AgentSchema](https://github.com/microsoft/AgentSchema)
