"""
Mock Microsoft Defender XDR API client for MVP demonstration.

This module simulates Defender XDR API operations for containment actions
like endpoint isolation, account disabling, and IP blocking.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from src.shared.schemas import ActionType
from src.shared.logging import get_logger


logger = get_logger(__name__)


class MockDefenderAction:
    """Represents a containment action in Defender XDR."""
    
    def __init__(
        self,
        action_id: UUID,
        action_type: ActionType,
        target_entity: str,
        status: str = "Pending"
    ):
        """
        Initialize mock Defender action.
        
        Args:
            action_id: Unique action ID
            action_type: Type of action
            target_entity: Target entity identifier
            status: Action status
        """
        self.action_id = action_id
        self.action_type = action_type
        self.target_entity = target_entity
        self.status = status
        self.created_time = datetime.utcnow()
        self.completed_time: Optional[datetime] = None
        self.result_message: Optional[str] = None


class MockDefenderClient:
    """Mock client for Microsoft Defender XDR API operations."""
    
    def __init__(self):
        """Initialize mock Defender client."""
        self._actions: Dict[UUID, MockDefenderAction] = {}
        self._isolated_endpoints: set[str] = set()
        self._disabled_accounts: set[str] = set()
        self._blocked_ips: set[str] = set()
        logger.info("Mock Defender XDR client initialized")
    
    async def isolate_endpoint(
        self,
        device_name: str,
        isolation_type: str = "Full"
    ) -> UUID:
        """
        Isolate an endpoint from the network.
        
        Args:
            device_name: Name of the device to isolate
            isolation_type: Type of isolation (Full or Selective)
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.ISOLATE_ENDPOINT,
            target_entity=device_name,
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"Device {device_name} isolated successfully"
        
        self._actions[action_id] = action
        self._isolated_endpoints.add(device_name)
        
        logger.info(
            "mock_endpoint_isolated",
            action_id=str(action_id),
            device_name=device_name,
            isolation_type=isolation_type
        )
        
        return action_id
    
    async def release_endpoint(self, device_name: str) -> UUID:
        """
        Release an endpoint from isolation.
        
        Args:
            device_name: Name of the device to release
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.ISOLATE_ENDPOINT,
            target_entity=device_name,
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"Device {device_name} released from isolation"
        
        self._actions[action_id] = action
        if device_name in self._isolated_endpoints:
            self._isolated_endpoints.remove(device_name)
        
        logger.info("mock_endpoint_released", action_id=str(action_id), device_name=device_name)
        
        return action_id
    
    async def disable_account(self, account_upn: str) -> UUID:
        """
        Disable a user account.
        
        Args:
            account_upn: User principal name of the account
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.DISABLE_ACCOUNT,
            target_entity=account_upn,
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"Account {account_upn} disabled successfully"
        
        self._actions[action_id] = action
        self._disabled_accounts.add(account_upn)
        
        logger.info("mock_account_disabled", action_id=str(action_id), account_upn=account_upn)
        
        return action_id
    
    async def enable_account(self, account_upn: str) -> UUID:
        """
        Enable a user account.
        
        Args:
            account_upn: User principal name of the account
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.DISABLE_ACCOUNT,
            target_entity=account_upn,
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"Account {account_upn} enabled successfully"
        
        self._actions[action_id] = action
        if account_upn in self._disabled_accounts:
            self._disabled_accounts.remove(account_upn)
        
        logger.info("mock_account_enabled", action_id=str(action_id), account_upn=account_upn)
        
        return action_id
    
    async def block_ip(self, ip_address: str, duration_hours: int = 24) -> UUID:
        """
        Block an IP address.
        
        Args:
            ip_address: IP address to block
            duration_hours: Duration of the block in hours
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.BLOCK_IP,
            target_entity=ip_address,
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"IP {ip_address} blocked for {duration_hours} hours"
        
        self._actions[action_id] = action
        self._blocked_ips.add(ip_address)
        
        logger.info(
            "mock_ip_blocked",
            action_id=str(action_id),
            ip_address=ip_address,
            duration_hours=duration_hours
        )
        
        return action_id
    
    async def unblock_ip(self, ip_address: str) -> UUID:
        """
        Unblock an IP address.
        
        Args:
            ip_address: IP address to unblock
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.BLOCK_IP,
            target_entity=ip_address,
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"IP {ip_address} unblocked"
        
        self._actions[action_id] = action
        if ip_address in self._blocked_ips:
            self._blocked_ips.remove(ip_address)
        
        logger.info("mock_ip_unblocked", action_id=str(action_id), ip_address=ip_address)
        
        return action_id
    
    async def quarantine_file(self, file_hash: str, device_name: str) -> UUID:
        """
        Quarantine a file on a device.
        
        Args:
            file_hash: Hash of the file to quarantine
            device_name: Name of the device
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.QUARANTINE_FILE,
            target_entity=f"{file_hash}@{device_name}",
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"File {file_hash} quarantined on {device_name}"
        
        self._actions[action_id] = action
        
        logger.info(
            "mock_file_quarantined",
            action_id=str(action_id),
            file_hash=file_hash,
            device_name=device_name
        )
        
        return action_id
    
    async def terminate_process(self, process_id: int, device_name: str) -> UUID:
        """
        Terminate a process on a device.
        
        Args:
            process_id: Process ID to terminate
            device_name: Name of the device
        
        Returns:
            UUID: Action ID
        """
        action_id = uuid4()
        action = MockDefenderAction(
            action_id=action_id,
            action_type=ActionType.TERMINATE_PROCESS,
            target_entity=f"{process_id}@{device_name}",
            status="Completed"
        )
        action.completed_time = datetime.utcnow()
        action.result_message = f"Process {process_id} terminated on {device_name}"
        
        self._actions[action_id] = action
        
        logger.info(
            "mock_process_terminated",
            action_id=str(action_id),
            process_id=process_id,
            device_name=device_name
        )
        
        return action_id
    
    async def get_action_status(self, action_id: UUID) -> Optional[MockDefenderAction]:
        """
        Get status of an action.
        
        Args:
            action_id: Action ID
        
        Returns:
            Optional[MockDefenderAction]: Action if found, None otherwise
        """
        return self._actions.get(action_id)
    
    def is_endpoint_isolated(self, device_name: str) -> bool:
        """
        Check if an endpoint is currently isolated.
        
        Args:
            device_name: Device name
        
        Returns:
            bool: True if isolated, False otherwise
        """
        return device_name in self._isolated_endpoints
    
    def is_account_disabled(self, account_upn: str) -> bool:
        """
        Check if an account is currently disabled.
        
        Args:
            account_upn: User principal name
        
        Returns:
            bool: True if disabled, False otherwise
        """
        return account_upn in self._disabled_accounts
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Check if an IP is currently blocked.
        
        Args:
            ip_address: IP address
        
        Returns:
            bool: True if blocked, False otherwise
        """
        return ip_address in self._blocked_ips


# Global mock Defender client instance
_defender_client: Optional[MockDefenderClient] = None


def get_defender_client() -> MockDefenderClient:
    """
    Get global mock Defender XDR client instance.
    
    Returns:
        MockDefenderClient: Global mock Defender client
    """
    global _defender_client
    if _defender_client is None:
        _defender_client = MockDefenderClient()
    return _defender_client
