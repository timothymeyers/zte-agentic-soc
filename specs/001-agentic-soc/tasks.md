# Tasks: Agentic Security Operations Center (SOC) - MVP

**Input**: Design documents from `/specs/001-agentic-soc/`  
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Branch**: `001-agentic-soc`  
**Date**: 2025-12-18

**Tests**: Tests are OPTIONAL and NOT included in this task list per MVP scope. Focus is on demonstrable functionality with mock data.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story following the two-phase architecture (Phase A: Infrastructure Deployment, Phase B: Runtime Orchestration).

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- **No story label**: Setup, Foundational, or Polish tasks that don't belong to a specific story
- Include exact file paths in descriptions

## Implementation Philosophy: Instructions > Code

**Critical Principle**: The MVP focuses on high-quality agent **instructions** (system prompts) as the primary mechanism for agent behavior. The LLM performs ALL reasoning, decision-making, and analysis based on instructions - NO custom Python business logic for risk scoring, query generation, correlation detection, etc. Python code is limited to:
1. Deployment scripts (using azure-ai-projects SDK)
2. Orchestration setup (using agent-framework magentic orchestrator)
3. Mock data loading and streaming
4. Demo scenarios and CLI

**Why Instructions First**:
- Leverages the model's capabilities (GPT-4.1-mini reasoning)
- Minimal codebase (fewer bugs, easier maintenance)
- Flexible and adaptable (change instructions vs. rewrite code)
- Faster iteration (no deployment needed to adjust behavior)

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (src/deployment/, src/orchestration/, src/data/, src/shared/, src/demo/, infra/, tests/, docs/, schemas/)
- [X] T002 Initialize Python 3.11+ project with pyproject.toml and dependencies (azure-ai-projects, agent-framework, azure-identity, azure-monitor-opentelemetry, pydantic, pandas, fastapi)
- [X] T003 [P] Configure linting and formatting tools (black, pylint, mypy) in pyproject.toml
- [X] T004 [P] Create .gitignore for Python project (exclude __pycache__, .venv, .env, *.pyc, .pytest_cache, .mypy_cache, checkpoints/)
- [X] T005 [P] Setup GitHub Actions CI/CD workflow skeleton in .github/workflows/ci.yml
- [X] T006 Create README.md with project overview and setup instructions
- [X] T007 Create environment variable template file .env.example with required variables (PROJECT_CONNECTION_STRING, AZURE_AI_MODEL_DEPLOYMENT_NAME, etc.)

---

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETE

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create Pydantic data models in src/shared/models.py (SecurityAlert, SecurityIncident, TriageResult, HuntingQuery, ResponseAction, ThreatBriefing, AgentState, AuditLog) from data-model.md
- [X] T009 [P] Implement authentication module in src/shared/auth.py (Managed Identity with DefaultAzureCredential, fallback to service principal if needed)
- [X] T010 [P] Implement structured logging in src/shared/logging.py (structlog with JSON formatting, OpenTelemetry integration)
- [X] T011 [P] Create mock data loader in src/data/datasets.py (load GUIDE and Attack datasets from mock-data/ directory, transform to Sentinel format)
- [X] T012 [P] Implement mock data streamer in src/data/streaming.py (MockDataStreamer class with configurable interval, checkpoint-based replay, async generator pattern)
- [X] T013 [P] Create scenario manager in src/data/scenarios.py (ScenarioManager with curated scenarios: brute_force, phishing_campaign, ransomware)
- [X] T014 Setup Bicep infrastructure templates skeleton in infra/main.bicep (modules for microsoft-foundry.bicep, cosmos.bicep, monitoring.bicep)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel ✅

---

## Phase 3: User Story 5 - Multi-Agent Orchestration (Priority: P1) 🎯 MVP FOUNDATION

**Goal**: Establish magentic orchestration as the MVP approach, enabling dynamic agent coordination with manager-driven selection. This is foundational for all other user stories.

