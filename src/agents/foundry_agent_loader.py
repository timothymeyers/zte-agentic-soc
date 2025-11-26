"""
Foundry Declarative Agent Loader using AgentFactory.

Uses agent-framework-declarative's AgentFactory to load agents from YAML.
Reference: https://github.com/microsoft/agent-framework/tree/main/agent-samples/foundry
"""

import os
from pathlib import Path
from typing import Optional, Any

from agent_framework_declarative import AgentFactory
from agent_framework import ChatAgent

from src.shared.logging import get_logger

logger = get_logger(__name__)


class FoundryAgentLoader:
    """Loads and manages Foundry declarative agents using AgentFactory."""

    def __init__(
        self,
        definitions_dir: str = "src/agents/definitions",
        env_file: Optional[str] = None,
    ):
        """
        Initialize Foundry Agent Loader.

        Args:
            definitions_dir: Directory containing agent YAML definitions
            env_file: Path to .env file for environment variable resolution
        """
        self.definitions_dir = Path(definitions_dir)
        self.env_file = env_file
        self._agent: Optional[ChatAgent] = None
        self._agent_factory: Optional[AgentFactory] = None

        logger.debug(f"FoundryAgentLoader initialized with definitions_dir: {definitions_dir}")

    @property
    def agent_factory(self) -> AgentFactory:
        """Get or create AgentFactory instance."""
        if self._agent_factory is None:
            self._agent_factory = AgentFactory(
                env_file=self.env_file,
                default_provider="AzureAIClient",
            )
            logger.info("AgentFactory initialized")
        return self._agent_factory

    def create_agent(
        self,
        yaml_file: str = "alert_triage_agent.yaml",
        force_recreate: bool = False
    ) -> ChatAgent:
        """
        Create agent from YAML definition using AgentFactory.

        AgentFactory handles:
        - YAML parsing with PowerFx Env.Variable pattern
        - Tool configuration (MCP, function tools)
        - Agent creation with the configured model

        Agent is created once and reused throughout the session.

        Args:
            yaml_file: Name of the YAML file in definitions directory
            force_recreate: If True, recreate agent even if one exists

        Returns:
            ChatAgent: The created agent instance
        """
        if self._agent is not None and not force_recreate:
            logger.info("Reusing existing agent instance")
            return self._agent

        yaml_path = self.definitions_dir / yaml_file
        logger.info(f"Loading agent from YAML: {yaml_path}")

        # AgentFactory.create_agent_from_yaml_path() handles:
        # - Loading YAML definition
        # - Resolving PowerFx Env.Variable references
        # - Configuring MCP tools (Foundry IQ)
        # - Creating ChatAgent with configured model
        self._agent = self.agent_factory.create_agent_from_yaml_path(
            yaml_path=str(yaml_path)
        )

        logger.info(f"✅ Agent created via AgentFactory from: {yaml_path}")
        return self._agent

    def load_yaml(self, yaml_file: str) -> dict[str, Any]:
        """
        Load and parse a YAML definition file.

        Args:
            yaml_file: Name of the YAML file in definitions directory

        Returns:
            dict: Parsed YAML content
        """
        import yaml

        yaml_path = self.definitions_dir / yaml_file
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    async def run(self, input_text: str) -> str:
        """
        Run agent with input.

        Args:
            input_text: The input text/prompt to send to the agent

        Returns:
            str: The agent's response text
        """
        if self._agent is None:
            self.create_agent()

        # Run the agent
        response = await self._agent.run(input_text)

        # Extract text from response
        if hasattr(response, 'text'):
            return response.text
        return str(response)

    def get_agent(self) -> Optional[ChatAgent]:
        """
        Get the current agent instance.

        Returns:
            Optional[ChatAgent]: The current agent or None if not created
        """
        return self._agent

    def reset(self) -> None:
        """Reset the loader, clearing the cached agent."""
        self._agent = None
        logger.info("Agent loader reset - agent cleared")
