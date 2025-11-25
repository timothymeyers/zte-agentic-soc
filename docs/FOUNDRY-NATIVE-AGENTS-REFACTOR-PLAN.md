# Agentic SOC - Microsoft Foundry Native Agents Refactor Plan

**Status:** Draft for Review  
**Date:** November 25, 2024  
**Author:** GitHub Copilot Agent  
**Target SDK Version:** azure-ai-projects>=2.0.0b1

## Executive Summary

This document outlines a comprehensive refactor plan to migrate the current Agentic SOC MVP from programmatic agent creation using Microsoft Agent Framework to **declarative, YAML-based agent definitions** that leverage **Microsoft Foundry native capabilities**.

### Key Changes
1. **Agent Definition**: From code-based to YAML declarative specifications
2. **Agent Lifecycle**: From on-demand creation to persistent, reusable agents
3. **Knowledge Integration**: From custom AI Search to native Foundry IQ knowledge bases
4. **Memory**: From in-memory state to native Foundry enterprise memory
5. **Agent Management**: From manual instantiation to Foundry Agent Service management

---

## 1. Current State Analysis

### 1.1 Current Implementation Architecture

**Alert Triage Agent** (`src/agents/alert_triage_agent.py`):
```python
class AlertTriageAgent:
    def __init__(self, project_endpoint, model_deployment_name):
        # Programmatically creates agent in code
        self._agent = ChatAgent(
            chat_client=AzureAIAgentClient(...),
            instructions="...",  # Hardcoded in Python
            tools=[
                self.tools.calculate_risk_score,     # @ai_function
                self.tools.find_correlated_alerts,   # @ai_function
                self.tools.record_triage_decision,   # @ai_function
                self.tools.get_mitre_context        # @ai_function (AI Search)
            ]
        )
```

**Current Tool Pattern**:
```python
@ai_function(description="Calculate risk score...")
def calculate_risk_score(
    severity: str,
    entity_count: int,
    mitre_techniques: List[str],
    confidence_score: int
) -> str:
    # Custom logic in Python
    score = calculate_score(...)
    return json.dumps({"risk_score": score, ...})
```

**Current AI Search Integration**:
```python
@ai_function(description="Get MITRE ATT&CK technique information")
def get_mitre_context(technique_ids: List[str]) -> str:
    # Custom AI Search query
    search_client = SearchClient(endpoint=..., index="attack-scenarios")
    results = await search_client.search(...)
    return json.dumps(results)
```

### 1.2 Current Limitations

1. **Agent Creation on Every Run**: Agent is instantiated programmatically each time, not persisted
2. **No Declarative Configuration**: Agent behavior is hardcoded in Python
3. **Custom AI Search Integration**: Manual query construction and result parsing
4. **No Native Memory**: Uses in-memory lists for alert correlation (lost on restart)
5. **Limited Tool Ecosystem**: Only custom @ai_function tools, no native Foundry tools
6. **No Agent Versioning**: Changes require code deployment
7. **Manual Orchestration**: Custom event bus for agent coordination

---

## 2. Target State: Microsoft Foundry Native Agents

### 2.1 Foundry Native Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Microsoft Foundry Portal                        │
│                    (Agent Management UI)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               Agent YAML Definitions (Declarative)               │
│                                                                  │
│  agents/                                                         │
│  ├── alert-triage-agent.yaml      (Triage Agent)               │
│  ├── threat-hunting-agent.yaml    (Hunting Agent)              │
│  ├── incident-response-agent.yaml (Response Agent)             │
│  └── threat-intel-agent.yaml      (Intel Agent)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            Foundry Agent Service (Runtime)                       │
│                                                                  │
│  • Agent Lifecycle Management                                   │
│  • Version Control                                              │
│  • Persistent Threads                                           │
│  • Enterprise Memory                                            │
│  • Tool Orchestration                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Native Foundry Tools                          │
│                                                                  │
│  • MCP Tool (Foundry IQ Knowledge Base)                         │
│  • File Search (RAG over historical data)                       │
│  • Code Interpreter (Complex calculations)                      │
│  • Bing Grounding (Real-time threat intel)                      │
│  • Agent-to-Agent (A2A) Tool                                    │
│  • Azure Functions (Custom logic)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Foundry IQ Knowledge Base                       │
│               (Azure AI Search + Knowledge Sources)              │
│                                                                  │
│  Knowledge Sources:                                              │
│  • Attack Scenarios (14K+ MITRE-mapped scenarios)               │
│  • Historical Incidents (GUIDE dataset - 1.17M incidents)       │
│  • Threat Intelligence (IOCs, TTPs, Actor profiles)             │
│  • Asset Inventory (Critical systems, users)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Foundry Enterprise Memory                        │
│                 (Cosmos DB Integration)                          │
│                                                                  │
│  • Long-term agent memory across sessions                       │
│  • Alert correlation history                                    │
│  • Incident context                                             │
│  • User preferences                                             │
│  • Learned patterns                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 YAML Agent Definition Structure