**Independent Test**: Deploy manager agent with minimal instructions, verify magentic workflow can be created and initialized, test event streaming without actual agent invocations.

**MVP Note**: Uses magentic orchestration for MVP. A research task (T095) will evaluate alternative orchestration approaches for production.

### Phase A: Infrastructure Deployment (US5)

- [ ] T015 [P] [US5] Create Manager Agent instructions in src/deployment/agent_definitions/manager_instructions.md (coordination rules, enforces triage-first behavior, agent selection criteria, plan creation format)
- [ ] T016 [US5] Implement agent deployment script in src/deployment/deploy_agents.py (uses azure-ai-projects SDK, creates v2 agents with AIProjectClient.agents.create_version(), deploys manager agent only for this phase)
- [ ] T017 [US5] Create CLI command in src/demo/cli.py for deploying agents (python -m src.demo.cli deploy)

### Phase B: Runtime Orchestration (US5)

- [ ] T018 [US5] Implement magentic orchestrator setup in src/orchestration/orchestrator.py (create_workflow() function with MagenticBuilder, plugin point clearly documented, manager agent discovery)
- [ ] T019 [P] [US5] Implement workflow execution module in src/orchestration/workflows.py (run_workflow() function with event streaming, AgentRunUpdateEvent handling, progress tracking)
- [ ] T020 [US5] Create demo main script in src/demo/main.py (initializes workflow, loads mock data, streams events, displays agent interactions)
- [ ] T021 [US5] Add CLI commands for running workflows in src/demo/cli.py (python -m src.demo.cli run-workflow <scenario_name>)

**Checkpoint**: At this point, orchestration infrastructure should be operational. Manager agent deployed, magentic workflow can be initialized and run (though without other agents yet).

---

## Phase 4: User Story 1 - Automated Alert Triage (Priority: P1) 🎯 MVP CORE

**Goal**: Implement Alert Triage Agent as the highest priority agent - analyzes, prioritizes, and filters security alerts to reduce alert fatigue

**Independent Test**: Stream batch of mixed alerts (critical, medium, benign) through triage agent, verify risk scoring, prioritization, correlation detection, and natural language explanations are generated correctly

### Phase A: Infrastructure Deployment (US1)

- [ ] T022 [P] [US1] Create Alert Triage Agent instructions in src/deployment/agent_definitions/alert_triage_instructions.md (comprehensive system prompt following Section 11 of research.md: role definition, risk scoring factors, correlation logic, output format with examples)
- [ ] T023 [US1] Update deployment script in src/deployment/deploy_agents.py to deploy Alert Triage Agent (add to agent_definitions dict, call create_version())
- [ ] T024 [US1] Create input/output JSON schemas in schemas/alert-triage-input.schema.json and schemas/alert-triage-output.schema.json (SecurityAlert input, TriageResult output)

### Phase B: Runtime Integration (US1)

- [ ] T025 [US1] Update magentic orchestrator in src/orchestration/orchestrator.py to include triage agent in participants (discover via AIProjectClient.agents.get_agent())
- [ ] T026 [US1] Create alert triage scenario in src/demo/scenarios/scenario_01_alert_triage.py (load mixed alert batch, run through triage agent, display results)
- [ ] T027 [US1] Update manager agent instructions in src/deployment/agent_definitions/manager_instructions.md to reference triage agent (add "triage" to team list, document triage-first rule)

**Checkpoint**: Alert Triage Agent should be fully functional and testable independently. Can ingest alerts and produce prioritized triage results with risk scores and explanations.

---

## Phase 5: User Story 4 - Threat Intelligence Integration (Priority: P3)

**Goal**: Provide threat intelligence enrichment and daily briefings to support triage and investigations

**Independent Test**: Pass alerts with known IOCs (IPs, hashes) to intelligence agent, verify enrichment with reputation data, MITRE mappings, and threat context from Attack dataset

