"""
Pydantic data models for Agentic SOC.

These models align with Microsoft Sentinel/Defender XDR schemas where applicable
and extend them for agent-specific requirements.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enumerations
# =============================================================================


class Severity(str, Enum):
    """Alert severity levels matching Microsoft Sentinel."""

    INFORMATIONAL = "Informational"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Status(str, Enum):
    """Incident status values."""

    NEW = "New"
    IN_PROGRESS = "InProgress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class PriorityLevel(str, Enum):
    """Triage priority levels."""

    P1_CRITICAL = "P1-Critical"
    P2_HIGH = "P2-High"
    P3_MEDIUM = "P3-Medium"
    P4_LOW = "P4-Low"
    P5_INFORMATIONAL = "P5-Informational"


class TriageDecision(str, Enum):
    """Triage decision outcomes."""

    ESCALATE = "Escalate"
    INVESTIGATE = "Investigate"
    MONITOR = "Monitor"
    DISMISS = "Dismiss"
    INSUFFICIENT_DATA = "InsufficientData"


class ResponseActionType(str, Enum):
    """Types of incident response actions."""

    ISOLATE_ENDPOINT = "IsolateEndpoint"
    BLOCK_IP = "BlockIP"
    BLOCK_URL = "BlockURL"
    DISABLE_ACCOUNT = "DisableAccount"
    RESET_PASSWORD = "ResetPassword"
    QUARANTINE_FILE = "QuarantineFile"
    KILL_PROCESS = "KillProcess"
    COLLECT_FORENSICS = "CollectForensics"


class ActionStatus(str, Enum):
    """Status of response actions."""

    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class RiskLevel(str, Enum):
    """Risk levels for actions requiring approval."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# =============================================================================
# Core Entities (SDK-Aligned)
# =============================================================================


class SecurityAlert(BaseModel):
    """
    Security alert entity aligned with Microsoft Sentinel SecurityAlert schema.
    
    Reference: https://learn.microsoft.com/en-us/azure/defender-for-cloud/alerts-schemas
    """

    alert_id: UUID = Field(default_factory=uuid4, alias="AlertId")
    time_generated: datetime = Field(default_factory=datetime.utcnow, alias="TimeGenerated")
    alert_name: str = Field(alias="AlertName")
    alert_type: str = Field(alias="AlertType")
    severity: Severity = Field(alias="Severity")
    description: str = Field(alias="Description")
    remediation_steps: Optional[str] = Field(None, alias="RemediationSteps")
    extended_properties: Dict[str, Any] = Field(default_factory=dict, alias="ExtendedProperties")
    entities: List[Dict[str, Any]] = Field(default_factory=list, alias="Entities")
    confidence_score: Optional[float] = Field(None, alias="ConfidenceScore", ge=0.0, le=1.0)
    tactics: List[str] = Field(default_factory=list, alias="Tactics")
    techniques: List[str] = Field(default_factory=list, alias="Techniques")
    vendor_name: str = Field(default="Microsoft Sentinel", alias="VendorName")
    product_name: str = Field(default="Sentinel", alias="ProductName")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "AlertId": "550e8400-e29b-41d4-a716-446655440000",
                "TimeGenerated": "2025-12-18T12:00:00Z",
                "AlertName": "Suspicious Login Attempt",
                "AlertType": "Authentication",
                "Severity": "High",
                "Description": "Multiple failed login attempts detected",
                "Tactics": ["InitialAccess"],
                "Techniques": ["T1078"],
            }
        }


class SecurityIncident(BaseModel):
    """
    Security incident entity aligned with Microsoft Sentinel SecurityIncident schema.
    
    Reference: https://learn.microsoft.com/en-us/azure/sentinel/manage-soc-with-incident-metrics
    """

    incident_id: UUID = Field(default_factory=uuid4, alias="IncidentId")
    incident_number: int = Field(alias="IncidentNumber")
    title: str = Field(alias="Title")
    description: str = Field(alias="Description")
    severity: Severity = Field(alias="Severity")
    status: Status = Field(alias="Status")
    created_time: datetime = Field(default_factory=datetime.utcnow, alias="CreatedTime")
    last_modified_time: datetime = Field(default_factory=datetime.utcnow, alias="LastModifiedTime")
    owner: Optional[str] = Field(None, alias="Owner")
    labels: List[str] = Field(default_factory=list, alias="Labels")
    alerts: List[SecurityAlert] = Field(default_factory=list, alias="Alerts")
    tactics: List[str] = Field(default_factory=list, alias="Tactics")
    techniques: List[str] = Field(default_factory=list, alias="Techniques")

    class Config:
        populate_by_name = True


# =============================================================================
# Agent-Specific Entities (Custom)
# =============================================================================


class TriageResult(BaseModel):
    """
    Output from Alert Triage Agent - risk assessment and prioritization.
    """

    triage_id: UUID = Field(default_factory=uuid4)
    alert_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    risk_score: int = Field(ge=0, le=100, description="Risk score from 0-100")
    priority: PriorityLevel
    triage_decision: TriageDecision
    explanation: str = Field(description="Natural language explanation for the triage decision")
    contributing_factors: List[str] = Field(default_factory=list)
    correlated_alerts: List[UUID] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)

    class Config:
        json_schema_extra = {
            "example": {
                "triage_id": "123e4567-e89b-12d3-a456-426614174000",
                "alert_id": "550e8400-e29b-41d4-a716-446655440000",
                "risk_score": 85,
                "priority": "P1-Critical",
                "triage_decision": "Escalate",
                "explanation": "Critical severity brute force attack with successful login",
                "contributing_factors": ["High alert severity", "Successful login after failures"],
                "confidence": 0.9,
            }
        }