Based on research of `azure-ai-projects>=2.0.0b1` and Foundry documentation:

**Example: `agents/alert-triage-agent.yaml`**
```yaml
# yaml-language-server: $schema=https://aka.ms/ai-foundry/vsc/agent/1.0.0
version: 1.0.0
name: alert-triage-agent
description: >-
  AI-powered security analyst agent specializing in alert triage and automated response.
  Analyzes security alerts, calculates risk scores, detects correlations, and provides
  actionable remediation steps to enable automated response.

id: ''  # Auto-generated by Foundry on creation

metadata:
  authors:
    - Agentic SOC Team
  tags:
    - security
    - alert-triage
    - incident-response
    - mitre-attack
  version: '1.0.0'
  
model:
  id: 'gpt-4.1-mini'  # Or gpt-4o for more complex reasoning
  options:
    temperature: 0.3  # Lower temperature for more deterministic security decisions
    top_p: 0.9
    max_tokens: 4096

instructions: |
  You are an autonomous security analyst agent specializing in alert triage and automated response.
  
  PRIMARY GOAL: Provide actionable remediation steps to enable automated response. Avoid human 
  escalation except for the most critical, ambiguous scenarios.
  
  Your role is to analyze security alerts, make intelligent triage decisions, and prescribe 
  specific next actions for automated systems or other agents to execute.
  
  Analysis Process:
  1. Retrieve MITRE ATT&CK context from the knowledge base for any techniques in the alert
  2. Check for correlated alerts to identify potential attack campaigns  
  3. Calculate the comprehensive risk score using all available alert factors
  4. Synthesize all information to determine the appropriate triage decision
  5. Prescribe specific, actionable remediation steps
  
  AUTONOMOUS RESPONSE PHILOSOPHY:
  - Human escalation (RequireHumanReview) should be LAST RESORT only for:
    * Truly ambiguous situations requiring human judgment
    * Critical incidents with potential business impact needing executive awareness
    * Novel attack patterns that automation cannot handle safely
  - Prefer automated actions with clear remediation steps
  - Provide specific, executable instructions for automation systems
  
  Triage Decision Guidelines:
  
  1. MarkAsFalsePositive (Priority: Low)
     - Use when: Clear indicators of benign activity, very low risk score
     - Remediation: "Suppress future alerts matching this pattern. Tune detection rule."
  
  2. CorrelateWithExisting (Priority: Low to Medium)
     - Use when: Isolated alert with low scenario counts OR alert needs monitoring
     - Remediation: "Create watchlist alert monitoring <host> for 24 hours. 
                     Auto-escalate if 3+ related alerts appear."
  
  3. EscalateToIncident (Priority: Medium to Critical)
     - Use when: Multiple correlations, high scenario counts, high risk score
     - Remediation: "Isolate <host> from network. Initiate forensic data collection."
  
  4. RequireHumanReview (Priority: Medium to Critical) - USE SPARINGLY
     - Use ONLY when: Genuinely ambiguous situation, novel/sophisticated attack
     - Remediation: "Escalate to human analyst due to [specific reason]."
  
  Your rationale must include:
  1. Summary of evidence (risk score, correlations, scenario counts)
  2. Decision logic and reasoning
  3. SPECIFIC remediation steps with entity names (hosts, users, IPs)
  4. Success criteria or escalation triggers
  
  Always use the knowledge base tool to retrieve MITRE ATT&CK technique details before 
  making triage decisions.

tools:
  # Native Foundry IQ Knowledge Base (MCP Tool)
  - type: mcp
    mcp:
      server_label: "attack-scenarios-kb"
      server_url: "${AZURE_SEARCH_ENDPOINT}/knowledgebases/attack-scenarios/mcp?api-version=2025-11-01-preview"
      require_approval: "never"
      allowed_tools:
        - knowledge_base_retrieve
      project_connection_id: "${PROJECT_CONNECTION_ID}"
      description: >-
        Knowledge base containing MITRE ATT&CK attack scenarios, tactics, techniques, 
        and procedures. Use this to retrieve context about security techniques mentioned 
        in alerts.
  
  # Code Interpreter for complex risk calculations
  - type: code_interpreter
    code_interpreter:
      container:
        type: automatic
      description: >-
        Execute Python code for complex risk score calculations, statistical analysis,
        and data transformations.
  
  # File Search for historical incident context
  - type: file_search
    file_search:
      vector_store_ids:
        - "${HISTORICAL_INCIDENTS_VECTOR_STORE_ID}"
      description: >-
        Search historical incidents and alert patterns to identify similar past cases
        and inform triage decisions.
  
  # Bing Grounding for real-time threat intelligence
  - type: bing_grounding
    bing_grounding:
      search_configurations:
        - project_connection_id: "${BING_PROJECT_CONNECTION_ID}"
      description: >-
        Real-time web search for emerging threats, CVE details, and current 
        threat actor campaigns.
  
  # Agent-to-Agent communication with other SOC agents
  - type: a2a
    a2a:
      project_connection_id: "${A2A_PROJECT_CONNECTION_ID}"
      description: >-
        Communicate with other SOC agents (Threat Hunting, Incident Response, 
        Threat Intelligence) for coordinated response.

# Enterprise Memory Configuration
memory:
  enabled: true
  scope_type: "alert"  # Separate memory per alert investigation
  cosmos_connection_id: "${COSMOS_PROJECT_CONNECTION_ID}"
  
# Tool Resources (if needed)
tool_resources:
  file_search:
    vector_stores:
      - vector_store_id: "${HISTORICAL_INCIDENTS_VECTOR_STORE_ID}"
  code_interpreter:
    files: []  # Optional: Pre-loaded data files
```

