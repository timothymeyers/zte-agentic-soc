"""
Workflow execution module for Agentic SOC.

Handles workflow execution with event streaming and progress tracking.
"""

import asyncio
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional
from uuid import uuid4

from agent_framework import AgentRunUpdateEvent

from src.shared.logging import get_logger
from src.shared.models import SecurityAlert

logger = get_logger(__name__, module="workflows")


class WorkflowExecutor:
    """
    Execute SOC workflows with event streaming and progress tracking.
    """

    def __init__(self, workflow):
        """
        Initialize workflow executor.

        Args:
            workflow: Magentic workflow instance from orchestrator
        """
        self.workflow = workflow
        self.execution_id = str(uuid4())
        self.start_time = None
        self.end_time = None
        self.events = []

        logger.info("WorkflowExecutor initialized", execution_id=self.execution_id)

    async def run_workflow(
        self,
        task: str,
        context: Optional[Dict] = None,
    ) -> AsyncIterator[Dict]:
        """
        Execute workflow with event streaming.

        Args:
            task: Task description for the workflow
            context: Optional context information

        Yields:
            Event dictionaries with workflow progress

        Example:
            >>> executor = WorkflowExecutor(workflow)
            >>> async for event in executor.run_workflow("Analyze this alert"):
            ...     print(event["type"], event["data"])
        """
        self.start_time = datetime.utcnow()

        logger.info(
            "Starting workflow execution",
            execution_id=self.execution_id,
            task_length=len(task),
        )

        try:
            # Yield start event
            yield {
                "type": "workflow_start",
                "execution_id": self.execution_id,
                "timestamp": self.start_time.isoformat(),
                "task": task,
                "context": context,
            }

            # Stream workflow execution
            async for event in self.workflow.run(task):
                if isinstance(event, AgentRunUpdateEvent):
                    event_dict = self._process_event(event)
                    self.events.append(event_dict)
                    yield event_dict

            # Workflow complete
            self.end_time = datetime.utcnow()
            duration = (self.end_time - self.start_time).total_seconds()

            # Get final state and outputs
            final_state = self.workflow.get_final_state() if hasattr(self.workflow, 'get_final_state') else "complete"
            outputs = self.workflow.get_outputs() if hasattr(self.workflow, 'get_outputs') else {}

            yield {
                "type": "workflow_complete",
                "execution_id": self.execution_id,
                "timestamp": self.end_time.isoformat(),
                "duration_seconds": duration,
                "final_state": final_state,
                "outputs": outputs,
                "event_count": len(self.events),
            }

            logger.info(
                "Workflow execution complete",
                execution_id=self.execution_id,
                duration_seconds=duration,
                event_count=len(self.events),
            )

        except Exception as e:
            self.end_time = datetime.utcnow()
            duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0

            logger.error(
                "Workflow execution failed",
                execution_id=self.execution_id,
                duration_seconds=duration,
                error=str(e),
                exc_info=True,
            )

            yield {
                "type": "workflow_error",
                "execution_id": self.execution_id,
                "timestamp": self.end_time.isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
            }

            raise

    def _process_event(self, event: AgentRunUpdateEvent) -> Dict:
        """
        Process AgentRunUpdateEvent into standardized dictionary.

        Args:
            event: Agent run update event

        Returns:
            Event dictionary
        """
        event_dict = {
            "type": "agent_event",
            "execution_id": self.execution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_data": {},
        }

        # Extract magentic-specific event type if available
        if hasattr(event, "magentic_event_type"):
            magentic_type = event.magentic_event_type
            event_dict["magentic_type"] = magentic_type
            event_dict["type"] = f"magentic_{magentic_type}"

        # Extract executor ID (agent name)
        if hasattr(event, "executor_id"):
            event_dict["agent"] = event.executor_id

        # Extract event data
        if hasattr(event, "data"):
            event_dict["event_data"] = event.data

        # Log event
        logger.debug(
            "Workflow event",
            execution_id=self.execution_id,
            event_type=event_dict.get("type"),
            agent=event_dict.get("agent"),
        )

        return event_dict

    def get_execution_summary(self) -> Dict:
        """
        Get execution summary with statistics.

        Returns:
            Summary dictionary
        """
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        # Count events by type
        event_counts = {}
        for event in self.events:
            event_type = event.get("type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Count events by agent
        agent_counts = {}
        for event in self.events:
            agent = event.get("agent")
            if agent:
                agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "total_events": len(self.events),
            "event_counts": event_counts,
            "agent_counts": agent_counts,
        }


# =============================================================================
# Alert Workflow Functions
# =============================================================================


