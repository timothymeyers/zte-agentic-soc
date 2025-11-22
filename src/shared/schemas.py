"""
Shared Pydantic models for the Agentic SOC MVP.

This module contains core data models used across all agents and services,
aligned with Microsoft Sentinel/Graph Security API schemas where applicable.
"""

from __future__ import annotations  # Enable forward references

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Enumerations
# ============================================================================

class SeverityLevel(str, Enum):
    """Alert and incident severity levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class EntityType(str, Enum):
    """Types of security entities."""
    ACCOUNT = "Account"
    HOST = "Host"
    IP = "IP"
    FILE = "File"
    PROCESS = "Process"
    URL = "URL"
    MAIL_MESSAGE = "MailMessage"
    CLOUD_APPLICATION = "CloudApplication"


class IncidentStatus(str, Enum):
    """Incident lifecycle states."""
    NEW = "New"
    INVESTIGATING = "Investigating"
    CONTAINED = "Contained"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class IncidentClassification(str, Enum):
    """Incident classification types."""
    TRUE_POSITIVE = "TruePositive"
    BENIGN_POSITIVE = "BenignPositive"
    FALSE_POSITIVE = "FalsePositive"
    UNDETERMINED = "Undetermined"


class TriagePriority(str, Enum):
    """Alert triage priority levels."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TriageDecision(str, Enum):
    """Alert triage decision types."""
    ESCALATE_TO_INCIDENT = "EscalateToIncident"
    CORRELATE_WITH_EXISTING = "CorrelateWithExisting"
    MARK_AS_FALSE_POSITIVE = "MarkAsFalsePositive"
    REQUIRE_HUMAN_REVIEW = "RequireHumanReview"


class ActionType(str, Enum):
    """Incident response action types."""
    ISOLATE_ENDPOINT = "IsolateEndpoint"
    DISABLE_ACCOUNT = "DisableAccount"
    BLOCK_IP = "BlockIP"
    QUARANTINE_FILE = "QuarantineFile"
    TERMINATE_PROCESS = "TerminateProcess"
    RESET_PASSWORD = "ResetPassword"


class ActionStatus(str, Enum):
    """Response action status."""
    PENDING = "Pending"
    APPROVAL_REQUIRED = "ApprovalRequired"
    APPROVED = "Approved"
    EXECUTING = "Executing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class RiskLevel(str, Enum):
    """Risk level for actions and threats."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class AgentStatusEnum(str, Enum):
    """Agent operational status."""
    IDLE = "Idle"
    PROCESSING = "Processing"
    ERROR = "Error"
    MAINTENANCE = "Maintenance"


class EventType(str, Enum):
    """Audit log event types."""
    AGENT_ACTION = "AgentAction"
    HUMAN_ACTION = "HumanAction"
    SYSTEM_EVENT = "SystemEvent"


class ActorType(str, Enum):
    """Actor types for audit logs."""
    AGENT = "Agent"
    USER = "User"
    SYSTEM = "System"


class AuditResult(str, Enum):
    """Audit log result types."""
    SUCCESS = "Success"
    FAILURE = "Failure"
    PARTIAL_SUCCESS = "PartialSuccess"


# ============================================================================
# Core Security Entities (Sentinel/Graph Security aligned)
# ============================================================================

class AlertEntity(BaseModel):
    """Security entity within an alert (user, host, IP, etc.)."""
    model_config = ConfigDict(populate_by_name=True)
    
    Type: EntityType = Field(alias="Type")
    Properties: Dict[str, Any] = Field(default_factory=dict, alias="Properties")


class SecurityAlert(BaseModel):
    """
    Security alert from any source (Sentinel, Defender, mock data).
    Schema aligned with Microsoft Sentinel SecurityAlert table.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    SystemAlertId: UUID = Field(default_factory=uuid4, alias="SystemAlertId")
    AlertName: str = Field(alias="AlertName")
    AlertType: str = Field(alias="AlertType")
    Severity: SeverityLevel = Field(alias="Severity")
    Description: str = Field(alias="Description")
    TimeGenerated: datetime = Field(default_factory=datetime.utcnow, alias="TimeGenerated")
    StartTime: datetime = Field(alias="StartTime")
    EndTime: datetime = Field(alias="EndTime")
    Entities: List[AlertEntity] = Field(default_factory=list, alias="Entities")
    ExtendedProperties: Dict[str, Any] = Field(default_factory=dict, alias="ExtendedProperties")
    ProviderName: str = Field(alias="ProviderName")
    ProductName: str = Field(alias="ProductName")
    RemediationSteps: List[str] = Field(default_factory=list, alias="RemediationSteps")
    ResourceId: Optional[str] = Field(None, alias="ResourceId")