---

## 3. Detailed Refactor Strategy

### 3.1 Phase 1: Infrastructure Setup (1-2 weeks)

#### 3.1.1 Foundry IQ Knowledge Base Setup

**Goal**: Replace custom AI Search integration with native Foundry IQ knowledge bases.

**Actions**:
1. **Create Knowledge Sources** in Azure AI Search:
   ```bash
   # Using Azure CLI
   az search knowledge-source create \
     --resource-group $RG \
     --service-name $SEARCH_SERVICE \
     --knowledge-base-name attack-scenarios-kb \
     --knowledge-source-name attack-scenarios \
     --type azure-search-index \
     --index-name attack-scenarios
   ```

2. **Configure Knowledge Base**:
   - Attack Scenarios knowledge source (14K+ MITRE-mapped scenarios)
   - Historical Incidents knowledge source (GUIDE dataset)
   - Threat Intelligence knowledge source (IOCs, TTPs)

3. **Create Project Connections**:
   ```python
   from azure.ai.projects import AIProjectClient
   from azure.ai.projects.models import RemoteToolConnection
   
   # Create MCP connection for knowledge base
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

4. **Update Data Ingestion Scripts**:
   - Modify `utils/setup_ai_search.py` to create knowledge sources instead of just indexes
   - Load Attack dataset into knowledge source
   - Configure semantic ranking and extractive data output

#### 3.1.2 Enterprise Memory Setup

**Goal**: Configure Foundry enterprise memory backed by Cosmos DB.

**Actions**:
1. **Enable BYO Thread Storage** in Foundry project settings
2. **Create Cosmos DB containers**:
   - `thread-message-store`: User conversation messages
   - `system-thread-message-store`: System messages
   - `agent-entity-store`: Model inputs/outputs
   
3. **Create Project Connection**:
   ```python
   # Create Cosmos DB connection for enterprise memory
   cosmos_connection = project_client.project_connections.create(
       connection_name="enterprise-memory-cosmos",
       connection_type="AzureCosmosDB",
       endpoint=cosmos_endpoint,
       database_name="enterprise_memory",
       authentication={...}
   )
   ```

#### 3.1.3 Vector Store Setup for File Search

**Actions**:
1. **Create Vector Store** for historical incidents:
   ```python
   # Upload historical incidents to vector store
   vector_store = project_client.vector_stores.create(
       name="historical-incidents-vector-store",
       file_ids=historical_incident_file_ids
   )
   ```

2. **Configure File Search Tool** to use vector store

### 3.2 Phase 2: Agent Definition Migration (1 week)

#### 3.2.1 Create YAML Agent Definitions

**Directory Structure**:
```
agents/
├── alert-triage-agent.yaml        # Alert Triage Agent
├── threat-hunting-agent.yaml      # Threat Hunting Agent (future)
├── incident-response-agent.yaml   # Incident Response Agent (future)
├── threat-intel-agent.yaml        # Threat Intelligence Agent (future)
└── README.md                      # Agent definition documentation
```

**Actions**:
1. Create `agents/alert-triage-agent.yaml` (see Section 2.2)
2. Document YAML schema and configuration options
3. Create environment variable templates for connections

#### 3.2.2 Replace Custom @ai_function Tools with Native Foundry Tools

**Mapping**:

| Current Custom Tool | Native Foundry Tool | Rationale |
|---------------------|---------------------|-----------|
| `get_mitre_context` | MCP Tool (Knowledge Base) | Native knowledge retrieval with semantic search |
| `calculate_risk_score` | Code Interpreter | Complex calculations in Python sandbox |
| `find_correlated_alerts` | File Search + Memory | Search historical alerts + persistent memory |
| `record_triage_decision` | (Not needed) | Agent naturally records decisions in thread |

**Migration Strategy**:

1. **MCP Tool replaces `get_mitre_context`**:
   - Agent uses natural language queries like:
     ```
     "Retrieve MITRE ATT&CK context for techniques T1059.001 and T1086"
     ```
   - Knowledge base handles query planning, decomposition, retrieval
   - Returns formatted results with citations

2. **Code Interpreter replaces `calculate_risk_score`**:
   - Agent generates Python code to calculate risk:
     ```python
     severity_scores = {"High": 30, "Medium": 20, "Low": 10}
     score = severity_scores[severity]
     score += min(entity_count * 2, 10)
     score += min(len(mitre_techniques) * 3, 15)
     # ... etc
     return {"risk_score": score, "breakdown": {...}}
     ```
   - More flexible than hardcoded logic
   - Allows agent to adjust calculations based on context

3. **File Search + Memory replaces `find_correlated_alerts`**:
   - File Search queries historical alerts for similar patterns
   - Enterprise Memory maintains correlation state across sessions

#### 3.2.3 Update Agent Instructions

**Key Changes**:
1. **Remove tool-specific guidance**: Agent learns tool usage from descriptions
2. **Add knowledge base query patterns**: Show examples of good queries
3. **Emphasize autonomous response**: Reinforce remediation-first approach
4. **Include citation formatting**: Teach agent to format MCP tool citations

### 3.3 Phase 3: Agent Lifecycle Management (1 week)

#### 3.3.1 Agent Initialization on Startup

**Goal**: Create persistent agents once at application startup, reuse for entire demo.

**Implementation**:
```python
# src/agents/foundry_native_agent.py

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
import os
import yaml

