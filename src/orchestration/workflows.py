"""
Multi-agent workflows for context propagation and coordination.

This module defines workflows that coordinate multiple agents with
shared context via SecurityIncident objects and Cosmos DB.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from src.shared.schemas import (
    SecurityAlert,
    SecurityIncident,
    IncidentStatus,
    SeverityLevel
)
from src.shared.logging import get_logger
from src.data.cosmos import get_cosmos_client


logger = get_logger(__name__)


class WorkflowContext:
    """Shared context for multi-agent workflows."""
    
    def __init__(self, workflow_id: UUID):
        """
        Initialize workflow context.
        
        Args:
            workflow_id: Unique workflow identifier
        """
        self.workflow_id = workflow_id
        self.created_at = datetime.utcnow()
        self.shared_state: Dict[str, Any] = {}
        self.agent_outputs: Dict[str, Any] = {}
        logger.debug(f"Workflow context created: {workflow_id}")
    
    def set_state(self, key: str, value: Any) -> None:
        """
        Set shared state value.
        
        Args:
            key: State key
            value: State value
        """
        self.shared_state[key] = value
        logger.debug(f"Workflow state updated: {key}")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get shared state value.
        
        Args:
            key: State key
            default: Default value if key not found
        
        Returns:
            State value or default
        """
        return self.shared_state.get(key, default)
    
    def record_agent_output(self, agent_name: str, output: Dict[str, Any]) -> None:
        """
        Record output from an agent.
        
        Args:
            agent_name: Name of the agent
            output: Agent output
        """
        self.agent_outputs[agent_name] = {
            "timestamp": datetime.utcnow(),
            "output": output
        }
        logger.debug(f"Agent output recorded: {agent_name}")


class AlertTriageWorkflow:
    """Workflow for alert triage and incident creation."""
    
    def __init__(self):
        """Initialize alert triage workflow."""
        logger.info("Alert triage workflow initialized")
    
    async def execute(
        self,
        alert: SecurityAlert,
        context: WorkflowContext
    ) -> Optional[SecurityIncident]:
        """
        Execute alert triage workflow.
        
        Args:
            alert: Security alert
            context: Workflow context
        
        Returns:
            Optional[SecurityIncident]: Created incident if escalated
        """
        logger.info(
            "alert_triage_workflow_executing",
            alert_id=str(alert.SystemAlertId),
            workflow_id=str(context.workflow_id)
        )
        
        # Store alert in context
        context.set_state("alert", alert)
        
        # TODO: Call Alert Triage Agent (Phase 4)
        # For now, create a placeholder triage result
        
        # If high-severity, create incident
        if alert.Severity in [SeverityLevel.HIGH, SeverityLevel.MEDIUM]:
            incident = await self._create_incident(alert, context)
            context.set_state("incident", incident)
            return incident
        
        return None
    
    async def _create_incident(
        self,
        alert: SecurityAlert,
        context: WorkflowContext
    ) -> SecurityIncident:
        """
        Create a security incident from an alert.
        
        Args:
            alert: Security alert
            context: Workflow context
        
        Returns:
            SecurityIncident: Created incident
        """
        incident = SecurityIncident(
            Title=alert.AlertName,
            Description=alert.Description,
            Severity=alert.Severity,
            Status=IncidentStatus.NEW,
            AlertIds=[alert.SystemAlertId],
            Entities=alert.Entities,
            MitreTechniques=alert.ExtendedProperties.get("MitreTechniques", []),
            FirstActivityTime=alert.StartTime,
            LastActivityTime=alert.EndTime
        )
        
        # TODO: Persist to Cosmos DB when available
        # cosmos_client = get_cosmos_client()
        # await cosmos_client.create_item("incidents", incident.model_dump())
        
        logger.info(
            "incident_created",
            incident_id=str(incident.IncidentId),
            alert_id=str(alert.SystemAlertId),
            severity=incident.Severity
        )
        
        return incident


class IncidentResponseWorkflow:
    """Workflow for incident response and containment."""
    
    def __init__(self):
        """Initialize incident response workflow."""
        logger.info("Incident response workflow initialized")
    
    async def execute(
        self,
        incident: SecurityIncident,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """
        Execute incident response workflow.
        
        Args:
            incident: Security incident
            context: Workflow context
        
        Returns:
            Dict containing response actions taken
        """
        logger.info(
            "incident_response_workflow_executing",
            incident_id=str(incident.IncidentId),
            workflow_id=str(context.workflow_id)
        )
        
        # Store incident in context
        context.set_state("incident", incident)
        
        # TODO: Implement actual response workflow (Phase 6)
        # 1. Analyze incident
        # 2. Determine containment actions
        # 3. Execute approved actions
        # 4. Update incident status
        
        response_actions = {
            "incident_id": str(incident.IncidentId),
            "actions_taken": [],
            "status": "pending"
        }
        
        return response_actions


class ThreatHuntingWorkflow:
    """Workflow for proactive threat hunting."""
    
    def __init__(self):
        """Initialize threat hunting workflow."""
        logger.info("Threat hunting workflow initialized")
    
    async def execute(
        self,
        query: str,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """
        Execute threat hunting workflow.
        
        Args:
            query: Natural language hunting query
            context: Workflow context
        
        Returns:
            Dict containing hunting results
        """
        logger.info(
            "threat_hunting_workflow_executing",
            query=query,
            workflow_id=str(context.workflow_id)
        )
        
        # TODO: Implement actual hunting workflow (Phase 5)
        # 1. Translate natural language to KQL
        # 2. Execute query
        # 3. Detect anomalies
        # 4. Generate findings
        
        hunting_results = {
            "query": query,
            "findings": [],
            "status": "pending"
        }
        
        return hunting_results


# Global workflow instances
_triage_workflow: Optional[AlertTriageWorkflow] = None
_response_workflow: Optional[IncidentResponseWorkflow] = None
_hunting_workflow: Optional[ThreatHuntingWorkflow] = None


def get_triage_workflow() -> AlertTriageWorkflow:
    """Get global alert triage workflow instance."""
    global _triage_workflow
    if _triage_workflow is None:
        _triage_workflow = AlertTriageWorkflow()
    return _triage_workflow


def get_response_workflow() -> IncidentResponseWorkflow:
    """Get global incident response workflow instance."""
    global _response_workflow
    if _response_workflow is None:
        _response_workflow = IncidentResponseWorkflow()
    return _response_workflow


def get_hunting_workflow() -> ThreatHuntingWorkflow:
    """Get global threat hunting workflow instance."""
    global _hunting_workflow
    if _hunting_workflow is None:
        _hunting_workflow = ThreatHuntingWorkflow()
    return _hunting_workflow
