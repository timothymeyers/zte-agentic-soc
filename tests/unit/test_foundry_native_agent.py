"""
Unit tests for FoundryNativeAgent wrapper.

Tests the MVP implementation of declarative YAML-based agent definitions
and persistent agent lifecycle management.
"""

import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
import yaml

from src.agents.foundry_native_agent import FoundryNativeAgent


@pytest.fixture
def sample_agent_yaml():
    """Create a sample agent YAML configuration."""
    return {
        'version': '1.0.0',
        'name': 'test-agent',
        'description': 'Test agent for unit testing',
        'metadata': {
            'authors': ['Test Team'],
            'tags': ['test', 'unit-test'],
            'version': '1.0.0'
        },
        'model': {
            'id': 'gpt-4.1-mini',
            'options': {
                'temperature': 0.3,
                'top_p': 0.9,
                'max_tokens': 4096
            }
        },
        'instructions': 'You are a test agent for unit testing.',
        'tools': [],
        'memory': {
            'enabled': False
        }
    }


@pytest.fixture
def agent_yaml_file(sample_agent_yaml):
    """Create a temporary YAML file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_agent_yaml, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.mark.asyncio
class TestFoundryNativeAgent:
    """Test suite for FoundryNativeAgent."""
    
    async def test_agent_creation(self, agent_yaml_file):
        """Test that agent can be created with YAML file."""
        agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
        
        assert agent is not None
        assert agent.agent_yaml_path == agent_yaml_file
        assert not agent.is_initialized
    
    async def test_agent_initialization_without_azure(self, agent_yaml_file):
        """Test agent initialization without Azure endpoint (should log warning but not fail)."""
        # Ensure no Azure endpoint is set
        original_endpoint = os.environ.get('AZURE_AI_PROJECT_ENDPOINT')
        original_foundry = os.environ.get('AZURE_AI_FOUNDRY_ENDPOINT')
        
        try:
            if 'AZURE_AI_PROJECT_ENDPOINT' in os.environ:
                del os.environ['AZURE_AI_PROJECT_ENDPOINT']
            if 'AZURE_AI_FOUNDRY_ENDPOINT' in os.environ:
                del os.environ['AZURE_AI_FOUNDRY_ENDPOINT']
            
            agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
            
            with patch('src.agents.foundry_native_agent.DefaultAzureCredential'):
                await agent.initialize()
            
            assert agent.is_initialized
            assert agent.name == 'test-agent'
            assert agent.version == '1.0.0'
            assert agent.agent_config is not None
            
        finally:
            # Restore original environment
            if original_endpoint:
                os.environ['AZURE_AI_PROJECT_ENDPOINT'] = original_endpoint
            if original_foundry:
                os.environ['AZURE_AI_FOUNDRY_ENDPOINT'] = original_foundry
    
    async def test_yaml_loading(self, agent_yaml_file, sample_agent_yaml):
        """Test that YAML configuration is properly loaded."""
        agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
        
        with patch('src.agents.foundry_native_agent.DefaultAzureCredential'):
            await agent.initialize()
        
        assert agent.agent_config == sample_agent_yaml
        assert agent.agent_config['name'] == 'test-agent'
        assert agent.agent_config['model']['id'] == 'gpt-4.1-mini'
    
    async def test_env_var_resolution(self, agent_yaml_file):
        """Test environment variable resolution in YAML values."""
        agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
        
        # Set test environment variable
        os.environ['TEST_VAR'] = 'test-value'
        
        try:
            # Test resolution
            result = agent._resolve_env_vars('prefix-${TEST_VAR}-suffix')
            assert result == 'prefix-test-value-suffix'
            
            # Test multiple variables
            os.environ['TEST_VAR2'] = 'value2'
            result = agent._resolve_env_vars('${TEST_VAR}/${TEST_VAR2}')
            assert result == 'test-value/value2'
            
            # Test missing variable (should keep placeholder)
            result = agent._resolve_env_vars('${NONEXISTENT_VAR}')
            assert result == '${NONEXISTENT_VAR}'
            
        finally:
            # Cleanup
            if 'TEST_VAR' in os.environ:
                del os.environ['TEST_VAR']
            if 'TEST_VAR2' in os.environ:
                del os.environ['TEST_VAR2']
    
    async def test_agent_properties(self, agent_yaml_file):
        """Test agent property accessors."""
        agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
        
        # Before initialization
        assert agent.name == 'uninitialized'
        assert agent.version == '0.0.0'
        
        with patch('src.agents.foundry_native_agent.DefaultAzureCredential'):
            await agent.initialize()
        
        # After initialization
        assert agent.name == 'test-agent'
        assert agent.version == '1.0.0'
    
    async def test_double_initialization(self, agent_yaml_file):
        """Test that double initialization is handled correctly."""
        agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
        
        with patch('src.agents.foundry_native_agent.DefaultAzureCredential'):
            await agent.initialize()
            
            # Second initialization should be skipped
            await agent.initialize()
            
            assert agent.is_initialized
    
    async def test_run_without_initialization(self, agent_yaml_file):
        """Test that running agent without initialization raises error."""
        agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
        
        with pytest.raises(RuntimeError, match="not initialized"):
            await agent.run(query="test query")
    
    async def test_cleanup(self, agent_yaml_file):
        """Test agent resource cleanup."""
        agent = FoundryNativeAgent(agent_yaml_path=agent_yaml_file)
        
        # Mock credential and client
        mock_credential = AsyncMock()
        mock_client = AsyncMock()
        
        agent.credential = mock_credential
        agent.project_client = mock_client
        
        await agent.close()
        
        # Verify cleanup was called
        mock_credential.close.assert_called_once()
        mock_client.close.assert_called_once()
    
    async def test_invalid_yaml_file(self):
        """Test handling of invalid YAML file path."""
        agent = FoundryNativeAgent(agent_yaml_path='/nonexistent/file.yaml')
        
        with pytest.raises(FileNotFoundError):
            await agent.initialize()
    
    async def test_malformed_yaml(self):
        """Test handling of malformed YAML content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            temp_path = f.name
        
        try:
            agent = FoundryNativeAgent(agent_yaml_path=temp_path)
            
            with pytest.raises(yaml.YAMLError):
                await agent.initialize()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


@pytest.mark.asyncio
class TestAgentManagement:
    """Test suite for global agent management functions."""
    
    async def test_initialize_agents_without_yaml(self):
        """Test agent initialization when YAML files don't exist."""
        from src.agents import initialize_agents
        
        # This should log warnings but not fail
        with patch('os.path.exists', return_value=False):
            with patch('src.agents.foundry_native_agent.DefaultAzureCredential'):
                await initialize_agents()
    
    async def test_get_agent_before_initialization(self):
        """Test that getting agent before initialization raises error."""
        from src.agents import get_alert_triage_agent
        
        # Reset global state
        import src.agents
        src.agents._alert_triage_agent = None
        
        with pytest.raises(RuntimeError, match="not initialized"):
            get_alert_triage_agent()
    
    async def test_cleanup_agents(self):
        """Test cleanup of all agents."""
        from src.agents import cleanup_agents
        
        # Mock agent
        mock_agent = AsyncMock()
        
        import src.agents
        src.agents._alert_triage_agent = mock_agent
        
        await cleanup_agents()
        
        # Verify cleanup was called
        mock_agent.close.assert_called_once()
        assert src.agents._alert_triage_agent is None
