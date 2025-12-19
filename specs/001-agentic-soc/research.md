# Phase 0: Research & Technology Decisions

**Date**: 2025-11-21  
**Phase**: 0 (Research)  
**Status**: Complete

This document consolidates technology research findings and architectural decisions for the Agentic SOC MVP implementation. All "NEEDS CLARIFICATION" items from the Technical Context section of the implementation plan have been resolved through research and analysis.

## Research Methodology

Research conducted using:
- Microsoft Learn documentation (official Azure and Security documentation)
- Microsoft Foundry and Microsoft Agent Framework documentation
- Microsoft Security Copilot developer resources
- KQL and Microsoft Sentinel documentation
- Security best practices and architectural patterns

---

## 1. Microsoft Foundry (AI Foundry) Integration

### Decision: Use Microsoft Foundry with Python SDK

**Rationale**: Microsoft Foundry provides the most comprehensive, enterprise-ready platform for building AI agents with built-in support for:
- Persistent agent instances with managed conversation threads
- Integration with Azure OpenAI models (GPT-4, embeddings)
- Native authentication via Azure Managed Identity
- Built-in observability and monitoring
- Service-managed infrastructure (no manual orchestration required)

**Implementation Approach**:

1. **Agent Creation Pattern** (Python):
```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

async def create_triage_agent():
    async with (
        AzureCliCredential() as credential,
        AzureAIAgentClient(async_credential=credential).create_agent(
            name="AlertTriageAgent",
            instructions="You are an expert SOC analyst specializing in alert triage..."
        ) as agent,
    ):
        return agent
```

2. **Model Selection** (see [MODEL-SELECTION-AOA.md](./MODEL-SELECTION-AOA.md) for comprehensive analysis):
   
   **MVP Phase** (November 2025 - Stable, GA Models):
   - **GPT-4.1-mini**: All agents (reasoning, explanations, risk scoring)
     - Avoids deprecated GPT-4o-mini (retirement Feb 2026 - only 3 months away)
     - ~85% MMLU, GA since April 2025, 5+ months lifecycle remaining
     - Cost: ~$190/month for 10K alerts/day + hunting + response + intelligence
   - **text-embedding-3-large**: Alert similarity, threat intelligence matching
   
   **Production Phase** (Performance-Optimized, Leveraging GPT-5 Family):
   - **GPT-5-nano**: Alert Triage (high volume, 272K context, $120/month)
   - **GPT-5**: Threat Hunting (complex reasoning, 1M context, $60/month)
   - **GPT-5 or Claude-Opus-4-1**: Incident Response (safety-critical, frontier reasoning, $35-50/month)
   - **GPT-4.1-mini**: Threat Intelligence (summarization, cost-optimized, $36/month)
   - **Total**: $251/month (GPT-5 strategy) or $276/month (diversified with Claude/Grok)
   - **Migration Timeline**: Q1 2026 evaluation → Q2 2026 production deployment
   
   **Rationale**: GPT-4.1-mini avoids deprecated GPT-4o family (mid-deprecation, Feb 2026 retirement). Production leverages GPT-5 family (released Aug 2025) with 21-month lifecycle, 272K context, and advanced reasoning. Diversified strategy includes alternatives from Microsoft Foundry catalog (Claude, Grok, DeepSeek, Llama) to hedge vendor risk.

3. **Deployment Model**:
   - **Azure Container Apps**: Host agent application code (FastAPI backend, orchestration logic)
   - **AI Foundry Agents Service**: Persistent agent instances accessed via SDK
   - **Azure Functions**: Lightweight scheduled tasks (daily threat briefings, automated hunts)

**Alternatives Considered**:
- **Custom orchestration with OpenAI SDK**: More flexibility but requires manual state management, authentication, and infrastructure. Rejected due to increased complexity and operational overhead.
- **Azure OpenAI directly**: Lacks agent framework features (persistent threads, managed state). Rejected.
- **Self-hosted LLMs**: No support for production-grade security models. Rejected for MVP.

**References**:
- [Microsoft Foundry Agents Python Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent)
- [Agent Development Lifecycle](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/development-lifecycle?view=foundry)

---

## 2. Microsoft Agent Framework for Orchestration

### Decision: Use Microsoft Agent Framework with Event-Driven Architecture

**Rationale**: Microsoft Agent Framework provides:
- Built-in agent-to-agent communication (A2A protocol)
- Standardized agent interfaces and schemas
- Context propagation between agents
- Integration with Azure services (Event Hubs, Service Bus, Cosmos DB)
- Support for both synchronous and asynchronous workflows

**Architecture Pattern**:

```
Event Hubs (Alert Ingestion)
    ↓
Orchestrator (Microsoft Agent Framework)
    ↓
├── Alert Triage Agent (GPT-4o-mini) → Sentinel Incident API
├── Threat Intelligence Agent (GPT-4o-mini + embeddings) → Enrichment
├── Threat Hunting Agent (GPT-4o-mini + KQL) → Fabric/Sentinel Query
└── Incident Response Agent (GPT-4o-mini) → Approval → Containment APIs
```

**Event-Driven Triggers**:
1. **Alert Ingestion Event** → Triage Agent
2. **Triage Complete Event** → Intelligence Agent (enrichment)
3. **High-Risk Alert Event** → Response Agent (containment workflow)
4. **Schedule Event** (cron) → Hunting Agent (automated hunts)

**Context Passing**:
- **Sentinel Incidents**: Shared context for all agents (incident fields, comments, tags)
- **Cosmos DB**: Agent state, intermediate results, audit logs
- **Event Hubs Messages**: Trigger payloads with correlation IDs

**Alternatives Considered**:
- **Azure Durable Functions**: Stateful orchestration but explicitly excluded per issue requirements. Rejected.
- **Azure Logic Apps**: Visual workflow designer but excluded per issue requirements. Rejected.
- **Custom orchestration in code**: More control but requires reinventing agent coordination patterns. Rejected due to complexity.