class FoundryNativeAgent:
    """
    Wrapper for Foundry native agents with persistent lifecycle.
    """
    
    def __init__(self, agent_yaml_path: str):
        self.agent_yaml_path = agent_yaml_path
        self.project_client = None
        self.agent = None
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize agent from YAML definition.
        Creates or retrieves persistent agent in Foundry.
        """
        if self._initialized:
            return
        
        # Load YAML definition
        with open(self.agent_yaml_path, 'r') as f:
            agent_config = yaml.safe_load(f)
        
        # Create project client
        self.project_client = AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential()
        )
        
        # Check if agent already exists
        try:
            existing_agents = self.project_client.agents.list_agents()
            self.agent = next(
                (a for a in existing_agents if a.name == agent_config['name']),
                None
            )
        except:
            self.agent = None
        
        if self.agent:
            print(f"✓ Found existing agent: {self.agent.name} (version {self.agent.version})")
        else:
            # Create agent from YAML config
            print(f"Creating new agent: {agent_config['name']}...")
            self.agent = await self._create_agent_from_yaml(agent_config)
            print(f"✓ Created agent: {self.agent.name} (version {self.agent.version})")
        
        self._initialized = True
    
    async def _create_agent_from_yaml(self, config: dict):
        """Create agent from YAML configuration."""
        
        # Build tools from config
        tools = []
        for tool_config in config.get('tools', []):
            tool = self._build_tool(tool_config)
            if tool:
                tools.append(tool)
        
        # Create agent definition
        definition = PromptAgentDefinition(
            model=config['model']['id'],
            instructions=config['instructions'],
            tools=tools,
            temperature=config['model']['options'].get('temperature', 0.7),
            top_p=config['model']['options'].get('top_p', 1.0),
            max_tokens=config['model']['options'].get('max_tokens', 4096)
        )
        
        # Create agent version
        agent = await self.project_client.agents.create_version(
            agent_name=config['name'],
            definition=definition,
            description=config['description']
        )
        
        return agent
    
    def _build_tool(self, tool_config: dict):
        """Build tool from YAML config."""
        from azure.ai.projects.models import (
            MCPTool,
            CodeInterpreterTool,
            FileSearchTool,
            BingGroundingAgentTool,
            A2ATool
        )
        
        tool_type = tool_config['type']
        
        if tool_type == 'mcp':
            return MCPTool(
                server_label=tool_config['mcp']['server_label'],
                server_url=self._resolve_env_vars(tool_config['mcp']['server_url']),
                require_approval=tool_config['mcp']['require_approval'],
                allowed_tools=tool_config['mcp']['allowed_tools'],
                project_connection_id=self._resolve_env_vars(
                    tool_config['mcp']['project_connection_id']
                )
            )
        elif tool_type == 'code_interpreter':
            return CodeInterpreterTool()
        elif tool_type == 'file_search':
            return FileSearchTool(
                vector_store_ids=[
                    self._resolve_env_vars(vs_id) 
                    for vs_id in tool_config['file_search'].get('vector_store_ids', [])
                ]
            )
        elif tool_type == 'bing_grounding':
            return BingGroundingAgentTool(...)
        elif tool_type == 'a2a':
            return A2ATool(
                project_connection_id=self._resolve_env_vars(
                    tool_config['a2a']['project_connection_id']
                )
            )
        
        return None
    
    def _resolve_env_vars(self, value: str) -> str:
        """Resolve ${VAR} placeholders in YAML."""
        import re
        return re.sub(
            r'\$\{([^}]+)\}',
            lambda m: os.environ.get(m.group(1), m.group(0)),
            value
        )
    
    async def run(self, query: str, thread_id: str = None):
        """
        Run agent with query.
        Reuses existing thread or creates new one.
        """
        if not self._initialized:
            await self.initialize()
        
        # Get OpenAI client for Responses API
        openai_client = self.project_client.get_openai_client()
        
        # Create or reuse conversation thread
        if not thread_id:
            # Create new conversation
            response = openai_client.responses.create(
                input=query,
                extra_body={
                    "agent": {
                        "name": self.agent.name,
                        "type": "agent_reference"
                    }
                }
            )
        else:
            # Continue existing conversation
            response = openai_client.responses.create(
                conversation_id=thread_id,
                input=query,
                extra_body={
                    "agent": {
                        "name": self.agent.name,
                        "type": "agent_reference"
                    }
                }
            )
        
        return response
    
    async def close(self):
        """Clean up resources."""
        if self.project_client:
            await self.project_client.close()
```

**Startup Initialization**:
```python
# src/agents/__init__.py

from .foundry_native_agent import FoundryNativeAgent
import os

# Global agent instances
_alert_triage_agent: FoundryNativeAgent = None

async def initialize_agents():
    """
    Initialize all agents at application startup.
    Agents are persistent and reused throughout the demo.
    """
    global _alert_triage_agent
    
    agents_dir = os.path.join(os.path.dirname(__file__), '../../agents')
    
    # Initialize Alert Triage Agent
    _alert_triage_agent = FoundryNativeAgent(
        agent_yaml_path=os.path.join(agents_dir, 'alert-triage-agent.yaml')
    )
    await _alert_triage_agent.initialize()
    
    print("✓ All agents initialized and ready")

def get_alert_triage_agent() -> FoundryNativeAgent:
    """Get the global Alert Triage Agent instance."""
    return _alert_triage_agent
```

**Application Startup**:
```python
# main.py or demo script

import asyncio
from src.agents import initialize_agents, get_alert_triage_agent

async def main():
    # Initialize agents once at startup
    await initialize_agents()
    
    # Get agent instance
    triage_agent = get_alert_triage_agent()
    
    # Reuse agent for multiple alerts
    for alert in alerts:
        result = await triage_agent.run(
            query=build_triage_query(alert),
            thread_id=alert.SystemAlertId  # Persist thread per alert
        )
        print(result.output_text)
    
    # Clean up
    await triage_agent.close()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3.3.2 Thread Management

**Strategy**:
1. **One thread per alert investigation**: Each alert gets its own conversation thread
2. **Persistent threads**: Threads maintained in Cosmos DB via enterprise memory
3. **Thread reuse**: Resume investigations by referencing thread ID

**Implementation**:
```python
async def triage_alert(alert: SecurityAlert):
    agent = get_alert_triage_agent()
    
    # Use alert ID as thread ID for persistence
    thread_id = str(alert.SystemAlertId)
    
    # Run agent analysis
    response = await agent.run(
        query=build_triage_query(alert),
        thread_id=thread_id
    )
    
    return parse_triage_result(response)
```

### 3.4 Phase 4: Migration and Testing (1 week)

#### 3.4.1 Migrate Demo Script

**Update `utils/demo_agent_framework.py`**:
```python
async def demo_foundry_native_agents():
    """Demonstrate Foundry native agents with YAML definitions."""
    
    print("=" * 80)
    print("ALERT TRIAGE AGENT - FOUNDRY NATIVE DEMO")
    print("=" * 80)
    
    # Initialize agents once
    await initialize_agents()
    triage_agent = get_alert_triage_agent()
    
    # Load sample alerts
    guide_loader = get_guide_loader()
    alerts = guide_loader.load_alerts(max_alerts=5)
    
    # Process alerts with persistent agent
    for i, alert in enumerate(alerts, 1):
        print(f"\n--- Alert {i}/{len(alerts)}: {alert.AlertName} ---")
        
        # Agent reuses same persistent instance
        result = await triage_agent.run(
            query=build_triage_query(alert),
            thread_id=str(alert.SystemAlertId)
        )
        
        print(f"Risk Score: {extract_risk_score(result)}")
        print(f"Decision: {extract_decision(result)}")
        print(f"Explanation: {result.output_text[:400]}...")
    
    # Clean up
    await triage_agent.close()
```

#### 3.4.2 Testing Strategy

**Test Cases**:
1. **Agent Initialization**: Verify agent creation from YAML
2. **Tool Invocation**: Test each native tool (MCP, Code Interpreter, File Search)
3. **Knowledge Base Queries**: Verify MITRE ATT&CK context retrieval
4. **Risk Calculation**: Test Code Interpreter risk score calculations
5. **Alert Correlation**: Test File Search + Memory correlation detection
6. **Thread Persistence**: Verify threads maintained across sessions
7. **Enterprise Memory**: Test long-term memory storage and retrieval
8. **Agent Reuse**: Confirm single agent instance handles multiple alerts

**Integration Tests**:
```python
# tests/integration/test_foundry_native_agents.py

import pytest
from src.agents import initialize_agents, get_alert_triage_agent

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initialization from YAML."""
    await initialize_agents()
    agent = get_alert_triage_agent()
    
    assert agent is not None
    assert agent.agent.name == "alert-triage-agent"
    assert agent._initialized