**Rationale for Priority**: Implemented before US2/US3 because triage agent (US1) benefits from threat intelligence enrichment, and intelligence agent is simpler to implement (fewer dependencies)

### Phase A: Infrastructure Deployment (US4)

- [ ] T028 [P] [US4] Create Threat Intelligence Agent instructions in src/deployment/agent_definitions/threat_intelligence_instructions.md (IOC enrichment logic, briefing generation format, MITRE mapping, Attack dataset integration guidance)
- [ ] T029 [US4] Update deployment script in src/deployment/deploy_agents.py to deploy Threat Intelligence Agent
- [ ] T030 [US4] Create JSON schemas in schemas/threat-intelligence-input.schema.json and schemas/threat-intelligence-output.schema.json

### Phase B: Runtime Integration (US4)

- [ ] T031 [US4] Update magentic orchestrator in src/orchestration/orchestrator.py to include intel agent in participants
- [ ] T032 [US4] Create threat intelligence scenario in src/demo/scenarios/scenario_04_threat_intel.py (test IOC enrichment and daily briefing generation)
- [ ] T033 [US4] Update manager agent instructions to coordinate with intelligence agent (when to request threat context)

**Checkpoint**: Threat Intelligence Agent functional. Can enrich alerts with threat context and generate daily briefings.

---

## Phase 6: User Story 2 - Proactive Threat Hunting (Priority: P2)

**Goal**: Enable natural language threat hunting queries with KQL generation and anomaly detection

**Independent Test**: Submit natural language hunting queries (e.g., "Show lateral movement attempts in last 24 hours"), verify KQL generation, query execution simulation, and finding presentation

### Phase A: Infrastructure Deployment (US2)

- [ ] T034 [P] [US2] Create Threat Hunting Agent instructions in src/deployment/agent_definitions/threat_hunting_instructions.md (natural language to KQL translation, anomaly detection reasoning, pivot logic, finding explanation format)
- [ ] T035 [US2] Update deployment script in src/deployment/deploy_agents.py to deploy Threat Hunting Agent
- [ ] T036 [US2] Create JSON schemas in schemas/threat-hunting-input.schema.json and schemas/threat-hunting-output.schema.json
- [ ] T037 [P] [US2] Create KQL query templates library in src/data/kql_templates.py (common hunting queries from research.md Section 4: lateral movement, suspicious sign-in, uncommon process execution)

### Phase B: Runtime Integration (US2)

- [ ] T038 [US2] Update magentic orchestrator in src/orchestration/orchestrator.py to include hunting agent in participants
- [ ] T039 [US2] Create threat hunting scenario in src/demo/scenarios/scenario_02_threat_hunt.py (demonstrate natural language query workflow)
- [ ] T040 [US2] Update manager agent instructions to trigger hunting agent (after triage identifies suspicious patterns, or on analyst request)

**Checkpoint**: Threat Hunting Agent functional. Can accept natural language queries, generate KQL, and present findings with explanations.

---

## Phase 7: User Story 3 - Automated Incident Response (Priority: P2)

**Goal**: Automate containment actions with risk-based approval workflows

**Independent Test**: Create simulated incident (e.g., malware detection), verify response agent generates appropriate containment recommendations (endpoint isolation, account suspension), documents actions, and requests human approval for high-risk actions

### Phase A: Infrastructure Deployment (US3)

- [ ] T041 [P] [US3] Create Incident Response Agent instructions in src/deployment/agent_definitions/incident_response_instructions.md (containment strategy selection, risk assessment, playbook adherence, approval criteria, action documentation format)
- [ ] T042 [US3] Update deployment script in src/deployment/deploy_agents.py to deploy Incident Response Agent
- [ ] T043 [US3] Create JSON schemas in schemas/incident-response-input.schema.json and schemas/incident-response-output.schema.json
- [ ] T044 [P] [US3] Create risk-based approval matrix in src/shared/approval_matrix.py (defines which actions require human approval based on asset criticality and action type)

### Phase B: Runtime Integration (US3)

