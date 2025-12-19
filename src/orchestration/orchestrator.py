"""
Magentic orchestrator setup for Agentic SOC.

Implements magentic workflow creation with clear plugin point for alternative strategies.
"""

from typing import Any, Dict, Optional

from agent_framework import MagenticBuilder
from azure.ai.projects import AIProjectClient

from src.shared.auth import get_project_credential, get_project_endpoint
from src.shared.logging import get_logger

logger = get_logger(__name__, module="orchestrator")


class SOCOrchestrator:
    """
    SOC workflow orchestrator using magentic strategy (MVP).

    This class provides a clear plugin point for changing orchestration strategies.
    The create_workflow() method can be replaced with alternative implementations
    (sequential, concurrent, custom, Azure Durable Functions) by modifying this class.
    
    Uses azure-ai-projects SDK (2.0.0b1+) with AIProjectClient for agent management.
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

        # Initialize AIProjectClient (azure-ai-projects 2.0.0b1+)
        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=self.credential
        )

        logger.info(
            "SOCOrchestrator initialized",
            strategy="magentic",
            max_rounds=max_round_count,
            max_stalls=max_stall_count,
        )

    def discover_agents(self) -> Dict[str, Any]:
        """
        Discover deployed agents in Microsoft Foundry.
        
        Uses client.agents.get(agent_name=...) from azure-ai-projects 2.0.

        Returns:
            Dictionary mapping agent role to agent object

        Note:
            Agent roles: manager, triage, hunting, response, intelligence
        """
        logger.info("Discovering agents")

        agents = {}
        agent_mapping = {
            "manager": "SOC_Manager",
            "triage": "AlertTriageAgent",
            "hunting": "ThreatHuntingAgent",
            "response": "IncidentResponseAgent",
            "intelligence": "ThreatIntelligenceAgent",
        }

        for role, name in agent_mapping.items():
            try:
                # Use get() method with agent_name parameter (azure-ai-projects 2.0+)
                agent = self.client.agents.get(agent_name=name)
                agents[role] = agent
                logger.info("Agent discovered", role=role, name=name, agent_id=agent.id, version=agent.version)
            except Exception as e:
                logger.warning(
                    "Agent not found or error",
                    role=role,
                    name=name,
                    error=str(e),
                )

        if not agents:
            logger.error("No agents discovered")
            raise ValueError("No agents found in Microsoft Foundry project")

        logger.info("Agent discovery complete", agent_count=len(agents))
        return agents

    def create_workflow(self, agents: Optional[Dict[str, Any]] = None):
        """
        Create magentic workflow with discovered agents.

        This is the PLUGIN POINT for orchestration strategy changes.
        To use a different orchestration approach:
        1. Replace this method implementation
        2. Return workflow object compatible with run() method
        3. Update documentation with new strategy details

        Args:
            agents: Dictionary mapping agent role to Agent instance.
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
            agents = self.discover_agents()

        logger.info("Creating magentic workflow", agent_count=len(agents))

        # Get manager agent (required for magentic)
        if "manager" not in agents:
            raise ValueError("Manager agent not found - required for magentic orchestration")

        manager_agent = agents["manager"]

        # Build participant dict (exclude manager from participants)
        participants = {
            role: agent
            for role, agent in agents.items()
            if role != "manager"
        }

        if not participants:
            logger.warning("No participant agents found - workflow will have limited functionality")

        # Get OpenAI client for chat completions
        openai_client = self.client.get_openai_client()
        chat_client = openai_client.chat.completions

        # =====================================================================
        # PLUGIN POINT: Magentic Orchestration (MVP Strategy)
        # =====================================================================
        # To change orchestration strategy, replace the code below with
        # alternative implementation (sequential, concurrent, custom, etc.)
        # =====================================================================

        try:
            workflow = (
                MagenticBuilder()
                .participants(**participants)  # Specialized agents
                .with_standard_manager(
                    chat_client=chat_client,
                    max_round_count=self.max_round_count,
                    max_stall_count=self.max_stall_count,
                    max_reset_count=self.max_reset_count,
                )
                .build()
            )

            logger.info(
                "Magentic workflow created",
                participants=list(participants.keys()),
                manager=manager_agent.name,
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

    Args:
        max_round_count: Maximum collaboration rounds (default: 10)
        max_stall_count: Rounds without progress before intervention (default: 3)
        max_reset_count: Maximum plan resets allowed (default: 2)

    Returns:
        Workflow instance ready for execution

    Example:
        >>> workflow = create_soc_workflow()
        >>> async for event in workflow.run("Analyze this alert: ..."):
        ...     print(event)
    """
    orchestrator = SOCOrchestrator(
        max_round_count=max_round_count,
        max_stall_count=max_stall_count,
        max_reset_count=max_reset_count,
    )

    return orchestrator.create_workflow()


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