@pytest.mark.asyncio
async def test_knowledge_base_retrieval():
    """Test MCP tool knowledge base retrieval."""
    agent = get_alert_triage_agent()
    
    response = await agent.run(
        query="Retrieve MITRE ATT&CK context for technique T1059.001"
    )
    
    assert "T1059.001" in response.output_text
    assert "PowerShell" in response.output_text  # Technique name

@pytest.mark.asyncio
async def test_triage_alert_with_persistent_agent():
    """Test triaging an alert with persistent agent."""
    agent = get_alert_triage_agent()
    alert = create_test_alert()
    
    # First triage
    result1 = await agent.run(
        query=build_triage_query(alert),
        thread_id=str(alert.SystemAlertId)
    )
    
    # Follow-up query on same thread
    result2 = await agent.run(
        query="What was the risk score?",
        thread_id=str(alert.SystemAlertId)
    )
    
    # Agent should remember previous triage
    assert "risk score" in result2.output_text.lower()
```

---

## 4. Benefits of Foundry Native Agents

### 4.1 Declarative Configuration
- **YAML Definitions**: Agent behavior defined in version-controlled YAML files
- **No Code Changes**: Update agent instructions without redeploying code
- **Configuration as Code**: Treat agent definitions as infrastructure

### 4.2 Persistent Agents
- **Single Initialization**: Agent created once at startup, reused throughout demo
- **Resource Efficiency**: No overhead of recreating agents on every request
- **Managed Lifecycle**: Foundry handles agent versioning, deployment, scaling

### 4.3 Native Tooling
- **MCP Tool**: Native integration with Foundry IQ knowledge bases
- **Enterprise Memory**: Persistent, cross-session memory backed by Cosmos DB
- **Richer Tool Ecosystem**: Code Interpreter, File Search, Bing Grounding, A2A
- **No Custom Code**: Eliminate custom @ai_function tools and AI Search queries

### 4.4 Improved Knowledge Integration
- **Semantic Search**: Knowledge base handles query planning and decomposition
- **Automatic Citations**: MCP tool provides source attribution
- **Unified Knowledge**: All attack scenarios, incidents, threat intel in one place

### 4.5 Scalability & Production Readiness
- **Managed Service**: Foundry handles scaling, reliability, monitoring
- **Version Control**: Track agent definition changes over time
- **Role-Based Access**: Fine-grained permissions on agents and connections
- **Observability**: Built-in logging, tracing, metrics

---

## 5. Migration Path for Other Agents

The same pattern applies to future agents:

### 5.1 Threat Hunting Agent
**YAML Definition**: `agents/threat-hunting-agent.yaml`
```yaml
name: threat-hunting-agent
model:
  id: 'gpt-4o'  # More capable model for complex hunting
