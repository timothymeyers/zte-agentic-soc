"""
Magentic orchestrator setup for Agentic SOC.

Implements magentic workflow creation with clear plugin point for alternative strategies.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from agent_framework import ChatAgent, MagenticBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

from src.shared.auth import get_project_credential, get_project_endpoint
from src.shared.logging import get_logger

logger = get_logger(__name__, module="orchestrator")


class SOCOrchestrator:
    """
    SOC workflow orchestrator using magentic strategy (MVP).

    This class provides a clear plugin point for changing orchestration strategies.
    The create_workflow() method can be replaced with alternative implementations
    (sequential, concurrent, custom, Azure Durable Functions) by modifying this class.
    
    Uses agent_framework's ChatAgent with OpenAIChatClient for agents.
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
        
        # Store credential for cleanup
        self._credential = None

        logger.info(
            "SOCOrchestrator initialized",
            strategy="magentic",
            max_rounds=max_round_count,
            max_stalls=max_stall_count,
        )
    
    def _load_agent_instructions(self, filename: str) -> str:
        """
        Load agent instructions from file.
        
        Args:
            filename: Instruction filename in agent_definitions directory
            
        Returns:
            Instructions as string
        """
        instructions_dir = Path(__file__).parent.parent / "deployment" / "agent_definitions"
        instructions_path = instructions_dir / filename
        
        if instructions_path.exists():
            with open(instructions_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            logger.warning(f"Instructions file not found: {instructions_path}")
            return f"You are a {filename.replace('_', ' ').replace('.md', '')} agent."

    async def create_workflow(self, agents: Optional[Dict[str, Any]] = None):
        """
        Create magentic workflow with ChatAgent instances.

        This is the PLUGIN POINT for orchestration strategy changes.
        To use a different orchestration approach:
        1. Replace this method implementation
        2. Return workflow object compatible with run() method
        3. Update documentation with new strategy details

        Args:
            agents: Dictionary mapping agent role to agent instances.
                   If None, creates agents automatically.

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
        logger.info("Creating magentic workflow with ChatAgent instances")

        # Get model deployment name from environment
        model_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-1-mini")
        logger.info("Using model for agents", model_id=model_id)
        
        # Create Azure credential
        credential = AzureCliCredential()
        
        # Load instructions for agents
        manager_instructions = self._load_agent_instructions("manager_instructions.md")
        triage_instructions = self._load_agent_instructions("alert_triage_instructions.md")
        
        # Create ChatAgent instances with AzureOpenAIChatClient
        logger.info("Creating manager agent")
        manager_agent = ChatAgent(
            name="soc-manager",
            description="SOC Manager Agent - Coordinates multi-agent security workflows",
            instructions=manager_instructions,
            chat_client=AzureOpenAIChatClient(
                credential=credential,
                deployment_name=model_id,
            ),
        )
        
        logger.info("Creating triage agent")
        triage_agent = ChatAgent(
            name="alert-triage-agent", 
            description="Alert Triage Agent - Risk assessment and prioritization",
            instructions=triage_instructions,
            chat_client=AzureOpenAIChatClient(
                credential=credential,
                deployment_name=model_id,
            ),
        )
        
        # Build participants dict
        participants = {
            "triage": triage_agent,
        }

        logger.info("Participant agents created", count=len(participants))

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
                    agent=manager_agent,  # Use 'agent' parameter for manager
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

    async def cleanup(self):
        """
        Cleanup resources (credential, client).
        
        Should be called when done with orchestrator.
        """
        if self._credential:
            await self._credential.close()
            self._credential = None
        logger.info("Orchestrator resources cleaned up")

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


async def create_soc_workflow(
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
        >>> import asyncio
        >>> async def main():
        ...     workflow = await create_soc_workflow()
        ...     async for event in workflow.run("Analyze this alert: ..."):
        ...         print(event)
        >>> asyncio.run(main())
    """
    orchestrator = SOCOrchestrator(
        max_round_count=max_round_count,
        max_stall_count=max_stall_count,
        max_reset_count=max_reset_count,
    )
    
    workflow = await orchestrator.create_workflow()
    return workflow


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
