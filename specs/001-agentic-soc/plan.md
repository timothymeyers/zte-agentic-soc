# Implementation Plan: Agentic Security Operations Center (SOC) - MVP

**Branch**: `001-agentic-soc` | **Date**: 2025-11-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-agentic-soc/spec.md`

**Note**: This plan follows the `.specify` template structure and is generated per the `/speckit.plan` command workflow.

## Summary

The Agentic SOC MVP is an AI-first security operations platform that uses specialized AI agents (Alert Triage, Threat Hunting, Incident Response, Threat Intelligence) to augment human SOC analysts. The MVP will be demonstrable with simulated/mock data from the GUIDE and Attack datasets, focusing on the Alert Triage Agent as Priority 1. The system leverages Microsoft Foundry for cloud-hosted agent deployment and Microsoft Agent Framework's magentic orchestrator for demonstration workflows, following constitutional principles for safe, explainable, autonomous-but-supervised operations.

**Primary Technical Approach**: 
1. **Infrastructure Deployment** (separate process): Use `azure-ai-projects` SDK to create/discover cloud-hosted v2 agents in Microsoft Foundry, deployed as part of infrastructure setup
2. **MVP Demonstration**: Use Microsoft Agent Framework's magentic orchestrator to coordinate the deployed agents, using the GUIDE dataset (1.17M+ real security incidents) and Attack dataset (14K+ attack scenarios) for simulated scenarios
3. **Initial Focus**: Solid agent instructions to direct behavior; tools and integrations deferred to later phases
4. **Priority**: Alert Triage Agent (P1) first, then Threat Hunting (P2), Incident Response (P2), and Threat Intelligence (P3), with magentic orchestration (P1) enabling dynamic multi-agent collaboration

## Technical Context

**Language/Version**: Python 3.11+ (primary), TypeScript/Node.js 20+ (for Teams integration)  
**Primary Dependencies**: 
- `azure-ai-projects` (Latest SDK for v2 agent deployment and management in Microsoft Foundry)
- `azure-identity` (Managed Identity / Entra ID authentication)
- `agent-framework` (Microsoft Agent Framework - magentic orchestrator for MVP demonstration)
- `azure-monitor-opentelemetry` (observability)
- `pydantic` (data validation and schema management)
- `pandas` / `polars` (dataset processing for mock data)
- `fastapi` (API endpoints for human approvals/feedback - future phase)
- `azure-search-documents` (Azure AI Search for RAG knowledge base - future phase)

**AI Models** (see [MODEL-SELECTION-AOA.md](./MODEL-SELECTION-AOA.md) for full analysis):
- **MVP**: GPT-4.1-mini for all agents - cost-optimized ($190/month, avoids deprecated GPT-4o-mini)
- **Production**: Multi-model - GPT-5-nano for Triage, GPT-5 for Hunting/Response, GPT-4.1-mini for Intelligence ($251/month)

**Storage**: 
- Microsoft Sentinel incidents (shared context for agents)
- Azure Cosmos DB (agent state, audit logs, configuration)
- Microsoft Fabric (scalable telemetry storage for hunting)
- Azure Blob Storage (mock data ingestion, checkpoint files)

**Testing**: 
- `pytest` (unit and integration tests)
- `pytest-asyncio` (async test support)
- `pytest-mock` (mocking external services)
- Contract testing with JSON Schema validation
- Scenario-based testing with curated mock incidents

**Target Platform**: 
- Azure Container Apps (agent host environments)
- Microsoft Foundry (agent runtime and model orchestration)
- Azure Event Hubs (event-driven triggers for agents)
- Azure Functions (lightweight orchestration tasks, scheduled jobs)

**Project Type**: Web + API (backend services with Teams chat interface)

**Performance Goals**: 
- Alert ingestion: < 2 seconds at p95
- Alert triage processing: < 5 seconds at p95
- Containment actions: < 60 seconds at p95
- Hunt queries (Sentinel): < 30 seconds at p95
- Throughput: 10,000 alerts/day sustained (MVP)

**Constraints**: 
- MVP MUST be demonstrable with mock data only (no production integrations required)
- No Azure Logic Apps (per issue requirements)
- No Azure Durable Functions (per issue requirements)
- Mock data delivery in configurable "realtime" intervals (default: 15 seconds)
- Initial MVP: Focus on agent instructions only; NO tools or integrations initially
- Use Microsoft Agent Framework's magentic orchestrator for MVP (make it obvious where this would be changed)
- Separate infrastructure deployment (agent creation) from demonstration (agent orchestration)
- Human approval required for high-risk actions (risk-scored threshold - future phase)
- All agent decisions MUST include natural language explanations

**Scale/Scope**: 
- MVP: 4 core agents + orchestration layer
- ~10K lines of Python code estimated
- Support 10,000 alerts/day throughput
- Demonstrable end-to-end scenarios (alert ingestion → triage → hunting → containment → intelligence)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **MVP/POC Scope**: Yes - System is demonstrable with GUIDE and Attack datasets (1.17M+ mock incidents). Clear "plugin points" defined for production integration (Sentinel API, Defender XDR API, Entra ID API). All integrations abstracted behind interfaces.

- [x] **AI-First Security Operations**: Yes - Four core agents (Alert Triage, Threat Hunting, Incident Response, Threat Intelligence) implemented using Microsoft Foundry. Each agent is a top-level AI agent that may be composed of sub-agents, tools (KQL query generator, IOC enrichment), or knowledge sources (Attack dataset, MITRE ATT&CK mappings).

- [x] **Agent Collaboration & Orchestration**: Yes - Microsoft Agent Framework orchestrates agent-to-agent communication. Context passed via Sentinel incident objects and Cosmos DB shared state. Event-driven triggers via Event Hubs. Escalation to humans via Teams approval workflows.

- [x] **Autonomous-but-Supervised Operations**: Yes - Agents operate autonomously for low-risk actions (alert correlation, hunting queries, intelligence enrichment). Human approval gates implemented using risk-scored threshold for high-risk actions (account disabling, endpoint isolation affecting critical systems). All actions logged with full audit trail in Cosmos DB.

- [x] **Proactive Threat Detection**: Yes - Threat Hunting Agent performs scheduled automated hunts independent of alerts. Natural language interface for analyst-driven hunts. Anomaly detection using ML models trained on GUIDE dataset patterns.

- [x] **Continuous Context Sharing**: Yes - All agents read/write to Sentinel incidents for shared context. Threat Intelligence Agent outputs automatically available to Triage and Hunting agents via shared knowledge base in Cosmos DB. Incident Response Agent actions visible to all agents via event publication.

- [x] **Explainability & Transparency**: Yes - Every agent action includes natural language explanation generated using Azure OpenAI GPT-4. Alert prioritization shows contributing risk factors. Hunting findings explain detected anomaly patterns. Response recommendations cite threat intelligence or past incidents. All explanations stored in Sentinel incident comments.

- [x] **Continuous Learning & Adaptation**: Yes - Alert Triage Agent incorporates analyst feedback via feedback API endpoint. Threat Intelligence Agent continuously ingests new threat data from Attack dataset updates. Models versioned in Azure ML registry. A/B testing not required for MVP but plugin point defined.

- [x] **Observability & Operational Excellence**: Yes - Structured logging with Azure Monitor and Application Insights. Metrics for latency, throughput, error rates, agent-specific KPIs. Distributed tracing with correlation IDs. Dashboards in Azure Monitor. Health endpoints for all services. Runbooks for common scenarios documented in `/docs/runbooks/`.

- [x] **Technology Stack**: Yes - Microsoft Foundry for all agents. Microsoft Agent Framework for orchestration. Microsoft Fabric considered for telemetry storage (Sentinel + Fabric hybrid approach). Logic Apps avoided. Alert Triage, Hunting, Response, and Intelligence agents properly implemented.

- [x] **Code Quality & CI/CD**: Yes - GitHub Actions CI/CD pipeline with automated testing, linting (black, pylint, mypy), security scanning (Dependabot, CodeQL). 80%+ unit test coverage enforced. Infrastructure as Code using Bicep. Automated deployment with approval gates.

- [x] **Testing**: Yes - Unit tests with pytest (80%+ coverage target). Integration tests for agent communication. Contract tests with JSON Schema validation. Scenario tests with curated mock incidents. Edge cases covered (API failures, insufficient data, conflicting recommendations, zero-day threats, insider threats).

- [x] **Documentation**: Yes - Architecture diagrams included (System Context, Component, Deployment, Data Flow, Sequence) in AgenticSOC_Architecture.md. API contracts documented with OpenAPI specs in `/contracts/`. Agent input/output schemas in `/schemas/`. README with setup instructions. ADRs for key decisions.

- [x] **Production Deployment**: N/A for MVP - MVP uses mock data and does not require production deployment. However, production deployment guidance documented: Azure Landing Zone architecture, Azure Verified Modules, Cloud Adoption Framework alignment, Well-Architected Framework principles. Plugin points clearly defined for production integration.

- [x] **Security & Compliance**: Yes - Azure Managed Identity with Entra ID RBAC (recommended primary approach) OR service principals with least-privilege permissions for agent authentication. Managed Identity recommended for production; service principals with Key Vault may be used as alternative when Managed Identity is not available. Encrypted communication (HTTPS, Azure Private Link). Data classification respected. Sensitive data not logged in plaintext. Audit logs immutable. Data retention configurable (MVP default: 5 days).

*All constitutional principles are satisfied for the MVP scope.*

## Implementation Approach: Two-Phase Architecture

The MVP follows a clear separation between infrastructure deployment and demonstration orchestration:

### Phase A: Infrastructure Deployment (One-time Setup)

**Purpose**: Create and configure cloud-hosted v2 agents in Microsoft Foundry

**Tools**: `azure-ai-projects` SDK (version 2.0.0b2 or later)

**Process**:
1. Connect to existing Microsoft Foundry workspace via environment variables (`PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME`) or deploy new workspace if not available
2. Use `AIProjectClient.agents.create_version()` to create persistent v2 agents:
   - Alert Triage Agent with instructions for risk scoring and prioritization
   - Threat Hunting Agent with instructions for query generation and anomaly detection
   - Incident Response Agent with instructions for containment recommendations
   - Threat Intelligence Agent with instructions for threat briefing generation
   - Manager/Coordinator Agent with instructions for task coordination and agent selection
3. Each agent is created with:
   - Clear name (e.g., "AlertTriageAgent")
   - Detailed instructions (system prompt defining behavior)
   - Model deployment reference (e.g., "gpt-4.1-mini")
   - NO tools initially (focus on instruction quality) - tools will be added in later phases
4. Agents persist in Microsoft Foundry and can be discovered by name/ID

**Output**: Cloud-hosted agents that can be referenced by name in demonstration code

### Phase B: MVP Demonstration (Runtime Orchestration)

**Purpose**: Orchestrate the deployed agents to demonstrate SOC workflows

**Tools**: Microsoft Agent Framework with magentic orchestrator

**Process**:
1. Discover deployed agents using `AIProjectClient.agents.get_agent()` or list operations:
   ```python
   from azure.ai.projects import AIProjectClient
   from azure.identity import DefaultAzureCredential
   
   # Connect to Foundry and discover deployed agents
   project_client = AIProjectClient(
       endpoint=os.environ["PROJECT_ENDPOINT"],
       credential=DefaultAzureCredential()
   )
   
   # Get all deployed agents (including manager)
   triage_agent = project_client.agents.get_agent(agent_name="AlertTriageAgent")
   hunting_agent = project_client.agents.get_agent(agent_name="ThreatHuntingAgent")
   response_agent = project_client.agents.get_agent(agent_name="IncidentResponseAgent")
   intel_agent = project_client.agents.get_agent(agent_name="ThreatIntelligenceAgent")
   manager_agent = project_client.agents.get_agent(agent_name="SOC_Coordinator")
   ```

2. Wrap discovered Foundry agents in Agent Framework wrappers (if needed for magentic orchestration)

3. Build magentic workflow using the deployed manager agent:
   ```python
   from agent_framework import MagenticBuilder
   
   # Build magentic workflow with discovered agents
   workflow = (
       MagenticBuilder()
       .participants(
           triage=triage_agent,
           hunting=hunting_agent,
           response=response_agent,
           intel=intel_agent
       )
       .with_standard_manager(
           agent=manager_agent,  # Use the deployed manager agent from Foundry
           max_round_count=10,
           max_stall_count=3
       )
       .build()
   )
   ```
4. Stream mock data (GUIDE/Attack datasets) to trigger workflows
5. Manager agent (deployed in Phase A with coordination instructions) dynamically selects which agent to invoke based on task context
6. **Note on triage-first behavior**: Manager agent's deployed instructions enforce "ALWAYS start with Triage agent" - no runtime ChatAgent creation needed

**Output**: Demonstrable SOC scenarios showing multi-agent collaboration

### Agent Design Philosophy: Instructions > Code

**What Agents ARE**:
- **Instruction sets**: Detailed markdown files with system prompts guiding LLM behavior
- **LLM-powered reasoning**: The model performs analysis, decision-making, and generation
- **Stateless participants**: Each invocation receives context, produces output via LLM

**What Agents ARE NOT**:
- ❌ **NOT** traditional Python classes with business logic methods
- ❌ **NOT** deterministic algorithms (risk scoring, query parsing, etc.)
- ❌ **NOT** rule engines or state machines
- ❌ **NOT** tools/plugins (initially - deferred to future phases)

**Example - Alert Triage Agent**:
```markdown
# Alert Triage Agent Instructions