- [ ] T045 [US3] Update magentic orchestrator in src/orchestration/orchestrator.py to include response agent in participants
- [ ] T046 [US3] Implement human-in-the-loop approval workflow in src/orchestration/workflows.py (handle FunctionApprovalRequestContent events, prompt for approval, integrate with approval matrix)
- [ ] T047 [US3] Create incident response scenario in src/demo/scenarios/scenario_03_incident_response.py (demonstrate containment workflow with approval gates)
- [ ] T048 [US3] Update manager agent instructions to trigger response agent (after triage identifies critical incidents)

**Checkpoint**: Incident Response Agent functional. Can generate containment recommendations, request approvals for high-risk actions, and document all actions taken.

---

## Phase 8: End-to-End Integration & Multi-Agent Workflows

**Purpose**: Connect all agents in comprehensive attack scenarios demonstrating full system capabilities

- [ ] T049 Create comprehensive end-to-end scenario in src/demo/scenarios/scenario_05_full_attack_chain.py (brute force → triage → intel enrichment → hunting → response → threat context)
- [ ] T050 [P] Implement scenario controller in src/demo/scenario_controller.py (pause, resume, reset, jump_to controls for demos)
- [ ] T051 Add observability instrumentation to all workflows (structured logging, OpenTelemetry tracing with correlation IDs, metrics collection)
- [ ] T052 Create workflow visualization in src/demo/visualizer.py (display agent interactions, decision points, context flow)
- [ ] T053 Implement agent state tracking in src/shared/agent_state.py (persist agent metrics, feedback summary, configuration)
- [ ] T054 Create audit logging for all agent actions in src/shared/audit_log.py (immutable logs with actor, action, result, correlation ID)

---

## Phase 9: Infrastructure & Deployment

**Purpose**: Complete infrastructure templates and deployment automation

- [ ] T055 [P] Complete Microsoft Foundry Bicep module in infra/modules/microsoft-foundry.bicep (workspace, model deployments, networking)
- [ ] T056 [P] Complete Cosmos DB Bicep module in infra/modules/cosmos.bicep (database, collections with partition keys and TTL settings from data-model.md)
- [ ] T057 [P] Complete monitoring Bicep module in infra/modules/monitoring.bicep (Application Insights, Log Analytics workspace, dashboards)
- [ ] T058 Complete main Bicep template in infra/main.bicep (orchestrate all modules, parameters)
- [ ] T059 [P] Create dev parameters file in infra/parameters/dev.parameters.json
- [ ] T060 [P] Create prod parameters file in infra/parameters/prod.parameters.json
- [ ] T061 Update GitHub Actions CI workflow in .github/workflows/ci.yml (linting, type checking, security scanning)
- [ ] T062 Create GitHub Actions deployment workflow in .github/workflows/cd-dev.yml (deploy infrastructure, deploy agents)

---

## Phase 10: Documentation & Knowledge Base

**Purpose**: Complete documentation for setup, operation, and extension

- [ ] T063 [P] Create quickstart guide in specs/001-agentic-soc/quickstart.md (Phase A setup: deploy agents, Phase B setup: run demos, customize instructions, change orchestration strategy)
- [ ] T064 [P] Create architecture diagrams in docs/architecture/ (system-context.md, component-diagram.md, deployment-diagram.md, data-flow.md using Mermaid)
- [ ] T065 [P] Create operational runbooks in docs/runbooks/ (agent-failure-recovery.md, scaling-guidance.md, incident-escalation.md)
- [ ] T066 [P] Document orchestration plugin points in docs/orchestration-guide.md (how to change from magentic to sequential/concurrent/custom, migration checklist)
- [ ] T067 [P] Create ADR for orchestration approach in docs/adr/002-orchestration-approach.md (why magentic for MVP, evaluation criteria for alternatives)
- [ ] T068 [P] Document agent instruction best practices in docs/agent-instruction-guide.md (template structure, examples, safety guardrails from research.md Section 11)
- [ ] T069 Update main README.md with complete setup, usage, and architecture overview

