# Tasks: Agentic Security Operations Center (SOC) - MVP

**Input**: Design documents from `/specs/001-agentic-soc/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests are NOT explicitly requested in the feature specification, so test tasks are NOT included in this implementation plan. Focus is on building demonstrable agents with mock data.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per plan.md: src/, tests/, infra/, docs/, schemas/, .github/workflows/
- [ ] T002 Initialize Python project with pyproject.toml and configure Poetry or pip for dependency management
- [ ] T003 [P] Create .gitignore for Python (.venv/, __pycache__/, *.pyc, .env, logs/)
- [ ] T004 [P] Create requirements.txt with core dependencies: azure-ai-projects, azure-identity, agent-framework, azure-monitor-opentelemetry, pydantic, pandas, fastapi, azure-search-documents, azure-cosmos
- [ ] T005 [P] Setup environment template .env.example with Azure AI Foundry, Cosmos DB, Event Hubs, Application Insights configuration variables
- [ ] T006 [P] Create README.md with project overview and quick start instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create shared Pydantic models in src/shared/schemas.py: SeverityLevel, EntityType, AlertEntity, SecurityAlert per data-model.md
- [ ] T008 [P] Create SecurityIncident model in src/shared/schemas.py with incident lifecycle states (New, Investigating, Contained, Resolved, Closed)
- [ ] T009 [P] Create authentication module in src/shared/auth.py using Azure Managed Identity with DefaultAzureCredential
- [ ] T010 [P] Create structured logging setup in src/shared/logging.py using structlog with JSON formatting
- [ ] T011 [P] Create metrics collection module in src/shared/metrics.py with Prometheus counters and histograms
- [ ] T012 Implement Cosmos DB client in src/data/cosmos.py with connection pooling and error handling
- [ ] T013 [P] Create Cosmos DB initialization script in utils/setup_cosmos_db.py to create collections: alerts, incidents, triage_results, response_actions, agent_state, audit_logs with TTL and partition keys per data-model.md
- [ ] T014 [P] Create mock Sentinel API client in src/mock/sentinel_mock.py implementing SecurityAlert CRUD operations
- [ ] T015 [P] Create mock Defender XDR API client in src/mock/defender_mock.py for containment actions (isolate endpoint, disable account, block IP)
- [ ] T016 Implement GUIDE dataset loader in src/data/datasets.py to transform GUIDE records to Sentinel SecurityAlert schema
- [ ] T017 [P] Implement Attack dataset loader in src/data/datasets.py for attack scenario lookup and MITRE ATT&CK mapping
- [ ] T018 Create mock data streamer in src/mock/stream.py with configurable interval (default 15s) and checkpoint-based replay
- [ ] T019 [P] Setup Event Hubs client wrapper in src/orchestration/event_handlers.py for alert ingestion events
- [ ] T020 [P] Create FastAPI application scaffold in src/api/main.py with health and readiness endpoints
- [ ] T021 [P] Configure Azure Monitor OpenTelemetry in src/shared/logging.py with distributed tracing using correlation IDs
- [ ] T022 Create AuditLog model in src/shared/schemas.py for immutable audit trail with actor, action, target entity, result fields
- [ ] T023 [P] Implement audit logging service in src/shared/audit.py that writes to Cosmos DB audit_logs collection

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 5 - Multi-Agent Orchestration and Collaboration (Priority: P1) 🎯 MVP Foundation

**Goal**: Enable all AI agents to work together seamlessly with shared context, task routing, and human escalation

**Independent Test**: Simulate a multi-stage attack scenario (e.g., failed login → successful login → lateral movement) and verify agents coordinate appropriately: triage identifies threat → response agent receives context → hunting agent searches related activity → intelligence agent provides context. Verify context is maintained and no information is lost between agents.

### Implementation for User Story 5

- [ ] T024 [P] [US5] Create AgentState model in src/shared/schemas.py with agent metrics, configuration, and feedback tracking per data-model.md
- [ ] T025 [P] [US5] Create base orchestrator in src/orchestration/orchestrator.py using Microsoft Agent Framework for agent-to-agent communication
- [ ] T026 [US5] Implement event handler registration in src/orchestration/event_handlers.py for alert ingestion, triage complete, high-risk alert, and schedule events
- [ ] T027 [US5] Implement context propagation in src/orchestration/workflows.py using Sentinel incidents and Cosmos DB for shared state
- [ ] T028 [US5] Create correlation ID generation and tracking in src/shared/logging.py for distributed tracing across agents
- [ ] T029 [US5] Implement escalation logic in src/orchestration/orchestrator.py to detect when automated capabilities are exceeded and trigger human notification
- [ ] T030 [US5] Create conflict resolution handler in src/orchestration/workflows.py to resolve conflicting agent recommendations or escalate to humans
- [ ] T031 [US5] Implement graceful degradation in src/orchestration/orchestrator.py to handle service unavailability and alert humans to failures
- [ ] T032 [P] [US5] Create approval workflow integration stub in src/api/routes/approval.py for human approval requests with pending actions queue
- [ ] T033 [US5] Add audit logging integration in src/orchestration/orchestrator.py for all agent decisions and actions using shared audit service
- [ ] T034 [US5] Implement agent health monitoring in src/orchestration/orchestrator.py with heartbeat tracking and status checks

**Checkpoint**: Orchestration framework ready - individual agents can now be implemented and will automatically coordinate

---

## Phase 4: User Story 1 - Automated Alert Triage and Prioritization (Priority: P1) 🎯 MVP Core

**Goal**: Automatically analyze, prioritize, and filter security alerts to reduce alert fatigue and surface critical threats first

**Independent Test**: Ingest a batch of mixed security alerts (high-severity credential theft, medium-severity failed logins, low-severity benign process execution) and verify: (1) high-risk alerts are prioritized first with risk scores > 70, (2) related alerts from same user/asset are correlated into single incident, (3) benign alerts are marked low priority with clear explanations, (4) each decision includes natural language explanation

### Implementation for User Story 1

- [ ] T035 [P] [US1] Create TriageResult model in src/agents/alert_triage/models.py with risk score, priority, decision, explanation, correlation fields per data-model.md
- [ ] T036 [P] [US1] Create alert-triage-input.schema.json and alert-triage-output.schema.json validation in src/agents/alert_triage/ using existing contracts/ schemas
- [ ] T037 [US1] Implement risk scoring logic in src/agents/alert_triage/scoring.py based on severity, entity count, MITRE techniques, asset criticality, user risk level
- [ ] T038 [US1] Implement alert correlation logic in src/agents/alert_triage/scoring.py to detect related alerts by user account, device, IP address, time window
- [ ] T039 [US1] Create Alert Triage Agent in src/agents/alert_triage/agent.py using Azure AI Foundry Agent Framework with GPT-4.1-mini model
- [ ] T040 [US1] Implement agent system prompt in src/agents/alert_triage/agent.py with instructions for SOC analyst expertise, risk assessment, triage decisions, and explanation generation
- [ ] T041 [US1] Implement threat intelligence enrichment integration in src/agents/alert_triage/agent.py to query Attack dataset for IOC context and MITRE mappings
- [ ] T042 [US1] Implement false positive detection in src/agents/alert_triage/agent.py using historical patterns from GUIDE dataset and benign process lists
- [ ] T043 [US1] Create incident creation logic in src/agents/alert_triage/agent.py to generate SecurityIncident from high-risk alerts (risk score > 70) and write to Cosmos DB incidents collection
- [ ] T044 [US1] Implement analyst feedback processing in src/agents/alert_triage/feedback.py to accept corrections and store for future learning
- [ ] T045 [US1] Add triage metrics collection in src/agents/alert_triage/agent.py: processing time, risk score distribution, triage decision breakdown
- [ ] T046 [US1] Register Alert Triage Agent with orchestrator in src/orchestration/orchestrator.py to handle alert ingestion events
- [ ] T047 [US1] Create Triage Agent event handler in src/orchestration/event_handlers.py to trigger on new alert events from Event Hubs
- [ ] T048 [P] [US1] Create feedback API endpoint in src/api/routes/feedback.py: POST /api/v1/feedback with alert_id, triage_id, correction, analyst fields

**Checkpoint**: Alert Triage Agent is fully functional - can process alerts, prioritize, correlate, and create incidents independently

---

## Phase 5: User Story 2 - Proactive Threat Hunting (Priority: P2)

**Goal**: Enable proactive searching for hidden threats using natural language queries without requiring complex query language expertise

**Independent Test**: Submit natural language hunting query "Show machines communicating with suspicious IPs from yesterday" and verify: (1) query translates to valid KQL, (2) query executes against mock dataset, (3) anomalous patterns are detected and flagged, (4) findings include explanations of what makes them suspicious, (5) results include anomaly scores and recommended actions

### Implementation for User Story 2

- [ ] T049 [P] [US2] Create HuntingQuery model in src/agents/threat_hunting/models.py with natural language, KQL, findings, status fields per data-model.md
- [ ] T050 [P] [US2] Create threat-hunting-input.schema.json and threat-hunting-output.schema.json validation in src/agents/threat_hunting/
- [ ] T051 [US2] Implement KQL query generator in src/agents/threat_hunting/query_generator.py using GPT-4.1-mini with system prompt containing KQL syntax, table schemas, and common patterns
- [ ] T052 [US2] Create KQL validation module in src/agents/threat_hunting/query_generator.py to check syntax before execution
- [ ] T053 [US2] Implement mock KQL executor in src/agents/threat_hunting/query_generator.py that searches GUIDE dataset based on query filters
- [ ] T054 [US2] Create anomaly detector in src/agents/threat_hunting/anomaly_detector.py using statistical baselines and deviation scoring
- [ ] T055 [US2] Create Threat Hunting Agent in src/agents/threat_hunting/agent.py using Azure AI Foundry Agent Framework with GPT-4.1-mini model
- [ ] T056 [US2] Implement agent system prompt in src/agents/threat_hunting/agent.py with threat hunting expertise, query translation, anomaly detection, pivot recommendations
- [ ] T057 [US2] Implement automated hunt scheduler in src/agents/threat_hunting/agent.py for periodic scheduled hunts (e.g., daily lateral movement detection)
- [ ] T058 [US2] Implement pivot logic in src/agents/threat_hunting/agent.py to automatically generate follow-up queries from findings (e.g., find related activity from suspicious IP)
- [ ] T059 [US2] Implement finding storage in src/agents/threat_hunting/agent.py to write HuntingQuery results to Cosmos DB with findings and recommendations
- [ ] T060 [US2] Add hunting metrics collection in src/agents/threat_hunting/agent.py: query count, execution time, finding count, anomaly score distribution
- [ ] T061 [US2] Register Threat Hunting Agent with orchestrator in src/orchestration/orchestrator.py for both interactive (analyst-triggered) and automated (scheduled) modes
- [ ] T062 [US2] Create hunting query API endpoint in src/api/routes/hunting.py: POST /api/v1/hunting/queries with natural language query, GET /api/v1/hunting/queries/{id} for results
- [ ] T063 [P] [US2] Implement hunt event handler in src/orchestration/event_handlers.py to trigger hunting after high-risk incident containment

**Checkpoint**: Threat Hunting Agent is fully functional - can translate natural language to KQL, execute queries, detect anomalies, and provide findings independently

---

## Phase 6: User Story 3 - Automated Incident Response and Containment (Priority: P2)

**Goal**: Automatically execute containment actions following response procedures to stop attacks faster than manual intervention

**Independent Test**: Create a confirmed critical incident (e.g., ransomware detection with malware execution on critical asset) and verify: (1) response agent recommends isolation within 60 seconds, (2) high-risk action requires human approval before execution, (3) approval workflow is triggered with action details and rationale, (4) after approval, containment action executes (mocked), (5) action log documents timestamps, rationale, and outcome

### Implementation for User Story 3

- [ ] T064 [P] [US3] Create ResponseAction model in src/agents/incident_response/models.py with action type, target entity, status, risk level, approval workflow fields per data-model.md
- [ ] T065 [P] [US3] Create incident-response-input.schema.json and incident-response-output.schema.json validation in src/agents/incident_response/
- [ ] T066 [US3] Implement risk-based approval matrix in src/agents/incident_response/approval.py based on action type and asset criticality per data-model.md approval rules
- [ ] T067 [US3] Create response playbook definitions in src/agents/incident_response/playbooks.py for common incident types (ransomware, credential theft, lateral movement) with multi-step procedures
- [ ] T068 [US3] Implement containment action executor in src/agents/incident_response/playbooks.py with mocked API calls to defender_mock.py (isolate endpoint, disable account, block IP, quarantine file, terminate process)
- [ ] T069 [US3] Create Incident Response Agent in src/agents/incident_response/agent.py using Azure AI Foundry Agent Framework with GPT-4.1-mini model
- [ ] T070 [US3] Implement agent system prompt in src/agents/incident_response/agent.py with incident response expertise, playbook selection, containment recommendations, recovery actions
- [ ] T071 [US3] Implement approval request generation in src/agents/incident_response/approval.py to create approval records in Cosmos DB with action details, risk level, rationale
- [ ] T072 [US3] Implement action execution workflow in src/agents/incident_response/agent.py: check approval status → execute if approved or auto-approved → log results → update incident status
- [ ] T073 [US3] Implement action verification in src/agents/incident_response/playbooks.py to confirm containment success (e.g., endpoint is isolated, account is disabled)
- [ ] T074 [US3] Create action logging in src/agents/incident_response/agent.py to write ResponseAction records to Cosmos DB response_actions collection with full audit trail
- [ ] T075 [US3] Add response metrics collection in src/agents/incident_response/agent.py: action count by type, approval rate, execution time, success rate
- [ ] T076 [US3] Register Incident Response Agent with orchestrator in src/orchestration/orchestrator.py to handle high-risk alert events and containment triggers
- [ ] T077 [US3] Create response event handler in src/orchestration/event_handlers.py to trigger on critical incident creation events
- [ ] T078 [P] [US3] Create approval API endpoints in src/api/routes/approval.py: GET /api/v1/approvals (list pending), POST /api/v1/approvals/{id} (approve/reject with decision, approver, comment)

**Checkpoint**: Incident Response Agent is fully functional - can recommend containment actions, follow approval workflows, execute actions, and log results independently

---

## Phase 7: User Story 4 - Threat Intelligence Integration and Enrichment (Priority: P3)

**Goal**: Automatically integrate threat intelligence to provide context for alerts, incidents, and investigations with proactive threat alerts

**Independent Test**: Ingest an alert containing an IP address and file hash, and verify: (1) IP and hash are automatically enriched with reputation data from Attack dataset, (2) enrichment includes threat actor associations, known campaigns, MITRE techniques, (3) if IOC matches known malicious pattern, threat context is added to alert, (4) daily briefing includes trending attack patterns from recent alerts, (5) briefing provides executive summary and recommended actions

### Implementation for User Story 4

- [ ] T079 [P] [US4] Create ThreatBriefing model in src/agents/threat_intelligence/models.py with briefing date, executive summary, key threats, trending patterns, IOCs per data-model.md
- [ ] T080 [P] [US4] Create threat-intelligence-input.schema.json and threat-intelligence-output.schema.json validation in src/agents/threat_intelligence/
- [ ] T081 [US4] Implement IOC enrichment service in src/agents/threat_intelligence/enrichment.py to query Attack dataset for IP addresses, domains, file hashes with reputation scoring
- [ ] T082 [US4] Implement MITRE ATT&CK lookup in src/agents/threat_intelligence/enrichment.py to map IOCs and alerts to techniques using Attack dataset (99.8% MITRE coverage)
- [ ] T083 [US4] Create threat intelligence cache in src/agents/threat_intelligence/enrichment.py using Cosmos DB for recently enriched IOCs to reduce duplicate lookups
- [ ] T084 [US4] Create Threat Intelligence Agent in src/agents/threat_intelligence/agent.py using Azure AI Foundry Agent Framework with GPT-4.1-mini model
- [ ] T085 [US4] Implement agent system prompt in src/agents/threat_intelligence/agent.py with threat intelligence expertise, IOC analysis, briefing generation, vulnerability correlation
- [ ] T086 [US4] Implement daily briefing generator in src/agents/threat_intelligence/briefing.py to analyze last 24h alerts, extract trending techniques, match with Attack scenarios, generate natural language briefing using GPT-4.1-mini
- [ ] T087 [US4] Implement proactive alerting in src/agents/threat_intelligence/agent.py to detect emerging threats from Attack dataset updates and notify SOC analysts
- [ ] T088 [US4] Implement threat context injection in src/agents/threat_intelligence/agent.py to enrich alerts/incidents with intelligence during triage and response workflows
- [ ] T089 [US4] Create intelligence knowledge base in src/agents/threat_intelligence/enrichment.py storing threat profiles, past incidents, IOC repository in Cosmos DB
- [ ] T090 [US4] Add intelligence metrics collection in src/agents/threat_intelligence/agent.py: enrichment count, IOC match rate, briefing generation time
- [ ] T091 [US4] Register Threat Intelligence Agent with orchestrator in src/orchestration/orchestrator.py for enrichment requests and scheduled briefing generation
- [ ] T092 [US4] Create intelligence event handler in src/orchestration/event_handlers.py to trigger enrichment on new alerts and daily briefing on schedule (e.g., 8 AM daily)
- [ ] T093 [P] [US4] Create briefing retrieval API endpoint in src/api/routes/intelligence.py: GET /api/v1/intelligence/briefings with date filter and latest briefing

**Checkpoint**: Threat Intelligence Agent is fully functional - can enrich IOCs, generate daily briefings, provide threat context, and alert on emerging threats independently

---

## Phase 8: Azure AI Search Knowledge Base (RAG for All Agents)

**Purpose**: Enable all agents to query contextual knowledge beyond training data using agentic retrieval

- [ ] T094 [P] Setup Azure AI Search indexes: attack-scenarios (14K scenarios), historical-incidents (10K GUIDE samples), threat-intelligence (IOCs)
- [ ] T095 [P] Implement knowledge agent client in src/data/knowledge.py using KnowledgeAgentRetrievalClient from azure.search.documents.agent
- [ ] T096 Create index population script in utils/populate_knowledge_base.py to load Attack dataset scenarios, GUIDE historical incidents, and IOC data into Azure AI Search indexes
- [ ] T097 [P] Integrate knowledge retrieval tool in Alert Triage Agent (src/agents/alert_triage/agent.py) for similar incident lookup
- [ ] T098 [P] Integrate knowledge retrieval tool in Threat Hunting Agent (src/agents/threat_hunting/agent.py) for attack scenario matching
- [ ] T099 [P] Integrate knowledge retrieval tool in Incident Response Agent (src/agents/incident_response/agent.py) for playbook recommendations
- [ ] T100 [P] Integrate knowledge retrieval tool in Threat Intelligence Agent (src/agents/threat_intelligence/agent.py) for threat context enrichment

---

## Phase 9: Infrastructure as Code (Bicep Deployment)

**Purpose**: Azure resource provisioning for dev and prod environments

- [ ] T101 Create main Bicep template in infra/main.bicep with parameters for environment, location, resource naming
- [ ] T102 [P] Create AI Foundry module in infra/modules/ai-foundry.bicep with workspace, model deployments (gpt-4.1-mini, text-embedding-3-large)
- [ ] T103 [P] Create Cosmos DB module in infra/modules/cosmos.bicep with database, collections, partition keys, TTL settings per data-model.md
- [ ] T104 [P] Create Event Hubs module in infra/modules/event-hubs.bicep with namespace, alert-ingestion hub, consumer groups
- [ ] T105 [P] Create Container Apps module in infra/modules/container-apps.bicep with environment, agent services, orchestrator service, API service
- [ ] T106 [P] Create Application Insights module in infra/modules/monitoring.bicep with workspace, Log Analytics, dashboards
- [ ] T107 [P] Create Azure AI Search module in infra/modules/ai-search.bicep with Standard S1 tier, 3 indexes (attack-scenarios, historical-incidents, threat-intelligence)
- [ ] T108 Create parameter files in infra/parameters/: dev.parameters.json, prod.parameters.json with environment-specific settings
- [ ] T109 [P] Create deployment script in utils/deploy_infrastructure.sh using az deployment group create with Bicep templates

---

## Phase 10: CI/CD Pipeline

**Purpose**: Automated testing, linting, building, and deployment

- [ ] T110 Create CI workflow in .github/workflows/ci.yml with Python linting (black, pylint, mypy), unit tests (pytest with 80% coverage), security scanning (Dependabot, CodeQL)
- [ ] T111 [P] Create CD dev workflow in .github/workflows/cd-dev.yml with automated deployment to dev environment on main branch merge
- [ ] T112 [P] Create CD prod workflow in .github/workflows/cd-prod.yml with manual approval gate before production deployment

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T113 [P] Create architecture diagrams in docs/architecture/: system-context.md, component-diagram.md, deployment-diagram.md, data-flow.md, sequence-diagrams.md using Mermaid
- [ ] T114 [P] Create operational runbooks in docs/runbooks/: incident-escalation.md, agent-failure-recovery.md, scaling-guidance.md
- [ ] T115 [P] Create ADRs in docs/adr/: 001-ai-foundry-vs-custom.md, 002-orchestration-approach.md, 003-mock-data-strategy.md documenting key technology decisions from research.md
- [ ] T116 Create development setup guide in docs/setup.md with prerequisites, environment configuration, local development workflow
- [ ] T117 Validate quickstart.md scenarios: run basic alert triage, incident correlation, interactive hunting, containment with approval, daily briefing generation
- [ ] T118 [P] Create demo data curation script in utils/curate_demo_scenarios.py for 3 scenarios: brute force attack, phishing campaign, ransomware infection per research.md
- [ ] T119 Performance optimization: review agent processing times, optimize KQL queries, tune model parameters (temperature, max tokens) for p95 < 5s triage latency
- [ ] T120 Security hardening: validate Managed Identity configuration, ensure secrets not logged, verify HTTPS endpoints, test RBAC permissions
- [ ] T121 Code cleanup: remove debug statements, standardize error messages, ensure consistent code style, add docstrings to all public functions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 5 - Orchestration (Phase 3)**: Depends on Foundational - BLOCKS agent implementations
- **User Stories 1-4 (Phases 4-7)**: All depend on Orchestration completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Knowledge Base (Phase 8)**: Can proceed in parallel with user stories, integrated when agents are ready
- **Infrastructure (Phase 9)**: Can proceed in parallel with implementation, needed for deployment
- **CI/CD (Phase 10)**: Depends on Infrastructure and some implementation being complete
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 5 - Orchestration (P1)**: MUST complete first - provides framework for all other agents
- **User Story 1 - Alert Triage (P1)**: Can start after Orchestration - No dependencies on other stories
- **User Story 2 - Threat Hunting (P2)**: Can start after Orchestration - May integrate with US1 (hunt after triage) but independently testable
- **User Story 3 - Incident Response (P2)**: Can start after Orchestration - May integrate with US1 (respond after triage) but independently testable
- **User Story 4 - Threat Intelligence (P3)**: Can start after Orchestration - May integrate with US1/US2/US3 (enrich alerts/hunts/responses) but independently testable

### Within Each User Story

- Orchestration framework before agent implementations
- Models before agent logic
- Agent logic before API endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (8 tasks: T003-T006)
- All Foundational tasks marked [P] can run in parallel within Phase 2 (15 tasks: T008-T011, T013-T015, T017, T019-T023)
- Once Orchestration (Phase 3) completes, User Stories 1-4 can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Knowledge base integration tasks marked [P] can run in parallel (T097-T100)
- Infrastructure modules marked [P] can run in parallel (T102-T107, T109)
- CI/CD workflows marked [P] can run in parallel (T111-T112)
- Documentation tasks marked [P] can run in parallel (T113-T115, T118)

---

## Parallel Example: Foundational Phase

```bash
# Launch schema models in parallel (different files):
Task T007: "Create shared Pydantic models in src/shared/schemas.py: SecurityAlert"
Task T008: "Create SecurityIncident model in src/shared/schemas.py"

