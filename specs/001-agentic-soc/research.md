# Phase 0: Research & Technology Decisions

**Date**: 2025-11-21  
**Phase**: 0 (Research)  
**Status**: Complete

This document consolidates technology research findings and architectural decisions for the Agentic SOC MVP implementation. All "NEEDS CLARIFICATION" items from the Technical Context section of the implementation plan have been resolved through research and analysis.

## Research Methodology

Research conducted using:
- Microsoft Learn documentation (official Azure and Security documentation)
- Azure AI Foundry and Microsoft Agent Framework documentation
- Microsoft Security Copilot developer resources
- KQL and Microsoft Sentinel documentation
- Security best practices and architectural patterns

---

## 1. Microsoft Foundry (AI Foundry) Integration

### Decision: Use Azure AI Foundry with Python SDK

**Rationale**: Azure AI Foundry provides the most comprehensive, enterprise-ready platform for building AI agents with built-in support for:
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
- [Azure AI Foundry Agents Python Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent)
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
- **Integration**: Native integration with Azure AI Foundry Agent Framework
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
| **AI Platform** | Azure AI Foundry with Python SDK | Enterprise-ready, persistent agents, managed infrastructure |
| **Orchestration** | Microsoft Agent Framework + Event Hubs | Standardized A2A communication, event-driven architecture |
| **Security Copilot** | Plugin points defined, not implemented in MVP | Production integration path documented, not required for demo |
| **Query Language** | KQL with LLM-powered generation | Industry standard for Sentinel/Defender, powerful analytics |
| **Mock Data** | GUIDE + Attack datasets, configurable streaming | Real-world data quality, reproducible demos, ground truth labels |
| **Threat Intelligence** | Multi-tier (MITRE, Attack dataset, historical) | Comprehensive coverage, tactical + operational intelligence |
| **Knowledge Base** | Azure AI Search with Agentic Retrieval | RAG pattern for agent context, 14K attack scenarios + 10K historical incidents |
| **Observability** | Azure Monitor + Application Insights + OpenTelemetry | Unified platform, distributed tracing, production-ready |

---

## Next Steps (Phase 1: Design)

With all technology decisions finalized, Phase 1 will create:

1. **data-model.md**: Entity definitions (Alert, Incident, Finding, IOC, Agent State)
2. **contracts/**: API contracts and JSON schemas for agent interfaces
3. **quickstart.md**: Setup instructions and demo walkthrough
4. **Agent context updates**: Technology additions to Copilot agent file

---

**Research Status**: ✅ Complete  
**All NEEDS CLARIFICATION items resolved**: ✅ Yes  
**Ready for Phase 1 (Design)**: ✅ Yes
