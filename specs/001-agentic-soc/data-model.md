# Phase 1: Data Model & Entity Definitions

**Date**: 2025-11-21  
**Phase**: 1 (Design - Data Model)  
**Status**: Complete

This document defines the core entities, data models, and schemas for the Agentic SOC MVP. These models align with Microsoft Sentinel/Graph Security API schemas where applicable and extend them for agent-specific requirements.

---

## 1. Core Entity: SecurityAlert

**Purpose**: Represents a security alert from any source (Sentinel, Defender, mock data stream)

**Schema** (based on Microsoft Sentinel Alert schema):

```json
{
  "SystemAlertId": "string (UUID)",
  "AlertName": "string",
  "AlertType": "string (unique identifier)",
  "Severity": "enum: High|Medium|Low|Informational",
  "Description": "string",
  "TimeGenerated": "datetime (ISO 8601)",
  "StartTime": "datetime (ISO 8601)",
  "EndTime": "datetime (ISO 8601)",
  "Entities": [
    {
      "Type": "enum: Account|Host|IP|File|Process|URL|MailMessage|CloudApplication",
      "Properties": "object (type-specific fields)"
    }
  ],
  "ExtendedProperties": {
    "MitreTechniques": ["string (ATT&CK technique IDs)"],
    "DataSources": ["string"],
    "ConfidenceScore": "number (0-100)",
    "ThreatCategory": "string"
  },
  "ProviderName": "string (e.g., 'Microsoft Sentinel', 'Microsoft Defender')",
  "ProductName": "string",
  "RemediationSteps": ["string"],
  "ResourceId": "string (affected resource ARM ID)"
}
```

**Pydantic Model** (Python):

```python
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class SeverityLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"

class EntityType(str, Enum):
    ACCOUNT = "Account"
    HOST = "Host"
    IP = "IP"
    FILE = "File"
    PROCESS = "Process"
    URL = "URL"
    MAIL_MESSAGE = "MailMessage"
    CLOUD_APPLICATION = "CloudApplication"

class AlertEntity(BaseModel):
    Type: EntityType
    Properties: Dict[str, Any]

class SecurityAlert(BaseModel):
    SystemAlertId: UUID4
    AlertName: str
    AlertType: str
    Severity: SeverityLevel
    Description: str
    TimeGenerated: datetime
    StartTime: datetime
    EndTime: datetime
    Entities: List[AlertEntity]
    ExtendedProperties: Dict[str, Any] = Field(default_factory=dict)
    ProviderName: str
    ProductName: str
    RemediationSteps: List[str] = Field(default_factory=list)
    ResourceId: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "SystemAlertId": "550e8400-e29b-41d4-a716-446655440000",
                "AlertName": "Suspicious PowerShell Execution",
                "AlertType": "SuspiciousPowerShell",
                "Severity": "High",
                "Description": "PowerShell executed with suspicious parameters",
                "TimeGenerated": "2025-11-21T10:30:00Z",
                "StartTime": "2025-11-21T10:29:45Z",
                "EndTime": "2025-11-21T10:30:15Z",
                "Entities": [
                    {"Type": "Host", "Properties": {"HostName": "WS-001"}},
                    {"Type": "Process", "Properties": {"ProcessName": "powershell.exe"}}
                ],
                "ProviderName": "Microsoft Defender for Endpoint",
                "ProductName": "Defender ATP"
            }
        }
```

---

## 2. Core Entity: SecurityIncident

**Purpose**: Represents a security incident (correlated alerts, investigation state)

**Schema** (based on Microsoft Sentinel Incident schema):

```json
{
  "IncidentId": "string (UUID)",
  "IncidentNumber": "integer (auto-increment)",
  "Title": "string",
  "Description": "string",
  "Severity": "enum: High|Medium|Low|Informational",
  "Status": "enum: New|Investigating|Contained|Resolved|Closed",
  "Classification": "enum: TruePositive|BenignPositive|FalsePositive|Undetermined",
  "ClassificationReason": "string",
  "ClassificationComment": "string",
  "Owner": {
    "AssignedTo": "string (user principal name)",
    "AssignedAt": "datetime (ISO 8601)"
  },
  "CreatedTime": "datetime (ISO 8601)",
  "FirstActivityTime": "datetime (ISO 8601)",
  "LastActivityTime": "datetime (ISO 8601)",
  "LastModifiedTime": "datetime (ISO 8601)",
  "ClosedTime": "datetime (ISO 8601, nullable)",
  "AlertIds": ["string (SystemAlertId references)"],
  "Entities": [
    {
      "Type": "enum: Account|Host|IP|File|Process|URL|MailMessage|CloudApplication",
      "Properties": "object"
    }
  ],
  "Labels": ["string (tags)"],
  "RelatedAnalyticRuleIds": ["string"],
  "MitreTechniques": ["string (ATT&CK IDs)"],
  "Comments": [
    {
      "CommentId": "string (UUID)",
      "Author": "string (user or agent name)",
      "Message": "string",
      "CreatedTime": "datetime (ISO 8601)"
    }
  ],
  "AdditionalData": {
    "AlertCount": "integer",
    "BookmarkCount": "integer",
    "AlertProductNames": ["string"],
    "Tactics": ["string (MITRE tactics)"]
  }
}
```

