#!/usr/bin/env python3
"""
Cosmos DB initialization script.

This script creates the required Cosmos DB database and collections
for the Agentic SOC MVP with appropriate partition keys and TTL settings.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.cosmos import initialize_cosmos_client
from src.shared.logging import get_logger, configure_logging


logger = get_logger(__name__)


async def setup_cosmos_db():
    """Initialize Cosmos DB database and collections."""
    
    # Get environment variables
    endpoint = os.getenv("COSMOS_DB_ENDPOINT")
    database_name = os.getenv("COSMOS_DB_DATABASE", "agentic-soc")
    key = os.getenv("COSMOS_DB_KEY")  # Optional, uses Managed Identity if not provided
    
    if not endpoint:
        logger.error("COSMOS_DB_ENDPOINT environment variable not set")
        sys.exit(1)
    
    logger.info(f"Initializing Cosmos DB at {endpoint}")
    
    try:
        # Initialize Cosmos DB client (creates database and collections)
        client = await initialize_cosmos_client(
            endpoint=endpoint,
            database_name=database_name,
            key=key
        )
        
        logger.info("Cosmos DB initialization complete")
        logger.info(f"Database: {database_name}")
        logger.info("Collections created:")
        logger.info("  - alerts (partition: /Severity, TTL: 5 days)")
        logger.info("  - incidents (partition: /Status, TTL: 30 days)")
        logger.info("  - triage_results (partition: /AlertId, TTL: 30 days)")
        logger.info("  - response_actions (partition: /IncidentId, TTL: 90 days)")
        logger.info("  - agent_state (partition: /AgentName, no TTL)")
        logger.info("  - audit_logs (partition: /EventType, TTL: 365 days)")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    configure_logging(log_level="INFO", json_output=False)
    
    # Run setup
    asyncio.run(setup_cosmos_db())