**References**:
- [Microsoft Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/)
- [Agent-to-Agent Communication](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/#azure-and-openai-sdk-options-reference)

---

## 3. Security Copilot Integration (Production Path)

### Decision: Plugin Architecture with Custom Skills

**Rationale**: Microsoft Security Copilot provides:
- Pre-built security context and threat intelligence
- Natural language interface for SOC analysts
- Integration with Microsoft Defender XDR and Sentinel
- Custom skills/plugins for organization-specific logic

**MVP Approach**: 
- **Not required for MVP** (simulated data only)
- Define plugin points for future integration
- Document API contracts for Copilot skills

**Production Integration Path**:

1. **Create Custom Skills** (OpenAPI spec):
   - Alert triage skill: Natural language → risk assessment
   - Threat hunting skill: Natural language → KQL query generation
   - Incident response skill: Natural language → playbook recommendation

2. **Authentication**: OAuth Authorization Code Flow with Entra ID

3. **Skill Manifest** (`plugin.yaml`):
```yaml
Descriptor:
  Name: AgenticSOC
  DisplayName: Agentic SOC Skills
  Description: AI-powered SOC agent skills

SkillGroups:
  - Format: API
    Settings:
      OpenApiSpecUrl: https://[domain]/openapi.yaml
      AuthType: OAuthAuthorizationCodeFlow
```

**Alternatives Considered**:
- **Direct Copilot API usage**: Limited to Copilot chat interface only. Rejected as too restrictive.
- **Copilot Agents (hosted)**: Requires containerized agents deployed to Copilot service. Considered for future enhancement.

**References**:
- [Security Copilot API Plugins](https://learn.microsoft.com/en-us/copilot/security/plugin-api)
- [Custom Agent Development](https://learn.microsoft.com/en-us/copilot/security/developer/custom-agent-overview)

---

## 4. KQL Query Patterns for Threat Hunting

### Decision: LLM-Powered KQL Generation with Template Library

**Rationale**: Kusto Query Language (KQL) is the standard query language for:
- Microsoft Sentinel (security logs and alerts)
- Microsoft Defender XDR (endpoint, identity, email telemetry)
- Azure Monitor / Log Analytics (infrastructure logs)
- Microsoft Fabric (long-term data lake queries)

**Implementation Strategy**:

1. **Natural Language → KQL Translation**:
   - Use GPT-4o-mini to translate analyst questions into KQL
   - Provide schema context (table names, field names) in system prompt
   - Validate generated queries against KQL syntax

2. **Common Hunting Query Templates**:

```kql
// Suspicious Sign-In Pattern
SigninLogs
| where TimeGenerated > ago(7d)
| where ResultType != 0
| where UserPrincipalName == "{user}"
| summarize FailedAttempts = count(), 
            IPAddresses = make_set(IPAddress), 
            Locations = make_set(Location)
  by UserPrincipalName
| where FailedAttempts > 10

// Lateral Movement Detection
DeviceNetworkEvents
| where TimeGenerated > ago(24h)
| where ActionType == "ConnectionSuccess"
| where RemotePort in (445, 3389, 5985) // SMB, RDP, WinRM
| summarize ConnectionCount = count(),
            TargetDevices = dcount(DeviceId)
  by InitiatingProcessAccountName
| where TargetDevices > 5

// Uncommon Process Execution
DeviceProcessEvents
| where TimeGenerated > ago(1d)
| where ProcessCommandLine has_any ("powershell", "cmd", "wscript")
| summarize ExecutionCount = count()
  by ProcessCommandLine, DeviceId
| join kind=leftanti (
    DeviceProcessEvents
    | where TimeGenerated between (ago(30d) .. ago(2d))
    | summarize by ProcessCommandLine
  ) on ProcessCommandLine
| top 50 by ExecutionCount desc
```

3. **Query Optimization**:
   - Use `ago()` for time filters (indexed)
   - Apply filters early in query pipeline
   - Use `summarize` before `join` when possible
   - Leverage `project` to reduce data volume
   - p95 latency target: < 30 seconds (Sentinel), < 5 minutes (Fabric deep search)

**Alternatives Considered**:
- **SQL-based queries**: Not supported by Sentinel/Defender. Rejected.
- **Custom DSL**: Requires building translator layer. Rejected as unnecessary complexity.
- **Pre-generated queries only**: Inflexible for novel threats. Rejected.

**References**:
- [KQL Threat Hunting in Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/hunting)
- [Common KQL Tasks](https://learn.microsoft.com/en-us/kusto/query/tutorials/common-tasks-microsoft-sentinel)
- [KQL Learning Resources](https://learn.microsoft.com/en-us/training/paths/sc-200-utilize-kql-for-azure-sentinel/)

---

## 5. Mock Data Strategy

### Decision: Transform GUIDE/Attack Datasets to Sentinel Format with Configurable Streaming

**Rationale**: 
- **GUIDE Dataset**: Real Microsoft security incidents (1.17M records, ground truth labels)
- **Attack Dataset**: Comprehensive attack scenarios (14K scenarios, 99.8% MITRE coverage)
- **Sentinel Alert Schema**: Industry-standard format (Microsoft Graph Security API compatible)

**Implementation Approach**:

1. **GUIDE Dataset Transformation** (Real incidents → Sentinel alerts):

```python
# Transform GUIDE format to Sentinel SecurityAlert schema
def transform_guide_to_sentinel(guide_record):
    return {
        "AlertName": guide_record["Category"],
        "AlertType": f"GUIDE_{guide_record['AlertId']}",
        "Severity": map_severity(guide_record["IncidentGrade"]),
        "Description": guide_record["AlertTitle"],
        "Entities": extract_entities(guide_record),
        "TimeGenerated": guide_record["Timestamp"],
        "ExtendedProperties": {
            "MitreTechniques": guide_record["MitreTechniques"],
            "EntityCount": guide_record["EntityCount"],
            "OrgId": guide_record["OrgId"]
        },
        "ProviderName": "Microsoft Sentinel (Mock)",
        "SystemAlertId": str(uuid.uuid4())
    }
```

2. **Attack Dataset Usage** (Scenario library for playbooks):
   - Map attack scenarios to MITRE ATT&CK techniques
   - Generate response playbooks from detection/remediation fields
   - Enrich alerts with threat intelligence from attack descriptions

3. **Configurable Streaming** (Mock real-time ingestion):

```python
class MockDataStreamer:
    def __init__(self, interval_seconds=15):
        self.interval = interval_seconds
        self.checkpoint_file = "/tmp/mock_data_checkpoint.json"
    
    async def stream_alerts(self):
        """Stream alerts at configured interval (default 15s)"""
        while True:
            batch = self.get_next_batch(batch_size=5)
            for alert in batch:
                await event_hub_client.send(alert)
            await asyncio.sleep(self.interval)
    
    def get_next_batch(self, batch_size):
        """Checkpoint-based replay for reproducible demos"""
        checkpoint = self.load_checkpoint()
        next_batch = self.dataset[checkpoint:checkpoint+batch_size]
        self.save_checkpoint(checkpoint + batch_size)
        return next_batch
```

4. **Demo Scenario Curation**:
   - **Scenario 1**: Brute force attack (20 failed logins → successful login → lateral movement)
   - **Scenario 2**: Phishing campaign (suspicious email → credential theft → data exfiltration)
   - **Scenario 3**: Ransomware infection (malware execution → file encryption → C2 communication)

**Alternatives Considered**:
- **Fully synthetic data generation**: Lower fidelity, no ground truth. Rejected.
- **Direct Sentinel integration**: Not allowed for MVP (mock data only). Deferred to production.
- **Static dataset (no streaming)**: Doesn't demonstrate real-time capabilities. Rejected.

**References**:
- [GUIDE Dataset Analysis](../dataset-analysis/guide-dataset-analysis.md)
- [Attack Dataset Analysis](../dataset-analysis/attack-dataset-analysis.md)
- [Implementation Guidance](../dataset-analysis/implementation-guidance.md)

---

## 6. Threat Intelligence Sources

### Decision: Multi-Tier Intelligence Architecture

**Rationale**: Effective threat intelligence requires multiple sources with different characteristics:
- **Strategic Intelligence**: High-level threat trends, campaigns, actor profiles
- **Tactical Intelligence**: TTPs, MITRE ATT&CK mappings, attack patterns
- **Operational Intelligence**: IOCs (IPs, domains, hashes), real-time threat feeds

**Intelligence Sources**:

1. **MITRE ATT&CK Framework** (Tactical):
   - 993 unique techniques in GUIDE dataset (42.5% coverage)
   - 5,406+ techniques in Attack dataset (99.8% coverage)
   - **Usage**: Map alerts to techniques, identify attack progression, generate hunting hypotheses

2. **Attack Dataset** (Scenario-Based Intelligence):
   - 14,133 attack scenarios across 64 categories
   - Detailed detection methods and remediation guidance
   - **Usage**: Generate threat briefings, enrich alerts with context, recommend countermeasures

3. **GUIDE Dataset** (Historical Intelligence):
   - 1.17M+ real-world security incidents
   - Ground truth labels (TruePositive, FalsePositive, BenignPositive)
   - **Usage**: Train ML models, establish baselines, identify false positive patterns

4. **Microsoft Threat Intelligence** (Production - Plugin Point):
   - Microsoft Defender Threat Intelligence API
   - Real-time IOC feeds (IPs, domains, file hashes)
   - Threat actor profiles and campaigns
   - **MVP Status**: Plugin point defined, not implemented (requires production API access)

**IOC Enrichment Pattern**:

```python
async def enrich_ioc(ioc_value, ioc_type):
    """Enrich IOC with threat intelligence"""
    
    # Check local Attack dataset
    local_intel = attack_dataset.search(ioc_value)
    
    # Check MITRE ATT&CK mappings
    mitre_context = mitre_framework.get_techniques_for_ioc(ioc_value)
    
    # [Production] Query Microsoft Threat Intelligence
    # external_intel = await ms_threat_intel_api.lookup(ioc_value)
    
    return {
        "ioc": ioc_value,
        "type": ioc_type,
        "reputation": calculate_reputation(local_intel),
        "associated_threats": local_intel.get("attack_types", []),
        "mitre_techniques": mitre_context,
        "first_seen": local_intel.get("timestamp"),
        "context": local_intel.get("description")
    }
```

**Daily Threat Briefing Generation**:

```python
async def generate_daily_briefing():
    """Generate daily threat intelligence briefing"""
    
    # Analyze recent alerts (last 24h)
    recent_alerts = await get_recent_alerts(hours=24)
    
    # Extract trending attack patterns
    trending_techniques = extract_mitre_techniques(recent_alerts)
    
    # Match with Attack dataset scenarios
    relevant_scenarios = attack_dataset.find_by_techniques(trending_techniques)
    
    # Generate natural language briefing (GPT-4o)
    prompt = f"""
    Generate a threat intelligence briefing for SOC analysts:
    
    Recent Activity:
    - {len(recent_alerts)} alerts in last 24h
    - Top MITRE techniques: {trending_techniques}
    
    Relevant Threat Scenarios:
    {relevant_scenarios}
    
    Format: Executive summary, key threats, recommended actions.
    """
    
    briefing = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return briefing.choices[0].message.content
```

**Alternatives Considered**:
- **Single intelligence source**: Insufficient coverage. Rejected.
- **Real-time threat feeds only**: Expensive for MVP, no offline capability. Deferred to production.
- **Manual intelligence curation**: Not scalable. Rejected.

**References**:
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [Microsoft Defender Threat Intelligence](https://learn.microsoft.com/en-us/defender-xdr/threat-intelligence-overview)

---

## 7. Observability Patterns

### Decision: Azure Monitor + Application Insights with OpenTelemetry

**Rationale**: Comprehensive observability requires:
- **Structured logging**: JSON-formatted logs with consistent schema
- **Distributed tracing**: Track requests across agents and services
- **Metrics collection**: Performance, error rates, agent-specific KPIs
- **Dashboards**: Real-time visualization of system health

**Implementation Architecture**:

1. **Structured Logging** (Python):

```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Usage in agent code
logger.info(
    "alert_triaged",
    alert_id="12345",
    severity="High",
    risk_score=85,
    triage_time_ms=1250,
    agent="AlertTriageAgent"
)
```

2. **Distributed Tracing** (OpenTelemetry):

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Configure Azure Monitor exporter
configure_azure_monitor(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
)

tracer = trace.get_tracer(__name__)

# Trace agent workflow
async def triage_alert(alert):
    with tracer.start_as_current_span("triage_alert") as span:
        span.set_attribute("alert.id", alert["SystemAlertId"])
        span.set_attribute("alert.severity", alert["Severity"])
        
        # Step 1: Risk scoring
        with tracer.start_as_current_span("risk_scoring"):
            risk_score = await calculate_risk_score(alert)
        
        # Step 2: Correlation
        with tracer.start_as_current_span("alert_correlation"):
            related_alerts = await find_related_alerts(alert)
        
        # Step 3: Enrichment
        with tracer.start_as_current_span("threat_intelligence"):
            enrichment = await enrich_with_threat_intel(alert)
        
        span.set_attribute("risk_score", risk_score)
        span.set_attribute("related_alert_count", len(related_alerts))
        
        return {
            "risk_score": risk_score,
            "related_alerts": related_alerts,
            "enrichment": enrichment
        }
```

3. **Metrics Collection** (Prometheus-compatible):

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
alerts_processed = Counter(
    "agentic_soc_alerts_processed_total",
    "Total alerts processed",
    ["agent", "severity", "outcome"]
)

triage_duration = Histogram(
    "agentic_soc_triage_duration_seconds",
    "Alert triage processing duration",
    ["severity"]
)

active_incidents = Gauge(
    "agentic_soc_active_incidents",
    "Number of active incidents"
)

# Usage
async def triage_alert(alert):
    with triage_duration.labels(severity=alert["Severity"]).time():
        result = await perform_triage(alert)
    
    alerts_processed.labels(
        agent="AlertTriageAgent",
        severity=alert["Severity"],
        outcome=result["outcome"]
    ).inc()
    
    return result
```

4. **Health Checks**:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """Kubernetes liveness probe"""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    checks = {
        "cosmos_db": await check_cosmos_db_connection(),
        "ai_foundry": await check_ai_foundry_connection(),
        "event_hubs": await check_event_hubs_connection()
    }
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ready else "not_ready", "checks": checks}
    )
```

5. **Azure Monitor Dashboard** (KQL queries):

```kql
// Agent Performance Dashboard

// Alert Triage Processing Time (p95)
traces
| where message == "alert_triaged"
| extend triage_time_ms = toreal(customDimensions.triage_time_ms)
| summarize p95_triage_ms = percentile(triage_time_ms, 95) by bin(timestamp, 5m)
| render timechart

// Error Rate by Agent
traces
| where severityLevel >= 3 // ERROR or CRITICAL
| summarize ErrorCount = count() by agent = tostring(customDimensions.agent), bin(timestamp, 5m)
| render timechart

// Active Incidents Over Time
customMetrics
| where name == "agentic_soc_active_incidents"
| summarize avg(value) by bin(timestamp, 5m)
| render timechart

// Containment Action Success Rate
traces
| where message == "containment_action_executed"
| extend success = customDimensions.success == "true"
| summarize SuccessRate = avg(todouble(success)) * 100 by bin(timestamp, 1h)
| render timechart
```

**Alternatives Considered**:
- **ELK Stack**: Requires self-hosted infrastructure. Rejected for MVP (use Azure-managed services).
- **Prometheus + Grafana**: Good for metrics but weak on logs/traces. Rejected (prefer integrated solution).
- **Custom logging**: Reinventing the wheel. Rejected.

**References**:
- [Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)
- [Distributed Tracing in Functions](https://learn.microsoft.com/en-us/azure/azure-monitor/app/monitor-functions#distributed-tracing-for-java-applications)
- [Application Insights for Python](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python)

---

## 8. Azure AI Search for Knowledge Base (RAG Pattern)

### Decision: Use Azure AI Search with Agentic Retrieval for Agent Knowledge

**Rationale**: Agents need access to contextual knowledge beyond their training data:
- **Attack Dataset + Runbooks**: 14K attack scenarios with MITRE-mapped tactics, response playbooks
- **Historical Incident Patterns**: Query GUIDE dataset (1.17M incidents) for similar past incidents
- **Threat Intelligence**: IOC databases, vulnerability information, threat actor profiles
- **SOC Documentation**: Internal runbooks, escalation procedures, analyst notes

**Why Azure AI Search**:
- **Agentic Retrieval** (preview): Purpose-built for AI agents with intelligent query decomposition
- **Hybrid Search**: Combines vector similarity + keyword matching for best relevance
- **Integration**: Native integration with Microsoft Foundry Agent Framework
- **Performance**: Sub-second retrieval latency, scales to millions of documents
- **Security**: Integrated with Azure Entra ID, supports document-level security

**Implementation** (Agent Framework Integration):

```python
from azure.search.documents.agent import KnowledgeAgentRetrievalClient
from azure.search.documents.agent.models import (
    KnowledgeAgentRetrievalRequest,
    KnowledgeAgentMessage,
    KnowledgeAgentMessageTextContent,
    SearchIndexKnowledgeSourceParams
)
from agent_framework import ChatAgent, ChatMessage, Role
from agent_framework.azure import AzureOpenAIChatClient

# Initialize knowledge agent client
knowledge_client = KnowledgeAgentRetrievalClient(
    endpoint=search_endpoint,
    agent_name="soc-knowledge-agent",
    credential=credential
)

# Agent uses natural language to query knowledge base
async def enrich_alert_with_knowledge(alert: SecurityAlert):
    """
    Alert Triage Agent queries knowledge base for context:
    - Similar past incidents
    - Known attack patterns matching alert indicators
    - Threat intelligence on entities (IPs, domains, hashes)
    """
    
    # Construct contextual query
    query = f"""
    Alert: {alert.AlertName}
    Entities: {', '.join([e.Properties.get('Address', e.Properties.get('Name', '')) for e in alert.Entities])}
    MITRE Techniques: {', '.join(alert.ExtendedProperties.get('MitreTechniques', []))}
    
    Find:
    1. Similar historical incidents with outcomes
    2. Known attack scenarios matching these indicators
    3. Threat intelligence on observed entities
    """
    
    # Agentic retrieval - automatically decomposes query into focused sub-queries
    retrieval_request = KnowledgeAgentRetrievalRequest(
        messages=[
            KnowledgeAgentMessage(
                role="user",
                content=[KnowledgeAgentMessageTextContent(text=query)]
            )
        ],
        knowledge_source_params=[
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name="attack-scenarios",
                kind="searchIndex"
            ),
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name="historical-incidents",
                kind="searchIndex"
            ),
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name="threat-intelligence",
                kind="searchIndex"
            )
        ]
    )
    
    result = knowledge_client.retrieve(retrieval_request=retrieval_request)
    
    # Extract grounding data from retrieval response
    enrichment_data = {
        "similar_incidents": extract_incidents(result),
        "matched_attack_scenarios": extract_scenarios(result),
        "threat_intel_matches": extract_threat_intel(result),
        "response_playbooks": extract_playbooks(result)
    }
    
    return enrichment_data

# Alert Triage Agent with knowledge retrieval tool
async def create_triage_agent_with_knowledge():
    chat_client = AzureOpenAIChatClient()
    
    async def query_knowledge_base(query: str) -> str:
        """Tool for agent to query knowledge base"""
        result = await knowledge_client.retrieve(
            KnowledgeAgentRetrievalRequest(
                messages=[KnowledgeAgentMessage(
                    role="user",
                    content=[KnowledgeAgentMessageTextContent(text=query)]
                )],
                knowledge_source_params=[
                    SearchIndexKnowledgeSourceParams(
                        knowledge_source_name="attack-scenarios",
                        kind="searchIndex"
                    )
                ]
            )
        )
        return format_knowledge_results(result)
    
    agent = ChatAgent(
        name="AlertTriageAgent",
        chat_client=chat_client,
        instructions="""
        You are an expert SOC analyst specializing in alert triage.
        
        When analyzing alerts:
        1. Use query_knowledge_base to find similar past incidents
        2. Look up attack scenarios matching MITRE techniques
        3. Check threat intelligence for entity reputation
        4. Reference response playbooks for known patterns
        
        Provide risk score (0-100), triage decision, and explanation.
        """,
        tools=[query_knowledge_base]
    )
    
    return agent
```

**Knowledge Base Structure** (3 search indexes):

```python
# Index 1: Attack Scenarios & Response Playbooks (14K scenarios from Attack dataset)
# Index 2: Historical Incidents (10K curated incidents from GUIDE dataset)
# Index 3: Threat Intelligence & IOCs (50K indicators, refreshed weekly)
```

**Performance Targets**:
- **Retrieval Latency**: < 500ms p95 (parallel sub-queries)
- **Relevance**: Top-3 results @ 85%+ precision (hybrid + semantic ranking)
- **Index Size**: ~75K documents total across 3 indexes

**Cost Estimation** (MVP):
- **Azure AI Search Standard S1**: ~$250/month (50GB storage, 100K docs, 3 indexes)
- **OpenAI Embeddings**: ~$20/month (one-time indexing + incremental updates)

**Alternatives Considered**:
- **Agent in-context only**: Insufficient for 14K attack scenarios. Rejected - context window limits.
- **Cosmos DB vector search**: Less mature, no agentic retrieval. Deferred to evaluation phase.
- **Fabric OneLake**: Not optimized for real-time retrieval. Better for batch analytics.
- **No knowledge base**: Agents would lack context. Poor triage quality. Rejected.

**References**:
- [Azure AI Search Agentic Retrieval](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview)
- [RAG Pattern with Azure AI Search](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview)
- [Agent Framework Knowledge Retrieval](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/knowledge-retrieval)

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **AI Platform** | Microsoft Foundry with Python SDK | Enterprise-ready, persistent agents, managed infrastructure |
| **Orchestration** | Microsoft Agent Framework + Event Hubs | Standardized A2A communication, event-driven architecture |
| **Security Copilot** | Plugin points defined, not implemented in MVP | Production integration path documented, not required for demo |
| **Query Language** | KQL with LLM-powered generation | Industry standard for Sentinel/Defender, powerful analytics |
| **Mock Data** | GUIDE + Attack datasets, configurable streaming | Real-world data quality, reproducible demos, ground truth labels |
| **Threat Intelligence** | Multi-tier (MITRE, Attack dataset, historical) | Comprehensive coverage, tactical + operational intelligence |
| **Knowledge Base** | Azure AI Search with Agentic Retrieval | RAG pattern for agent context, 14K attack scenarios + 10K historical incidents |
| **Observability** | Azure Monitor + Application Insights + OpenTelemetry | Unified platform, distributed tracing, production-ready |

---

## 9. Azure AI Projects SDK - V2 Agent Deployment Patterns

### Decision: Use Azure AI Projects SDK 2.0.0b2+ for V2 Agent Deployment

**Rationale**: The Azure AI Projects SDK provides cloud-hosted, persistent agent instances that can be deployed once and reused across multiple orchestration scenarios. This enables clean separation between infrastructure deployment (Phase A) and runtime orchestration (Phase B).

**Implementation Approach**:

**IMPORTANT - Correct SDK Usage (azure-ai-projects >=2.0.0b1)**:

**✅ VERIFIED APPROACH (December 2025)**: Use `AIProjectClient` from `azure-ai-projects>=2.0.0b1` package.

**Correct imports**:
```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition  # For defining agent configuration
from azure.identity import DefaultAzureCredential
from typing import Any  # Use Any for agent type hints
```

**Agent objects**: Agents returned by the SDK include `AgentObject` (from `get()` and `list()`) and `AgentVersionObject` (from `create_version()`). Both are compatible with MutableMapping.

1. **Agent Creation and Update with `AIProjectClient.agents`**:

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
import os

# Connect to Microsoft Foundry project
client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# Create a NEW agent (first time)
agent = client.agents.create(
    name="AlertTriageAgent",
    definition=PromptAgentDefinition(
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        instructions="""
You are an expert SOC analyst specializing in alert triage and risk assessment.

Your role is to analyze security alerts and provide:
1. Risk assessment (Critical/High/Medium/Low)
2. Clear reasoning for the assessment
3. Identification of related alerts for correlation
4. Recommended next steps for the SOC team

Input format: You will receive security alerts in JSON format.
Output format: Provide structured JSON with riskLevel, explanation, relatedAlerts, and nextSteps.
        """,
    ),
    description="Alert triage and risk assessment agent"
)

print(f"Agent created: {agent.name} (id: {agent.id}, version: {agent.version})")

# UPDATE an existing agent (creates new version)
updated_agent = client.agents.create_version(
    agent_name="AlertTriageAgent",
    definition=PromptAgentDefinition(
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        instructions="Updated instructions here...",
    ),
    description="Updated alert triage agent"
)

print(f"Agent updated: {updated_agent.name} (version: {updated_agent.version})")
```

2. **Agent Discovery and Listing Patterns**:

```python
# List all agents in the project
agents = list(client.agents.list())
for agent in agents:
    print(f"Agent: {agent.name}")

# Get a specific agent by name (azure-ai-projects 2.0+)
# ✅ CORRECT: get() method accepts agent_name parameter
agent = client.agents.get(agent_name="AlertTriageAgent")
print(f"Retrieved agent: {agent.name} (id: {agent.id})")

# Delete agent by name
client.agents.delete(agent_name="AlertTriageAgent")
print("Agent deleted")
```

3. **Separation of Deployment from Orchestration**:

**Phase A: Infrastructure Deployment (One-time)**
```python
# deploy_agents.py - Run once to create/update persistent agents
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
import os

def deploy_all_agents():
    """Deploy all SOC agents to Microsoft Foundry"""
    
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential()
    )
    
    # Agent definitions from instruction files
    agent_definitions = {
        "AlertTriageAgent": load_instructions("alert_triage_instructions.md"),
        "ThreatHuntingAgent": load_instructions("threat_hunting_instructions.md"),
        "IncidentResponseAgent": load_instructions("incident_response_instructions.md"),
        "ThreatIntelligenceAgent": load_instructions("threat_intelligence_instructions.md"),
        "SOC_Manager": load_instructions("manager_instructions.md")
    }
    
    deployed_agents = {}
    model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    
    for agent_name, instructions in agent_definitions.items():
        # Check if agent exists
        try:
            existing = client.agents.get(agent_name=agent_name)
            # Agent exists, create new version
            agent = client.agents.create_version(
                agent_name=agent_name,
                definition=PromptAgentDefinition(
                    model=model,
                    instructions=instructions,
                ),
                description=f"{agent_name} for Agentic SOC MVP"
            )
            print(f"✓ Updated: {agent_name} (version: {agent.version})")
        except:
            # Agent doesn't exist, create new one
            agent = client.agents.create(
                name=agent_name,
                definition=PromptAgentDefinition(
                    model=model,
                    instructions=instructions,
                ),
                description=f"{agent_name} for Agentic SOC MVP"
            )
            print(f"✓ Created: {agent_name} (version: {agent.version})")
        
        deployed_agents[agent_name] = agent
    
    return deployed_agents

# Run deployment
if __name__ == "__main__":
    deploy_all_agents()
```

**Important SDK Notes (azure-ai-projects 2.0.0b1+)**:
- **Package**: `azure-ai-projects>=2.0.0b1` (NOT azure-ai-agents)
- **Client**: Use `AIProjectClient` with project endpoint
- **Methods on `client.agents`**:
  - `create(name, definition, description)` - Create new agent
  - `create_version(agent_name, definition, description)` - Update/create version
  - `get(agent_name)` - Retrieve agent by name ✅ This works!
  - `list()` - List all agents
  - `delete(agent_name)` - Delete agent by name
- **Agent Definition**: Use `PromptAgentDefinition(model, instructions)` for prompt agents
- **Returns**: `AgentObject` (get/list) or `AgentVersionObject` (create_version)
- **Example from user**: See their working code snippet with `get(agent_name=...)`

**Phase B: Runtime Orchestration (Demonstration)**
```python
# orchestrator.py - Use deployed agents in workflows
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def discover_agents():
    """Discover pre-deployed agents for orchestration"""
    
    project_client = AIProjectClient.from_connection_string(
        conn_str=os.environ["PROJECT_CONNECTION_STRING"],
        credential=DefaultAzureCredential()
    )
    
    # Discover deployed agents by name
    # Note: get_agent() takes agent_id, not agent_name. Must list and filter by name.
    all_agents = list(project_client.agents.list_agents())
    
    agent_mapping = {
        "triage": "AlertTriageAgent",
        "hunting": "ThreatHuntingAgent",
        "response": "IncidentResponseAgent",
        "intel": "ThreatIntelligenceAgent",
        "manager": "SOC_Manager"
    }
    
    agents = {}
    for role, name in agent_mapping.items():
        agent = next((a for a in all_agents if a.name == name), None)
        if agent:
            agents[role] = agent
    
    print(f"Discovered {len(agents)} agents for orchestration")
    return agents

# Agents are now ready for magentic orchestration (see next section)
```

4. **Using Agents with OpenAI Client**:

```python
# Create conversation and get responses using discovered agents
with project_client.get_openai_client() as openai_client:
    # Reference agent by name in extra_body
    conversation = openai_client.conversations.create(
        items=[{
            "type": "message",
            "role": "user",
            "content": "Analyze this high-severity brute force alert..."
        }]
    )
    
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent": {"name": "AlertTriageAgent", "type": "agent_reference"}},
        input=""
    )
    
    print(f"Triage result: {response.output_text}")
```

**Key Benefits**:
- **Persistence**: Agents are created once and can be referenced by name across multiple sessions
- **Versioning**: Full version control for agent definitions
- **Reusability**: Same agents can be used in different orchestration patterns
- **Separation**: Infrastructure deployment is decoupled from demonstration logic
- **Discovery**: Agents can be discovered and listed at runtime
- **Metadata**: Rich metadata support for agent categorization and tracking

**Alternatives Considered**:
- **Ephemeral local agents**: No persistence, requires recreation. Rejected.
- **Custom agent storage**: More complex, no native SDK support. Rejected.

**References**:
- [Azure AI Projects SDK - Agent Creation](https://azuresdkdocs.z19.web.core.windows.net/python/azure-ai-projects/2.0.0b2/)
- [Agent Version Management API](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/)

---

## 10. Microsoft Agent Framework - Magentic Orchestration

### Decision: Use Magentic Orchestration for MVP Demonstration

**Rationale**: Magentic orchestration (based on AutoGen's Magentic-One system) is specifically designed for complex, open-ended security operations tasks where the solution path is not known in advance. A dedicated manager agent dynamically selects which specialized agent should act next based on evolving context, making it ideal for SOC workflows.

**Core Concepts**:

1. **Dynamic Agent Selection**: Manager agent decides which agent to invoke based on current context and progress
2. **Iterative Refinement**: System can break down complex problems and iterate through multiple rounds
3. **Progress Tracking**: Built-in mechanisms to detect stalls and reset plans if needed
4. **Human Oversight**: Optional human-in-the-loop for plan review, tool approval, and stall intervention
5. **Flexible Collaboration**: Agents can be called multiple times in any order

**Implementation Pattern**:

1. **Building a Magentic Workflow**:

```python
from agent_framework import MagenticBuilder
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

async def create_soc_workflow():
    """Create magentic workflow with discovered SOC agents"""
    
    # Connect to Foundry and discover agents
    project_client = AIProjectClient.from_connection_string(
        connection_string=os.environ["PROJECT_CONNECTION_STRING"],
        credential=DefaultAzureCredential()
    )
    
    # Get deployed agents
    triage_agent = project_client.agents.get_agent(agent_name="AlertTriageAgent")
    hunting_agent = project_client.agents.get_agent(agent_name="ThreatHuntingAgent")
    response_agent = project_client.agents.get_agent(agent_name="IncidentResponseAgent")
    intel_agent = project_client.agents.get_agent(agent_name="ThreatIntelligenceAgent")
    manager_agent = project_client.agents.get_agent(agent_name="SOC_Coordinator")
    
    # Get chat client for manager
    chat_client = project_client.inference.get_chat_completions_client()
    
    # Build magentic workflow
    workflow = (
        MagenticBuilder()
        .participants(
            triage=triage_agent,
            hunting=hunting_agent,
            response=response_agent,
            intel=intel_agent
        )
        .with_standard_manager(
            chat_client=chat_client,
            max_round_count=10,      # Maximum collaboration rounds
            max_stall_count=3,       # Rounds without progress before intervention
            max_reset_count=2        # Maximum plan resets allowed
        )
        .build()
    )
    
    return workflow
```

2. **Running Workflow with Event Streaming**:

```python
from agent_framework import AgentRunUpdateEvent

async def run_alert_triage_workflow(alert_data):
    """Execute SOC workflow with streaming events"""
    
    workflow = await create_soc_workflow()
    
    # Construct task for manager
    task = f"""
    Analyze this security alert and coordinate appropriate response:
    
    Alert: {alert_data['AlertName']}
    Severity: {alert_data['Severity']}
    Description: {alert_data['Description']}
    Entities: {alert_data['Entities']}
    """
    
    # Stream workflow execution
    async for event in workflow.run(task):
        if isinstance(event, AgentRunUpdateEvent):
            # Handle different event types
            if event.magentic_event_type == "plan_created":
                print(f"📋 Manager Plan: {event.data}")
            elif event.magentic_event_type == "agent_selected":
                print(f"🎯 Selected Agent: {event.executor_id}")
            elif event.magentic_event_type == "agent_response":
                print(f"💬 {event.executor_id}: {event.data}")
            elif event.magentic_event_type == "progress_update":
                print(f"⏳ Progress: {event.data}")
            elif event.magentic_event_type == "workflow_complete":
                print(f"✅ Workflow Complete: {event.data}")
    
    # Get final result
    final_state = workflow.get_final_state()
    outputs = workflow.get_outputs()
    
    return {
        "state": final_state,
        "outputs": outputs
    }
```

3. **Human-in-the-Loop: Plan Review**:

```python
async def run_with_plan_review():
    """Enable human review of manager's plan before execution"""
    
    workflow = (
        MagenticBuilder()
        .participants(
            triage=triage_agent,
            hunting=hunting_agent,
            response=response_agent
        )
        .with_standard_manager(
            chat_client=chat_client,
            max_round_count=10,
            max_stall_count=3
        )
        .with_plan_review()  # Enable plan review
        .build()
    )
    
    async for event in workflow.run(task):
        if event.magentic_event_type == "plan_review_request":
            # Present plan to human reviewer
            plan = event.data['plan']
            print(f"📋 Proposed Plan:\n{plan}")
            
            # Get human approval
            decision = input("Approve plan? (approve/revise/continue): ")
            
            if decision == "approve":
                event.respond(action="APPROVE")
            elif decision == "revise":
                feedback = input("Revision feedback: ")
                event.respond(action="REVISE", feedback=feedback)
            else:
                event.respond(action="CONTINUE")
```

4. **Human-in-the-Loop: Tool Approval**:

```python
from agent_framework import FunctionApprovalRequestContent

async def run_with_tool_approval():
    """Enable human approval for agent tool calls"""
    
    workflow = create_soc_workflow()
    
    async for event in workflow.run(task):
        if isinstance(event.data, FunctionApprovalRequestContent):
            # Agent is requesting permission to call a tool
            tool_name = event.data.function_name
            tool_args = event.data.arguments
            
            print(f"🔧 Agent wants to call: {tool_name}")
            print(f"   Arguments: {tool_args}")
            
            approval = input("Approve? (yes/no): ")
            
            if approval.lower() == "yes":
                event.respond(action="APPROVE")
            else:
                event.respond(action="DENY", reason="High-risk action requires manual review")
```

5. **Human-in-the-Loop: Stall Intervention**:

```python
async def run_with_stall_intervention():
    """Enable human intervention when workflow stalls"""
    
    workflow = (
        MagenticBuilder()
        .participants(triage=triage_agent, hunting=hunting_agent)
        .with_standard_manager(
            chat_client=chat_client,
            max_round_count=10,
            max_stall_count=1  # Detect stall after 1 round without progress
        )
        .with_human_input_on_stall()  # Request human input when stalled
        .build()
    )
    
    async for event in workflow.run(task):
        if event.magentic_event_type == "stall_intervention_request":
            print("⚠️  Workflow has stalled. Agents are not making progress.")
            print(f"   Current state: {event.data['current_state']}")
            
            # Options: CONTINUE (try again), REPLAN (create new plan), GUIDANCE (provide hint)
            action = input("Action (continue/replan/guidance): ")
            
            if action == "guidance":
                hint = input("Provide guidance for agents: ")
                event.respond(action="GUIDANCE", guidance=hint)
            elif action == "replan":
                event.respond(action="REPLAN")
            else:
                event.respond(action="CONTINUE")
```

**Manager Agent Instructions Pattern** (Enforcing Triage-First):

```markdown
# SOC Coordinator Agent Instructions

You are the SOC Coordinator managing a team of security analysts (agents).

## Your Team
- **triage**: Alert Triage Agent - Risk assessment and prioritization
- **hunting**: Threat Hunting Agent - Proactive threat detection and KQL queries
- **response**: Incident Response Agent - Containment and remediation recommendations
- **intel**: Threat Intelligence Agent - Threat context and briefings

## Coordination Rules
1. **ALWAYS START WITH TRIAGE**: Every security task must begin with the triage agent to assess risk
2. After triage, select agents based on the risk level and findings:
   - High/Critical risk: Invoke response agent for containment recommendations
   - Suspicious patterns: Invoke hunting agent to search for related activity
   - Unknown threats: Invoke intel agent for threat context
3. Agents can be called multiple times if needed
4. Track progress and detect when agents are not making progress
5. Create clear, actionable plans with specific agent assignments

## Plan Format
For each task, create a plan with:
- Step 1: triage - Assess alert risk and identify key indicators
- Step 2: [agent] - Based on triage results, investigate further
- Step 3: [agent] - Complete response actions
```

**Key Configuration Parameters**:

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| `max_round_count` | Maximum collaboration rounds before stopping | 10-20 |
| `max_stall_count` | Rounds without progress before intervention | 2-3 |
| `max_reset_count` | Maximum plan resets allowed | 1-2 |

**Alternatives Considered**:
- **Sequential orchestration**: Too rigid for security operations. Rejected.
- **Concurrent orchestration**: No coordination between agents. Rejected.
- **Custom orchestrator**: Reinventing planning logic. Rejected - leverage proven patterns.

**References**:
- [Magentic Orchestration Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/magentic)
- [MagenticBuilder API Reference](https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.magenticbuilder)
- [AutoGen Magentic-One System](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html)

---

## 11. Agent Instructions - Best Practices for System Prompts

### Decision: Instruction-First Approach with Comprehensive System Prompts

**Rationale**: The MVP focuses on high-quality agent instructions as the primary mechanism for agent behavior. The LLM performs all reasoning, decision-making, and analysis based on instructions - NO custom Python business logic (risk scoring, query generation, etc.). This leverages the model's capabilities while keeping the codebase minimal.

**Core Principles**:

1. **Clarity and Specificity**: Instructions must be clear, specific, and unambiguous
2. **Role Definition**: Explicitly define the agent's role and expertise
3. **Input/Output Contracts**: Clearly specify expected input format and output structure
4. **Examples and Few-Shot Learning**: Provide concrete examples to guide behavior
5. **Safety and Boundaries**: Define what the agent should NOT do
6. **Give an "Out"**: Provide alternative paths when the agent cannot complete a task

**Instruction Template Structure**:

```markdown
# [Agent Name] Instructions

## Role and Expertise
[Define who the agent is and their specialized domain]

## Your Responsibilities
[List specific tasks and responsibilities]

## Input Format
[Describe the structure and format of inputs you will receive]

## Processing Guidelines
[Step-by-step guidelines for how to approach tasks]

## Output Format
[Specify the exact structure and format of responses]

## Constraints and Safety
[Define boundaries - what NOT to do]

## Examples
[Provide 2-3 concrete examples of input/output pairs]
```

**Example: Alert Triage Agent Instructions**:

```markdown
# Alert Triage Agent Instructions

## Role and Expertise
You are an expert SOC analyst specializing in alert triage, risk assessment, and incident prioritization. You have deep knowledge of security threats, attack patterns, and MITRE ATT&CK framework.

## Your Responsibilities
1. Analyze security alerts to determine risk level
2. Identify critical indicators of compromise (IOCs)
3. Correlate alerts to detect multi-stage attacks
4. Recommend immediate next steps for SOC analysts
5. Provide clear, concise explanations for all assessments

## Input Format
You will receive security alerts in JSON format:
```json
{
  "SystemAlertId": "uuid",
  "AlertName": "string",
  "Severity": "High|Medium|Low|Informational",
  "Description": "string",
  "TimeGenerated": "ISO 8601 timestamp",
  "Entities": [
    {"Type": "ip|user|host|file|url", "Properties": {...}}
  ],
  "ExtendedProperties": {
    "MitreTechniques": ["T1078", "T1083"],
    "SourceSystem": "Defender|Sentinel|..."
  }
}
```

## Processing Guidelines

### Step 1: Initial Assessment
- Examine alert severity, source, and description
- Identify involved entities (users, IPs, hosts, files)
- Check for MITRE ATT&CK technique mappings

### Step 2: Risk Scoring Factors
Assess risk level (Critical/High/Medium/Low) based on:

**Severity Indicators** (increases risk):
- Data exfiltration attempts
- Lateral movement activity
- Privilege escalation
- Credential theft
- Ransomware indicators
- Command and control (C2) communication

**Asset Criticality** (increases risk):
- Production systems
- Domain controllers
- Sensitive data repositories
- Executive accounts
- Internet-facing services

**User Context** (increases risk):
- Privileged accounts (admin, domain admin)
- Service accounts with broad access
- External/unusual login locations
- After-hours activity

**Historical Patterns** (adjusts risk):
- Known false positive patterns (decreases)
- Repeat offender hosts/users (increases)
- Similar past incidents (reference outcome)

### Step 3: Correlation Analysis
Identify related alerts that may indicate:
- Multi-stage attack progression
- Lateral movement across hosts
- Coordinated activity from same source
- Attack chain completion (reconnaissance → access → exfiltration)

### Step 4: Recommendation Generation
Provide actionable next steps:
- Immediate actions (e.g., "Isolate host", "Disable account")
- Investigation tasks (e.g., "Check for lateral movement", "Review login history")
- Escalation criteria (e.g., "Escalate if exfiltration confirmed")

## Output Format
Respond with structured JSON:
```json
{
  "riskLevel": "Critical|High|Medium|Low",
  "riskScore": 0-100,
  "explanation": "Clear 2-3 sentence explanation of risk assessment",
  "keyIndicators": [
    "Most important IOCs or patterns identified"
  ],
  "relatedAlerts": [
    {"alertId": "uuid", "relationship": "description"}
  ],
  "mitreTechniques": ["T1078", "T1083"],
  "attackStage": "Initial Access|Execution|Persistence|...",
  "nextSteps": [
    {"action": "description", "priority": "immediate|high|normal"}
  ],
  "confidence": "high|medium|low"
}
```

## Constraints and Safety
**DO NOT**:
- Make assumptions beyond available data
- Ignore low-severity alerts without assessment
- Recommend destructive actions without justification
- Provide risk scores without clear reasoning

**ALWAYS**:
- Explain your reasoning clearly
- Cite specific indicators from the alert
- Consider both technical and business impact
- If information is insufficient, state: "Unable to fully assess - require additional context: [specify what's needed]"

## Examples

### Example 1: High-Risk Brute Force Attack
**Input**:
```json
{
  "AlertName": "Multiple failed logins followed by success",
  "Severity": "Medium",
  "Description": "User account showed 25 failed login attempts from 5 different IPs, followed by successful login",
  "Entities": [
    {"Type": "user", "Properties": {"Name": "admin@contoso.com", "IsPrivileged": true}},
    {"Type": "ip", "Properties": {"Address": "203.0.113.42", "GeoLocation": "Russia"}}
  ],
  "ExtendedProperties": {
    "MitreTechniques": ["T1078"],
    "FailedAttempts": 25,
    "SuccessfulLogin": true
  }
}
```

**Output**:
```json
{
  "riskLevel": "High",
  "riskScore": 85,
  "explanation": "Successful brute force attack against privileged account (admin) from suspicious foreign IP after 25 failed attempts. High risk of account compromise.",
  "keyIndicators": [
    "25 failed login attempts",
    "Privileged admin account targeted",
    "Foreign IP (Russia) - unusual for organization",
    "Successful authentication after failed attempts"
  ],
  "relatedAlerts": [],
  "mitreTechniques": ["T1078"],
  "attackStage": "Initial Access",
  "nextSteps": [
    {"action": "Immediately disable account admin@contoso.com pending investigation", "priority": "immediate"},
    {"action": "Check for subsequent activity from this account (lateral movement, data access)", "priority": "immediate"},
    {"action": "Review all logins from IP 203.0.113.42 in last 7 days", "priority": "high"},
    {"action": "Implement MFA if not already enabled", "priority": "normal"}
  ],
  "confidence": "high"
}
```

### Example 2: Low-Risk False Positive
**Input**:
```json
{
  "AlertName": "Suspicious PowerShell execution",
  "Severity": "Low",
  "Description": "PowerShell script executed with encoded command",
  "Entities": [
    {"Type": "host", "Properties": {"Name": "WORKSTATION-42"}},
    {"Type": "file", "Properties": {"Name": "update-inventory.ps1"}}
  ],
  "ExtendedProperties": {
    "MitreTechniques": ["T1059.001"],
    "CommandLine": "powershell.exe -EncodedCommand [base64]"
  }
}
```

**Output**:
```json
{
  "riskLevel": "Low",
  "riskScore": 25,
  "explanation": "PowerShell execution detected, but appears to be legitimate inventory update script based on filename and historical pattern. Low risk, likely administrative task.",
  "keyIndicators": [
    "Encoded command usage (common in malware)",
    "Script name suggests inventory management",
    "No unusual network activity",
    "Workstation is IT management system"
  ],
  "relatedAlerts": [],
  "mitreTechniques": ["T1059.001"],
  "attackStage": "Execution",
  "nextSteps": [
    {"action": "Verify script source and purpose with IT team", "priority": "normal"},
    {"action": "Add to allowlist if confirmed legitimate", "priority": "normal"}
  ],
  "confidence": "medium"
}
```

### Example 3: Insufficient Information
**Input**:
```json
{
  "AlertName": "Anomalous user behavior",
  "Severity": "Medium",
  "Description": "User behavior deviated from baseline",
  "Entities": [
    {"Type": "user", "Properties": {"Name": "jsmith@contoso.com"}}
  ]
}
```

**Output**:
```json
{
  "riskLevel": "Medium",
  "riskScore": 50,
  "explanation": "Unable to fully assess - alert lacks specific indicators of compromise. Require additional context to determine if behavior is malicious or benign.",
  "keyIndicators": [
    "Baseline deviation detected (specifics not provided)"
  ],
  "relatedAlerts": [],
  "mitreTechniques": [],
  "attackStage": "Unknown",
  "nextSteps": [
    {"action": "Request detailed baseline deviation metrics (What specific behaviors changed?)", "priority": "immediate"},
    {"action": "Review recent user activity logs for jsmith@contoso.com", "priority": "high"},
    {"action": "Check for recent role changes or access grants", "priority": "normal"}
  ],
  "confidence": "low"
}
```
```

**Additional Agent Instruction Guidelines**:

1. **Alert Triage Instructions**: Focus on risk assessment logic, correlation patterns, and prioritization criteria
2. **Threat Hunting Instructions**: Emphasize KQL query formulation, anomaly detection reasoning, and hypothesis generation
3. **Incident Response Instructions**: Detail containment strategy selection, playbook adherence, and impact assessment
4. **Threat Intelligence Instructions**: Specify briefing structure, IOC enrichment logic, and MITRE mapping
5. **Manager/Coordinator Instructions**: Define task decomposition, agent selection criteria, and progress tracking

**Best Practices Summary**:

| Practice | Description | Example |
|----------|-------------|---------|
| **Be Specific** | Avoid vague language | "Assess risk based on: asset criticality, user privileges, attack stage" vs. "Look at the alert" |
| **Use Examples** | Provide 2-3 concrete cases | Include input/output pairs with varied scenarios |
| **Keep it Concise** | Long instructions cause latency | Aim for < 2000 characters for custom sections |
| **Give an Out** | Provide alternative paths | "If data is insufficient, respond with 'Unable to assess - require: [X]'" |
| **Safety Guardrails** | Define boundaries | "DO NOT recommend account deletion without explicit approval" |
| **Structured Output** | Enforce JSON schemas | Provide exact format with all required fields |

**References**:
- [Microsoft Agent Instructions Best Practices](https://learn.microsoft.com/en-us/microsoft-copilot-studio/nlu-prompt-node#best-practices-for-prompt-instructions)
- [Prompt Engineering for Security Agents](https://learn.microsoft.com/en-us/security/benchmark/azure/mcsb-v2-artificial-intelligence-security#ai-3-adopt-safety-meta-prompts)
- [Declarative Agent Instructions Guide](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-instructions)

---

## 12. Mock Data Strategy - Streaming Simulation

### Decision: Configurable Streaming with Checkpoint-Based Replay

**Rationale**: To demonstrate real-time SOC operations, mock data must be streamed at realistic intervals (not dumped all at once). Checkpoint-based replay enables reproducible demos, allowing operators to pause, resume, and replay scenarios from specific points.

**Implementation Strategy**:

1. **Async Generator-Based Streaming**:

```python
import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

class MockDataStreamer:
    """Streams mock security alerts with configurable intervals"""
    
    def __init__(
        self,
        dataset_path: str,
        interval_seconds: float = 15.0,
        checkpoint_file: str = "/tmp/mock_stream_checkpoint.json"
    ):
        self.dataset_path = Path(dataset_path)
        self.interval = interval_seconds
        self.checkpoint_file = Path(checkpoint_file)
        self.alerts = self._load_dataset()
    
    def _load_dataset(self) -> list[Dict[str, Any]]:
        """Load GUIDE/Attack dataset from JSON/CSV"""
        with open(self.dataset_path, 'r') as f:
            if self.dataset_path.suffix == '.json':
                data = json.load(f)
            else:
                import pandas as pd
                data = pd.read_csv(self.dataset_path).to_dict('records')
        return data
    
    def _load_checkpoint(self) -> int:
        """Load checkpoint index for replay"""
        if not self.checkpoint_file.exists():
            return 0
        with open(self.checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        return checkpoint.get('last_index', 0)
    
    def _save_checkpoint(self, index: int):
        """Save checkpoint for replay capability"""
        checkpoint = {
            'last_index': index,
            'timestamp': datetime.utcnow().isoformat(),
            'dataset': str(self.dataset_path)
        }
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f)
    
    async def stream_alerts(
        self,
        batch_size: int = 5,
        start_index: int = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream alerts at configured interval with batching
        
        Args:
            batch_size: Number of alerts per batch (default: 5)
            start_index: Override checkpoint start index
        
        Yields:
            Alert data dictionaries
        """
        # Resume from checkpoint or specified index
        current_index = start_index if start_index is not None else self._load_checkpoint()
        
        print(f"📡 Starting stream from index {current_index} (interval: {self.interval}s)")
        
        while current_index < len(self.alerts):
            # Get next batch
            batch_end = min(current_index + batch_size, len(self.alerts))
            batch = self.alerts[current_index:batch_end]
            
            # Stream each alert in batch
            for alert in batch:
                # Transform to Sentinel format
                sentinel_alert = self._transform_to_sentinel(alert)
                yield sentinel_alert
            
            # Update checkpoint
            current_index = batch_end
            self._save_checkpoint(current_index)
            
            # Wait before next batch
            if current_index < len(self.alerts):
                print(f"⏸️  Streamed {current_index}/{len(self.alerts)} alerts, waiting {self.interval}s...")
                await asyncio.sleep(self.interval)
        
        print(f"✅ Stream complete: {len(self.alerts)} alerts processed")
    
    def _transform_to_sentinel(self, guide_record: Dict) -> Dict[str, Any]:
        """Transform GUIDE/Attack data to Sentinel SecurityAlert schema"""
        return {
            "SystemAlertId": guide_record.get("AlertId", f"alert-{hash(str(guide_record))}"),
            "AlertName": guide_record.get("Category", "Unknown Alert"),
            "Severity": self._map_severity(guide_record.get("IncidentGrade")),
            "Description": guide_record.get("AlertTitle", "No description"),
            "TimeGenerated": guide_record.get("Timestamp", datetime.utcnow().isoformat()),
            "Entities": self._extract_entities(guide_record),
            "ExtendedProperties": {
                "MitreTechniques": guide_record.get("MitreTechniques", []),
                "EntityCount": guide_record.get("EntityCount", 0),
                "OrgId": guide_record.get("OrgId", "demo-org"),
                "SourceDataset": "GUIDE"
            },
            "ProviderName": "Microsoft Sentinel (Mock)",
        }
    
    def _map_severity(self, incident_grade: str) -> str:
        """Map GUIDE IncidentGrade to Sentinel severity"""
        mapping = {
            "TruePositive": "High",
            "BenignPositive": "Low",
            "FalsePositive": "Informational"
        }
        return mapping.get(incident_grade, "Medium")
    
    def _extract_entities(self, record: Dict) -> list[Dict]:
        """Extract entities from GUIDE record"""
        entities = []
        
        # Extract IPs
        if "IpAddress" in record:
            entities.append({
                "Type": "ip",
                "Properties": {"Address": record["IpAddress"]}
            })
        
        # Extract user accounts
        if "AccountName" in record:
            entities.append({
                "Type": "account",
                "Properties": {"Name": record["AccountName"]}
            })
        
        # Extract hosts
        if "DeviceName" in record:
            entities.append({
                "Type": "host",
                "Properties": {"HostName": record["DeviceName"]}
            })
        
        return entities
    
    def reset_checkpoint(self):
        """Reset checkpoint to start from beginning"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        print("✅ Checkpoint reset")
```

2. **Integration with Event Hubs (Mock)**:

```python
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

async def stream_to_event_hub():
    """Stream mock alerts to Azure Event Hubs"""
    
    # Create streamer
    streamer = MockDataStreamer(
        dataset_path="mock-data/guide_alerts.json",
        interval_seconds=15,
        checkpoint_file="/tmp/soc_demo_checkpoint.json"
    )
    
    # Connect to Event Hub
    producer = EventHubProducerClient.from_connection_string(
        conn_str=os.environ["EVENTHUB_CONNECTION_STRING"],
        eventhub_name="security-alerts"
    )
    
    async with producer:
        async for alert in streamer.stream_alerts(batch_size=5):
            # Send to Event Hub
            event_data = EventData(json.dumps(alert))
            await producer.send_event(event_data)
            
            print(f"📤 Sent alert: {alert['AlertName']} (ID: {alert['SystemAlertId']})")

# Run streaming
asyncio.run(stream_to_event_hub())
```

3. **Scenario-Based Test Data**:

```python
class ScenarioManager:
    """Manage curated security scenarios for demos"""
    
    SCENARIOS = {
        "brute_force": {
            "name": "Brute Force Attack",
            "description": "20 failed logins → successful login → lateral movement",
            "alerts": [
                "failed_login_attempt_1.json",
                "failed_login_attempt_20.json",
                "successful_login_suspicious_ip.json",
                "lateral_movement_rdp.json"
            ],
            "interval": 10  # seconds between alerts
        },
        "phishing_campaign": {
            "name": "Phishing Campaign",
            "description": "Suspicious email → credential theft → data exfiltration",
            "alerts": [
                "suspicious_email_received.json",
                "credential_harvesting_detected.json",
                "large_data_upload.json"
            ],
            "interval": 20
        },
        "ransomware": {
            "name": "Ransomware Infection",
            "description": "Malware execution → file encryption → C2 communication",
            "alerts": [
                "malware_execution.json",
                "file_encryption_activity.json",
                "c2_communication_detected.json",
                "ransom_note_created.json"
            ],
            "interval": 15
        }
    }
    
    def __init__(self, scenarios_dir: str = "mock-data/scenarios"):
        self.scenarios_dir = Path(scenarios_dir)
    
    async def run_scenario(self, scenario_name: str) -> AsyncGenerator[Dict, None]:
        """Run a specific demo scenario"""
        if scenario_name not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.SCENARIOS[scenario_name]
        print(f"🎬 Running scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        for alert_file in scenario['alerts']:
            # Load alert data
            alert_path = self.scenarios_dir / scenario_name / alert_file
            with open(alert_path, 'r') as f:
                alert = json.load(f)
            
            yield alert
            
            # Wait between alerts
            await asyncio.sleep(scenario['interval'])
        
        print(f"✅ Scenario complete: {scenario['name']}")

# Usage
async def demo_brute_force():
    """Demo brute force attack scenario"""
    manager = ScenarioManager()
    
    async for alert in manager.run_scenario("brute_force"):
        print(f"📧 New Alert: {alert['AlertName']}")
        # Process alert through workflow...
```

4. **Replay and Control Interface**:

```python
class StreamController:
    """Control interface for demo streaming"""
    
    def __init__(self, streamer: MockDataStreamer):
        self.streamer = streamer
        self.paused = False
        self.current_index = 0
    
    async def start(self):
        """Start streaming"""
        async for alert in self.streamer.stream_alerts():
            if not self.paused:
                yield alert
            else:
                # Wait while paused
                await asyncio.sleep(1)
    
    def pause(self):
        """Pause streaming"""
        self.paused = True
        print("⏸️  Stream paused")
    
    def resume(self):
        """Resume streaming"""
        self.paused = False
        print("▶️  Stream resumed")
    
    def reset(self):
        """Reset to beginning"""
        self.streamer.reset_checkpoint()
        self.current_index = 0
        print("⏮️  Stream reset")
    
    def jump_to(self, index: int):
        """Jump to specific index"""
        self.streamer._save_checkpoint(index)
        self.current_index = index
        print(f"⏭️  Jumped to index {index}")
```

**Configuration Options**:

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `interval_seconds` | Time between alert batches | 15 | 5-300 |
| `batch_size` | Alerts per batch | 5 | 1-100 |
| `checkpoint_file` | Path to checkpoint storage | `/tmp/checkpoint.json` | Any writable path |

**Alternatives Considered**:
- **Static dataset dump**: No demonstration of real-time processing. Rejected.
- **Fully synthetic generation**: Lower fidelity than GUIDE/Attack datasets. Rejected.
- **External streaming platform**: Unnecessary complexity for MVP. Deferred to production.

**References**:
- [Python Streaming Data Generators](https://github.com/satvik-ap/DATA-STREAMING-SIMULATION-USING-GENERATORS)
- [Azure Event Hubs Python SDK](https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-python-get-started-send)

---

## 13. Orchestration Plugin Points - Strategy Flexibility

### Decision: Clear Extension Point for Orchestration Strategy Changes

**Rationale**: While magentic orchestration is ideal for the MVP's dynamic, manager-driven approach, production deployments may require different orchestration strategies (sequential, concurrent, or custom). The architecture must make it obvious where and how to change orchestration without rewriting the entire system.

**Plugin Point Location**:

```
src/orchestration/orchestrator.py
└── create_workflow() function  ← PRIMARY PLUGIN POINT
```

**Current Implementation (Magentic)**:

```python
# src/orchestration/orchestrator.py

from agent_framework import MagenticBuilder, Workflow
from azure.ai.projects import AIProjectClient
from typing import Dict, Any

def create_workflow(
    agents: Dict[str, Any],
    orchestration_type: str = "magentic",
    **config
) -> Workflow:
    """
    Create orchestration workflow for SOC agents
    
    ⚙️  PLUGIN POINT: Change orchestration strategy here
    
    Args:
        agents: Dictionary of deployed agents (triage, hunting, response, intel, manager)
        orchestration_type: Type of orchestration ("magentic", "sequential", "concurrent", "custom")
        **config: Orchestration-specific configuration
    
    Returns:
        Workflow instance
    """
    
    if orchestration_type == "magentic":
        return _create_magentic_workflow(agents, **config)
    elif orchestration_type == "sequential":
        return _create_sequential_workflow(agents, **config)
    elif orchestration_type == "concurrent":
        return _create_concurrent_workflow(agents, **config)
    elif orchestration_type == "custom":
        return _create_custom_workflow(agents, **config)
    else:
        raise ValueError(f"Unknown orchestration type: {orchestration_type}")

# ------------------------------------------------------------
# CURRENT MVP IMPLEMENTATION: Magentic Orchestration
# ------------------------------------------------------------

def _create_magentic_workflow(agents: Dict, **config) -> Workflow:
    """
    Magentic orchestration with dynamic agent selection
    
    Characteristics:
    - Manager agent dynamically selects next agent
    - Iterative refinement through multiple rounds
    - Human-in-the-loop support (plan review, tool approval, stall intervention)
    - Best for: Complex, open-ended tasks with unclear solution paths
    
    Use Cases:
    - Security incident investigation (unknown attack patterns)
    - Threat hunting (hypothesis-driven exploration)
    - Complex alert correlation
    """
    
    return (
        MagenticBuilder()
        .participants(
            triage=agents['triage'],
            hunting=agents['hunting'],
            response=agents['response'],
            intel=agents['intel']
        )
        .with_standard_manager(
            chat_client=agents['manager'],
            max_round_count=config.get('max_rounds', 10),
            max_stall_count=config.get('max_stalls', 3),
            max_reset_count=config.get('max_resets', 2)
        )
        .with_plan_review(enable=config.get('plan_review', False))
        .with_human_input_on_stall()
        .build()
    )

# ------------------------------------------------------------
# ALTERNATIVE 1: Sequential Orchestration
# ------------------------------------------------------------

def _create_sequential_workflow(agents: Dict, **config) -> Workflow:
    """
    Sequential orchestration with fixed agent order
    
    Characteristics:
    - Predefined sequence: triage → hunting → response → intel
    - No dynamic routing
    - Predictable execution path
    - Best for: Standardized workflows with known steps
    
    Use Cases:
    - Standard alert triage pipeline
    - Routine threat intelligence gathering
    - Compliance-driven investigations (must follow specific steps)
    """
    from agent_framework import SequentialOrchestration
    
    return SequentialOrchestration(
        agents['triage'],
        agents['hunting'],
        agents['response'],
        agents['intel']
    )

# ------------------------------------------------------------
# ALTERNATIVE 2: Concurrent Orchestration
# ------------------------------------------------------------

def _create_concurrent_workflow(agents: Dict, **config) -> Workflow:
    """
    Concurrent orchestration with parallel agent execution
    
    Characteristics:
    - All agents execute simultaneously
    - No coordination between agents
    - Fastest execution time
    - Best for: Independent tasks that don't require coordination
    
    Use Cases:
    - Bulk alert triage (process multiple alerts in parallel)
    - Parallel threat hunting across multiple data sources
    - Independent intelligence enrichment tasks
    """
    from agent_framework import ConcurrentOrchestration
    
    # All agents run in parallel, results aggregated at end
    return ConcurrentOrchestration([
        agents['triage'],
        agents['hunting'],
        agents['response'],
        agents['intel']
    ])

# ------------------------------------------------------------
# ALTERNATIVE 3: Custom Orchestrator
# ------------------------------------------------------------

def _create_custom_workflow(agents: Dict, **config) -> Workflow:
    """
    Custom orchestration with business-specific logic
    
    Characteristics:
    - Imperative control flow in Python
    - Full flexibility for complex routing
    - Can enforce mandatory triage-first behavior
    - Best for: Organization-specific workflows with strict requirements
    
    Use Cases:
    - Regulated environments requiring specific agent sequences
    - Complex conditional logic (if high risk, skip hunting and go directly to response)
    - Integration with external approval systems
    """
    from agent_framework import CustomOrchestration
    
    class SOCOrchestrator(CustomOrchestration):
        async def run(self, task: str):
            # ALWAYS start with triage (guaranteed)
            triage_result = await agents['triage'].run(task)
            
            # Route based on triage risk level
            risk_level = triage_result.get('riskLevel')
            
            if risk_level in ['Critical', 'High']:
                # High risk: immediate response, skip hunting
                response_result = await agents['response'].run(triage_result)
                return response_result
            elif risk_level == 'Medium':
                # Medium risk: investigate with hunting, then respond
                hunting_result = await agents['hunting'].run(triage_result)
                response_result = await agents['response'].run(hunting_result)
                return response_result
            else:
                # Low risk: enrich with intel only
                intel_result = await agents['intel'].run(triage_result)
                return intel_result
    
    return SOCOrchestrator()

# ------------------------------------------------------------
# FUTURE: Azure Durable Functions (Production Scale)
# ------------------------------------------------------------

def _create_durable_functions_workflow(agents: Dict, **config):
    """
    Azure Durable Functions for production-scale orchestration
    
    ⚠️  NOT IMPLEMENTED IN MVP
    
    Characteristics:
    - Stateful, serverless orchestration
    - Automatic retry and error handling
    - Long-running workflows (days/weeks)
    - Best for: Production deployments requiring scale and reliability
    
    Migration Path:
    1. Keep agent definitions unchanged (reuse deployed Foundry agents)
    2. Replace MagenticBuilder with Durable Functions orchestrator client
    3. Implement orchestration logic as Durable Function
    4. Deploy to Azure Functions Premium or Container Apps
    
    Code structure:
    ```python
    import azure.functions as func
    import azure.durable_functions as df
    
    @df.activity_function
    async def triage_activity(context):
        # Call deployed triage agent
        result = await call_foundry_agent("AlertTriageAgent", context)
        return result
    
    @df.orchestrator_function
    def soc_orchestrator(context):
        # Orchestration logic
        triage_result = yield context.call_activity("triage_activity", input_data)
        
        if triage_result['riskLevel'] == 'High':
            response_result = yield context.call_activity("response_activity", triage_result)
            return response_result
        # ... more logic
    ```
    """
    raise NotImplementedError("Durable Functions orchestration not implemented in MVP")
```

**How to Change Orchestration Strategy**:

1. **Configuration-based** (Recommended for MVP):
```python
# config.yaml
orchestration:
  type: "magentic"  # Change to "sequential", "concurrent", "custom"
  max_rounds: 10
  plan_review: false

# Load and apply
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)

workflow = create_workflow(
    agents=deployed_agents,
    orchestration_type=config['orchestration']['type'],
    **config['orchestration']
)
```

2. **Environment variable**:
```bash
export SOC_ORCHESTRATION_TYPE=sequential
```

3. **Runtime override**:
```python
# For specific scenarios
workflow = create_workflow(agents, orchestration_type="custom")
```

**Migration Checklist** (Magentic → Alternative):

- [ ] Identify orchestration requirements (predictable vs. dynamic, fast vs. thorough)
- [ ] Update `config.yaml` with new orchestration type
- [ ] Test workflow with sample alerts
- [ ] Verify agent interactions match expectations
- [ ] Update documentation (quickstart.md) with new behavior
- [ ] No changes needed to agent instructions or deployment scripts ✅

**Comparison Matrix**:

| Strategy | Execution Order | Coordination | Speed | Use Case |
|----------|----------------|--------------|-------|----------|
| **Magentic** | Dynamic (manager decides) | High (manager plans) | Slower | Complex investigations, unknown paths |
| **Sequential** | Fixed (predefined) | None (linear) | Medium | Standard workflows, compliance |
| **Concurrent** | Parallel (all at once) | None (independent) | Fastest | Bulk processing, independent tasks |
| **Custom** | Imperative (Python code) | Full (programmatic) | Medium | Organization-specific logic |
| **Durable Functions** | Stateful (orchestrator) | High (built-in retry) | Scalable | Production, long-running, high-volume |

**References**:
- [Agent Framework Orchestration Patterns](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/)
- [Azure Durable Functions](https://learn.microsoft.com/en-us/azure/azure-functions/durable/)

---

## 14. Azure SDK Layer Clarification: Phase A vs Phase B

### Two-Phase Architecture Explained

**Terminology Confusion**: The terms "Microsoft Foundry" and "Microsoft Agent Framework" are sometimes used interchangeably, but they serve distinct purposes in our MVP architecture.

#### Phase A: Infrastructure Deployment (azure-ai-projects SDK)

**Purpose**: Deploy persistent, cloud-hosted v2 agents to Microsoft Foundry

**SDK**: `azure-ai-projects` (version 2.0.0b2+)

**What it does**:
- Creates and configures cloud-hosted agents in Microsoft Foundry service
- Agents persist in the cloud and can be referenced by name/ID
- Provides `AIProjectClient.agents.create_version()` for agent deployment
- Enables agent discovery via `get_agent()`, `list_agents()`, `list_versions()`
- Agents are configured with instructions (system prompts), model references, and tools

**Usage**:
```python
from azure.ai.projects import AIProjectClient, PromptAgentDefinition
from azure.identity import DefaultAzureCredential

# Deploy agent to Microsoft Foundry (one-time setup)
project_client = AIProjectClient.from_connection_string(
    connection_string=os.environ["PROJECT_CONNECTION_STRING"],
    credential=DefaultAzureCredential()
)

agent = project_client.agents.create_version(
    agent_name="AlertTriageAgent",
    definition=PromptAgentDefinition(
        model="gpt-4.1-mini",
        instructions="You are an expert SOC analyst..."
    )
)
```

**Key Point**: This is about **agent creation and configuration**, not orchestration.

#### Phase B: Runtime Orchestration (agent-framework)

**Purpose**: Orchestrate deployed agents at runtime using coordination patterns

**Package**: `agent-framework` (Microsoft Agent Framework)

**What it does**:
- Provides orchestration patterns (magentic, sequential, concurrent, custom)
- Coordinates agent-to-agent communication at runtime
- Requires **wrapper** around Foundry agents to participate in orchestration
- Implements `MagenticBuilder`, `ChatAgent`, `Workflow` abstractions
- Manages conversation flow, state passing, and human-in-the-loop

**Usage**:
```python
from agent_framework import MagenticBuilder
from azure.ai.projects import AIProjectClient

# Discover deployed agents (Phase A)
project_client = AIProjectClient.from_connection_string(...)
triage_agent = project_client.agents.get_agent(agent_name="AlertTriageAgent")

# Wrap in Agent Framework for orchestration (Phase B)
workflow = (
    MagenticBuilder()
    .participants(triage=triage_agent)  # Wrapper applied internally
    .with_standard_manager(...)
    .build()
)

# Run orchestrated workflow
async for event in workflow.run(task):
    # Process events
    pass
```

**Key Point**: This is about **agent orchestration and coordination**, not deployment.

#### The Wrapper Requirement

**Why a wrapper is needed**:
- `azure-ai-projects` agents are cloud-hosted Foundry agents (accessed via REST API)
- `agent-framework` expects agents that implement its `ChatAgent` interface
- The wrapper translates between these two interfaces

**Where the wrapper happens**:
- **Option 1 (Implicit)**: `MagenticBuilder.participants()` may handle wrapping internally
- **Option 2 (Explicit)**: Create wrapper class that implements `ChatAgent` interface:

```python
from agent_framework import ChatAgent, ChatMessage, Role

class FoundryAgentWrapper(ChatAgent):
    """Wraps a Foundry agent for Agent Framework orchestration"""
    
    def __init__(self, foundry_agent, project_client):
        self.foundry_agent = foundry_agent
        self.project_client = project_client
        self.openai_client = project_client.get_openai_client()
    
    async def run(self, messages: list[ChatMessage]) -> ChatMessage:
        # Convert Agent Framework messages to Foundry conversation format
        conversation = self.openai_client.conversations.create(
            items=[{"type": "message", "role": msg.role, "content": msg.content} 
                   for msg in messages]
        )
        
        # Call Foundry agent
        response = self.openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent": {"name": self.foundry_agent.name, "type": "agent_reference"}},
            input=""
        )
        
        # Convert response to Agent Framework message
        return ChatMessage(role=Role.ASSISTANT, content=response.output_text)

# Use wrapped agent in orchestration
wrapped_agent = FoundryAgentWrapper(triage_agent, project_client)
workflow = MagenticBuilder().participants(triage=wrapped_agent).build()
```

#### Summary: Phase A vs Phase B

| Aspect | Phase A (Deployment) | Phase B (Orchestration) |
|--------|---------------------|------------------------|
| **SDK/Package** | `azure-ai-projects` | `agent-framework` |
| **Purpose** | Deploy agents to cloud | Orchestrate agents at runtime |
| **Key Classes** | `AIProjectClient`, `PromptAgentDefinition` | `MagenticBuilder`, `ChatAgent`, `Workflow` |
| **Output** | Persistent cloud-hosted agents | Runtime workflows and coordination |
| **Frequency** | One-time (or per deployment) | Every execution |
| **MVP Note** | Deploy 5 agents (triage, hunting, response, intel, manager) | Use magentic orchestration for demos |

#### Research Task Created

A research task will be added to tasks.md to evaluate orchestration approaches beyond magentic for production scenarios, including:
- Sequential orchestration (predictable workflows)
- Concurrent orchestration (parallel execution)
- Custom orchestrator (organization-specific logic)
- Azure Durable Functions (production scale)

**References**:
- [Azure AI Projects SDK Documentation](https://azuresdkdocs.z19.web.core.windows.net/python/azure-ai-projects/2.0.0b2/)
- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/)
- [Agent Framework Architecture Overview](https://learn.microsoft.com/en-us/agent-framework/concepts/)

---

## Next Steps (Phase 1: Design)

With all technology decisions finalized (including newly researched areas), Phase 1 will create:

1. **data-model.md**: Entity definitions (Alert, Incident, Finding, IOC, Agent State)
2. **contracts/**: API contracts and JSON schemas for agent interfaces, plus agent instruction templates
3. **quickstart.md**: Setup instructions and demo walkthrough (rewritten for two-phase approach)
4. **Agent context updates**: Technology additions to Copilot agent file

---

**Research Status**: ✅ Complete (Updated)  
**All NEEDS CLARIFICATION items resolved**: ✅ Yes  
**New research sections added**: ✅ Yes (5 new sections: Azure AI Projects SDK, Magentic Orchestration, Agent Instructions Best Practices, Mock Data Streaming, Orchestration Plugin Points)  
**Ready for Phase 1 (Design)**: ✅ Yes
