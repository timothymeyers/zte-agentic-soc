"""
Agent deployment script for Agentic SOC.

Deploys AI agents to Microsoft Foundry using azure-ai-projects SDK.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

from src.shared.auth import get_project_credential, get_project_endpoint, get_openai_deployment
from src.shared.logging import get_logger

logger = get_logger(__name__, module="deployment")


class AgentDeployer:
    """
    Deploy and manage AI agents in Microsoft Foundry.
    
    Uses azure-ai-projects SDK (2.0.0b1+) with AIProjectClient for agent management.
    """

    def __init__(self, project_endpoint: Optional[str] = None, model_deployment: Optional[str] = None):
        """
        Initialize agent deployer.

        Args:
            project_endpoint: Microsoft Foundry project endpoint.
                            Defaults to AZURE_AI_FOUNDRY_PROJECT_ENDPOINT env var.
            model_deployment: OpenAI model deployment name.
                            Defaults to AZURE_OPENAI_DEPLOYMENT_NAME or
                            AZURE_AI_MODEL_DEPLOYMENT_NAME env var.
        """
        self.project_endpoint = project_endpoint or get_project_endpoint()
        self.model_deployment = model_deployment or get_openai_deployment()
        self.credential = get_project_credential()

        # Initialize AIProjectClient (azure-ai-projects 2.0.0b1+)
        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=self.credential
        )

        logger.info(
            "AgentDeployer initialized",
            project_endpoint=self.project_endpoint,
            model_deployment=self.model_deployment,
        )

    def _get_instructions_path(self) -> Path:
        """Get path to agent_definitions directory."""
        current_file = Path(__file__)
        return current_file.parent / "agent_definitions"

    def _load_instructions(self, filename: str) -> str:
        """
        Load agent instructions from markdown file.

        Args:
            filename: Name of the instruction file (e.g., "manager_instructions.md")

        Returns:
            Instruction content as string

        Raises:
            FileNotFoundError: If instruction file not found
        """
        instructions_path = self._get_instructions_path() / filename

        if not instructions_path.exists():
            raise FileNotFoundError(f"Instruction file not found: {instructions_path}")

        with open(instructions_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info("Instructions loaded", filename=filename, size=len(content))
        return content

    def deploy_agent(
        self,
        name: str,
        instructions_file: str,
        description: str,
    ) -> Any:
        """
        Deploy a specialized agent to Microsoft Foundry.
        
        Creates a new agent or updates existing agent with create_version().

        Args:
            name: Agent name
            instructions_file: Filename of instruction markdown (e.g., "triage_instructions.md")
            description: Agent description

        Returns:
            Deployed agent object (AgentObject from azure.ai.projects)
        """
        logger.info("Deploying agent", name=name, instructions_file=instructions_file)

        # Load instructions
        instructions = self._load_instructions(instructions_file)

        try:
            # Check if agent already exists
            try:
                existing_agent = self.get_agent(name)
                if existing_agent:
                    logger.info(
                        "Agent exists, creating new version",
                        agent_id=existing_agent.id,
                        name=name,
                        current_version=existing_agent.version,
                    )
                    # Update with new version
                    agent = self.client.agents.create_version(
                        agent_name=name,
                        definition=PromptAgentDefinition(
                            model=self.model_deployment,
                            instructions=instructions,
                        ),
                        description=description,
                    )
                    logger.info(
                        "Agent version created",
                        agent_id=agent.id,
                        name=name,
                        version=agent.version,
                        model=self.model_deployment,
                    )
                    return agent
            except Exception:
                # Agent doesn't exist, create new one
                pass

            # Create new agent using azure-ai-projects 2.0 API
            agent = self.client.agents.create(
                name=name,
                definition=PromptAgentDefinition(
                    model=self.model_deployment,
                    instructions=instructions,
                ),
                description=description,
            )

            logger.info(
                "Agent deployed successfully",
                agent_id=agent.id,
                name=name,
                version=agent.version,
                model=self.model_deployment,
            )

            return agent

        except Exception as e:
            logger.error(
                "Failed to deploy agent",
                name=name,
                error=str(e),
                exc_info=True,
            )
            raise

    def list_agents(self) -> List[Any]:
        """
        List all deployed agents in the project.

        Returns:
            List of agent objects
        """
        try:
            agents = self.client.agents.list()
            agent_list = list(agents)

            logger.info("Listed agents", count=len(agent_list))
            return agent_list

        except Exception as e:
            logger.error("Failed to list agents", error=str(e), exc_info=True)
            raise

    def get_agent(self, name: str) -> Optional[Any]:
        """
        Get a deployed agent by name.
        
        Uses client.agents.get(agent_name=...) from azure-ai-projects 2.0.

        Args:
            name: Agent name

        Returns:
            Agent object or None if not found
        """
        try:
            # azure-ai-projects 2.0+ has get() method that takes agent_name
            agent = self.client.agents.get(agent_name=name)
            logger.info("Retrieved agent", name=name, agent_id=agent.id, version=agent.version)
            return agent

        except Exception as e:
            # Agent not found or other error
            logger.warning("Agent not found or error retrieving", name=name, error=str(e))
            return None

    def delete_agent(self, name: str) -> bool:
        """
        Delete a deployed agent.

        Args:
            name: Agent name

        Returns:
            True if deleted, False if not found
        """
        try:
            agent = self.get_agent(name)
            if not agent:
                return False

            self.client.agents.delete(agent_name=name)
            logger.info("Agent deleted", name=name, agent_id=agent.id)
            return True

        except Exception as e:
            logger.error("Failed to delete agent", name=name, error=str(e), exc_info=True)
            raise


# =============================================================================
# Agent Definitions
# =============================================================================

AGENT_DEFINITIONS = {
    "manager": {
        "name": "SOC_Manager",
        "instructions_file": "manager_instructions.md",
        "description": "SOC Manager Agent - Coordinates multi-agent security workflows",
    },
    # Future agents to be added in later phases:
    # "triage": {
    #     "name": "AlertTriageAgent",
    #     "instructions_file": "alert_triage_instructions.md",
    #     "description": "Alert Triage Agent - Risk assessment and prioritization",
    # },
    # "hunting": {
    #     "name": "ThreatHuntingAgent",
    #     "instructions_file": "threat_hunting_instructions.md",
    #     "description": "Threat Hunting Agent - Proactive threat detection",
    # },
    # "response": {
    #     "name": "IncidentResponseAgent",
    #     "instructions_file": "incident_response_instructions.md",
    #     "description": "Incident Response Agent - Automated containment",
    # },
    # "intelligence": {
    #     "name": "ThreatIntelligenceAgent",
    #     "instructions_file": "threat_intelligence_instructions.md",
    #     "description": "Threat Intelligence Agent - IOC enrichment and briefings",
    # },
}


# =============================================================================
# Convenience Functions
# =============================================================================


async def deploy_all_agents(agent_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Deploy multiple agents to Microsoft Foundry.

    Args:
        agent_keys: List of agent keys to deploy (e.g., ["manager", "triage"]).
                   If None, deploys all defined agents.

    Returns:
        Dictionary mapping agent key to deployed agent object

    Example:
        >>> agents = await deploy_all_agents(["manager"])
        >>> manager = agents["manager"]
    """
    deployer = AgentDeployer()

    if agent_keys is None:
        agent_keys = list(AGENT_DEFINITIONS.keys())

    deployed = {}
    for key in agent_keys:
        if key not in AGENT_DEFINITIONS:
            logger.warning(f"Unknown agent key: {key}")
            continue

        definition = AGENT_DEFINITIONS[key]

        agent = deployer.deploy_agent(
            name=definition["name"],
            instructions_file=definition["instructions_file"],
            description=definition["description"],
        )

        deployed[key] = agent

    logger.info("Deployment complete", deployed_count=len(deployed))
    return deployed


