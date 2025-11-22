# Implementation Plan: Agentic Security Operations Center (SOC) - MVP

**Branch**: `001-agentic-soc` | **Date**: 2025-11-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-agentic-soc/spec.md`

**Note**: This plan follows the `.specify` template structure and is generated per the `/speckit.plan` command workflow.

## Summary

The Agentic SOC MVP is an AI-first security operations platform that uses specialized AI agents (Alert Triage, Threat Hunting, Incident Response, Threat Intelligence) to augment human SOC analysts. The MVP will be demonstrable with simulated/mock data from the GUIDE and Attack datasets, focusing on the Alert Triage Agent as Priority 1. The system leverages Microsoft Foundry (AI Foundry) for agent implementation, Microsoft Agent Framework for orchestration, and follows constitutional principles for safe, explainable, autonomous-but-supervised operations.

**Primary Technical Approach**: Build four specialized AI agents on Azure AI Foundry with Microsoft Agent Framework orchestration, using the GUIDE dataset (1.17M+ real security incidents) and Attack dataset (14K+ attack scenarios) for training and demonstration. Start with Alert Triage Agent (P1), then add Threat Hunting (P2), Incident Response (P2), and Threat Intelligence (P3), with agent collaboration orchestration (P1) enabling seamless multi-agent workflows.

## Technical Context

**Language/Version**: Python 3.11+ (primary), TypeScript/Node.js 20+ (for Teams integration)  
**Primary Dependencies**: 
- `azure-ai-projects` (AI Foundry Client SDK)
- `azure-identity` (Managed Identity / Entra ID authentication)
- `agent-framework` (Microsoft Agent Framework - replaces langchain/semantic-kernel)
- `azure-monitor-opentelemetry` (observability)
- `pydantic` (data validation and schema management)
- `pandas` / `polars` (dataset processing)
- `fastapi` (API endpoints for human approvals/feedback)
- `azure-search-documents` (Azure AI Search for RAG knowledge base)

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
- Azure AI Foundry (agent runtime and model orchestration)
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
- Human approval required for high-risk actions (risk-scored threshold)
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

- [x] **AI-First Security Operations**: Yes - Four core agents (Alert Triage, Threat Hunting, Incident Response, Threat Intelligence) implemented using Azure AI Foundry. Each agent is a top-level AI agent that may be composed of sub-agents, tools (KQL query generator, IOC enrichment), or knowledge sources (Attack dataset, MITRE ATT&CK mappings).

- [x] **Agent Collaboration & Orchestration**: Yes - Microsoft Agent Framework orchestrates agent-to-agent communication. Context passed via Sentinel incident objects and Cosmos DB shared state. Event-driven triggers via Event Hubs. Escalation to humans via Teams approval workflows.

- [x] **Autonomous-but-Supervised Operations**: Yes - Agents operate autonomously for low-risk actions (alert correlation, hunting queries, intelligence enrichment). Human approval gates implemented using risk-scored threshold for high-risk actions (account disabling, endpoint isolation affecting critical systems). All actions logged with full audit trail in Cosmos DB.

- [x] **Proactive Threat Detection**: Yes - Threat Hunting Agent performs scheduled automated hunts independent of alerts. Natural language interface for analyst-driven hunts. Anomaly detection using ML models trained on GUIDE dataset patterns.

- [x] **Continuous Context Sharing**: Yes - All agents read/write to Sentinel incidents for shared context. Threat Intelligence Agent outputs automatically available to Triage and Hunting agents via shared knowledge base in Cosmos DB. Incident Response Agent actions visible to all agents via event publication.

- [x] **Explainability & Transparency**: Yes - Every agent action includes natural language explanation generated using Azure OpenAI GPT-4. Alert prioritization shows contributing risk factors. Hunting findings explain detected anomaly patterns. Response recommendations cite threat intelligence or past incidents. All explanations stored in Sentinel incident comments.

- [x] **Continuous Learning & Adaptation**: Yes - Alert Triage Agent incorporates analyst feedback via feedback API endpoint. Threat Intelligence Agent continuously ingests new threat data from Attack dataset updates. Models versioned in Azure ML registry. A/B testing not required for MVP but plugin point defined.

- [x] **Observability & Operational Excellence**: Yes - Structured logging with Azure Monitor and Application Insights. Metrics for latency, throughput, error rates, agent-specific KPIs. Distributed tracing with correlation IDs. Dashboards in Azure Monitor. Health endpoints for all services. Runbooks for common scenarios documented in `/docs/runbooks/`.

- [x] **Technology Stack**: Yes - Azure AI Foundry (AI Foundry Client SDK) for all agents. Microsoft Agent Framework for orchestration. Microsoft Fabric considered for telemetry storage (Sentinel + Fabric hybrid approach). Logic Apps avoided. Alert Triage, Hunting, Response, and Intelligence agents properly implemented.

- [x] **Code Quality & CI/CD**: Yes - GitHub Actions CI/CD pipeline with automated testing, linting (black, pylint, mypy), security scanning (Dependabot, CodeQL). 80%+ unit test coverage enforced. Infrastructure as Code using Bicep. Automated deployment with approval gates.

- [x] **Testing**: Yes - Unit tests with pytest (80%+ coverage target). Integration tests for agent communication. Contract tests with JSON Schema validation. Scenario tests with curated mock incidents. Edge cases covered (API failures, insufficient data, conflicting recommendations, zero-day threats, insider threats).

- [x] **Documentation**: Yes - Architecture diagrams included (System Context, Component, Deployment, Data Flow, Sequence) in AgenticSOC_Architecture.md. API contracts documented with OpenAPI specs in `/contracts/`. Agent input/output schemas in `/schemas/`. README with setup instructions. ADRs for key decisions.

- [x] **Production Deployment**: N/A for MVP - MVP uses mock data and does not require production deployment. However, production deployment guidance documented: Azure Landing Zone architecture, Azure Verified Modules, Cloud Adoption Framework alignment, Well-Architected Framework principles. Plugin points clearly defined for production integration.

- [x] **Security & Compliance**: Yes - Azure Managed Identity with Entra ID RBAC for authentication. Service principals with Key Vault as fallback. Encrypted communication (HTTPS, Azure Private Link). Data classification respected. Sensitive data not logged in plaintext. Audit logs immutable. Data retention configurable (MVP default: 5 days).

*All constitutional principles are satisfied for the MVP scope.*

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
├── agents/                          # AI agent implementations
│   ├── alert_triage/                # Alert Triage Agent (P1)
│   │   ├── __init__.py
│   │   ├── agent.py                 # Main agent logic (AI Foundry)
│   │   ├── models.py                # Input/output models (Pydantic)
│   │   ├── scoring.py               # Risk scoring logic
│   │   └── feedback.py              # Analyst feedback processing
│   ├── threat_hunting/              # Threat Hunting Agent (P2)
│   │   ├── __init__.py
│   │   ├── agent.py                 # Main agent logic
│   │   ├── query_generator.py       # KQL query generation
│   │   └── anomaly_detector.py      # Anomaly detection models
│   ├── incident_response/           # Incident Response Agent (P2)
│   │   ├── __init__.py
│   │   ├── agent.py                 # Main agent logic
│   │   ├── playbooks.py             # Response playbook execution
│   │   └── approval.py              # Human approval workflows
│   └── threat_intelligence/         # Threat Intelligence Agent (P3)
│       ├── __init__.py
│       ├── agent.py                 # Main agent logic
│       ├── enrichment.py            # IOC enrichment
│       └── briefing.py              # Daily briefing generation
├── orchestration/                   # Agent orchestration layer
│   ├── __init__.py
│   ├── orchestrator.py              # Microsoft Agent Framework orchestrator
│   ├── event_handlers.py            # Event-driven triggers
│   └── workflows.py                 # Multi-agent workflows
├── data/                            # Data access layer
│   ├── __init__.py
│   ├── sentinel.py                  # Sentinel API client (mock for MVP)
│   ├── fabric.py                    # Fabric query interface (mock for MVP)
│   ├── cosmos.py                    # Cosmos DB client (state, config, audit)
│   └── datasets.py                  # Mock data loader (GUIDE, Attack datasets)
├── api/                             # REST API for human interaction
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── routes/                      # API routes
│   │   ├── approval.py              # Approval workflows
│   │   ├── feedback.py              # Analyst feedback
│   │   └── hunting.py               # Interactive hunting
│   └── models.py                    # API request/response models
├── shared/                          # Shared utilities
│   ├── __init__.py
│   ├── auth.py                      # Authentication (Managed Identity)
│   ├── logging.py                   # Structured logging setup
│   ├── metrics.py                   # Metrics collection
│   └── schemas.py                   # Shared schemas (Pydantic models)
└── mock/                            # Mock service implementations
    ├── __init__.py
    ├── sentinel_mock.py             # Mock Sentinel API
    ├── defender_mock.py             # Mock Defender XDR API
    └── stream.py                    # Mock data streaming (15s intervals)

# Infrastructure as Code
infra/
├── main.bicep                       # Main infrastructure template
├── modules/                         # Bicep modules
│   ├── ai-foundry.bicep             # AI Foundry workspace
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

**Structure Decision**: Web + API structure selected. Backend contains all agent logic, orchestration, and data access. API layer provides REST endpoints for human interaction (approval workflows, feedback submission, interactive hunting). Infrastructure defined as Bicep templates. Comprehensive testing structure with unit, integration, contract, and scenario tests. Schemas directory for formal input/output contracts. Documentation includes architecture diagrams, runbooks, and ADRs.

## Complexity Tracking

> **No violations - table intentionally left empty**

No constitutional violations requiring justification. All complexity is inherent to the problem domain (multi-agent coordination, security operations, real-time event processing) and aligned with constitutional principles.

## Phase 0: Research & Technology Decisions (Next Step)

The next phase will generate `research.md` covering:

1. **Microsoft Foundry / AI Foundry Integration**:
   - AI Foundry Client SDK usage patterns
   - Agent deployment models (Container Apps vs Functions)
   - Model selection (GPT-4 for reasoning, embeddings for similarity)

2. **Microsoft Agent Framework**:
   - Agent-to-agent communication patterns
   - State management and context passing
   - Event-driven orchestration with Event Hubs

3. **Security Copilot Integration** (for production):
   - Copilot API integration patterns
   - Skills development for custom agents
   - Prompt engineering best practices

4. **KQL Query Patterns**:
   - Natural language to KQL translation
   - Common threat hunting queries
   - Advanced hunting query optimization

5. **Mock Data Strategy**:
   - GUIDE dataset transformation to Sentinel format
   - Attack dataset usage for playbook generation
   - Configurable streaming intervals (default 15s)
   - Checkpoint-based replay for reproducible demos

6. **Threat Intelligence Sources**:
   - MITRE ATT&CK technique mappings
   - IOC enrichment patterns
   - Threat briefing generation

7. **Observability Patterns**:
   - Structured logging with Application Insights
   - Distributed tracing with correlation IDs
   - Agent performance metrics and dashboards

## Phase 1: Design Artifacts (Future)

Phase 1 will generate:

- `data-model.md`: Entity definitions (Alert, Incident, Finding, IOC, Agent State)
- `contracts/`: OpenAPI specs and JSON schemas for all agent interfaces
- `quickstart.md`: Step-by-step setup and demo instructions
- Agent context updates via `update-agent-context.sh`

## Phase 2: Implementation Tasks (Future)

Phase 2 will generate `tasks.md` with implementation work breakdown (not created by this plan command).

---

**Status**: Phase 0 (Research) is the next step. Run Phase 0 workflow to generate `research.md`.