# Launch infrastructure modules in parallel:
Task T009: "Create authentication module in src/shared/auth.py"
Task T010: "Create structured logging setup in src/shared/logging.py"
Task T011: "Create metrics collection module in src/shared/metrics.py"

# Launch mock services in parallel:
Task T014: "Create mock Sentinel API client in src/mock/sentinel_mock.py"
Task T015: "Create mock Defender XDR API client in src/mock/defender_mock.py"
```

---

## Parallel Example: User Story 1 (Alert Triage)

```bash
# Launch models and schemas in parallel:
Task T035: "Create TriageResult model in src/agents/alert_triage/models.py"
Task T036: "Create alert-triage-input.schema.json and alert-triage-output.schema.json validation"

# After agent is implemented, launch API endpoint in parallel:
Task T048: "Create feedback API endpoint in src/api/routes/feedback.py"
```

---

## Parallel Example: Knowledge Base Integration

```bash
# Once knowledge base is ready, integrate into all agents in parallel:
Task T097: "Integrate knowledge retrieval in Alert Triage Agent"
Task T098: "Integrate knowledge retrieval in Threat Hunting Agent"
Task T099: "Integrate knowledge retrieval in Incident Response Agent"
Task T100: "Integrate knowledge retrieval in Threat Intelligence Agent"
```

---

## Implementation Strategy

### MVP First (User Stories 5 + 1 Only - Orchestration + Alert Triage)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T023) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 5 - Orchestration (T024-T034) - CRITICAL - enables agents
4. Complete Phase 4: User Story 1 - Alert Triage (T035-T048)
5. **STOP and VALIDATE**: Test orchestration + triage independently with mock data
6. Deploy/demo if ready

**MVP Deliverable**: Alert Triage Agent processing mock alerts with risk scoring, correlation, and incident creation - demonstrating core agentic SOC capability

### Incremental Delivery

1. Complete Setup + Foundational + Orchestration → Foundation ready
2. Add User Story 1 (Alert Triage) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Threat Hunting) → Test independently → Deploy/Demo
4. Add User Story 3 (Incident Response) → Test independently → Deploy/Demo
5. Add User Story 4 (Threat Intelligence) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Orchestration together
2. Once Orchestration is done:
   - Developer A: User Story 1 (Alert Triage)
   - Developer B: User Story 2 (Threat Hunting)
   - Developer C: User Story 3 (Incident Response)
   - Developer D: User Story 4 (Threat Intelligence)
   - Developer E: Infrastructure (Bicep) + Knowledge Base (Azure AI Search)
3. Stories complete and integrate independently through orchestration framework

---

## Task Summary

### Total Tasks: 121

### Tasks by Phase:
- Phase 1 (Setup): 6 tasks
- Phase 2 (Foundational): 17 tasks
- Phase 3 (US5 - Orchestration): 11 tasks
- Phase 4 (US1 - Alert Triage): 14 tasks
- Phase 5 (US2 - Threat Hunting): 15 tasks
- Phase 6 (US3 - Incident Response): 15 tasks
- Phase 7 (US4 - Threat Intelligence): 15 tasks
- Phase 8 (Knowledge Base): 7 tasks
- Phase 9 (Infrastructure): 9 tasks
- Phase 10 (CI/CD): 3 tasks
- Phase 11 (Polish): 9 tasks

### Tasks by User Story:
- US1 (Alert Triage): 14 tasks (T035-T048)
- US2 (Threat Hunting): 15 tasks (T049-T063)
- US3 (Incident Response): 15 tasks (T064-T078)
- US4 (Threat Intelligence): 15 tasks (T079-T093)
- US5 (Orchestration): 11 tasks (T024-T034)

### Parallel Opportunities:
- 38 tasks marked [P] for parallel execution
- Setup phase: 4 parallel tasks
- Foundational phase: 15 parallel tasks
- User story implementation: 19 parallel tasks across different agents
- Infrastructure/docs: Multiple parallel opportunities in final phases

### MVP Scope (Suggested):
- Phase 1: Setup (6 tasks)
- Phase 2: Foundational (17 tasks)
- Phase 3: User Story 5 - Orchestration (11 tasks)
- Phase 4: User Story 1 - Alert Triage (14 tasks)
- **Total MVP: 48 tasks** (~40% of total work)

This provides a demonstrable end-to-end system: mock alerts → orchestration → AI triage → risk scoring → incident creation → audit logging

---

## Format Validation

✅ **ALL tasks follow the checklist format**: `- [ ] [ID] [P?] [Story?] Description with file path`

✅ **Task IDs**: Sequential T001-T121

✅ **[P] markers**: 38 tasks marked for parallel execution (different files, no dependencies)

✅ **[Story] labels**: 
- US1: 14 tasks (Alert Triage)
- US2: 15 tasks (Threat Hunting)  
- US3: 15 tasks (Incident Response)
- US4: 15 tasks (Threat Intelligence)
- US5: 11 tasks (Orchestration)

✅ **File paths**: All implementation tasks include exact file paths

✅ **Independent test criteria**: Defined for each user story phase

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are NOT included per feature specification (mock data demonstration focus)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP scope: Orchestration + Alert Triage (48 tasks) provides demonstrable system
