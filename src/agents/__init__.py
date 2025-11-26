"""
Agentic SOC - Agent Management Module.

This module provides global agent management for the Agentic SOC system.
Agents are initialized once at application startup and reused throughout
the application lifecycle.

This follows the MVP refactor pattern for Microsoft Foundry native agents,
where agents are defined declaratively in YAML files and managed centrally.
"""

import os
from typing import Optional

from src.agents.foundry_native_agent import FoundryNativeAgent
from src.shared.logging import get_logger

logger = get_logger(__name__)

# Global agent instances
_alert_triage_agent: Optional[FoundryNativeAgent] = None


async def initialize_agents() -> None:
    """
    Initialize all agents at application startup.
    
    This function creates persistent agent instances that are reused
    throughout the application. Agents are loaded from YAML definitions
    in the agents/ directory.
    
    Usage:
        ```python
        # At application startup
        await initialize_agents()
        
        # Later, get agent instances
        triage_agent = get_alert_triage_agent()
        ```
    """
    global _alert_triage_agent
    
    logger.info("Initializing Foundry native agents...")
    
    # Determine agents directory path
    # Assuming this file is at src/agents/__init__.py
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(os.path.dirname(current_dir))
    agents_dir = os.path.join(project_root, 'agents')
    
    logger.debug(f"Agents directory: {agents_dir}")
    
    # Initialize Alert Triage Agent
    alert_triage_yaml = os.path.join(agents_dir, 'alert-triage-agent.yaml')
    
    if os.path.exists(alert_triage_yaml):
        logger.info(f"Initializing Alert Triage Agent from {alert_triage_yaml}")
        _alert_triage_agent = FoundryNativeAgent(agent_yaml_path=alert_triage_yaml)
        await _alert_triage_agent.initialize()
        logger.info(f"✓ Alert Triage Agent initialized: {_alert_triage_agent.name} v{_alert_triage_agent.version}")
    else:
        logger.warning(f"Alert Triage Agent YAML not found: {alert_triage_yaml}")
        _alert_triage_agent = None
    
    logger.info("✓ All agents initialized and ready")


def get_alert_triage_agent() -> Optional[FoundryNativeAgent]:
    """
    Get the global Alert Triage Agent instance.
    
    Returns:
        FoundryNativeAgent: The initialized alert triage agent, or None if not initialized
        
    Raises:
        RuntimeError: If agents have not been initialized yet
    """
    if _alert_triage_agent is None:
        raise RuntimeError(
            "alert-triage-agent not initialized. "
            "Call initialize_agents() at application startup first."
        )
    return _alert_triage_agent


async def cleanup_agents() -> None:
    """
    Clean up all agent resources.
    
    This function should be called at application shutdown to properly
    close all agent connections and release resources.
    """
    global _alert_triage_agent
    
    logger.info("Cleaning up agent resources...")
    
    if _alert_triage_agent is not None:
        await _alert_triage_agent.close()
        _alert_triage_agent = None
        logger.debug("Alert Triage Agent cleaned up")
    
    logger.info("✓ All agent resources cleaned up")


# For backward compatibility, also export the existing AlertTriageAgent
# This allows gradual migration of existing code
from src.agents.alert_triage_agent import AlertTriageAgent, get_triage_agent

__all__ = [
    'FoundryNativeAgent',
    'initialize_agents',
    'get_alert_triage_agent',
    'cleanup_agents',
    'AlertTriageAgent',  # Backward compatibility
    'get_triage_agent',  # Backward compatibility
]