**Incident Lifecycle States**:

```
New → Investigating → Contained → Resolved → Closed
  ↓         ↓            ↓           ↓
  └─────────┴────────────┴───────────→ (can escalate back)
```

---

## 3. Agent-Specific Entity: TriageResult

**Purpose**: Output from Alert Triage Agent

```json
{
  "AlertId": "string (SystemAlertId reference)",
  "TriageId": "string (UUID)",
  "Timestamp": "datetime (ISO 8601)",
  "RiskScore": "integer (0-100)",
  "Priority": "enum: Critical|High|Medium|Low",
  "TriageDecision": "enum: EscalateToIncident|CorrelateWithExisting|MarkAsFalsePositive|RequireHumanReview",
  "Explanation": "string (natural language rationale)",
  "CorrelatedAlertIds": ["string"],
  "RecommendedIncidentId": "string (UUID, nullable)",
  "EnrichmentData": {
    "AssetCriticality": "enum: Critical|High|Medium|Low",
    "UserRiskLevel": "enum: High|Medium|Low",
    "ThreatIntelligenceMatches": [
      {
        "IOC": "string",
        "IOCType": "enum: IP|Domain|FileHash|URL",
        "Reputation": "enum: Malicious|Suspicious|Unknown|Benign",
        "Source": "string"
      }
    ]
  },
  "ProcessingTimeMs": "integer",
  "AgentVersion": "string"
}
```

**Pydantic Model**:

```python
class TriagePriority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class TriageDecision(str, Enum):
    ESCALATE_TO_INCIDENT = "EscalateToIncident"
    CORRELATE_WITH_EXISTING = "CorrelateWithExisting"
    MARK_AS_FALSE_POSITIVE = "MarkAsFalsePositive"
    REQUIRE_HUMAN_REVIEW = "RequireHumanReview"

class ThreatIntelMatch(BaseModel):
    IOC: str
    IOCType: str
    Reputation: str
    Source: str

class TriageResult(BaseModel):
    AlertId: UUID4
    TriageId: UUID4
    Timestamp: datetime
    RiskScore: int = Field(ge=0, le=100)
    Priority: TriagePriority
    TriageDecision: TriageDecision
    Explanation: str
    CorrelatedAlertIds: List[UUID4] = Field(default_factory=list)
    RecommendedIncidentId: Optional[UUID4] = None
    EnrichmentData: Dict[str, Any] = Field(default_factory=dict)
    ProcessingTimeMs: int
    AgentVersion: str
```

---

## 4. Agent-Specific Entity: HuntingQuery

**Purpose**: Represents a threat hunting query (natural language or KQL)

```json
{
  "QueryId": "string (UUID)",
  "QueryName": "string",
  "NaturalLanguage": "string (original analyst question)",
  "KQL": "string (generated KQL query)",
  "DataSources": ["string (table names)"],
  "MitreTechniques": ["string (relevant ATT&CK techniques)"],
  "CreatedBy": "string (analyst or 'AutomatedHunt')",
  "CreatedTime": "datetime (ISO 8601)",
  "ExecutionTime": "datetime (ISO 8601, nullable)",
  "ExecutionDurationMs": "integer (nullable)",
  "ResultCount": "integer (nullable)",
  "Status": "enum: Pending|Running|Completed|Failed",
  "Findings": [
    {
      "FindingId": "string (UUID)",
      "SuspiciousEntity": "object (entity that triggered finding)",
      "AnomalyScore": "number (0-100)",
      "Description": "string",
      "RecommendedAction": "string"
    }
  ]
}
```

---

## 5. Agent-Specific Entity: ResponseAction

**Purpose**: Represents a containment/response action

