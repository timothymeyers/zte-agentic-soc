"""
Audit logging service for immutable compliance trail.

This module provides audit logging functionality that writes to Cosmos DB
for all agent actions and human interactions.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from src.shared.schemas import (
    AuditLog,
    EventType,
    ActorType,
    AuditResult,
    AuditTargetEntity
)
from src.shared.logging import get_logger, get_correlation_id


logger = get_logger(__name__)


class AuditService:
    """Service for creating and managing audit logs."""
    
    def __init__(self, cosmos_client=None):
        """
        Initialize audit service.
        
        Args:
            cosmos_client: Cosmos DB client for persistence (optional for MVP)
        """
        self.cosmos_client = cosmos_client
        self._audit_logs: list[AuditLog] = []  # In-memory storage for MVP
    
    async def log_agent_action(
        self,
        agent_name: str,
        action: str,
        target_entity_type: str,
        target_entity_id: str,
        result: AuditResult,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an agent action.
        
        Args:
            agent_name: Name of the agent performing the action
            action: Action being performed (e.g., "TriagedAlert", "ExecutedContainment")
            target_entity_type: Type of entity being acted upon
            target_entity_id: ID of the target entity
            result: Result of the action
            details: Additional details about the action
            error_message: Error message if action failed
        
        Returns:
            AuditLog: Created audit log entry
        """
        audit_log = AuditLog(
            EventType=EventType.AGENT_ACTION,
            Actor=agent_name,
            ActorType=ActorType.AGENT,
            Action=action,
            TargetEntity=AuditTargetEntity(
                EntityType=target_entity_type,
                EntityId=target_entity_id
            ),
            Details=details or {},
            Result=result,
            ErrorMessage=error_message,
            CorrelationId=UUID(get_correlation_id())
        )
        
        await self._persist_audit_log(audit_log)
        
        logger.info(
            "audit_log_created",
            event_type=audit_log.EventType,
            actor=audit_log.Actor,
            action=audit_log.Action,
            result=audit_log.Result
        )
        
        return audit_log
    
    async def log_human_action(
        self,
        user_upn: str,
        action: str,
        target_entity_type: str,
        target_entity_id: str,
        result: AuditResult,
        details: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a human action.
        
        Args:
            user_upn: User principal name of the person performing the action
            action: Action being performed
            target_entity_type: Type of entity being acted upon
            target_entity_id: ID of the target entity
            result: Result of the action
            details: Additional details about the action
            client_ip: Client IP address
            user_agent: User agent string
        
        Returns:
            AuditLog: Created audit log entry
        """
        audit_log = AuditLog(
            EventType=EventType.HUMAN_ACTION,
            Actor=user_upn,
            ActorType=ActorType.USER,
            Action=action,
            TargetEntity=AuditTargetEntity(
                EntityType=target_entity_type,
                EntityId=target_entity_id
            ),
            Details=details or {},
            Result=result,
            CorrelationId=UUID(get_correlation_id()),
            ClientIP=client_ip,
            UserAgent=user_agent
        )
        
        await self._persist_audit_log(audit_log)
        
        logger.info(
            "audit_log_created",
            event_type=audit_log.EventType,
            actor=audit_log.Actor,
            action=audit_log.Action,
            result=audit_log.Result
        )
        
        return audit_log
    
    async def log_system_event(
        self,
        system_component: str,
        action: str,
        target_entity_type: str,
        target_entity_id: str,
        result: AuditResult,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log a system event.
        
        Args:
            system_component: Name of the system component
            action: Action or event
            target_entity_type: Type of entity
            target_entity_id: ID of the target entity
            result: Result of the event
            details: Additional details
        
        Returns:
            AuditLog: Created audit log entry
        """
        audit_log = AuditLog(
            EventType=EventType.SYSTEM_EVENT,
            Actor=system_component,
            ActorType=ActorType.SYSTEM,
            Action=action,
            TargetEntity=AuditTargetEntity(
                EntityType=target_entity_type,
                EntityId=target_entity_id
            ),
            Details=details or {},
            Result=result,
            CorrelationId=UUID(get_correlation_id())
        )
        
        await self._persist_audit_log(audit_log)
        
        logger.info(
            "audit_log_created",
            event_type=audit_log.EventType,
            actor=audit_log.Actor,
            action=audit_log.Action,
            result=audit_log.Result
        )
        
        return audit_log
    
    async def _persist_audit_log(self, audit_log: AuditLog) -> None:
        """
        Persist audit log to Cosmos DB.
        
        Args:
            audit_log: Audit log entry to persist
        
        Note:
            For MVP, stores in memory. Production will use Cosmos DB.
        """
        # MVP: Store in memory
        self._audit_logs.append(audit_log)
        
        # TODO: Production implementation
        # if self.cosmos_client:
        #     container = self.cosmos_client.get_container("audit_logs")
        #     await container.create_item(audit_log.model_dump())
    
    def get_audit_logs(
        self,
        limit: int = 100,
        actor: Optional[str] = None,
        action: Optional[str] = None
    ) -> list[AuditLog]:
        """
        Retrieve audit logs.
        
        Args:
            limit: Maximum number of logs to retrieve
            actor: Filter by actor name
            action: Filter by action name
        
        Returns:
            list[AuditLog]: List of audit log entries
        """
        logs = self._audit_logs
        
        if actor:
            logs = [log for log in logs if log.Actor == actor]
        
        if action:
            logs = [log for log in logs if log.Action == action]
        
        return logs[-limit:]


# Global audit service instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """
    Get global audit service instance.
    
    Returns:
        AuditService: Global audit service
    """
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