class HuntingQuery(BaseModel):
    """
    Natural language hunting query and generated KQL.
    """

    query_id: UUID = Field(default_factory=uuid4)
    natural_language: str = Field(description="Natural language query from analyst")
    kql_query: str = Field(description="Generated KQL query")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    time_range: str = Field(default="24h")
    expected_results: Optional[str] = Field(None)
    explanation: str = Field(description="Explanation of what the query searches for")
    tactics: List[str] = Field(default_factory=list)
    techniques: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "789e4567-e89b-12d3-a456-426614174000",
                "natural_language": "Show lateral movement attempts in last 24 hours",
                "kql_query": "SecurityEvent | where TimeGenerated > ago(24h) | where EventID == 4624",
                "explanation": "Searches for successful logon events that may indicate lateral movement",
                "tactics": ["LateralMovement"],
                "techniques": ["T1021"],
            }
        }


class ResponseAction(BaseModel):
    """
    Automated response action with approval workflow.
    """

    action_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    action_type: ResponseActionType
    target_entity: str = Field(description="Entity to act on (IP, hostname, username, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: ActionStatus = Field(default=ActionStatus.PENDING)
    risk_level: RiskLevel
    requires_approval: bool = Field(default=True)
    approved_by: Optional[str] = Field(None)
    approval_timestamp: Optional[datetime] = Field(None)
    rationale: str = Field(description="Explanation for the action")
    execution_details: Optional[Dict[str, Any]] = Field(None)
    result: Optional[str] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "456e4567-e89b-12d3-a456-426614174000",
                "incident_id": "123e4567-e89b-12d3-a456-426614174000",
                "action_type": "IsolateEndpoint",
                "target_entity": "WORKSTATION-01",
                "status": "Pending",
                "risk_level": "High",
                "requires_approval": True,
                "rationale": "Malware detected on endpoint, isolate to prevent spread",
            }
        }


class ThreatBriefing(BaseModel):
    """
    Daily threat intelligence briefing.
    """

    briefing_id: UUID = Field(default_factory=uuid4)
    date: datetime = Field(default_factory=datetime.utcnow)
    title: str
    summary: str = Field(description="Executive summary of threat landscape")
    key_findings: List[str] = Field(default_factory=list)
    emerging_threats: List[Dict[str, Any]] = Field(default_factory=list)
    ioc_summary: Dict[str, int] = Field(
        default_factory=dict, description="Count of IOCs by type (IPs, domains, hashes)"
    )
    mitre_tactics: Dict[str, int] = Field(
        default_factory=dict, description="Count of observed tactics"
    )
    recommendations: List[str] = Field(default_factory=list)
    generated_by: str = Field(default="Threat Intelligence Agent")

    class Config:
        json_schema_extra = {
            "example": {
                "briefing_id": "abc12345-e89b-12d3-a456-426614174000",
                "date": "2025-12-18T00:00:00Z",
                "title": "Daily Threat Intelligence Briefing - Dec 18, 2025",
                "summary": "Increased phishing activity targeting financial sector",
                "key_findings": ["50% increase in phishing emails", "New ransomware variant detected"],
                "ioc_summary": {"ips": 150, "domains": 75, "hashes": 200},
            }
        }


class AgentState(BaseModel):
    """
    Persistent state for agent execution tracking.
    """

    agent_name: str = Field(description="Name of the agent (e.g., 'AlertTriageAgent')")
    agent_version: str = Field(default="1.0.0")
    last_execution: datetime = Field(default_factory=datetime.utcnow)
    execution_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    average_latency_ms: float = Field(default=0.0)
    last_error: Optional[str] = Field(None)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "AlertTriageAgent",
                "agent_version": "1.0.0",
                "execution_count": 1250,
                "success_count": 1200,
                "failure_count": 50,
                "average_latency_ms": 1250.5,
            }
        }


class AuditLog(BaseModel):
    """
    Immutable audit trail for agent actions (compliance requirement).
    """

    audit_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = Field(description="Agent or user that performed the action")
    action: str = Field(description="Action performed")
    target: Optional[str] = Field(None, description="Target entity or resource")
    result: str = Field(description="Success, Failure, or Pending")
    details: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[UUID] = Field(None, description="Correlation ID for distributed tracing")
    session_id: Optional[UUID] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": "def45678-e89b-12d3-a456-426614174000",
                "timestamp": "2025-12-18T12:30:00Z",
                "actor": "AlertTriageAgent",
                "action": "TriageAlert",
                "target": "550e8400-e29b-41d4-a716-446655440000",
                "result": "Success",
                "correlation_id": "cor12345-e89b-12d3-a456-426614174000",
            }
        }


# =============================================================================
# Helper Functions
# =============================================================================


def create_sample_alert(
    alert_name: str = "Test Alert",
    severity: Severity = Severity.MEDIUM,
    alert_type: str = "TestAlert",
) -> SecurityAlert:
    """Create a sample security alert for testing."""
    return SecurityAlert(
        AlertName=alert_name,
        AlertType=alert_type,
        Severity=severity,
        Description=f"Sample {severity.value} severity alert for testing",
        Tactics=["InitialAccess"],
        Techniques=["T1078"],
    )


def create_sample_incident(
    title: str = "Test Incident", severity: Severity = Severity.HIGH
) -> SecurityIncident:
    """Create a sample security incident for testing."""
    return SecurityIncident(
        IncidentNumber=12345,
        Title=title,
        Description=f"Sample {severity.value} severity incident for testing",
        Severity=severity,
        Status=Status.NEW,
        Tactics=["InitialAccess", "Persistence"],
        Techniques=["T1078", "T1098"],
    )