```json
{
  "ActionId": "string (UUID)",
  "IncidentId": "string (UUID reference)",
  "ActionType": "enum: IsolateEndpoint|DisableAccount|BlockIP|QuarantineFile|TerminateProcess|ResetPassword",
  "TargetEntity": {
    "EntityType": "enum: Host|Account|IP|File|Process",
    "EntityId": "string",
    "EntityName": "string"
  },
  "Status": "enum: Pending|ApprovalRequired|Approved|Executing|Completed|Failed|Cancelled",
  "RequestedBy": "string (agent or analyst)",
  "RequestedTime": "datetime (ISO 8601)",
  "ApprovedBy": "string (user principal name, nullable)",
  "ApprovedTime": "datetime (ISO 8601, nullable)",
  "ExecutedTime": "datetime (ISO 8601, nullable)",
  "CompletedTime": "datetime (ISO 8601, nullable)",
  "RiskLevel": "enum: Critical|High|Medium|Low",
  "RequiresApproval": "boolean",
  "Rationale": "string (AI-generated explanation)",
  "PlaybookId": "string (UUID, nullable)",
  "ExecutionDetails": {
    "CommandExecuted": "string",
    "ResultCode": "integer",
    "ResultMessage": "string",
    "AffectedResources": ["string"]
  }
}
```

**Risk-Based Approval Matrix**:

| Action Type | Asset Criticality | Auto-Approved | Requires Approval |
|-------------|-------------------|---------------|-------------------|
| IsolateEndpoint | Low/Medium | ✅ Yes | ❌ No |
| IsolateEndpoint | High/Critical | ❌ No | ✅ Yes (human) |
| DisableAccount | Standard User | ✅ Yes | ❌ No |
| DisableAccount | Admin/Service Account | ❌ No | ✅ Yes (human) |
| BlockIP | External IP | ✅ Yes | ❌ No |
| BlockIP | Internal Subnet | ❌ No | ✅ Yes (human) |

---

## 6. Agent-Specific Entity: ThreatBriefing

**Purpose**: Daily threat intelligence briefing generated by Intelligence Agent

```json
{
  "BriefingId": "string (UUID)",
  "BriefingDate": "date (YYYY-MM-DD)",
  "GeneratedTime": "datetime (ISO 8601)",
  "ExecutiveSummary": "string (natural language)",
  "KeyThreats": [
    {
      "ThreatName": "string",
      "Severity": "enum: Critical|High|Medium|Low",
      "MitreTechniques": ["string"],
      "AffectedAssets": ["string"],
      "RecommendedActions": ["string"]
    }
  ],
  "TrendingAttackPatterns": [
    {
      "Pattern": "string (e.g., 'Credential Dumping')",
      "IncreasePercentage": "number",
      "RelatedIncidents": ["string (IncidentId references)"]
    }
  ],
  "EmergingThreats": [
    {
      "ThreatDescription": "string",
      "Source": "string (e.g., 'Attack Dataset', 'MITRE')",
      "Relevance": "string (why relevant to organization)"
    }
  ],
  "IOCs": [
    {
      "Value": "string",
      "Type": "enum: IP|Domain|FileHash|URL",
      "Reputation": "enum: Malicious|Suspicious",
      "FirstSeen": "datetime (ISO 8601)",
      "Context": "string"
    }
  ]
}
```

---

## 7. Shared Entity: AgentState

**Purpose**: Persistent state for each agent instance

```json
{
  "AgentId": "string (UUID)",
  "AgentName": "string (e.g., 'AlertTriageAgent')",
  "AgentVersion": "string (semver)",
  "Status": "enum: Idle|Processing|Error|Maintenance",
  "LastHeartbeat": "datetime (ISO 8601)",
  "ProcessingQueue": {
    "PendingTasks": "integer",
    "AverageProcessingTimeMs": "number"
  },
  "Metrics": {
    "TotalTasksProcessed": "integer",
    "SuccessRate": "number (0-100)",
    "AverageLatencyMs": "number",
    "ErrorCount": "integer"
  },
  "Configuration": {
    "ModelDeploymentName": "string",
    "Temperature": "number (0-1)",
    "MaxTokens": "integer",
    "CustomInstructions": "string"
  },
  "LastModelUpdate": "datetime (ISO 8601, nullable)",
  "FeedbackSummary": {
    "PositiveFeedback": "integer",
    "NegativeFeedback": "integer",
    "FeedbackScore": "number (0-100)"
  }
}
```

---

