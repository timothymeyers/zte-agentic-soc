# Refactoring Plan: Declarative Agents with Microsoft Agent Framework

## Executive Summary

This document outlines a plan to refactor the current Agentic SOC MVP implementation from programmatic agent creation to **declarative YAML-based agent definitions** using the **Microsoft Agent Framework's `agent-framework-declarative` package**.

The goal is to leverage:
1. **`agent-framework-declarative --pre`** for YAML-based agent definitions
2. **Declarative workflow patterns** from [Microsoft Agent Framework samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/declarative)
3. **Persistent agent instances** created at startup and reused throughout the demo session
4. **Native Microsoft Foundry tooling** (AI Search integration, Enterprise Memory) via `azure-ai-projects>=2.0.0b2`

### Key Reference

- **Declarative examples**: https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/declarative
- **Workflow samples**: https://github.com/microsoft/agent-framework/tree/main/workflow-samples

---

## Current State Analysis

### Current Implementation

The Alert Triage Agent (`src/agents/alert_triage_agent.py`) currently uses:

```python
# Current approach - Programmatic agent creation
from agent_framework import ChatAgent, ai_function
from agent_framework.azure import AzureAIAgentClient

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

**Current Limitations:**
1. Agent recreated each time application starts
2. No declarative configuration (requires code changes to modify behavior)
3. Tools tightly coupled with agent definition
4. Difficult to test agent logic without full execution

---

## Target State: Declarative Agents

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           alert_triage_workflow.yaml (Declarative)              │
│                                                                  │
│  agents:                                                         │
│    - name: triage_agent                                          │
│      instructions: <system prompt>                               │
│      tools: [calculate_risk_score, find_correlated_alerts, ...] │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              DeclarativeAgentLoader                              │
│         (agent-framework-declarative)                            │
│                                                                  │
│  • Loads agents from YAML                                        │
│  • Binds tool implementations                                    │
│  • Creates workflow if defined                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ChatAgent (in-memory)                         │
│                                                                  │
│  • Persistent for demo session                                   │
│  • Uses AzureOpenAIChatClient                                    │
│  • Tools: @ai_function decorated                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Optional: Microsoft Foundry Integration             │
│                                                                  │
│  • Enterprise Memory (azure-ai-projects>=2.0.0b2)                │
│  • AI Search for MITRE knowledge base                            │
│  • Agent persistence in Foundry                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Benefits of Declarative Agents

| Aspect | Current (Programmatic) | Target (Declarative) |
|--------|------------------------|----------------------|
| **Configuration** | Python code | YAML files |
| **Agent Lifecycle** | Created at runtime | Loaded at startup, reused |
| **Testing** | Full execution required | Dry-run mode available |
| **Tool Binding** | Hardcoded in class | Dynamic from YAML |
| **Deployment** | Code changes | YAML updates |
| **Experimentation** | Requires code changes | Edit YAML, reload |

---

## Detailed Refactoring Plan

### Phase 1: Add Declarative Dependencies

**Objective:** Install `agent-framework-declarative` and update dependencies

**Tasks:**

1. **Update `requirements.txt`**
   ```diff
    # Keep current agent-framework packages
    agent-framework #>=0.1.0
    agent-framework-azure-ai #>=0.1.0
   + # Add declarative support
   + agent-framework-declarative --pre
   + 
   + # Add Foundry SDK for native features
   + azure-ai-projects>=2.0.0b2
   + azure-ai-agents>=1.0.0b1
   ```

2. **Install Packages**
   ```bash
   # Install full agent-framework suite with declarative support
   pip install agent-framework --pre
   
   # Or install specific packages
   pip install agent-framework-declarative --pre
   pip install --pre azure-ai-projects>=2.0.0b2
   pip install azure-ai-agents>=1.0.0b1
   ```

3. **Verify Installation**
   ```bash
   python -c "from agent_framework.declarative import load_workflow; print('✓ Declarative support installed')"
   ```

**Estimated Effort:** 0.5 days

**Deliverables:**
- Updated `requirements.txt`
- Verified package installation

---

### Phase 2: Create Declarative YAML Definitions

**Objective:** Define Alert Triage Agent as a declarative YAML workflow

**Reference:** 
- https://github.com/microsoft/agent-framework/tree/main/workflow-samples
- Examples: `CustomerSupport.yaml`, `Marketing.yaml`, `MathChat.yaml`

**Tasks:**

1. **Create Main Workflow YAML**

   Create file: `src/agents/definitions/alert_triage_workflow.yaml`

   ```yaml
   # Alert Triage Workflow - Declarative Definition
   # Based on Microsoft Agent Framework workflow samples
   
   name: AlertTriageWorkflow
   description: AI-powered security alert triage workflow for SOC operations
   
   agents:
     - name: triage_agent
       type: chat_agent
       instructions: |
         You are an autonomous security analyst agent specializing in alert triage.
         
         Your role is to analyze security alerts, make intelligent triage decisions, 
         and prescribe specific next actions for automated systems.
         
         Analysis Process:
         1. Search the MITRE ATT&CK knowledge base for technique context
         2. Check for correlated alerts to identify attack campaigns
         3. Calculate risk score using all available alert factors
         4. Synthesize information to determine the triage decision
         5. Prescribe specific, actionable remediation steps
         
         Triage Decisions:
         - EscalateToIncident: High risk, critical threat
         - CorrelateWithExisting: Moderate risk, needs monitoring
         - MarkAsFalsePositive: Clear benign activity
         - RequireHumanReview: Ambiguous, requires expert judgment
       
       tools:
         # These tools will be bound to implementations at runtime
         - name: calculate_risk_score
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
         
         - name: find_correlated_alerts
           description: Find related alerts by entity overlap
           parameters:
             type: object
             properties:
               alert_entities:
                 type: array
                 items:
                   type: object
                 description: List of entities from the current alert
             required:
               - alert_entities
         
         - name: record_triage_decision
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
         
         - name: search_mitre_attack
           description: Search MITRE ATT&CK knowledge base for technique information
           parameters:
             type: object
             properties:
               technique_ids:
                 type: array
                 items:
                   type: string
                 description: MITRE technique IDs to search for
             required:
               - technique_ids
   ```

2. **Create Dry-Run Workflow for Testing**

   Create file: `src/agents/definitions/alert_triage_dryrun.yaml`

   ```yaml
   # Dry-run agent for testing without execution
   # Tools are declared without implementations - agent plans actions only
   
   name: AlertTriageDryRun
   description: Dry-run triage agent for planning without execution
   
   agents:
     - name: triage_planner
       type: chat_agent
       instructions: |
         You plan security alert triage actions but do not execute them.
         Outline the steps you would take to analyze and triage this alert.
         
         Explain your reasoning for each tool you would call and what 
         decision you would make based on the analysis.
       
       tools:
         # Declarative tools without implementations - dry-run mode
         - name: calculate_risk_score
           description: Simulate calculating risk score
         - name: find_correlated_alerts
           description: Simulate finding correlated alerts
         - name: record_triage_decision
           description: Simulate recording triage decision
         - name: search_mitre_attack
           description: Simulate MITRE ATT&CK search
   ```

3. **Create YAML Validation Utility**

   Create file: `utils/validate_agent_yaml.py`

   ```python
   """
   Validate agent YAML definitions.
   Ensures YAML files conform to expected structure.
   """
   
   import yaml
   from pathlib import Path
   import sys
   
   def validate_yaml(yaml_path: str) -> bool:
       """Validate agent YAML file structure."""
       try:
           with open(yaml_path, 'r') as f:
               config = yaml.safe_load(f)
           
           # Check required top-level fields
           required_fields = ['name', 'agents']
           for field in required_fields:
               if field not in config:
                   print(f"❌ Error: Missing required field '{field}'")
                   return False
           
           # Validate agents
           for agent in config.get('agents', []):
               if 'name' not in agent:
                   print(f"❌ Error: Agent missing 'name' field")
                   return False
               if 'instructions' not in agent:
                   print(f"❌ Error: Agent '{agent.get('name')}' missing 'instructions'")
                   return False
               
               # Validate tools if present
               tools = agent.get('tools', [])
               for tool in tools:
                   if 'name' not in tool:
                       print(f"❌ Error: Tool in agent '{agent.get('name')}' missing 'name'")
                       return False
           
           print(f"✅ YAML validation passed: {yaml_path}")
           return True
           
       except yaml.YAMLError as e:
           print(f"❌ Error: Invalid YAML syntax: {e}")
           return False
       except Exception as e:
           print(f"❌ Error: {e}")
           return False
   
   if __name__ == "__main__":
       if len(sys.argv) < 2:
           print("Usage: python validate_agent_yaml.py <yaml_file>")
           sys.exit(1)
       
       yaml_file = sys.argv[1]
       if not Path(yaml_file).exists():
           print(f"❌ Error: File not found: {yaml_file}")
           sys.exit(1)
       
       success = validate_yaml(yaml_file)
       sys.exit(0 if success else 1)
   ```

**Estimated Effort:** 1.5 days

**Deliverables:**
- `alert_triage_workflow.yaml` - Main agent definition
- `alert_triage_dryrun.yaml` - Dry-run testing agent
- `validate_agent_yaml.py` - YAML validation utility

---

### Phase 3: Implement Declarative Agent Loader

**Objective:** Create service to load agents from YAML using `agent-framework-declarative`

**Tasks:**

1. **Create Declarative Loader Module**

   Create file: `src/agents/declarative_loader.py`

   ```python
   """
   Declarative Agent Loader using Microsoft Agent Framework.
   
   Loads agents from YAML definitions and manages their lifecycle.
   Reference: https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/declarative
   """
   
   import asyncio
   import os
   import yaml
   from pathlib import Path
   from typing import Optional, Dict, Any, Callable
   
   from agent_framework import ChatAgent, WorkflowBuilder
   from agent_framework.azure import AzureOpenAIChatClient
   from azure.identity import AzureCliCredential
   
   from src.shared.logging import get_logger
   
   logger = get_logger(__name__)
   
   
   class DeclarativeAgentLoader:
       """Loads and manages declarative agents from YAML files."""
       
       def __init__(
           self,
           definitions_dir: str = "src/agents/definitions",
       ):
           """
           Initialize the declarative agent loader.
           
           Args:
               definitions_dir: Directory containing YAML agent definitions
           """
           self.definitions_dir = Path(definitions_dir)
           self._agents_cache: Dict[str, ChatAgent] = {}
           self._chat_client = None
       
       def _get_chat_client(self) -> AzureOpenAIChatClient:
           """Get or create Azure OpenAI chat client."""
           if self._chat_client is None:
               # Use Azure CLI credential for authentication
               self._chat_client = AzureOpenAIChatClient(
                   credential=AzureCliCredential()
               )
               logger.info("Created Azure OpenAI chat client")
           return self._chat_client
       
       def load_yaml_definition(self, yaml_path: Path) -> dict:
           """Load agent definition from YAML file."""
           logger.info(f"Loading YAML definition from: {yaml_path}")
           with open(yaml_path, 'r') as f:
               return yaml.safe_load(f)
       
       async def load_agent_from_yaml(
           self,
           yaml_filename: str,
           tool_implementations: Optional[Dict[str, Callable]] = None,
           force_reload: bool = False
       ) -> ChatAgent:
           """
           Load an agent from a YAML definition file.
           
           Args:
               yaml_filename: Name of the YAML file (e.g., "alert_triage_workflow.yaml")
               tool_implementations: Dict mapping tool names to @ai_function implementations
               force_reload: Force reload even if cached
           
           Returns:
               ChatAgent instance configured from YAML
               
           Example:
               tools = AlertTriageTools()
               tool_impls = {
                   "calculate_risk_score": tools.calculate_risk_score,
                   "find_correlated_alerts": tools.find_correlated_alerts,
               }
               agent = await loader.load_agent_from_yaml(
                   "alert_triage_workflow.yaml",
                   tool_implementations=tool_impls
               )
           """
           yaml_path = self.definitions_dir / yaml_filename
           
           # Check cache
           cache_key = str(yaml_path)
           if not force_reload and cache_key in self._agents_cache:
               logger.info(f"Using cached agent from: {yaml_filename}")
               return self._agents_cache[cache_key]
           
           # Load YAML definition
           definition = self.load_yaml_definition(yaml_path)
           
           # Extract agent configuration
           agents_config = definition.get('agents', [])
           if not agents_config:
               raise ValueError(f"No agents defined in {yaml_filename}")
           
           # Support single agent for now (can be extended to workflows)
           agent_config = agents_config[0]
           agent_name = agent_config.get('name', 'unnamed_agent')
           instructions = agent_config.get('instructions', '')
           
           logger.info(f"Configuring agent: {agent_name}")
           
           # Build tools list
           tools = []
           tool_configs = agent_config.get('tools', [])
           
           for tool_config in tool_configs:
               tool_name = tool_config.get('name')
               
               # Get implementation from provided dict
               if tool_implementations and tool_name in tool_implementations:
                   tools.append(tool_implementations[tool_name])
                   logger.debug(f"  ✓ Bound tool: {tool_name}")
               else:
                   # Tool declared but not implemented (dry-run mode)
                   logger.warning(f"  ⚠ Tool '{tool_name}' has no implementation (dry-run mode)")
           
           # Create agent
           chat_client = self._get_chat_client()
           agent = chat_client.create_agent(
               instructions=instructions,
               name=agent_name,
               tools=tools if tools else None
           )
           
           # Cache agent
           self._agents_cache[cache_key] = agent
           logger.info(f"✅ Agent loaded successfully: {agent_name} ({len(tools)} tools)")
           
           return agent
       
       async def load_workflow_from_yaml(
           self,
           yaml_filename: str,
           tool_implementations: Optional[Dict[str, Callable]] = None
       ):
           """
           Load a workflow from a YAML definition file.
           
           For workflows with multiple agents, this creates a WorkflowBuilder
           and connects agents based on the workflow definition.
           
           Args:
               yaml_filename: Name of the YAML file
               tool_implementations: Dict mapping tool names to implementations
           
           Returns:
               Workflow instance or single agent if no workflow defined
           """
           yaml_path = self.definitions_dir / yaml_filename
           definition = self.load_yaml_definition(yaml_path)
           
           logger.info(f"Loading workflow from: {yaml_filename}")
           
           # Load agents
           agents_config = definition.get('agents', [])
           agents = {}
           
           for agent_config in agents_config:
               agent_name = agent_config.get('name')
               instructions = agent_config.get('instructions', '')
               
               # Build tools for this agent
               tools = []
               tool_configs = agent_config.get('tools', [])
               
               for tool_config in tool_configs:
                   tool_name = tool_config.get('name')
                   if tool_implementations and tool_name in tool_implementations:
                       tools.append(tool_implementations[tool_name])
               
               # Create agent
               chat_client = self._get_chat_client()
               agent = chat_client.create_agent(
                   instructions=instructions,
                   name=agent_name,
                   tools=tools if tools else None
               )
               agents[agent_name] = agent
               logger.debug(f"  Created agent: {agent_name}")
           
           # Build workflow if multiple agents
           workflow_config = definition.get('workflow')
           if workflow_config and len(agents) > 1:
               builder = WorkflowBuilder()
               
               # Set start agent
               start_agent_name = workflow_config.get('start')
               if start_agent_name and start_agent_name in agents:
                   builder.set_start_executor(agents[start_agent_name])
                   logger.debug(f"  Set start agent: {start_agent_name}")
               
               # Add edges
               edges = workflow_config.get('edges', [])
               for edge in edges:
                   from_agent = agents.get(edge.get('from'))
                   to_agent = agents.get(edge.get('to'))
                   if from_agent and to_agent:
                       builder.add_edge(from_agent, to_agent)
                       logger.debug(f"  Added edge: {edge.get('from')} -> {edge.get('to')}")
               
               workflow = builder.build()
               logger.info(f"✅ Workflow loaded: {len(agents)} agents, {len(edges)} edges")
               return workflow
           
           # Return single agent if no workflow
           if agents:
               single_agent = list(agents.values())[0]
               logger.info(f"✅ Single agent loaded: {single_agent.name if hasattr(single_agent, 'name') else 'unnamed'}")
               return single_agent
           
           raise ValueError(f"No agents found in {yaml_filename}")
       
       def clear_cache(self):
           """Clear the agents cache."""
           self._agents_cache.clear()
           logger.info("Agent cache cleared")
   ```

2. **Create Startup Initialization Script**

   Create file: `utils/initialize_declarative_agents.py`

   ```python
   """
   Initialize Declarative Agents on application startup.
   
   This script loads agents from YAML definitions and prepares them for use.
   Run once at demo startup to load and cache agents for the session.
   """
   
   import asyncio
   import sys
   from pathlib import Path
   
   # Add src to path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   
   from src.agents.declarative_loader import DeclarativeAgentLoader
   from src.agents.alert_triage_agent import AlertTriageTools
   from src.shared.logging import configure_logging, get_logger
   
   logger = get_logger(__name__)
   
   
   async def initialize_agents():
       """Initialize all declarative agents for the Agentic SOC."""
       
       logger.info("=" * 60)
       logger.info("Initializing Declarative Agents")
       logger.info("=" * 60)
       
       loader = DeclarativeAgentLoader()
       
       # Initialize tool implementations
       logger.info("\n📦 Setting up tool implementations...")
       tools = AlertTriageTools()
       tool_implementations = {
           "calculate_risk_score": tools.calculate_risk_score,
           "find_correlated_alerts": tools.find_correlated_alerts,
           "record_triage_decision": tools.record_triage_decision,
           "search_mitre_attack": tools.get_mitre_context,
       }
       logger.info(f"✓ Configured {len(tool_implementations)} tool implementations")
       
       # Load Alert Triage Agent from YAML
       logger.info("\n🤖 Loading Alert Triage Agent from YAML...")
       triage_agent = await loader.load_agent_from_yaml(
           "alert_triage_workflow.yaml",
           tool_implementations=tool_implementations
       )
       
       # Load dry-run agent for testing
       logger.info("\n🧪 Loading Dry-run Agent for testing...")
       dryrun_agent = await loader.load_agent_from_yaml(
           "alert_triage_dryrun.yaml"
       )
       
       agents = {
           "alert_triage": triage_agent,
           "alert_triage_dryrun": dryrun_agent,
       }
       
       logger.info("\n" + "=" * 60)
       logger.info(f"✅ Successfully initialized {len(agents)} agents")
       logger.info("=" * 60)
       logger.info("")
       
       return agents
   
   
   if __name__ == "__main__":
       configure_logging(log_level="INFO")
       
       try:
           agents = asyncio.run(initialize_agents())
           print(f"\n✨ Agents ready for demo session:")
           for name in agents:
               print(f"   • {name}")
       except Exception as e:
           logger.error(f"Failed to initialize agents: {e}", exc_info=True)
           sys.exit(1)
   ```

**Estimated Effort:** 2 days

**Deliverables:**
- `declarative_loader.py` - YAML agent loader
- `initialize_declarative_agents.py` - Startup initialization script

---

### Phase 4: Refactor Alert Triage Agent

**Objective:** Update to use declarative agent loaded from YAML

**Tasks:**

1. **Extract Tool Implementations**

   Update `src/agents/alert_triage_agent.py` to keep only tool implementations:

   ```python
   """
   Alert Triage Tools - Implementation of @ai_function tools.
   
   These tools are bound to the declarative agent defined in YAML.
   """
   
   import json
   import random
   from typing import Annotated, List, Dict
   from pydantic import Field
   
   from agent_framework import ai_function
   from src.shared.logging import get_logger
   
   logger = get_logger(__name__)
   
   
   class AlertTriageTools:
       """Tool implementations for Alert Triage Agent."""
       
       def __init__(self):
           self._recent_alerts = []
       
       @ai_function(description="Calculate risk score for a security alert")
       def calculate_risk_score(
           severity: Annotated[str, Field(description="Alert severity")],
           entity_count: Annotated[int, Field(description="Number of entities")],
           mitre_techniques: Annotated[List[str], Field(description="MITRE technique IDs")],
           confidence_score: Annotated[int, Field(description="Detection confidence")]
       ) -> str:
           """Calculate risk score (same logic as before)."""
           score = 0
           # ... existing calculation logic ...
           return json.dumps({"risk_score": score, "explanation": "..."})
       
       @ai_function(description="Find related alerts by entity overlap")
       def find_correlated_alerts(
           alert_entities: Annotated[List[Dict], Field(description="Entities from alert")]
       ) -> str:
           """Find correlated alerts."""
           # ... existing logic ...
           return json.dumps({"correlated_count": 0})
       
       @ai_function(description="Record triage decision")
       def record_triage_decision(
           decision: Annotated[str, Field(description="Triage decision")],
           priority: Annotated[str, Field(description="Priority level")],
           rationale: Annotated[str, Field(description="Decision rationale")]
       ) -> str:
           """Record the triage decision."""
           # ... existing logic ...
           return json.dumps({"decision": decision, "priority": priority})
       
       @ai_function(description="Search MITRE ATT&CK knowledge base")
       def get_mitre_context(
           technique_ids: Annotated[List[str], Field(description="MITRE technique IDs")]
       ) -> str:
           """Get MITRE ATT&CK context."""
           # ... existing logic ...
           return json.dumps({"techniques": []})
   ```

2. **Create New Agent Wrapper**

   Create file: `src/agents/alert_triage_agent_v2.py`

   ```python
   """
   Alert Triage Agent V2 - Using Declarative YAML Definition.
   
   This version loads the agent from a YAML file at startup and reuses
   it throughout the demo session.
   """
   
   import time
   from typing import Optional
   from uuid import uuid4
   from datetime import datetime
   
   from agent_framework import ChatAgent
   
   from src.agents.declarative_loader import DeclarativeAgentLoader
   from src.agents.alert_triage_agent import AlertTriageTools
   from src.shared.schemas import SecurityAlert, TriageResult, TriagePriority, TriageDecision
   from src.shared.logging import get_logger
   from src.shared.metrics import counter
   from src.shared.audit import get_audit_service, AuditResult
   
   logger = get_logger(__name__)
   
   
   class AlertTriageAgentV2:
       """Alert Triage Agent using declarative YAML definition."""
       
       AGENT_VERSION = "2.0.0-declarative"
       YAML_FILE = "alert_triage_workflow.yaml"
       
       def __init__(self):
           """Initialize the declarative agent."""
           self._loader = DeclarativeAgentLoader()
           self._agent: Optional[ChatAgent] = None
           self._tools = AlertTriageTools()
           self.audit_service = get_audit_service()
       
       async def initialize(self) -> None:
           """Load agent from YAML definition."""
           if self._agent is not None:
               logger.info("Agent already initialized, reusing existing instance")
               return
           
           logger.info(f"Loading agent from YAML: {self.YAML_FILE}")
           
           # Prepare tool implementations
           tool_implementations = {
               "calculate_risk_score": self._tools.calculate_risk_score,
               "find_correlated_alerts": self._tools.find_correlated_alerts,
               "record_triage_decision": self._tools.record_triage_decision,
               "search_mitre_attack": self._tools.get_mitre_context,
           }
           
           # Load agent from YAML
           self._agent = await self._loader.load_agent_from_yaml(
               self.YAML_FILE,
               tool_implementations=tool_implementations
           )
           
           logger.info(f"✅ Agent initialized successfully (v{self.AGENT_VERSION})")
       
       async def triage_alert(self, alert: SecurityAlert) -> TriageResult:
           """
           Triage a security alert using the declarative agent.
           
           Args:
               alert: Security alert to triage
           
           Returns:
               TriageResult with analysis
           """
           start_time = time.time()
           
           # Ensure agent is loaded
           if self._agent is None:
               await self.initialize()
           
           logger.info(f"Triaging alert: {alert.AlertName}")
           
           # Build triage query
           query = self._build_triage_query(alert)
           
           # Run agent
           response = await self._agent.run(query)
           
           # Parse response
           triage_result = self._parse_response(response, alert, start_time)
           
           # Audit log
           await self.audit_service.log_agent_action(
               agent_name="AlertTriageAgentV2",
               action="TriagedAlert",
               target_entity_type="SecurityAlert",
               target_entity_id=str(alert.SystemAlertId),
               result=AuditResult.SUCCESS,
               details={"version": self.AGENT_VERSION, "declarative": True}
           )
           
           counter("alerts_triaged_total").inc()
           
           return triage_result
       
       def _build_triage_query(self, alert: SecurityAlert) -> str:
           """Build triage query for the agent."""
           # ... existing logic to format alert for agent ...
           return f"Analyze and triage this alert: {alert.AlertName}"
       
       def _parse_response(self, response, alert, start_time) -> TriageResult:
           """Parse agent response into TriageResult."""
           # ... existing parsing logic ...
           return TriageResult(
               AlertId=alert.SystemAlertId,
               TriageId=uuid4(),
               Timestamp=datetime.utcnow(),
               RiskScore=50,
               Priority=TriagePriority.MEDIUM,
               TriageDecision=TriageDecision.REQUIRE_HUMAN_REVIEW,
               Explanation=str(response),
               CorrelatedAlertIds=[],
               EnrichmentData={},
               ProcessingTimeMs=int((time.time() - start_time) * 1000),
               AgentVersion=self.AGENT_VERSION
           )
   ```

**Estimated Effort:** 1.5 days

**Deliverables:**
- Updated `alert_triage_agent.py` with tools only
- New `alert_triage_agent_v2.py` using declarative agent

---

### Phase 5: Update Demo Script

**Objective:** Update demo to use declarative agents

**Tasks:**

1. **Create New Demo Script**

   Create file: `utils/demo_declarative_agents.py`

   ```python
   """
   Demo script for Declarative Alert Triage Agent.
   
   Shows agent loaded from YAML definition.
   """
   
   import asyncio
   import sys
   from pathlib import Path
   
   sys.path.insert(0, str(Path(__file__).parent.parent))
   
   from src.agents.alert_triage_agent_v2 import AlertTriageAgentV2
   from src.data.datasets import get_guide_loader
   from src.shared.logging import configure_logging, get_logger
   
   logger = get_logger(__name__)
   
   
   async def demo_declarative_agent():
       """Demonstrate declarative alert triage agent."""
       
       print("=" * 80)
       print("DECLARATIVE ALERT TRIAGE AGENT DEMO")
       print("=" * 80)
       print()
       
       # Initialize agent (loads from YAML once)
       print("🔄 Initializing agent from YAML definition...")
       agent = AlertTriageAgentV2()
       await agent.initialize()
       print("✅ Agent ready\n")
       
       # Load sample alerts
       print("📥 Loading sample alerts...")
       guide_loader = get_guide_loader()
       alerts = guide_loader.load_alerts(max_alerts=3)
       print(f"✅ Loaded {len(alerts)} alerts\n")
       
       # Process alerts (reusing same agent)
       for i, alert in enumerate(alerts, 1):
           print(f"\n{'─' * 80}")
           print(f"📋 ALERT {i}/{len(alerts)}: {alert.AlertName}")
           print(f"{'─' * 80}")
           
           result = await agent.triage_alert(alert)
           
           print(f"\n✅ Triage Complete:")
           print(f"   Risk Score: {result.RiskScore}/100")
           print(f"   Priority: {result.Priority}")
           print(f"   Decision: {result.TriageDecision}")
           print(f"   Time: {result.ProcessingTimeMs}ms")
       
       print(f"\n{'=' * 80}")
       print("✨ Demo Complete - Agent was loaded once and reused")
       print(f"{'=' * 80}\n")
   
   
   if __name__ == "__main__":
       configure_logging(log_level="INFO", json_output=False)
       
       try:
           asyncio.run(demo_declarative_agent())
       except KeyboardInterrupt:
           print("\n\nDemo interrupted")
       except Exception as e:
           logger.error(f"Demo failed: {e}", exc_info=True)
           sys.exit(1)
   ```

**Estimated Effort:** 1 day

**Deliverables:**
- `demo_declarative_agents.py` - Demo script showing declarative approach

---

### Phase 6: Optional Foundry Integration

**Objective:** Add native Microsoft Foundry features (Enterprise Memory, AI Search)

This phase is optional and can be done after the declarative approach is working.

**Tasks:**

1. **Add Enterprise Memory** (using `azure-ai-projects>=2.0.0b2`)
2. **Native AI Search Integration**
3. **Persistent Agent Storage** in Foundry

**Estimated Effort:** 2-3 days

**Note:** This can be deferred to focus first on getting the declarative approach working.

---

## Implementation Timeline

| Phase | Description | Duration | Status |
|-------|-------------|----------|--------|
| 1 | Add declarative dependencies | 0.5 days | 📋 Planned |
| 2 | Create YAML definitions | 1.5 days | 📋 Planned |
| 3 | Implement declarative loader | 2 days | 📋 Planned |
| 4 | Refactor Alert Triage Agent | 1.5 days | 📋 Planned |
| 5 | Update demo script | 1 day | 📋 Planned |
| 6 | Optional: Foundry integration | 2-3 days | 🔜 Future |

**Total Core Effort: ~6.5 days**

---

## Testing Strategy

### 1. YAML Validation

```bash
# Validate YAML files
python utils/validate_agent_yaml.py src/agents/definitions/alert_triage_workflow.yaml
python utils/validate_agent_yaml.py src/agents/definitions/alert_triage_dryrun.yaml
```

### 2. Dry-Run Testing

```python
# Test with dry-run agent (no tool implementations)
loader = DeclarativeAgentLoader()
dryrun_agent = await loader.load_agent_from_yaml("alert_triage_dryrun.yaml")
response = await dryrun_agent.run("Analyze alert: Suspicious PowerShell")
# Agent should plan actions without executing
```

### 3. Full Integration Testing

```bash
# Test full agent with tool implementations
python utils/demo_declarative_agents.py
```

---

## Success Criteria

✅ **Phase 1-2:**
- [ ] `agent-framework-declarative` installed successfully
- [ ] YAML definitions created and validated
- [ ] Dry-run agent loads without errors

✅ **Phase 3-4:**
- [ ] Declarative loader successfully loads agents from YAML
- [ ] Tools correctly bound to agent
- [ ] Agent processes alerts successfully

✅ **Phase 5:**
- [ ] Demo runs successfully
- [ ] Agent is loaded once and reused
- [ ] YAML changes can be applied by restarting (no code changes)

---

## Environment Setup

### Required Environment Variables

```bash
# Azure OpenAI (for agent LLM)
export AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"  # or your model