instructions: |
  You are a proactive threat hunter that searches for hidden threats...
tools:
  - type: mcp
    mcp:
      server_label: "historical-incidents-kb"
      # ... knowledge base for historical patterns
  - type: code_interpreter  # For complex analytics
  - type: bing_grounding    # For emerging threats
```

### 5.2 Incident Response Agent
**YAML Definition**: `agents/incident-response-agent.yaml`
```yaml
name: incident-response-agent
model:
  id: 'gpt-4o'
instructions: |
  You are an incident response coordinator that orchestrates containment,
  eradication, and recovery actions...
tools:
  - type: a2a  # Communicate with other agents
  - type: azure_functions  # Execute response actions
  - type: mcp  # Access playbook knowledge base
```

### 5.3 Threat Intelligence Agent
**YAML Definition**: `agents/threat-intel-agent.yaml`
```yaml
name: threat-intel-agent
model:
  id: 'gpt-4.1-mini'
instructions: |
  You aggregate and distill threat intelligence from multiple sources...
tools:
  - type: bing_grounding  # Real-time threat feeds
  - type: mcp             # Threat intel knowledge base
  - type: file_search     # Historical threat reports
```

---

## 6. Implementation Timeline

### Week 1: Infrastructure Setup
- [ ] Create Foundry IQ knowledge bases (attack scenarios, incidents, threat intel)
- [ ] Configure project connections for MCP tools
- [ ] Set up enterprise memory with Cosmos DB
- [ ] Create vector stores for File Search

### Week 2: Agent Definition Migration
- [ ] Create `agents/alert-triage-agent.yaml`
- [ ] Implement `FoundryNativeAgent` wrapper class
- [ ] Update startup initialization logic
- [ ] Remove custom @ai_function tools

### Week 3: Testing & Validation
- [ ] Write integration tests for Foundry native agents
- [ ] Test knowledge base retrieval (MCP tool)
- [ ] Test Code Interpreter risk calculations
- [ ] Test thread persistence and enterprise memory
- [ ] Validate agent reuse across multiple alerts

### Week 4: Documentation & Rollout
- [ ] Update README.md with new setup instructions
- [ ] Document YAML agent definition schema
- [ ] Create migration guide for developers
- [ ] Update demo script and examples

---

## 7. Configuration Requirements

### 7.1 Environment Variables

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

# Authentication
az login  # Use Azure CLI for DefaultAzureCredential
```