You are an expert SOC analyst specializing in alert triage and prioritization.

## Your Role
Analyze security alerts and provide risk assessment with clear reasoning.

## Input Format
You will receive security alerts in JSON format with fields:
- alertId, timestamp, source, severity, description, entities (IPs, users, hosts)

## Your Tasks
1. Assess risk level (Critical/High/Medium/Low) based on:
   - Severity indicators (data exfiltration, lateral movement, privilege escalation)
   - Asset criticality (production systems, sensitive data repositories)
   - User context (privileged accounts, external access)
   - Historical patterns (repeat offender, known false positive source)

2. Provide clear explanation of your risk assessment
3. Identify any related alerts that should be correlated
4. Suggest immediate next steps for SOC analyst

## Output Format
Provide your analysis as JSON:
{
  "riskLevel": "High",
  "explanation": "This alert shows...",
  "relatedAlerts": [...],
  "nextSteps": [...]
}
```

**The LLM handles ALL logic** - risk assessment, correlation detection, reasoning - based on these instructions.

### Design Rationale

**Why Separate Deployment from Demonstration?**
- **Infrastructure-as-Code**: Agent definitions are versioned and deployed like any other cloud resource
- **Reusability**: Same agents can be orchestrated in different patterns (sequential, concurrent, magentic)
- **Scalability**: Deployed agents can handle concurrent requests from multiple orchestration instances
- **Flexibility**: Easy to swap orchestration strategies without redeploying agents

**Why Magentic Orchestrator for MVP?**
- **Dynamic Coordination**: Manager agent selects next agent based on evolving context (vs. hardcoded sequences)
- **Handles Uncertainty**: Well-suited for security scenarios where solution path is not predetermined
- **Human-in-the-Loop**: Built-in support for approval gates and stall intervention
- **Future-Proof**: Clear extension point - replace magentic with custom orchestrator in production
- **Triage-First Pattern**: Manager instructions can enforce "always start with triage" behavior, or implement custom manager for guaranteed routing

**Ensuring Triage Agent Goes First**:
Since the manager agent is deployed as a Foundry v2 agent (same as other agents), triage-first behavior is controlled via its deployed instructions:

1. **Via Manager Agent Instructions** (Recommended for MVP - simpler):
   - Manager agent deployed with instructions that explicitly state "ALWAYS start with the Triage agent"
   - Instructions baked into the deployed agent at infrastructure deployment time (Phase A)
   - Relies on LLM to follow its own instructions consistently
   - Example instruction content in `manager_instructions.md`:
     ```markdown
     You coordinate SOC agents. For each security task:
     1. ALWAYS start with the Triage agent to assess the alert
     2. Based on triage results, delegate to appropriate agents...
     ```
   - Pro: Simpler implementation, consistent with agent-as-instruction philosophy, leverages LLM reasoning
   - Con: Depends on LLM compliance with instructions (though this is true for all agents)

2. **Custom Manager Implementation** (Advanced option if LLM routing insufficient):
   - Deploy a standard manager agent, but wrap it with custom orchestration logic at runtime
   - Custom wrapper can enforce triage-first before delegating to magentic manager
   - Example:
     ```python
     async def run_workflow(task):
         # Force triage first
         triage_result = await triage_agent.run(task)
         
         # Then use magentic orchestration for remaining agents
         workflow_result = await workflow.run(
             f"Based on triage: {triage_result}, proceed with investigation"
         )
     ```
   - Pro: Guaranteed execution order without custom manager agent
   - Con: Adds orchestration wrapper code outside the agent paradigm

**Where to Change Orchestration Strategy** (Explicit Plugin Point):
- File: `src/orchestration/orchestrator.py`
- Function: `create_workflow()` 
- Current: Uses `MagenticBuilder` from Agent Framework
- Future Options:
  - Sequential orchestration for predictable workflows
  - Concurrent orchestration for parallel agent execution
  - Custom orchestrator implementing business-specific logic
  - Production: Replace with Azure Durable Functions or Logic Apps if scale requires

## Project Structure

### Documentation (this feature)

```text
specs/001-agentic-soc/
├── spec.md                          # Feature specification (existing)
├── AgenticSOC_Architecture.md       # Architecture assessment (existing)
├── PRE-IMPLEMENTATION-TODO.md       # Pre-implementation checklist (existing)
├── plan.md                          # This file (implementation plan)
├── research.md                      # Phase 0: Technology research and decisions
├── data-model.md                    # Phase 1: Entity and schema definitions
├── quickstart.md                    # Phase 1: Setup and demo instructions
├── contracts/                       # Phase 1: API contracts
│   ├── orchestrator-api.yaml        # Orchestrator REST API (approval, feedback)
│   ├── alert-triage-schema.json     # Triage agent I/O schema
│   ├── threat-hunting-schema.json   # Hunting agent I/O schema
│   ├── incident-response-schema.json # Response agent I/O schema
│   └── threat-intelligence-schema.json # Intelligence agent I/O schema
├── dataset-analysis/                # Dataset analysis docs (existing)
└── checklists/                      # Requirements tracking (existing)
```

### Source Code (repository root)

```text
# Backend services and agents
src/
├── deployment/                      # Phase A: Infrastructure deployment (one-time)
│   ├── __init__.py
│   ├── deploy_agents.py             # Script to deploy v2 agents to Foundry using azure-ai-projects
│   └── agent_definitions/           # Agent instruction files (system prompts) - THE CORE OF EACH AGENT
│       ├── alert_triage_instructions.md     # Instructions for alert triage, risk scoring, prioritization
│       ├── threat_hunting_instructions.md   # Instructions for threat hunting, query formulation, anomaly detection
│       ├── incident_response_instructions.md # Instructions for containment, remediation recommendations
│       ├── threat_intelligence_instructions.md # Instructions for briefings, IOC enrichment
│       └── manager_instructions.md          # Manager agent instructions (enforces triage-first, agent selection)
├── orchestration/                   # Phase B: Runtime orchestration (demonstration)
│   ├── __init__.py
│   ├── orchestrator.py              # Magentic orchestrator setup (PLUGIN POINT - change here for different orchestration)
│   └── workflows.py                 # Pre-defined workflow scenarios (alert triage, threat hunt, incident response)
├── data/                            # Data access layer
│   ├── __init__.py
│   ├── datasets.py                  # Mock data loader (GUIDE, Attack datasets)
│   └── scenarios.py                 # Pre-defined test scenarios for demonstration
├── shared/                          # Shared utilities
│   ├── __init__.py
│   ├── auth.py                      # Authentication (Managed Identity)
│   └── logging.py                   # Structured logging setup
└── demo/                            # Demo application (entry point)
    ├── __init__.py
    ├── main.py                      # Main demo script - runs workflows with mock data
    ├── scenarios/                   # Demo scenarios
    │   ├── scenario_01_alert_triage.py
    │   ├── scenario_02_threat_hunt.py
    │   └── scenario_03_incident_response.py
    └── cli.py                       # CLI for running demos and managing agents