# Optional: AI Search for MITRE knowledge base
export AZURE_SEARCH_ENDPOINT="https://your-search-resource.search.windows.net"
export AZURE_SEARCH_KEY="your-key"

# Optional: Foundry project (for Phase 6)
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/..."
```

### Authentication

```bash
# Azure CLI authentication (recommended)
az login
```

---

## Key Differences from Current Implementation

| Aspect | Current | After Refactor |
|--------|---------|----------------|
| Agent Definition | Python code | YAML file |
| Tool Binding | Hardcoded in `__init__` | Dynamic from YAML |
| Agent Lifecycle | Created at runtime | Loaded at startup |
| Configuration Changes | Code edit + restart | YAML edit + restart |
| Testing | Full execution | Dry-run mode available |
| Experimentation | Requires coding | Edit YAML |

---

## References

- **Declarative Agent Samples**: https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/declarative
- **Workflow Samples**: https://github.com/microsoft/agent-framework/tree/main/workflow-samples
- **Agent Framework Docs**: https://learn.microsoft.com/en-us/agent-framework/
- **Azure AI Projects SDK**: https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme

---

## Next Steps

1. ✅ Review and approve this plan
2. 📋 Create Phase 1 implementation task
3. 🔄 Iterative implementation (Phase 1 → Phase 2 → ...)
4. 🧪 Test each phase before proceeding
5. 📝 Document learnings and update examples

---

## Appendix: Example Workflow Samples

From the Microsoft Agent Framework repository:

- **CustomerSupport.yaml**: Multi-agent customer support workflow
- **Marketing.yaml**: Marketing content creation workflow  
- **MathChat.yaml**: Math problem solving with agent collaboration

These provide patterns for:
- Multi-agent workflows
- Agent handoffs
- Conditional execution
- Tool orchestration

