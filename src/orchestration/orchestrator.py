"""
Base orchestrator for multi-agent coordination.

This module provides the orchestration layer for coordinating multiple
AI agents in the Agentic SOC system.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from src.shared.schemas import (
    SecurityAlert,
    SecurityIncident,
    AgentState,
    AgentStatusEnum
)
from src.shared.logging import get_logger, set_correlation_id
from src.shared.metrics import counter
from src.orchestration.event_handlers import get_event_bus, OrchestrationEventType


logger = get_logger(__name__)


class AgentRegistry:
    """Registry for managing agent instances."""
    
    def __init__(self):
        """Initialize agent registry."""
        self._agents: Dict[str, Any] = {}
        logger.debug("Agent registry initialized")
    
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Register an agent.
        
        Args:
            agent_name: Name of the agent
            agent_instance: Agent instance
        """
        self._agents[agent_name] = agent_instance
        logger.debug(f"Agent registered: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """
        Get an agent by name.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Optional agent instance
        """
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agents.
        
        Returns:
            List of agent names
        """
        return list(self._agents.keys())


class Orchestrator:
    """
    Orchestrator for multi-agent coordination.
    
    This orchestrator uses a hybrid approach:
    - Event-driven for reactive workflows (alert ingestion → triage)
    - Sequential handoff for complex multi-stage scenarios
    - Shared context via SecurityIncident objects
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.agent_registry = AgentRegistry()
        self.event_bus = get_event_bus()
        self._active_workflows: Dict[UUID, Dict[str, Any]] = {}
        
        logger.debug("Orchestrator initialized")
    
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_name: Name of the agent
            agent_instance: Agent instance
        """
        self.agent_registry.register_agent(agent_name, agent_instance)
    
    async def process_alert(self, alert: SecurityAlert) -> None:
        """
        Process an incoming alert through the orchestration pipeline.
        
        Args:
            alert: Security alert to process
        
        Workflow:
            1. Ingest alert
            2. Publish alert ingestion event
            3. Alert Triage Agent picks up event (if registered)
            4. Based on triage result, may trigger other agents
        """
        # Set correlation ID for tracking
        correlation_id = str(uuid4())
        set_correlation_id(correlation_id)
        
        logger.info(
            "alert_processing_started",
            alert_id=str(alert.SystemAlertId),
            alert_name=alert.AlertName,
            severity=alert.Severity,
            correlation_id=correlation_id
        )
        
        # Track workflow
        workflow_id = uuid4()
        self._active_workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "alert_id": alert.SystemAlertId,
            "started_at": datetime.utcnow(),
            "status": "processing",
            "stages": []
        }
        
        try:
            # Publish alert ingestion event
            await self.event_bus.publish(
                OrchestrationEventType.ALERT_INGESTION,
                {
                    "alert_id": str(alert.SystemAlertId),
                    "alert": alert.model_dump(),
                    "correlation_id": correlation_id,
                    "workflow_id": str(workflow_id)
                }
            )
            
            counter("alerts_orchestrated_total").inc()
            
            self._active_workflows[workflow_id]["status"] = "completed"
            
            logger.info(
                "alert_processing_completed",
                alert_id=str(alert.SystemAlertId),
                workflow_id=str(workflow_id)
            )
            
        except Exception as e:
            logger.error(
                "alert_processing_failed",
                alert_id=str(alert.SystemAlertId),
                workflow_id=str(workflow_id),
                error=str(e),
                exc_info=True
            )
            
            self._active_workflows[workflow_id]["status"] = "failed"
            self._active_workflows[workflow_id]["error"] = str(e)
            
            counter("alerts_orchestration_failed_total").inc()
            raise
    
    async def escalate_to_human(
        self,
        incident_id: UUID,
        reason: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Escalate an incident to human analysts.
        
        Args:
            incident_id: Incident ID
            reason: Reason for escalation
            context: Additional context
        """
        logger.warning(
            "human_escalation_required",
            incident_id=str(incident_id),
            reason=reason,
            context=context
        )
        
        # TODO: Implement Teams notification or approval workflow
        # For MVP, just log the escalation
        
        counter("human_escalations_total").inc()
    
    async def coordinate_agents(
        self,
        workflow_type: str,
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents for a workflow.
        
        Args:
            workflow_type: Type of workflow (e.g., "incident_response", "threat_hunt")
            initial_context: Initial context for the workflow
        
        Returns:
            Dict containing workflow results
        """
        workflow_id = uuid4()
        correlation_id = str(uuid4())
        set_correlation_id(correlation_id)
        
        logger.info(
            "multi_agent_workflow_started",
            workflow_type=workflow_type,
            workflow_id=str(workflow_id),
            correlation_id=correlation_id
        )
        
        # Track workflow
        workflow = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "started_at": datetime.utcnow(),
            "agents_involved": [],
            "results": {}
        }
        
        # For MVP, implement simple sequential handoff
        # Production would use more sophisticated patterns
        
        try:
            # Example: Incident response workflow
            if workflow_type == "incident_response":
                # 1. Alert Triage → creates incident
                # 2. Threat Intelligence → enriches incident
                # 3. Incident Response → executes containment
                # 4. Threat Hunting → searches for related activity
                pass
            
            workflow["completed_at"] = datetime.utcnow()
            workflow["status"] = "completed"
            
            logger.info(
                "multi_agent_workflow_completed",
                workflow_id=str(workflow_id),
                workflow_type=workflow_type
            )
            
            return workflow
            
        except Exception as e:
            logger.error(
                "multi_agent_workflow_failed",
                workflow_id=str(workflow_id),
                workflow_type=workflow_type,
                error=str(e),
                exc_info=True
            )
            
            workflow["status"] = "failed"
            workflow["error"] = str(e)
            
            return workflow
    
    def get_workflow_status(self, workflow_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get status of a workflow.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Optional workflow status
        """
        return self._active_workflows.get(workflow_id)


# Global orchestrator instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """
    Get global orchestrator instance.
    
    Returns:
        Orchestrator: Global orchestrator
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