# Infrastructure as Code
infra/
├── main.bicep                       # Main infrastructure template
├── modules/                         # Bicep modules
│   ├── microsoft-foundry.bicep             # AI Foundry workspace
│   ├── container-apps.bicep         # Container Apps for agents
│   ├── cosmos.bicep                 # Cosmos DB
│   ├── event-hubs.bicep             # Event Hubs for triggers
│   └── monitoring.bicep             # Application Insights, Log Analytics
└── parameters/                      # Environment-specific parameters
    ├── dev.parameters.json
    └── prod.parameters.json

# Testing
tests/
├── unit/                            # Unit tests (80%+ coverage)
│   ├── test_alert_triage.py
│   ├── test_threat_hunting.py
│   ├── test_incident_response.py
│   ├── test_threat_intelligence.py
│   └── test_orchestrator.py
├── integration/                     # Integration tests
│   ├── test_agent_collaboration.py  # Agent-to-agent communication
│   ├── test_data_access.py          # Data layer tests
│   └── test_workflows.py            # End-to-end workflow tests
├── contract/                        # Contract tests
│   ├── test_schemas.py              # JSON Schema validation
│   └── test_api_contracts.py        # OpenAPI validation
└── scenarios/                       # Scenario-based tests
    ├── test_scenario_01_basic_triage.py
    ├── test_scenario_02_hunting_workflow.py
    └── test_scenario_03_containment.py