async def list_deployed_agents() -> List[Any]:
    """
    List all deployed agents.

    Returns:
        List of agent objects
    """
    deployer = AgentDeployer()
    return deployer.list_agents()


async def cleanup_agents(agent_names: List[str]) -> int:
    """
    Delete specified agents.

    Args:
        agent_names: List of agent names to delete

    Returns:
        Number of agents successfully deleted
    """
    deployer = AgentDeployer()
    deleted_count = 0

    for name in agent_names:
        if deployer.delete_agent(name):
            deleted_count += 1

    logger.info("Cleanup complete", deleted_count=deleted_count)
    return deleted_count


# =============================================================================
# CLI Entry Point
# =============================================================================


async def main():
    """
    Main entry point for agent deployment.
    
    Usage:
        python -m src.deployment.deploy_agents
    """
    import sys

    logger.info("Starting agent deployment")

    try:
        # Deploy manager agent only for Phase 3
        agents = await deploy_all_agents(["manager"])

        print("\n" + "=" * 60)
        print("Agent Deployment Complete")
        print("=" * 60)

        for key, agent in agents.items():
            print(f"\n{key.upper()} Agent:")
            print(f"  Name: {agent.name}")
            print(f"  ID: {agent.id}")
            print(f"  Model: {agent.model}")
            print(f"  Description: {agent.description}")

        print("\n" + "=" * 60)
        print("✓ Phase 3A: Infrastructure Deployment Complete")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error("Deployment failed", error=str(e), exc_info=True)
        print(f"\n❌ Deployment failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
