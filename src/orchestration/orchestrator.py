"""
Magentic orchestrator setup for Agentic SOC.

Implements magentic workflow creation with clear plugin point for alternative strategies.
"""

import os
from typing import Any, Dict, Optional

from agent_framework import MagenticBuilder
from agent_framework.azure import AzureAIClient
from azure.identity.aio import AzureCliCredential

from src.shared.auth import get_project_credential, get_project_endpoint
from src.shared.logging import get_logger

logger = get_logger(__name__, module="orchestrator")


class ManagerAgentWrapper:
    """
    Wraps a Foundry agent to add planning capabilities for Magentic orchestration.
    
    Acts as a proxy that implements the AgentProtocol for Magentic compatibility.
    """

    def __init__(self, foundry_agent):
        """
        Initialize wrapper with a Foundry agent.
        
        Args:
            foundry_agent: AIProjectAgent instance from azure-ai-projects SDK
        """
        self._agent = foundry_agent
        self._name = getattr(foundry_agent, 'name', 'manager')

    async def run(self, messages=None, *, thread=None, **kwargs):
        """
        Execute agent with messages - delegates to Foundry agent.
        
        Args:
            messages: Messages to send to agent
            thread: Optional thread for conversation
            **kwargs: Additional arguments
            
        Returns:
            Agent response
        """
        # For Foundry agents, we need to use the agents API properly
        # The agent is an AIProjectAgent which uses the create_message pattern
        try:
            response = self._agent.run(messages, thread=thread, **kwargs) if hasattr(self._agent, 'run') else str(messages)
            return response
        except Exception as e:
            logger.warning("Error executing manager agent", error=str(e))
            raise

    async def run_stream(self, messages=None, *, thread=None, **kwargs):
        """Stream agent execution - delegates to Foundry agent."""
        try:
            if hasattr(self._agent, 'run_stream'):
                async for event in await self._agent.run_stream(messages=messages, thread=thread, **kwargs):
                    yield event
            else:
                yield await self._agent.run(messages=messages, thread=thread, **kwargs)
        except Exception as e:
            logger.warning("Error streaming manager agent", error=str(e))
            raise