# Configuration and deployment
.github/
└── workflows/
    ├── ci.yml                       # CI pipeline (test, lint, build)
    ├── cd-dev.yml                   # Deploy to dev environment
    └── cd-prod.yml                  # Deploy to prod (with approval)

# Schemas (input/output contracts)
schemas/
├── alert-triage-input.schema.json
├── alert-triage-output.schema.json
├── threat-hunting-input.schema.json
├── threat-hunting-output.schema.json
├── incident-response-input.schema.json
├── incident-response-output.schema.json
├── threat-intelligence-input.schema.json
└── threat-intelligence-output.schema.json

# Documentation
docs/
├── architecture/                    # Architecture diagrams (Mermaid)
│   ├── system-context.md
│   ├── component-diagram.md
│   ├── deployment-diagram.md
│   ├── data-flow.md
│   └── sequence-diagrams.md
├── runbooks/                        # Operational runbooks
│   ├── incident-escalation.md
│   ├── agent-failure-recovery.md
│   └── scaling-guidance.md
├── adr/                             # Architecture Decision Records
│   ├── 001-ai-foundry-vs-custom.md
│   ├── 002-orchestration-approach.md
│   └── 003-mock-data-strategy.md
└── setup.md                         # Development setup guide
```

**Structure Decision**: Minimal structure focused on agent instructions and orchestration. Agents are defined primarily by their instruction sets (markdown files), not custom Python logic. The LLM handles all reasoning, decision-making, and analysis based on the instructions. Python code is limited to:
1. Deployment scripts (using azure-ai-projects SDK)
2. Orchestration setup (using agent-framework magentic orchestrator)
3. Mock data loading and streaming
4. Demo scenarios and CLI

NO custom business logic modules (risk scoring, query generation, etc.) - the LLM does this via instructions.

## Complexity Tracking

> **No violations - table intentionally left empty**

No constitutional violations requiring justification. All complexity is inherent to the problem domain (multi-agent coordination, security operations, real-time event processing) and aligned with constitutional principles.

## Phase 0: Research & Technology Decisions (✅ Complete - Updated)

The `research.md` has been updated with all identified research areas. All technology decisions are finalized and documented:

1. **Azure AI Projects SDK (azure-ai-projects 2.0.0b2+)**: ✅ Complete
   - ✅ V2 agent deployment with `AIProjectClient.agents.create_version()`
   - ✅ Agent discovery and listing patterns (`get_agent()`, `list_agents()`, `list_versions()`)
   - ✅ Separation of deployment from orchestration (Phase A vs Phase B)
   - ✅ Integration with OpenAI client for conversations
   - Documentation: Section 9 in research.md

2. **Microsoft Agent Framework - Magentic Orchestration**: ✅ Complete
   - ✅ Magentic orchestration patterns and core concepts
   - ✅ Configuration: `MagenticBuilder`, `with_standard_manager()`, participant agents
   - ✅ Human-in-the-loop: Plan review, tool approval, stall intervention
   - ✅ Event streaming: `AgentRunUpdateEvent` with `magentic_event_type`
   - ✅ Manager agent instructions for enforcing triage-first behavior
   - Documentation: Section 10 in research.md

3. **Agent Instructions (System Prompts)**: ✅ Complete
   - ✅ Best practices for writing agent instructions
   - ✅ Instruction template structure with examples
   - ✅ Alert Triage: Comprehensive example with risk scoring, correlation logic
   - ✅ Guidelines for other agents: Hunting, Response, Intelligence, Manager
   - ✅ Safety guardrails and "give an out" patterns
   - ✅ Structured output formats (JSON schemas in instructions)
   - Documentation: Section 11 in research.md

4. **Mock Data Strategy**: ✅ Complete
   - ✅ GUIDE and Attack datasets (already covered in Section 5)
   - ✅ Async generator-based streaming simulation with configurable intervals
   - ✅ Checkpoint-based replay for reproducible demos
   - ✅ Scenario-based test data (curated scenarios: brute force, phishing, ransomware)
   - ✅ Stream controller interface (pause, resume, reset, jump to index)
   - Documentation: Section 12 in research.md

5. **Orchestration Plugin Points**: ✅ Complete
   - ✅ Clear plugin point location (`src/orchestration/orchestrator.py`)
   - ✅ Current: Magentic orchestrator implementation
   - ✅ Alternatives: Sequential, concurrent, custom orchestrators
   - ✅ Migration path: Agent Framework → Azure Durable Functions/Logic Apps
   - ✅ Configuration-based strategy selection
   - ✅ Comparison matrix for orchestration strategies
   - Documentation: Section 13 in research.md

## Phase 1: Design Artifacts (Completed - Update Required)

The existing Phase 1 artifacts need updates to reflect the new approach:

- ✅ `data-model.md`: Already completed - covers Alert, Incident, Finding, IOC, Agent State
- ⚠️ `contracts/`: **UPDATE NEEDED** - Add agent instruction templates as "contracts"
  - Current: JSON schemas for agent I/O
  - Add: Markdown files with agent instruction templates
  - Add: Manager agent instruction template
- ⚠️ `quickstart.md`: **MAJOR UPDATE NEEDED** - Rewrite for two-phase approach
  - Section 1: Deploy agents to Foundry (Phase A)
  - Section 2: Run demonstration workflows (Phase B)
  - Section 3: Customize agent instructions
  - Section 4: Change orchestration strategy (plugin point)
- [ ] Agent context updates via `update-agent-context.sh` - TO BE EXECUTED

## Phase 2: Implementation Tasks (Future)

Phase 2 will generate `tasks.md` with implementation work breakdown (not created by this plan command).

Key implementation tasks will include:
1. **Agent Instructions** (PRIORITY 1): High-quality instruction sets for each agent
   - Alert Triage: Risk assessment, prioritization, correlation guidance
   - Threat Hunting: Query formulation, anomaly detection patterns
   - Incident Response: Containment recommendations, playbook guidance
   - Threat Intelligence: Briefing structure, IOC enrichment
   - Manager: Task decomposition, agent selection criteria
2. **Deployment Scripts**: Simple Python scripts using `azure-ai-projects` to deploy v2 agents
3. **Magentic Orchestrator**: Setup using `MagenticBuilder` from Agent Framework
4. **Mock Data Streaming**: Load and stream data from GUIDE/Attack datasets
5. **Demo Scenarios**: End-to-end workflows showcasing multi-agent collaboration
6. **Plugin Points**: Clear documentation for swapping orchestration strategies

---

## Key Changes from Original Plan

This updated plan incorporates new requirements from the issue:

### Architecture Changes
1. **Deployment Separation**: Infrastructure deployment (azure-ai-projects) is now separate from demonstration orchestration (agent-framework)
2. **V2 Agents**: Use cloud-hosted persistent agents created with `AIProjectClient.agents.create_version()`
3. **Magentic Orchestration**: Replace generic "Microsoft Agent Framework orchestration" with specific magentic orchestrator pattern
4. **Plugin Point**: Explicit documentation of where/how to change orchestration strategy

### Implementation Focus
1. **Instructions First**: MVP focuses on high-quality agent instructions; NO tools/integrations initially
2. **LLM Does the Logic**: Agents use LLM reasoning for ALL decisions - no custom Python business logic
3. **Priority 1: Triage Agent**: Start with Alert Triage Agent instruction quality as the primary focus
4. **Mock Data**: Use provided datasets in `mock-data/` directory with configurable streaming
5. **Demonstrable Quickly**: Two-phase approach enables faster demonstration without full infrastructure
6. **Simple = Better**: Minimal Python code; maximum instruction clarity

### SDK Updates (Verified via Context7)
1. **azure-ai-projects 2.0.0b2+**: Latest SDK for v2 agent deployment
2. **agent-framework**: Microsoft Agent Framework with magentic orchestration capabilities
3. **Foundry Agents**: Persistent, cloud-hosted agents vs. ephemeral local instances

### Documentation Updates Needed
1. **research.md**: Add magentic orchestration section, update azure-ai-projects patterns
2. **quickstart.md**: Rewrite for two-phase setup (deploy agents, then run demos)
3. **contracts/**: Add agent instruction templates as deployment "contracts"

---

**Status**: Plan updated to reflect new MVP requirements. Next steps:
1. Update `research.md` with magentic orchestration and azure-ai-projects patterns
2. Rewrite `quickstart.md` for two-phase approach
3. Create agent instruction template files
4. Run `update-agent-context.sh` to update copilot context