---

## Phase 11: Mock Data & Demo Scenarios

**Purpose**: Finalize mock data pipeline and curated demo scenarios

- [ ] T070 [P] Verify GUIDE dataset transformation in src/data/datasets.py (ensure all 1.17M+ records transform correctly to Sentinel format)
- [ ] T071 [P] Verify Attack dataset integration in src/data/datasets.py (14K+ scenarios mapped to MITRE techniques)
- [ ] T072 [P] Create brute force attack scenario data in mock-data/scenarios/brute_force/ (20 failed logins → successful login → lateral movement alerts)
- [ ] T073 [P] Create phishing campaign scenario data in mock-data/scenarios/phishing_campaign/ (suspicious email → credential theft → data exfiltration alerts)
- [ ] T074 [P] Create ransomware scenario data in mock-data/scenarios/ransomware/ (malware execution → file encryption → C2 communication alerts)
- [ ] T075 Implement scenario validation in src/data/scenario_validator.py (verify scenario data completeness, entity consistency, timeline ordering)
- [ ] T076 Create demo dashboard in src/demo/dashboard.py (FastAPI web UI showing real-time agent activity, alert queue, incident status)

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T077 [P] Add comprehensive error handling to all modules (try-except blocks, graceful degradation, user-friendly error messages)
- [ ] T078 [P] Add retry logic with exponential backoff to external API calls in src/shared/retry.py (azure-ai-projects calls, mock Event Hub integration)
- [ ] T079 Implement health check endpoints in src/demo/main.py (/health for liveness, /ready for readiness with dependency checks)
- [ ] T080 Add performance metrics collection (latency p95, throughput, error rates) with Prometheus client in src/shared/metrics.py
- [ ] T081 Create Azure Monitor dashboard queries in docs/dashboards/azure-monitor-queries.kql (agent performance, alert processing time, error rates)
- [ ] T082 Implement configuration management in src/shared/config.py (Pydantic settings, environment variable validation, defaults)
- [ ] T083 Add secrets management integration in src/shared/secrets.py (Azure Key Vault client, fallback to environment variables)
- [ ] T084 Create development setup script in scripts/setup-dev.sh (install dependencies, create .env from template, run linters)
- [ ] T085 Add model configuration documentation in docs/model-configuration.md (reference MODEL-SELECTION-AOA.md, migration path to GPT-5 family)
- [ ] T086 Implement graceful shutdown handling in src/demo/main.py (cleanup resources, save checkpoints, close connections)
- [ ] T087 Add rate limiting to prevent API quota exhaustion in src/shared/rate_limiter.py
- [ ] T088 Create troubleshooting guide in docs/troubleshooting.md (common issues, error codes, resolution steps)
- [ ] T089 Add agent versioning and rollback support in src/deployment/version_manager.py (list versions, rollback to previous version)
- [ ] T090 Implement feature flags in src/shared/feature_flags.py (enable/disable agents, orchestration strategies, approval workflows)
- [ ] T091 Run security scanning with Bandit and Safety in CI workflow
- [ ] T092 Add dependency vulnerability scanning with Dependabot in .github/dependabot.yml
- [ ] T093 Validate quickstart.md by following instructions from scratch (ensure all steps work, no missing dependencies)
- [ ] T094 Code cleanup and refactoring (remove debug code, add docstrings, ensure PEP 8 compliance)

---

## Phase 13: Research & Future Enhancements

**Purpose**: Research tasks for production readiness and future improvements

