"""
Unit tests for Foundry Agent Loader module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.foundry_agent_loader import FoundryAgentLoader


class TestFoundryAgentLoader:
    """Tests for FoundryAgentLoader class."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        loader = FoundryAgentLoader()
        assert loader.definitions_dir == Path("src/agents/definitions")
        assert loader.env_file is None
        assert loader._agent is None
        assert loader._agent_factory is None

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        loader = FoundryAgentLoader(
            definitions_dir="/custom/path",
            env_file=".env.test"
        )
        assert loader.definitions_dir == Path("/custom/path")
        assert loader.env_file == ".env.test"

    def test_load_yaml(self, tmp_path):
        """Test YAML file loading."""
        # Create a temporary YAML file
        yaml_content = """
kind: Prompt
name: test-agent
description: Test agent for unit tests
"""
        yaml_file = tmp_path / "test_agent.yaml"
        yaml_file.write_text(yaml_content)

        loader = FoundryAgentLoader(definitions_dir=str(tmp_path))
        definition = loader.load_yaml("test_agent.yaml")

        assert definition["kind"] == "Prompt"
        assert definition["name"] == "test-agent"
        assert definition["description"] == "Test agent for unit tests"

    def test_load_yaml_real_definition(self):
        """Test loading the actual agent definition file."""
        loader = FoundryAgentLoader()
        definition = loader.load_yaml("alert_triage_agent.yaml")

        assert definition["kind"] == "Prompt"
        assert definition["name"] == "alert-triage-agent"
        assert "instructions" in definition
        assert "tools" in definition

    def test_agent_factory_property_creates_factory(self):
        """Test agent_factory property creates factory on first access."""
        loader = FoundryAgentLoader()
        
        # First access should create the factory
        factory = loader.agent_factory
        assert factory is not None
        
        # Should be an AgentFactory instance
        from agent_framework_declarative import AgentFactory
        assert isinstance(factory, AgentFactory)

        # Second access should return same instance
        factory2 = loader.agent_factory
        assert factory2 is factory

    def test_create_agent_with_mocked_factory(self):
        """Test create_agent caches the agent instance using mocked factory."""
        loader = FoundryAgentLoader()
        
        # Create mock agent and factory
        mock_agent = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_agent_from_yaml_path.return_value = mock_agent
        
        # Inject mock factory
        loader._agent_factory = mock_factory
        
        # First call creates agent
        agent1 = loader.create_agent()
        assert agent1 == mock_agent
        mock_factory.create_agent_from_yaml_path.assert_called_once()

        # Second call returns cached agent
        agent2 = loader.create_agent()
        assert agent2 == mock_agent
        assert mock_factory.create_agent_from_yaml_path.call_count == 1

    def test_create_agent_force_recreate_with_mocked_factory(self):
        """Test create_agent with force_recreate=True using mocked factory."""
        loader = FoundryAgentLoader()
        
        # Create mock agents and factory
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_agent_from_yaml_path.side_effect = [mock_agent1, mock_agent2]
        
        # Inject mock factory
        loader._agent_factory = mock_factory
        
        # First call
        agent1 = loader.create_agent()
        assert agent1 == mock_agent1

        # Second call with force_recreate
        agent2 = loader.create_agent(force_recreate=True)
        assert agent2 == mock_agent2
        assert mock_factory.create_agent_from_yaml_path.call_count == 2

    def test_get_agent_returns_none_before_creation(self):
        """Test get_agent returns None before agent is created."""
        loader = FoundryAgentLoader()
        assert loader.get_agent() is None

    def test_get_agent_returns_agent_after_creation_with_mocked_factory(self):
        """Test get_agent returns agent after creation using mocked factory."""
        loader = FoundryAgentLoader()
        
        # Create mock agent and factory
        mock_agent = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_agent_from_yaml_path.return_value = mock_agent
        
        # Inject mock factory
        loader._agent_factory = mock_factory
        loader.create_agent()
        
        assert loader.get_agent() == mock_agent

    def test_reset_clears_agent_with_mocked_factory(self):
        """Test reset clears the cached agent using mocked factory."""
        loader = FoundryAgentLoader()
        
        # Create mock agent and factory
        mock_agent = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_agent_from_yaml_path.return_value = mock_agent
        
        # Inject mock factory
        loader._agent_factory = mock_factory
        loader.create_agent()
        assert loader.get_agent() is not None

        loader.reset()
        assert loader.get_agent() is None


class TestFoundryAgentLoaderYAMLParsing:
    """Tests for YAML parsing behavior."""

    def test_yaml_has_required_fields(self):
        """Test that the agent YAML has all required fields."""
        loader = FoundryAgentLoader()
        definition = loader.load_yaml("alert_triage_agent.yaml")

        # Required fields
        assert "kind" in definition
        assert "name" in definition
        assert "description" in definition
        assert "model" in definition
        assert "instructions" in definition
        assert "tools" in definition

    def test_yaml_model_configuration(self):
        """Test model configuration in YAML."""
        loader = FoundryAgentLoader()
        definition = loader.load_yaml("alert_triage_agent.yaml")

        model = definition["model"]
        assert "id" in model
        assert "options" in model
        assert "temperature" in model["options"]
        assert "max_tokens" in model["options"]

    def test_yaml_mcp_tool_configuration(self):
        """Test MCP tool configuration in YAML."""
        loader = FoundryAgentLoader()
        definition = loader.load_yaml("alert_triage_agent.yaml")

        tools = definition["tools"]
        assert len(tools) >= 1
        
        mcp_tool = tools[0]
        assert mcp_tool["kind"] == "mcp"
        assert "name" in mcp_tool
        assert "description" in mcp_tool
        assert "url" in mcp_tool
        assert "connection" in mcp_tool

    def test_yaml_metadata(self):
        """Test metadata in YAML."""
        loader = FoundryAgentLoader()
        definition = loader.load_yaml("alert_triage_agent.yaml")

        metadata = definition.get("metadata", {})
        assert "version" in metadata
        assert "author" in metadata
        assert "tags" in metadata