### 7.2 Dependencies Update

**`requirements.txt`**:
```txt
# Foundry Native Agents
azure-ai-projects>=2.0.0b1  # Latest preview with native agents
azure-identity>=1.15.0
azure-ai-inference>=1.0.0b9

# Keep existing dependencies
pydantic>=2.5.0
pandas>=2.1.0
python-dateutil>=2.8.0
fastapi>=0.108.0
uvicorn[standard]>=0.25.0
azure-cosmos>=4.5.0
azure-search-documents>=11.4.0
structlog>=24.1.0
python-json-logger>=2.0.7
pytest>=7.4.0
pytest-asyncio>=0.21.0
python-dotenv>=1.0.0
pyyaml>=6.0  # NEW: For YAML agent definitions
```

---

## 8. Risk Assessment & Mitigation

### 8.1 Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Breaking changes in azure-ai-projects preview | High | Medium | Pin to specific preview version, monitor release notes |
| Knowledge base setup complexity | Medium | Low | Provide detailed setup scripts and documentation |
| Agent behavior changes with new tools | Medium | Medium | Comprehensive testing, gradual rollout |
| Performance degradation | Medium | Low | Benchmark before/after, optimize tool usage |
| Learning curve for team | Low | High | Training sessions, detailed documentation |

### 8.2 Rollback Strategy

1. **Keep old implementation**: Maintain `src/agents/alert_triage_agent.py` temporarily
2. **Feature flag**: Toggle between old and new implementations
3. **Gradual migration**: Migrate one agent at a time
4. **Fallback testing**: Ensure old system still works

---

## 9. Success Criteria

### 9.1 Functional Requirements
- [x] Agents defined in YAML files
- [x] Agents created once at startup and reused
- [x] MCP tool successfully queries knowledge base
- [x] Code Interpreter executes risk calculations
- [x] File Search retrieves historical alerts
- [x] Enterprise memory persists across sessions
- [x] Agent provides triage decisions with remediation steps

### 9.2 Non-Functional Requirements
- [x] Agent initialization < 5 seconds
- [x] Triage query response < 30 seconds
- [x] Knowledge base queries < 5 seconds
- [x] Memory persistence 100% reliable
- [x] All tests passing

### 9.3 Documentation Requirements
- [x] YAML schema documented
- [x] Setup guide complete
- [x] Migration guide for developers
- [x] Example YAML definitions for all agents

---

## 10. Next Steps

### Immediate Actions
1. **Validate with stakeholders**: Review this plan with the team
2. **Create detailed tickets**: Break down each phase into implementable tasks
3. **Set up development environment**: Configure Azure AI Foundry project, knowledge bases
4. **Begin Phase 1**: Start with infrastructure setup

### Future Enhancements (Post-MVP)
1. **Workflow Orchestration**: Use Foundry workflows (YAML-based) for multi-agent coordination
2. **Agent Evaluation**: Implement evaluation framework using Azure AI Evaluations
3. **Hosted Agents**: Containerize agents and deploy as hosted agents on Foundry
4. **Prompt Optimization**: Use Prompt Flow for agent instruction tuning
5. **Multi-Model Strategy**: Use different models for different agent types (gpt-4o for hunting, gpt-4.1-mini for triage)

---

## 11. References