- [ ] T095 [P] Research Task: Evaluate orchestration approaches beyond magentic for production (document findings in docs/research/orchestration-evaluation.md - compare sequential, concurrent, custom, Durable Functions; provide migration guidance; recommend approach based on scale, complexity, predictability requirements)
- [ ] T096 [P] Research Task: Evaluate Azure AI Search integration for RAG knowledge base (assess agentic retrieval, cost, performance for 75K documents - Attack dataset + GUIDE + runbooks; document in docs/research/knowledge-base-evaluation.md)
- [ ] T097 [P] Research Task: Evaluate agent tool integration for future phases (KQL query executor, Defender XDR API, Sentinel API, Entra ID API; document tool calling patterns, error handling, approval workflows in docs/research/tool-integration-plan.md)
- [ ] T098 [P] Research Task: Evaluate Microsoft Fabric OneLake for long-term telemetry storage (compare with Cosmos DB + Blob Storage, assess query performance, cost at scale; document in docs/research/fabric-evaluation.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 5 - Orchestration (Phase 3)**: Depends on Foundational - MUST complete before other user stories (provides orchestration infrastructure)
- **User Story 1 - Triage (Phase 4)**: Depends on Foundational + US5 - First agent to implement
- **User Story 4 - Intelligence (Phase 5)**: Depends on Foundational + US5 - Can run parallel with US2/US3, but benefits US1
- **User Story 2 - Hunting (Phase 6)**: Depends on Foundational + US5 - Can run parallel with US3/US4
- **User Story 3 - Response (Phase 7)**: Depends on Foundational + US5 - Can run parallel with US2/US4
- **End-to-End Integration (Phase 8)**: Depends on US1, US2, US3, US4, US5 completion
- **Infrastructure (Phase 9)**: Can run parallel with user stories (different files)
- **Documentation (Phase 10)**: Can run parallel with user stories (different files)
- **Mock Data (Phase 11)**: Can run parallel with user stories (different files)
- **Polish (Phase 12)**: Depends on all desired user stories being complete
- **Research (Phase 13)**: Can run parallel with any phase (research only, no dependencies)

### User Story Dependencies

- **US5 (Orchestration - P1)**: FOUNDATIONAL - Must complete before any other user story
- **US1 (Triage - P1)**: Depends only on US5 - No dependencies on other stories
- **US4 (Intelligence - P3)**: Depends only on US5 - No dependencies on other stories, but enhances US1
- **US2 (Hunting - P2)**: Depends only on US5 - No dependencies on other stories
- **US3 (Response - P2)**: Depends only on US5 - No dependencies on other stories

### Within Each User Story

- Phase A (Infrastructure Deployment) tasks before Phase B (Runtime Integration) tasks
- Instruction files (.md) before deployment scripts
- Agent deployment before orchestrator integration
- Orchestrator updates before scenario creation
- Manager instructions updates after agent deployment

### Parallel Opportunities

**Setup (Phase 1)**:
- T003, T004, T005, T006 can run in parallel (different files)

**Foundational (Phase 2)**:
- T009, T010, T011, T012, T013, T014 can run in parallel (different modules)

**US5 Phase A**:
- T015 and T017 can run in parallel with T016 being written

**US5 Phase B**:
- T019 can run in parallel with T018

**US1 Phase A**:
- T022, T024 can run in parallel
- T023 depends on T022 (needs instructions file)

**US4, US2, US3 Entire Phases**:
- Once US5 is complete, US1, US2, US3, US4 can be developed in parallel by different team members
- Within each story, instruction creation tasks can run in parallel

**Infrastructure (Phase 9)**:
- T055, T056, T057, T059, T060, T061 can all run in parallel

**Documentation (Phase 10)**:
- T063-T069 can all run in parallel (different files)

**Mock Data (Phase 11)**:
- T070, T071, T072, T073, T074 can all run in parallel

**Polish (Phase 12)**:
- T077, T078, T082, T083, T084, T085, T091, T092 can run in parallel
- Research tasks T095-T098 can all run in parallel

---

## Parallel Example: Phases 5, 6, 7 After US5 Complete

```bash
# With a 4-person team after US5 (Orchestration) is complete:

# Developer A: User Story 1 (Triage Agent)
Tasks: T022, T023, T024, T025, T026, T027

# Developer B: User Story 4 (Intelligence Agent)
Tasks: T028, T029, T030, T031, T032, T033

# Developer C: User Story 2 (Hunting Agent)
Tasks: T034, T035, T036, T037, T038, T039, T040

# Developer D: User Story 3 (Response Agent)
Tasks: T041, T042, T043, T044, T045, T046, T047, T048

# All stories progress independently and integrate into shared orchestration framework
```

---

## Implementation Strategy

### MVP First (Minimum Viable Product)

**Recommended MVP Scope: Phases 1-4 Only**

1. Complete Phase 1: Setup ✅
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) ✅
3. Complete Phase 3: US5 - Orchestration (CRITICAL - enables multi-agent coordination) ✅
4. Complete Phase 4: US1 - Alert Triage Agent ✅
5. **STOP and VALIDATE**: 
   - Test orchestration with single triage agent
   - Stream mock alerts through triage workflow
   - Verify risk scoring, prioritization, explanations
   - Demonstrate manager agent coordinating triage agent
