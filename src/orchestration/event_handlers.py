"""
Event handlers for orchestration layer.

This module provides event handler registration and management for
alert ingestion, triage completion, and other agent events.
"""

from typing import Callable, Awaitable, Dict, List, Optional
from enum import Enum

from src.shared.schemas import SecurityAlert
from src.shared.logging import get_logger


logger = get_logger(__name__)


class EventType(str, Enum):
    """Types of events in the system."""
    ALERT_INGESTION = "alert_ingestion"
    TRIAGE_COMPLETE = "triage_complete"
    HIGH_RISK_ALERT = "high_risk_alert"
    INCIDENT_CREATED = "incident_created"
    RESPONSE_ACTION_REQUIRED = "response_action_required"
    HUNTING_QUERY_COMPLETE = "hunting_query_complete"
    SCHEDULED_HUNT = "scheduled_hunt"
    DAILY_BRIEFING = "daily_briefing"


EventHandler = Callable[[Dict], Awaitable[None]]


class EventBus:
    """Simple event bus for agent coordination."""
    
    def __init__(self):
        """Initialize event bus."""
        self._handlers: Dict[EventType, List[EventHandler]] = {
            event_type: [] for event_type in EventType
        }
        logger.info("Event bus initialized")
    
    def register(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        self._handlers[event_type].append(handler)
        logger.info(
            "event_handler_registered",
            event_type=event_type,
            handler_name=handler.__name__
        )
    
    async def publish(
        self,
        event_type: EventType,
        event_data: Dict
    ) -> None:
        """
        Publish an event to all registered handlers.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(
                "no_handlers_for_event",
                event_type=event_type
            )
            return
        
        logger.info(
            "event_published",
            event_type=event_type,
            handler_count=len(handlers)
        )
        
        for handler in handlers:
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(
                    "event_handler_error",
                    event_type=event_type,
                    handler_name=handler.__name__,
                    error=str(e),
                    exc_info=True
                )


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get global event bus instance.
    
    Returns:
        EventBus: Global event bus
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def handle_alert_ingestion(alert: SecurityAlert) -> None:
    """
    Handle alert ingestion event.
    
    Args:
        alert: Ingested alert
    """
    event_bus = get_event_bus()
    await event_bus.publish(
        EventType.ALERT_INGESTION,
        {
            "alert_id": str(alert.SystemAlertId),
            "alert_name": alert.AlertName,
            "severity": alert.Severity,
            "alert": alert.model_dump()
        }
    )


async def handle_triage_complete(alert_id: str, triage_result: Dict) -> None:
    """
    Handle triage completion event.
    
    Args:
        alert_id: Alert ID
        triage_result: Triage result data
    """
    event_bus = get_event_bus()
    await event_bus.publish(
        EventType.TRIAGE_COMPLETE,
        {
            "alert_id": alert_id,
            "triage_result": triage_result
        }
    )


async def handle_high_risk_alert(alert_id: str, risk_score: int) -> None:
    """
    Handle high-risk alert detection event.
    
    Args:
        alert_id: Alert ID
        risk_score: Risk score (0-100)
    """
    event_bus = get_event_bus()
    await event_bus.publish(
        EventType.HIGH_RISK_ALERT,
        {
            "alert_id": alert_id,
            "risk_score": risk_score
        }
    )


async def handle_incident_created(incident_id: str, severity: str) -> None:
    """
    Handle incident creation event.
    
    Args:
        incident_id: Incident ID
        severity: Incident severity
    """
    event_bus = get_event_bus()
    await event_bus.publish(
        EventType.INCIDENT_CREATED,
        {
            "incident_id": incident_id,
            "severity": severity
        }
    )