class IncidentComment(BaseModel):
    """Comment on a security incident."""
    model_config = ConfigDict(populate_by_name=True)
    
    CommentId: UUID = Field(default_factory=uuid4)
    Author: str
    Message: str
    CreatedTime: datetime = Field(default_factory=datetime.utcnow)


class IncidentOwner(BaseModel):
    """Incident owner information."""
    model_config = ConfigDict(populate_by_name=True)
    
    AssignedTo: Optional[str] = None
    AssignedAt: Optional[datetime] = None


class SecurityIncident(BaseModel):
    """
    Security incident (correlated alerts, investigation state).
    Schema aligned with Microsoft Sentinel SecurityIncident table.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    IncidentId: UUID = Field(default_factory=uuid4)
    IncidentNumber: Optional[int] = None
    Title: str
    Description: str
    Severity: SeverityLevel
    Status: IncidentStatus = Field(default=IncidentStatus.NEW)
    Classification: Optional[IncidentClassification] = None
    ClassificationReason: Optional[str] = None
    ClassificationComment: Optional[str] = None
    Owner: IncidentOwner = Field(default_factory=IncidentOwner)
    CreatedTime: datetime = Field(default_factory=datetime.utcnow)
    FirstActivityTime: Optional[datetime] = None
    LastActivityTime: Optional[datetime] = None
    LastModifiedTime: datetime = Field(default_factory=datetime.utcnow)
    ClosedTime: Optional[datetime] = None
    AlertIds: List[UUID] = Field(default_factory=list)
    Entities: List[AlertEntity] = Field(default_factory=list)
    Labels: List[str] = Field(default_factory=list)
    RelatedAnalyticRuleIds: List[str] = Field(default_factory=list)
    MitreTechniques: List[str] = Field(default_factory=list)
    Comments: List[IncidentComment] = Field(default_factory=list)
    AdditionalData: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Agent-Specific Entities
# ============================================================================

class ThreatIntelMatch(BaseModel):
    """Threat intelligence match for an IOC."""
    IOC: str
    IOCType: str
    Reputation: str
    Source: str


class TriageResult(BaseModel):
    """Output from Alert Triage Agent."""
    AlertId: UUID
    TriageId: UUID = Field(default_factory=uuid4)
    Timestamp: datetime = Field(default_factory=datetime.utcnow)
    RiskScore: int = Field(ge=0, le=100)
    Priority: TriagePriority
    TriageDecision: TriageDecision
    Explanation: str
    CorrelatedAlertIds: List[UUID] = Field(default_factory=list)
    RecommendedIncidentId: Optional[UUID] = None
    EnrichmentData: Dict[str, Any] = Field(default_factory=dict)
    ProcessingTimeMs: int
    AgentVersion: str


class HuntingFinding(BaseModel):
    """Finding from a threat hunting query."""
    FindingId: UUID = Field(default_factory=uuid4)
    SuspiciousEntity: Dict[str, Any]
    AnomalyScore: float = Field(ge=0, le=100)
    Description: str
    RecommendedAction: str


class HuntingQueryStatus(str, Enum):
    """Hunting query execution status."""
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class HuntingQuery(BaseModel):
    """Threat hunting query (natural language or KQL)."""
    QueryId: UUID = Field(default_factory=uuid4)
    QueryName: str
    NaturalLanguage: str
    KQL: Optional[str] = None
    DataSources: List[str] = Field(default_factory=list)
    MitreTechniques: List[str] = Field(default_factory=list)
    CreatedBy: str
    CreatedTime: datetime = Field(default_factory=datetime.utcnow)
    ExecutionTime: Optional[datetime] = None
    ExecutionDurationMs: Optional[int] = None
    ResultCount: Optional[int] = None
    Status: HuntingQueryStatus = Field(default=HuntingQueryStatus.PENDING)
    Findings: List[HuntingFinding] = Field(default_factory=list)


class ResponseTargetEntity(BaseModel):
    """Target entity for a response action."""
    EntityType: EntityType
    EntityId: str
    EntityName: str


class ExecutionDetails(BaseModel):
    """Execution details for a response action."""
    CommandExecuted: Optional[str] = None
    ResultCode: Optional[int] = None
    ResultMessage: Optional[str] = None
    AffectedResources: List[str] = Field(default_factory=list)


class ResponseAction(BaseModel):
    """Containment/response action."""
    ActionId: UUID = Field(default_factory=uuid4)
    IncidentId: UUID
    ActionType: "ActionType"
    TargetEntity: ResponseTargetEntity
    Status: "ActionStatus" = Field(default_factory=lambda: ActionStatus.PENDING)
    RequestedBy: str
    RequestedTime: datetime = Field(default_factory=datetime.utcnow)
    ApprovedBy: Optional[str] = None
    ApprovedTime: Optional[datetime] = None
    ExecutedTime: Optional[datetime] = None
    CompletedTime: Optional[datetime] = None
    RiskLevel: "RiskLevel"
    RequiresApproval: bool
    Rationale: str
    PlaybookId: Optional[UUID] = None
    ExecutionDetails: ExecutionDetails = Field(default_factory=ExecutionDetails)


class KeyThreat(BaseModel):
    """Key threat in a threat briefing."""
    ThreatName: str
    Severity: SeverityLevel
    MitreTechniques: List[str]
    AffectedAssets: List[str]
    RecommendedActions: List[str]


class AttackPattern(BaseModel):
    """Trending attack pattern."""
    Pattern: str
    IncreasePercentage: float
    RelatedIncidents: List[UUID]


class EmergingThreat(BaseModel):
    """Emerging threat information."""
    ThreatDescription: str
    Source: str
    Relevance: str


class IOCReputation(str, Enum):
    """IOC reputation levels."""
    MALICIOUS = "Malicious"
    SUSPICIOUS = "Suspicious"
    UNKNOWN = "Unknown"
    BENIGN = "Benign"


class IOCType(str, Enum):
    """IOC types."""
    IP = "IP"
    DOMAIN = "Domain"
    FILE_HASH = "FileHash"
    URL = "URL"


class IOC(BaseModel):
    """Indicator of Compromise."""
    Value: str
    Type: IOCType
    Reputation: IOCReputation
    FirstSeen: datetime
    Context: str


class ThreatBriefing(BaseModel):
    """Daily threat intelligence briefing."""
    BriefingId: UUID = Field(default_factory=uuid4)
    BriefingDate: datetime
    GeneratedTime: datetime = Field(default_factory=datetime.utcnow)
    ExecutiveSummary: str
    KeyThreats: List[KeyThreat] = Field(default_factory=list)
    TrendingAttackPatterns: List[AttackPattern] = Field(default_factory=list)
    EmergingThreats: List[EmergingThreat] = Field(default_factory=list)
    IOCs: List[IOC] = Field(default_factory=list)


# ============================================================================
# Agent State and Monitoring
# ============================================================================

class ProcessingQueue(BaseModel):
    """Agent processing queue metrics."""
    PendingTasks: int = 0
    AverageProcessingTimeMs: float = 0.0


class AgentMetrics(BaseModel):
    """Agent performance metrics."""
    TotalTasksProcessed: int = 0
    SuccessRate: float = 0.0
    AverageLatencyMs: float = 0.0
    ErrorCount: int = 0


class AgentConfiguration(BaseModel):
    """Agent configuration settings."""
    ModelDeploymentName: str
    Temperature: float = Field(ge=0.0, le=1.0)
    MaxTokens: int
    CustomInstructions: Optional[str] = None


class FeedbackSummary(BaseModel):
    """Agent feedback summary."""
    PositiveFeedback: int = 0
    NegativeFeedback: int = 0
    FeedbackScore: float = Field(ge=0.0, le=100.0, default=0.0)


class AgentState(BaseModel):
    """Persistent state for each agent instance."""
    AgentId: UUID = Field(default_factory=uuid4)
    AgentName: str
    AgentVersion: str
    Status: AgentStatusEnum = Field(default=AgentStatusEnum.IDLE)
    LastHeartbeat: datetime = Field(default_factory=datetime.utcnow)
    ProcessingQueue: ProcessingQueue = Field(default_factory=ProcessingQueue)
    Metrics: AgentMetrics = Field(default_factory=AgentMetrics)
    Configuration: AgentConfiguration
    LastModelUpdate: Optional[datetime] = None
    FeedbackSummary: FeedbackSummary = Field(default_factory=FeedbackSummary)


# ============================================================================
# Audit Logging
# ============================================================================

class AuditTargetEntity(BaseModel):
    """Target entity for an audit log entry."""
    EntityType: str
    EntityId: str


class AuditLog(BaseModel):
    """Immutable audit trail for compliance."""
    LogId: UUID = Field(default_factory=uuid4)
    Timestamp: datetime = Field(default_factory=datetime.utcnow)
    EventType: EventType
    Actor: str
    ActorType: ActorType
    Action: str
    TargetEntity: AuditTargetEntity
    Details: Dict[str, Any] = Field(default_factory=dict)
    Result: AuditResult
    ErrorMessage: Optional[str] = None
    CorrelationId: UUID = Field(default_factory=uuid4)
    ClientIP: Optional[str] = None
    UserAgent: Optional[str] = None


# Rebuild models to resolve forward references
ResponseAction.model_rebuild()
SecurityIncident.model_rebuild()
AuditLog.model_rebuild()