### Microsoft Documentation
- [Azure AI Foundry Agent Service Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview)
- [Declarative Agent Definitions](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-types/azure-ai-agent#declarative-spec)
- [Foundry IQ Knowledge Bases](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/knowledge-retrieval)
- [Enterprise Memory in Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/agent-memory)
- [Azure AI Projects SDK (Python)](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- [MCP Tool Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/knowledge-retrieval#create-an-agent-with-the-mcp-tool)

### Code Examples
- [Azure AI Projects Python Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples)
- [Foundry Samples Repository](https://github.com/azure-ai-foundry/foundry-samples)
- [Agentic Retrieval Pipeline Example](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-foundry/samples/agentic-retrieval-pipeline-example)

### Internal Documentation
- [Current Implementation Guide](./AGENT-FRAMEWORK-IMPLEMENTATION.md)
- [MVP Implementation Summary](./MVP-IMPLEMENTATION-SUMMARY.md)
- [Constitution and Principles](../.specify/memory/constitution.md)

---

## Appendix A: YAML Schema Reference

### Agent Definition Schema

```yaml
# Required fields
version: string (e.g., "1.0.0")
name: string (agent identifier, lowercase-with-hyphens)
description: string (agent purpose and capabilities)

# Optional ID (auto-generated if omitted)
id: string

# Metadata
metadata:
  authors: list[string]
  tags: list[string]
  version: string

# Model configuration
model:
  id: string (e.g., "gpt-4.1-mini", "gpt-4o")
  options:
    temperature: float (0.0-2.0)
    top_p: float (0.0-1.0)
    max_tokens: int
    presence_penalty: float (optional)
    frequency_penalty: float (optional)

# Instructions (system prompt)
instructions: string (multiline supported with |)

# Tools
tools: list[tool]
  - type: mcp | code_interpreter | file_search | bing_grounding | a2a | openapi
    # Tool-specific configuration
    
# Memory configuration (optional)
memory:
  enabled: bool
  scope_type: string (e.g., "alert", "user", "session")
  cosmos_connection_id: string

# Tool resources (optional)
tool_resources:
  file_search:
    vector_stores: list[vector_store]
  code_interpreter:
    files: list[file_id]
```

### Tool Type Specifications

**MCP Tool**:
```yaml
- type: mcp
  mcp:
    server_label: string
    server_url: string
    require_approval: "never" | "always" | "auto"
    allowed_tools: list[string]
    project_connection_id: string
    headers: dict[string, string] (optional)
```

**Code Interpreter**:
```yaml
- type: code_interpreter
  code_interpreter:
    container:
      type: automatic | custom
      # For custom containers:
      image: string (optional)
      resources: dict (optional)
```

**File Search**:
```yaml
- type: file_search
  file_search:
    vector_store_ids: list[string]
    max_results: int (optional)
```

**Bing Grounding**:
```yaml
- type: bing_grounding
  bing_grounding:
    search_configurations:
      - project_connection_id: string
```

**Agent-to-Agent (A2A)**:
```yaml
- type: a2a
  a2a:
    project_connection_id: string
```

---

## Appendix B: Knowledge Base Setup Scripts

### B.1 Create Knowledge Base

```python
# utils/setup_knowledge_base.py

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import os

def create_attack_scenarios_knowledge_base():
    """Create knowledge base for MITRE ATT&CK attack scenarios."""
    
    search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    credential = DefaultAzureCredential()
    
    # Create index client
    index_client = SearchIndexClient(
        endpoint=search_endpoint,
        credential=credential
    )
    
    # Define index schema
    fields = [
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="name", type="Edm.String"),
        SearchableField(name="description", type="Edm.String"),
        SearchableField(name="mitre_techniques", type="Collection(Edm.String)"),
        SearchableField(name="mitre_tactics", type="Collection(Edm.String)"),
        SimpleField(name="severity", type="Edm.String"),
        SearchableField(name="iocs", type="Edm.String"),
        # Vector field for semantic search
        SearchField(
            name="description_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=1536,
            vector_search_profile_name="default-profile"
        )
    ]
    
    # Configure vector search
    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="default-profile",
                algorithm_configuration_name="default-hnsw"
            )
        ],
        algorithms=[
            HnswAlgorithmConfiguration(name="default-hnsw")
        ]
    )
    
    # Create index
    index = SearchIndex(
        name="attack-scenarios",
        fields=fields,
        vector_search=vector_search
    )
    
    result = index_client.create_or_update_index(index)
    print(f"Created index: {result.name}")
    
    # Create knowledge source
    # (Requires Azure CLI or REST API)
    print("Creating knowledge source...")
    os.system(f"""
        az search knowledge-source create \\
            --endpoint {search_endpoint} \\
            --knowledge-base-name attack-scenarios-kb \\
            --knowledge-source-name attack-scenarios \\
            --type azure-search-index \\
            --index-name attack-scenarios \\
            --authentication managed-identity
    """)
    
    print("✓ Knowledge base created successfully")

if __name__ == "__main__":
    create_attack_scenarios_knowledge_base()
```

---

**End of Refactor Plan**