## 8. Shared Entity: AuditLog

**Purpose**: Immutable audit trail for compliance

```json
{
  "LogId": "string (UUID)",
  "Timestamp": "datetime (ISO 8601)",
  "EventType": "enum: AgentAction|HumanAction|SystemEvent",
  "Actor": "string (agent name or user UPN)",
  "ActorType": "enum: Agent|User|System",
  "Action": "string (verb, e.g., 'TriagedAlert', 'ApprovedAction')",
  "TargetEntity": {
    "EntityType": "string",
    "EntityId": "string"
  },
  "Details": "object (action-specific data)",
  "Result": "enum: Success|Failure|PartialSuccess",
  "ErrorMessage": "string (nullable)",
  "CorrelationId": "string (UUID for distributed tracing)",
  "ClientIP": "string (nullable)",
  "UserAgent": "string (nullable)"
}
```

---

## 9. Data Storage Strategy

### Cosmos DB Collections

**Collection: `alerts`**
- Primary Key: `SystemAlertId`
- Partition Key: `/TimeGenerated` (date partition, e.g., "2025-11-21")
- TTL: 5 days (MVP default)

**Collection: `incidents`**
- Primary Key: `IncidentId`
- Partition Key: `/Status`
- TTL: 30 days (MVP default)

**Collection: `triage_results`**
- Primary Key: `TriageId`
- Partition Key: `/AlertId`
- TTL: 30 days

**Collection: `response_actions`**
- Primary Key: `ActionId`
- Partition Key: `/IncidentId`
- TTL: 90 days

**Collection: `agent_state`**
- Primary Key: `AgentId`
- Partition Key: `/AgentName`
- TTL: None (persistent)

**Collection: `audit_logs`**
- Primary Key: `LogId`
- Partition Key: `/Timestamp` (date partition)
- TTL: 365 days (compliance requirement)

### Microsoft Fabric (Optional - for long-term storage)

**Delta Lake Tables**:
- `bronze.raw_alerts` - Raw alert data (1-year retention)
- `silver.enriched_alerts` - Processed alerts with enrichment (1-year retention)
- `gold.incident_analytics` - Aggregated incident metrics (permanent)

---

## 10. Validation Rules

### Alert Validation

```python
def validate_alert(alert: SecurityAlert) -> bool:
    """Validate alert meets minimum requirements"""
    
    # Must have system alert ID
    if not alert.SystemAlertId:
        raise ValueError("Missing SystemAlertId")
    
    # Must have severity
    if alert.Severity not in ["High", "Medium", "Low", "Informational"]:
        raise ValueError(f"Invalid severity: {alert.Severity}")
    
    # Must have at least one entity
    if len(alert.Entities) == 0:
        raise ValueError("Alert must have at least one entity")
    
    # Time range must be valid
    if alert.EndTime < alert.StartTime:
        raise ValueError("EndTime must be after StartTime")
    
    return True
```

### Incident Lifecycle Validation

```python
VALID_STATUS_TRANSITIONS = {
    "New": ["Investigating", "Closed"],
    "Investigating": ["Contained", "Resolved", "Closed"],
    "Contained": ["Resolved", "Investigating"],
    "Resolved": ["Closed", "Investigating"],
    "Closed": []  # Terminal state
}

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate incident status transition is allowed"""
    return new_status in VALID_STATUS_TRANSITIONS.get(current_status, [])
```

---

## 11. Entity Relationships

```mermaid
erDiagram
    SecurityAlert ||--o{ SecurityIncident : "aggregates into"
    SecurityIncident ||--o{ ResponseAction : "triggers"
    SecurityAlert ||--|| TriageResult : "produces"
    TriageResult ||--o| SecurityIncident : "recommends"
    SecurityIncident ||--o{ HuntingQuery : "spawns"
    HuntingQuery ||--o{ Finding : "produces"
    SecurityIncident ||--o{ ThreatBriefing : "informs"
    AgentState ||--o{ TriageResult : "tracks"
    AuditLog ||--o{ ResponseAction : "records"
```

---

## Summary

All core entities defined with:
- ✅ JSON schemas aligned with Microsoft Sentinel/Graph Security API
- ✅ Pydantic models for Python type safety
- ✅ Validation rules for data integrity
- ✅ Storage strategy (Cosmos DB collections with TTL)
- ✅ Entity relationships and lifecycle states
- ✅ Agent-specific entities (triage results, hunting queries, response actions)

**Next**: Create API contracts in `contracts/` directory.