6. Deploy/demo MVP: Orchestration + Triage = Demonstrable Value

**MVP Delivers**:
- ✅ Alert triage with AI risk assessment
- ✅ Natural language explanations
- ✅ Multi-agent orchestration framework (ready for expansion)
- ✅ Magentic coordination pattern
- ✅ Mock data streaming
- ✅ Demonstrable with curated scenarios

### Incremental Delivery (Recommended Approach)

1. **MVP**: Setup + Foundational + US5 + US1 (Phases 1-4)
   - Orchestration infrastructure + Triage agent
   - Test independently → Deploy/Demo
   
2. **Increment 2**: Add US4 - Intelligence (Phase 5)
   - Enrichment capability
   - Test with US1 integration → Deploy/Demo
   
3. **Increment 3**: Add US2 - Hunting (Phase 6)
   - Proactive threat detection
   - Test independently → Deploy/Demo
   
4. **Increment 4**: Add US3 - Response (Phase 7)
   - Automated containment
   - Test with approval workflows → Deploy/Demo
   
5. **Increment 5**: End-to-End + Polish (Phases 8, 12)
   - Full attack chain scenarios
   - Production readiness → Deploy/Demo

### Parallel Team Strategy

With multiple developers:

1. **Week 1-2**: Team completes Setup + Foundational together (Phases 1-2)
2. **Week 3**: Team completes US5 - Orchestration together (Phase 3) - CRITICAL FOUNDATION
3. **Week 4-6**: Once US5 is done, PARALLEL DEVELOPMENT:
   - Developer A: US1 - Triage (Phase 4)
   - Developer B: US4 - Intelligence (Phase 5)
   - Developer C: US2 - Hunting (Phase 6)
   - Developer D: US3 - Response (Phase 7)
4. **Week 7**: Integration (Phase 8)
5. **Week 8**: Polish & Documentation (Phases 9-12)

---

## Key Decisions & Notes

### MVP Orchestration: Magentic Builder

**Decision**: Use magentic orchestration for MVP (as documented in plan.md and research.md Section 10)

**Rationale**:
- **Dynamic Coordination**: Manager agent selects next agent based on evolving context
- **Handles Uncertainty**: Well-suited for security scenarios where solution path is not predetermined
- **Human-in-the-Loop**: Built-in support for approval gates and stall intervention
- **Future-Proof**: Clear plugin point in `src/orchestration/orchestrator.py` for changing strategies
- **Triage-First Pattern**: Manager instructions enforce "ALWAYS start with triage" behavior

**Plugin Point**: `src/orchestration/orchestrator.py` → `create_workflow()` function
- Current: Uses `MagenticBuilder` from Agent Framework
- Future Options: Sequential, concurrent, custom orchestrator, Azure Durable Functions
- Configuration-driven strategy selection (see research.md Section 13)

**Research Task T095** will evaluate alternative approaches for production.

### Instructions > Code Philosophy

