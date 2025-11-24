"""
Cosmos DB client for data persistence.

This module provides a client for interacting with Azure Cosmos DB
for storing alerts, incidents, triage results, and agent state.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.cosmos import PartitionKey, exceptions
from azure.identity import DefaultAzureCredential

from src.shared.logging import get_logger


logger = get_logger(__name__)


class CosmosDBClient:
    """Client for Azure Cosmos DB operations."""
    
    def __init__(
        self,
        endpoint: str,
        database_name: str = "agentic-soc",
        key: Optional[str] = None
    ):
        """
        Initialize Cosmos DB client.
        
        Args:
            endpoint: Cosmos DB endpoint URL
            database_name: Database name
            key: Cosmos DB key (optional, uses Managed Identity if not provided)
        """
        self.endpoint = endpoint
        self.database_name = database_name
        
        # Use key if provided (as string), otherwise use DefaultAzureCredential
        if key:
            credential = key  # Cosmos DB accepts the key as a string directly
        else:
            credential = DefaultAzureCredential()
        
        self.client = AsyncCosmosClient(endpoint, credential)
        self.database = None
        self._containers: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Initialize database and containers."""
        try:
            self.database = await self.client.create_database_if_not_exists(
                id=self.database_name
            )
            logger.info(f"Connected to Cosmos DB database: {self.database_name}")
            
            # Create containers
            await self._create_containers()
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    async def _create_containers(self) -> None:
        """Create all required containers."""
        container_configs = [
            {
                "id": "alerts",
                "partition_key": PartitionKey(path="/Severity"),
                "default_ttl": 432000  # 5 days
            },
            {
                "id": "incidents",
                "partition_key": PartitionKey(path="/Status"),
                "default_ttl": 2592000  # 30 days
            },
            {
                "id": "triage_results",
                "partition_key": PartitionKey(path="/AlertId"),
                "default_ttl": 2592000  # 30 days
            },
            {
                "id": "response_actions",
                "partition_key": PartitionKey(path="/IncidentId"),
                "default_ttl": 7776000  # 90 days
            },
            {
                "id": "agent_state",
                "partition_key": PartitionKey(path="/AgentName"),
                "default_ttl": -1  # No TTL (persistent)
            },
            {
                "id": "audit_logs",
                "partition_key": PartitionKey(path="/EventType"),
                "default_ttl": 31536000  # 365 days
            }
        ]
        
        for config in container_configs:
            try:
                container = await self.database.create_container_if_not_exists(
                    id=config["id"],
                    partition_key=config["partition_key"],
                    default_ttl=config["default_ttl"]
                )
                self._containers[config["id"]] = container
                logger.info(f"Container ready: {config['id']}")
            except Exception as e:
                logger.error(f"Failed to create container {config['id']}: {e}")
                raise
    
    def get_container(self, container_name: str):
        """
        Get container by name.
        
        Args:
            container_name: Name of the container
        
        Returns:
            Container client
        
        Raises:
            KeyError: If container not found
        """
        if container_name not in self._containers:
            raise KeyError(f"Container '{container_name}' not found")
        return self._containers[container_name]
    
    async def create_item(
        self,
        container_name: str,
        item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an item in a container.
        
        Args:
            container_name: Name of the container
            item: Item to create
        
        Returns:
            Dict: Created item
        """
        container = self.get_container(container_name)
        
        # Ensure id field exists
        if "id" not in item:
            # Use appropriate ID field based on container
            id_field_map = {
                "alerts": "SystemAlertId",
                "incidents": "IncidentId",
                "triage_results": "TriageId",
                "response_actions": "ActionId",
                "agent_state": "AgentId",
                "audit_logs": "LogId"
            }
            id_field = id_field_map.get(container_name)
            if id_field and id_field in item:
                item["id"] = str(item[id_field])
        
        try:
            created_item = await container.create_item(body=item)
            logger.debug(f"Created item in {container_name}: {created_item['id']}")
            return created_item
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Item already exists in {container_name}: {item.get('id')}")
            raise
        except Exception as e:
            logger.error(f"Failed to create item in {container_name}: {e}")
            raise
    
    async def read_item(
        self,
        container_name: str,
        item_id: str,
        partition_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Read an item from a container.
        
        Args:
            container_name: Name of the container
            item_id: ID of the item
            partition_key: Partition key value
        
        Returns:
            Optional[Dict]: Item if found, None otherwise
        """
        container = self.get_container(container_name)
        
        try:
            item = await container.read_item(
                item=item_id,
                partition_key=partition_key
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Item not found in {container_name}: {item_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to read item from {container_name}: {e}")
            raise
    
    async def query_items(
        self,
        container_name: str,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        max_items: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query items from a container.
        
        Args:
            container_name: Name of the container
            query: SQL query string
            parameters: Query parameters
            max_items: Maximum number of items to return
        
        Returns:
            List[Dict]: List of items
        """
        container = self.get_container(container_name)
        
        try:
            items = []
            async for item in container.query_items(
                query=query,
                parameters=parameters or [],
                max_item_count=max_items
            ):
                items.append(item)
            
            logger.debug(f"Query returned {len(items)} items from {container_name}")
            return items
        except Exception as e:
            logger.error(f"Failed to query {container_name}: {e}")
            raise
    
    async def update_item(
        self,
        container_name: str,
        item: Dict[str, Any],
        partition_key: str
    ) -> Dict[str, Any]:
        """
        Update an item in a container.
        
        Args:
            container_name: Name of the container
            item: Item to update (must include 'id' field)
            partition_key: Partition key value
        
        Returns:
            Dict: Updated item
        """
        container = self.get_container(container_name)
        
        try:
            updated_item = await container.upsert_item(
                body=item,
                partition_key=partition_key
            )
            logger.debug(f"Updated item in {container_name}: {updated_item['id']}")
            return updated_item
        except Exception as e:
            logger.error(f"Failed to update item in {container_name}: {e}")
            raise
    
    async def delete_item(
        self,
        container_name: str,
        item_id: str,
        partition_key: str
    ) -> None:
        """
        Delete an item from a container.
        
        Args:
            container_name: Name of the container
            item_id: ID of the item
            partition_key: Partition key value
        """
        container = self.get_container(container_name)
        
        try:
            await container.delete_item(
                item=item_id,
                partition_key=partition_key
            )
            logger.debug(f"Deleted item from {container_name}: {item_id}")
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Item not found for deletion in {container_name}: {item_id}")
        except Exception as e:
            logger.error(f"Failed to delete item from {container_name}: {e}")
            raise
    
    async def close(self) -> None:
        """Close the Cosmos DB client."""
        await self.client.close()
        logger.info("Cosmos DB client closed")


# Global Cosmos DB client instance
_cosmos_client: Optional[CosmosDBClient] = None


def get_cosmos_client() -> CosmosDBClient:
    """
    Get global Cosmos DB client instance.
    
    Returns:
        CosmosDBClient: Global Cosmos DB client
    
    Raises:
        RuntimeError: If client not initialized
    """
    if _cosmos_client is None:
        raise RuntimeError(
            "Cosmos DB client not initialized. "
            "Call initialize_cosmos_client() first."
        )
    return _cosmos_client


async def initialize_cosmos_client(
    endpoint: str,
    database_name: str = "agentic-soc",
    key: Optional[str] = None
) -> CosmosDBClient:
    """
    Initialize global Cosmos DB client.
    
    Args:
        endpoint: Cosmos DB endpoint URL
        database_name: Database name
        key: Cosmos DB key (optional)
    
    Returns:
        CosmosDBClient: Initialized client
    """
    global _cosmos_client
    _cosmos_client = CosmosDBClient(endpoint, database_name, key)
    await _cosmos_client.initialize()
    return _cosmos_client
