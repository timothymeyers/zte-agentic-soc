"""
Mock Microsoft Sentinel API client for MVP demonstration.

This module simulates Sentinel API operations using mock data,
providing CRUD operations for SecurityAlert objects.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from src.shared.schemas import SecurityAlert, SeverityLevel
from src.shared.logging import get_logger


logger = get_logger(__name__)


class MockSentinelClient:
    """Mock client for Microsoft Sentinel API operations."""
    
    def __init__(self):
        """Initialize mock Sentinel client."""
        self._alerts: dict[UUID, SecurityAlert] = {}
        logger.info("Mock Sentinel client initialized")
    
    async def create_alert(self, alert: SecurityAlert) -> SecurityAlert:
        """
        Create a new alert in Sentinel.
        
        Args:
            alert: Alert to create
        
        Returns:
            SecurityAlert: Created alert
        """
        self._alerts[alert.SystemAlertId] = alert
        logger.info(
            "mock_alert_created",
            alert_id=str(alert.SystemAlertId),
            alert_name=alert.AlertName,
            severity=alert.Severity
        )
        return alert
    
    async def get_alert(self, alert_id: UUID) -> Optional[SecurityAlert]:
        """
        Get an alert by ID.
        
        Args:
            alert_id: Alert ID
        
        Returns:
            Optional[SecurityAlert]: Alert if found, None otherwise
        """
        alert = self._alerts.get(alert_id)
        if alert:
            logger.debug("mock_alert_retrieved", alert_id=str(alert_id))
        else:
            logger.debug("mock_alert_not_found", alert_id=str(alert_id))
        return alert
    
    async def list_alerts(
        self,
        severity: Optional[SeverityLevel] = None,
        limit: int = 100
    ) -> List[SecurityAlert]:
        """
        List alerts with optional filtering.
        
        Args:
            severity: Filter by severity
            limit: Maximum number of alerts to return
        
        Returns:
            List[SecurityAlert]: List of alerts
        """
        alerts = list(self._alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.Severity == severity]
        
        alerts = sorted(alerts, key=lambda a: a.TimeGenerated, reverse=True)
        
        logger.debug(
            "mock_alerts_listed",
            count=len(alerts[:limit]),
            severity_filter=severity
        )
        
        return alerts[:limit]
    
    async def update_alert(self, alert: SecurityAlert) -> SecurityAlert:
        """
        Update an existing alert.
        
        Args:
            alert: Alert to update
        
        Returns:
            SecurityAlert: Updated alert
        """
        if alert.SystemAlertId not in self._alerts:
            raise ValueError(f"Alert {alert.SystemAlertId} not found")
        
        self._alerts[alert.SystemAlertId] = alert
        logger.info("mock_alert_updated", alert_id=str(alert.SystemAlertId))
        return alert
    
    async def delete_alert(self, alert_id: UUID) -> None:
        """
        Delete an alert.
        
        Args:
            alert_id: Alert ID to delete
        """
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            logger.info("mock_alert_deleted", alert_id=str(alert_id))
        else:
            logger.warning("mock_alert_not_found_for_deletion", alert_id=str(alert_id))
    
    def get_alert_count(self) -> int:
        """
        Get total number of alerts.
        
        Returns:
            int: Number of alerts
        """
        return len(self._alerts)


# Global mock Sentinel client instance
_sentinel_client: Optional[MockSentinelClient] = None


def get_sentinel_client() -> MockSentinelClient:
    """
    Get global mock Sentinel client instance.
    
    Returns:
        MockSentinelClient: Global mock Sentinel client
    """
    global _sentinel_client
    if _sentinel_client is None:
        _sentinel_client = MockSentinelClient()
    return _sentinel_client