class SOCOrchestrator:
    """
    SOC workflow orchestrator using magentic strategy (MVP).

    This class provides a clear plugin point for changing orchestration strategies.
    The create_workflow() method can be replaced with alternative implementations
    (sequential, concurrent, custom, Azure Durable Functions) by modifying this class.
    
    Uses agent_framework's AzureAIClient (v2 API) for agent-compatible agents.
    """

    def __init__(
        self,
        project_endpoint: Optional[str] = None,
        max_round_count: int = 10,
        max_stall_count: int = 3,
        max_reset_count: int = 2,
    ):
        """
        Initialize SOC orchestrator.

        Args:
            project_endpoint: Microsoft Foundry project endpoint.
                            Defaults to AZURE_AI_FOUNDRY_PROJECT_ENDPOINT env var.
            max_round_count: Maximum collaboration rounds (default: 10)
            max_stall_count: Rounds without progress before intervention (default: 3)
            max_reset_count: Maximum plan resets allowed (default: 2)
        """
        self.project_endpoint = project_endpoint or get_project_endpoint()
        self.credential = get_project_credential()

        self.max_round_count = max_round_count
        self.max_stall_count = max_stall_count
        self.max_reset_count = max_reset_count

        logger.info(
            "SOCOrchestrator initialized",
            strategy="magentic",
            max_rounds=max_round_count,
            max_stalls=max_stall_count,
        )

    async def discover_agents_async(self) -> Dict[str, Any]:
        """
        Discover existing agents in Microsoft Foundry using AzureAIClient.
        
        Retrieves existing agents by name from the Azure AI Foundry project.
        Uses AzureAIClient to wrap agents so they implement AgentProtocol.
        
        Returns:
            Dictionary mapping agent role to AzureAIClient agent instances
            that implement AgentProtocol for use with Magentic workflows.

        Note:
            Agent roles: manager, triage, hunting, response, intelligence
        """
        logger.info("Discovering existing agents")

        agents = {}
        agent_mapping = {
            "manager": "soc-manager",
            "triage": "alert-triage-agent",
            "hunting": "threat-hunting-agent",
            "response": "incident-response-agent",
            "intelligence": "threat-intelligence-agent",
        }

        # Set environment variable for AzureAIClient (it looks for AZURE_AI_PROJECT_ENDPOINT)
        os.environ["AZURE_AI_PROJECT_ENDPOINT"] = self.project_endpoint

        # Create async credential for AzureAIClient
        async with AzureCliCredential() as credential:
            ai_client = AzureAIClient(
                credential=credential
            )
            
            for role, name in agent_mapping.items():
                try:
                    # Load existing agent by name using AzureAIClient
                    # use_latest_version=True tells it to load existing agent, not create new one
                    agent = ai_client.create_agent(
                        name=name,
                        use_latest_version=True
                    )
                    
                    agents[role] = agent
                    logger.info("Agent discovered", role=role, name=name)
                    
                except Exception as e:
                    logger.warning(
                        "Agent not found",
                        role=role,
                        name=name,
                        error=str(e),
                    )

        if not agents:
            logger.error("No agents discovered")
            raise ValueError("No agents found in Microsoft Foundry project")

        logger.info("Agent discovery complete", agent_count=len(agents))
        return agents

    async def create_workflow(self, agents: Optional[Dict[str, Any]] = None):
        """
        Create magentic workflow with agent-framework compatible agents.

        This is the PLUGIN POINT for orchestration strategy changes.
        To use a different orchestration approach:
        1. Replace this method implementation
        2. Return workflow object compatible with run() method
        3. Update documentation with new strategy details

        Args:
            agents: Dictionary mapping agent role to agent instances.
                   If None, discovers agents automatically.

        Returns:
            Magentic workflow instance

        Alternative Strategies (Future):
        - Sequential: Execute agents in fixed order
        - Concurrent: Run independent agents in parallel
        - Custom: Implement domain-specific orchestration logic
        - Durable Functions: Use Azure Durable Functions for stateful workflows

        Example Migration:
            # To switch from magentic to sequential:
            # 1. Replace MagenticBuilder with SequentialBuilder
            # 2. Define agent execution order
            # 3. Update max_round_count → max_steps
        """
        if agents is None:
            agents = await self.discover_agents_async()

        logger.info("Creating magentic workflow", agent_count=len(agents))

        # Get manager agent (required for magentic)
        if "manager" not in agents:
            raise ValueError("Manager agent not found - required for magentic orchestration")

        manager_agent = agents["manager"]
        
        # Manager agent from Foundry already implements necessary protocol
        # Pass it directly to Magentic - don't wrap it
        manager_executor = manager_agent

        # Build participant dict (exclude manager from participants)
        # Agents from AzureAIClient already implement AgentProtocol
        participants = {
            role: agent
            for role, agent in agents.items()
            if role != "manager"
        }

        if not participants:
            logger.warning("No participant agents found - workflow will have limited functionality")

        # =====================================================================
        # PLUGIN POINT: Magentic Orchestration (MVP Strategy)
        # =====================================================================
        # To change orchestration strategy, replace the code below with
        # alternative implementation (sequential, concurrent, custom, etc.)
        # =====================================================================

        try:
            workflow = (
                MagenticBuilder()
                .participants(**participants)  # Agents implement AgentProtocol
                .with_standard_manager(
                    manager=manager_executor,  # Manager with planning support
                    max_round_count=self.max_round_count,
                    max_stall_count=self.max_stall_count,
                    max_reset_count=self.max_reset_count,
                )
                .build()
            )

            logger.info(
                "Magentic workflow created",
                participants=list(participants.keys()),
                manager="manager",
            )

            return workflow

        except Exception as e:
            logger.error(
                "Failed to create workflow",
                error=str(e),
                exc_info=True,
            )
            raise

    def get_workflow_config(self) -> Dict:
        """
        Get current workflow configuration.

        Returns:
            Configuration dictionary

        Useful for:
        - Logging workflow parameters
        - Auditing orchestration strategy
        - Comparing different configurations
        """
        return {
            "strategy": "magentic",
            "max_round_count": self.max_round_count,
            "max_stall_count": self.max_stall_count,
            "max_reset_count": self.max_reset_count,
            "project_endpoint": self.project_endpoint,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def create_soc_workflow(
    max_round_count: int = 10,
    max_stall_count: int = 3,
    max_reset_count: int = 2,
):
    """
    Create SOC workflow with default configuration.

    NOTE: This is a sync wrapper - callers should handle async creation.

    Args:
        max_round_count: Maximum collaboration rounds (default: 10)
        max_stall_count: Rounds without progress before intervention (default: 3)
        max_reset_count: Maximum plan resets allowed (default: 2)

    Returns:
        A coroutine that, when awaited, returns a Workflow instance

    Example:
        >>> import asyncio
        >>> async def main():
        ...     workflow = await create_soc_workflow()
        ...     async for event in workflow.run("Analyze this alert: ..."):
        ...         print(event)
        >>> asyncio.run(main())
    """
    async def _create():
        orchestrator = SOCOrchestrator(
            max_round_count=max_round_count,
            max_stall_count=max_stall_count,
            max_reset_count=max_reset_count,
        )
        return await orchestrator.create_workflow()
    
    return _create()


# =============================================================================
# Orchestration Strategy Documentation
# =============================================================================

"""
ORCHESTRATION STRATEGY: Magentic (MVP)

Current Implementation:
- Strategy: Magentic orchestration with manager-driven agent selection
- Manager: SOC_Manager agent coordinates workflow
- Participants: Triage, Hunting, Response, Intelligence agents
- Selection: Dynamic - manager chooses next agent based on context
- Benefits: Flexible, handles uncertainty, built-in human-in-loop support

Plugin Point: src/orchestration/orchestrator.py → create_workflow()

Alternative Strategies (Future):

1. Sequential Orchestration:
   - Fixed agent execution order
   - Predictable, simple to debug
   - Best for: Well-defined workflows (e.g., always Triage → Intel → Response)
   - Implementation: Replace MagenticBuilder with custom sequential executor

2. Concurrent Orchestration:
   - Run independent agents in parallel
   - Faster execution for independent tasks
   - Best for: Tasks without dependencies (e.g., parallel hunting queries)
   - Implementation: Use asyncio.gather() with agent invocations

3. Custom Orchestration:
   - Domain-specific logic and rules
   - Full control over agent coordination
   - Best for: Complex conditional logic, specialized workflows
   - Implementation: Custom orchestrator class with state machine

4. Azure Durable Functions:
   - Stateful, serverless orchestration
   - Built-in retry, timeout handling
   - Best for: Production scale, long-running workflows
   - Implementation: Durable Functions with activity functions per agent

Migration Guide:
1. Identify target strategy based on requirements
2. Update create_workflow() in SOCOrchestrator class
3. Test with existing demo scenarios
4. Update documentation and configuration
5. Consider backward compatibility for existing workflows

Research Task T095 will evaluate these alternatives for production deployment.
"""