**What Agents ARE**:
- ✅ Instruction sets (markdown files with system prompts)
- ✅ LLM-powered reasoning (the model performs analysis, decision-making)
- ✅ Stateless participants (each invocation receives context, produces output via LLM)

**What Agents ARE NOT**:
- ❌ Traditional Python classes with business logic methods
- ❌ Deterministic algorithms (risk scoring, query parsing)
- ❌ Rule engines or state machines
- ❌ Tools/plugins initially (deferred to future phases per plan.md)

**Example**: Alert Triage Agent instructions contain:
- Role definition and expertise
- Risk scoring FACTORS (severity indicators, asset criticality, user context)
- Correlation PATTERNS to detect (multi-stage attacks, lateral movement)
- Output FORMAT (JSON with risk score, explanation, next steps)
- Examples (high-risk brute force, low-risk false positive, insufficient info)

**The LLM does the actual risk calculation** based on these factors - NO Python `calculate_risk_score()` function.

### Terminology: Microsoft Foundry

All references to "Azure AI Foundry" and "AI Foundry" have been updated to "**Microsoft Foundry**" throughout documentation (spec.md, plan.md, research.md) per problem statement requirements.

### Security: Managed Identity OR Service Principals

**FR-053 Clarification**: System MUST use Azure Managed Identity OR service principals with least-privilege permissions for agent authentication. Managed Identity with Entra ID RBAC is RECOMMENDED as primary approach. Service principals with Azure Key Vault MAY be used as alternative when Managed Identity is not available.

This aligns with constitution.md line 207: "Agent identities MUST use managed identities or service principals with least-privilege permissions"

### Tests: Optional for MVP

Per MVP scope and implementation plan, tests are OPTIONAL and NOT included in this task breakdown. Focus is on:
- ✅ Demonstrable functionality with mock data
- ✅ Independent testing via demo scenarios
- ✅ Manual validation of agent outputs
- ⚠️ Future: Add comprehensive test suite (unit, integration, contract, scenario tests) in production phase

---

## Validation Checklist

Before considering tasks complete:

- [ ] All agent instruction files created and follow template from research.md Section 11
- [ ] All agents deployed to Microsoft Foundry using azure-ai-projects SDK
- [ ] Magentic orchestration workflow functional with manager agent
- [ ] All user stories (US1-US5) independently testable with demo scenarios
- [ ] Mock data streaming works with configurable intervals and checkpoint replay
- [ ] Manager agent enforces triage-first behavior in instructions
- [ ] Plugin point for orchestration strategy change is clearly documented
- [ ] All terminology uses "Microsoft Foundry" (not "Azure AI Foundry" or "AI Foundry")
- [ ] FR-053 correctly implements Managed Identity OR service principals
- [ ] Implementation follows "Instructions > Code" philosophy (no business logic in Python for agent reasoning)
- [ ] Research task T095 created for orchestration approach evaluation
- [ ] Quickstart.md validated by following from scratch
- [ ] All code passes linting (black, pylint, mypy)
- [ ] No secrets committed to source control
- [ ] README.md and documentation complete

---

**Total Tasks**: 98 tasks  
**Setup**: 7 tasks  
**Foundational**: 7 tasks  
**User Story 5 (Orchestration)**: 7 tasks  
**User Story 1 (Triage)**: 6 tasks  
**User Story 4 (Intelligence)**: 6 tasks  
**User Story 2 (Hunting)**: 7 tasks  
**User Story 3 (Response)**: 8 tasks  
**End-to-End Integration**: 6 tasks  
**Infrastructure**: 8 tasks  
**Documentation**: 7 tasks  
**Mock Data**: 7 tasks  
**Polish**: 18 tasks  
**Research**: 4 tasks  

**Suggested MVP Scope**: Phases 1-4 (27 tasks) → Orchestration + Alert Triage  
**Parallel Opportunities**: 45+ tasks can run in parallel across different phases  
**Independent Test Criteria**: Each user story has clear acceptance criteria and demo scenarios