async def run_alert_triage_workflow(
    workflow,
    alert: SecurityAlert,
) -> AsyncIterator[Dict]:
    """
    Execute alert triage workflow.

    Args:
        workflow: Magentic workflow instance
        alert: Security alert to triage

    Yields:
        Workflow events

    Example:
        >>> from src.orchestration.orchestrator import create_soc_workflow
        >>> from src.shared.models import SecurityAlert, Severity
        >>>
        >>> workflow = create_soc_workflow()
        >>> alert = SecurityAlert(
        ...     AlertName="Suspicious Login",
        ...     AlertType="Authentication",
        ...     Severity=Severity.HIGH,
        ...     Description="Multiple failed logins followed by success"
        ... )
        >>>
        >>> async for event in run_alert_triage_workflow(workflow, alert):
        ...     print(event["type"])
    """
    # Construct task for manager
    task = f"""
Analyze this security alert and coordinate appropriate response:

Alert: {alert.alert_name}
Severity: {alert.severity.value}
Type: {alert.alert_type}
Description: {alert.description}
Tactics: {', '.join(alert.tactics) if alert.tactics else 'None'}
Techniques: {', '.join(alert.techniques) if alert.techniques else 'None'}

IMPORTANT: Follow triage-first rule - ALWAYS start with Alert Triage Agent.
"""

    context = {
        "alert_id": str(alert.alert_id),
        "workflow_type": "alert_triage",
    }

    executor = WorkflowExecutor(workflow)

    async for event in executor.run_workflow(task, context):
        yield event


async def run_threat_hunt_workflow(
    workflow,
    hunt_query: str,
) -> AsyncIterator[Dict]:
    """
    Execute threat hunting workflow.

    Args:
        workflow: Magentic workflow instance
        hunt_query: Natural language hunting query

    Yields:
        Workflow events

    Example:
        >>> workflow = create_soc_workflow()
        >>> query = "Search for lateral movement attempts in last 24 hours"
        >>>
        >>> async for event in run_threat_hunt_workflow(workflow, query):
        ...     print(event["type"])
    """
    task = f"""
Execute proactive threat hunt:

Query: {hunt_query}

Generate KQL queries, execute search, analyze findings, and recommend actions.
"""

    context = {
        "workflow_type": "threat_hunt",
        "query": hunt_query,
    }

    executor = WorkflowExecutor(workflow)

    async for event in executor.run_workflow(task, context):
        yield event


async def run_scenario_workflow(
    workflow,
    scenario_name: str,
    alerts: List[SecurityAlert],
) -> AsyncIterator[Dict]:
    """
    Execute scenario workflow with multiple alerts.

    Args:
        workflow: Magentic workflow instance
        scenario_name: Name of the scenario
        alerts: List of security alerts in the scenario

    Yields:
        Workflow events

    Example:
        >>> from src.data.scenarios import ScenarioManager
        >>>
        >>> workflow = create_soc_workflow()
        >>> manager = ScenarioManager()
        >>> scenario = manager.get_scenario("brute_force")
        >>>
        >>> async for event in run_scenario_workflow(workflow, "brute_force", scenario.alerts):
        ...     print(event["type"])
    """
    # Construct task with scenario context
    alert_summaries = []
    for i, alert in enumerate(alerts[:5], 1):  # Show first 5 alerts
        alert_summaries.append(
            f"{i}. {alert.alert_name} ({alert.severity.value}) - {alert.description[:100]}"
        )

    task = f"""
Analyze and respond to security scenario: {scenario_name}

Alert sequence ({len(alerts)} alerts):
{chr(10).join(alert_summaries)}
{"... and " + str(len(alerts) - 5) + " more alerts" if len(alerts) > 5 else ""}

Coordinate comprehensive response:
1. Triage all alerts (triage-first rule)
2. Identify attack patterns and correlations
3. Recommend containment actions
4. Provide threat intelligence context
"""

    context = {
        "workflow_type": "scenario",
        "scenario_name": scenario_name,
        "alert_count": len(alerts),
    }

    executor = WorkflowExecutor(workflow)

    async for event in executor.run_workflow(task, context):
        yield event


# =============================================================================
# Progress Tracking
# =============================================================================


class WorkflowProgressTracker:
    """
    Track workflow progress across multiple executions.
    """

    def __init__(self):
        """Initialize progress tracker."""
        self.executions = []
        logger.info("WorkflowProgressTracker initialized")

    def add_execution(self, summary: Dict):
        """
        Add execution summary to tracker.

        Args:
            summary: Execution summary from WorkflowExecutor
        """
        self.executions.append(summary)
        logger.info(
            "Execution tracked",
            execution_id=summary["execution_id"],
            total_executions=len(self.executions),
        )

    def get_statistics(self) -> Dict:
        """
        Get aggregate statistics across all executions.

        Returns:
            Statistics dictionary
        """
        if not self.executions:
            return {
                "total_executions": 0,
                "total_events": 0,
                "average_duration_seconds": 0,
            }

        total_events = sum(e.get("total_events", 0) for e in self.executions)
        durations = [e.get("duration_seconds", 0) for e in self.executions if e.get("duration_seconds")]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_executions": len(self.executions),
            "total_events": total_events,
            "average_duration_seconds": avg_duration,
            "min_duration_seconds": min(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


async def execute_workflow(workflow, task: str, context: Optional[Dict] = None) -> List[Dict]:
    """
    Execute workflow and collect all events.

    Args:
        workflow: Magentic workflow instance
        task: Task description
        context: Optional context

    Returns:
        List of all events

    Example:
        >>> workflow = create_soc_workflow()
        >>> events = await execute_workflow(workflow, "Analyze this alert")
        >>> print(f"Collected {len(events)} events")
    """
    executor = WorkflowExecutor(workflow)
    events = []

    async for event in executor.run_workflow(task, context):
        events.append(event)

    return events
