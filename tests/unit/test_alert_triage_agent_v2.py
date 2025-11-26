"""
Unit tests for Alert Triage Agent V2 module.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.agents.alert_triage_agent_v2 import (
    AlertTriageAgentV2,
    get_triage_agent_v2,
)
from src.shared.schemas import (
    SecurityAlert,
    AlertEntity,
    EntityType,
    SeverityLevel,
    TriageDecision,
    TriagePriority,
)


@pytest.fixture
def sample_alert():
    """Create a sample security alert for testing."""
    return SecurityAlert(
        SystemAlertId=uuid4(),
        AlertName="Test Suspicious PowerShell",
        AlertType="SuspiciousPowerShell",
        Severity=SeverityLevel.HIGH,
        Description="PowerShell executed with encoded command",
        TimeGenerated=datetime.utcnow(),
        StartTime=datetime.utcnow(),
        EndTime=datetime.utcnow(),
        Entities=[
            AlertEntity(
                Type=EntityType.HOST,
                Properties={"HostName": "WS-001"}
            ),
            AlertEntity(
                Type=EntityType.ACCOUNT,
                Properties={"UserName": "testuser"}
            ),
        ],
        ExtendedProperties={
            "MitreTechniques": ["T1059.001"],
            "ConfidenceScore": 85
        },
        ProviderName="Test Provider",
        ProductName="Test Product",
    )


class TestAlertTriageAgentV2:
    """Tests for AlertTriageAgentV2 class."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        agent = AlertTriageAgentV2()
        assert agent.AGENT_VERSION == "2.0.0-foundry"
        assert agent.YAML_FILE == "alert_triage_agent.yaml"
        assert agent._loader is not None
        assert agent.audit_service is not None

    def test_init_custom_definitions_dir(self):
        """Test initialization with custom definitions directory."""
        agent = AlertTriageAgentV2(definitions_dir="/custom/path")
        assert str(agent._loader.definitions_dir) == "/custom/path"

    def test_initialize_calls_loader(self):
        """Test initialize method creates agent."""
        agent = AlertTriageAgentV2()
        # Replace loader with mock
        mock_loader = MagicMock()
        agent._loader = mock_loader
        
        agent.initialize()
        
        mock_loader.create_agent.assert_called_once_with("alert_triage_agent.yaml")

    def test_format_alert(self, sample_alert):
        """Test alert formatting for agent input."""
        agent = AlertTriageAgentV2()
        formatted = agent._format_alert(sample_alert)

        assert "Test Suspicious PowerShell" in formatted
        assert "SuspiciousPowerShell" in formatted
        assert "High" in formatted
        assert "PowerShell executed with encoded command" in formatted
        assert "WS-001" in formatted
        assert "testuser" in formatted
        assert "T1059.001" in formatted
        assert "85%" in formatted

    def test_format_alert_no_entities(self):
        """Test formatting alert with no entities."""
        alert = SecurityAlert(
            AlertName="Test Alert",
            AlertType="TestType",
            Severity=SeverityLevel.MEDIUM,
            Description="Test description",
            StartTime=datetime.utcnow(),
            EndTime=datetime.utcnow(),
            Entities=[],
            ProviderName="Test",
            ProductName="Test",
        )
        
        agent = AlertTriageAgentV2()
        formatted = agent._format_alert(alert)

        assert "None identified" in formatted

    def test_format_alert_no_mitre_techniques(self):
        """Test formatting alert with no MITRE techniques."""
        alert = SecurityAlert(
            AlertName="Test Alert",
            AlertType="TestType",
            Severity=SeverityLevel.LOW,
            Description="Test description",
            StartTime=datetime.utcnow(),
            EndTime=datetime.utcnow(),
            Entities=[],
            ExtendedProperties={},
            ProviderName="Test",
            ProductName="Test",
        )
        
        agent = AlertTriageAgentV2()
        formatted = agent._format_alert(alert)

        assert "None tagged" in formatted

    def test_parse_response_escalate(self, sample_alert):
        """Test parsing response with escalate decision."""
        agent = AlertTriageAgentV2()
        response = """
        Based on analysis, this should be escalated to incident.
        Risk Score: 85
        Priority: Critical
        """
        
        result = agent._parse_response(response, sample_alert, 0)
        
        assert result.TriageDecision == TriageDecision.ESCALATE_TO_INCIDENT
        assert result.RiskScore == 85
        assert result.Priority == TriagePriority.CRITICAL

    def test_parse_response_correlate(self, sample_alert):
        """Test parsing response with correlate decision."""
        agent = AlertTriageAgentV2()
        response = """
        This alert should be correlated with existing incidents.
        Risk Score: 45
        Priority: Medium
        """
        
        result = agent._parse_response(response, sample_alert, 0)
        
        assert result.TriageDecision == TriageDecision.CORRELATE_WITH_EXISTING
        assert result.RiskScore == 45
        assert result.Priority == TriagePriority.MEDIUM

    def test_parse_response_false_positive(self, sample_alert):
        """Test parsing response with false positive decision."""
        agent = AlertTriageAgentV2()
        response = """
        This appears to be a false positive.
        Risk Score: 10
        Priority: Low
        """
        
        result = agent._parse_response(response, sample_alert, 0)
        
        assert result.TriageDecision == TriageDecision.MARK_AS_FALSE_POSITIVE
        assert result.RiskScore == 10
        assert result.Priority == TriagePriority.LOW

    def test_parse_response_human_review(self, sample_alert):
        """Test parsing response with human review decision."""
        agent = AlertTriageAgentV2()
        response = """
        Unclear situation, needs review.
        Risk Score: 50
        """
        
        result = agent._parse_response(response, sample_alert, 0)
        
        assert result.TriageDecision == TriageDecision.REQUIRE_HUMAN_REVIEW
        assert result.Priority == TriagePriority.MEDIUM

    def test_parse_response_extracts_risk_score(self, sample_alert):
        """Test extraction of risk score from various formats."""
        agent = AlertTriageAgentV2()
        
        # Test "risk score: 75" format
        result1 = agent._parse_response("risk score: 75", sample_alert, 0)
        assert result1.RiskScore == 75
        
        # Test "75/100" format
        result2 = agent._parse_response("scored 85/100 on risk", sample_alert, 0)
        assert result2.RiskScore == 85

    def test_parse_response_caps_risk_score(self, sample_alert):
        """Test risk score is capped at 0-100."""
        agent = AlertTriageAgentV2()
        
        # Test score over 100
        result = agent._parse_response("risk score: 150", sample_alert, 0)
        assert result.RiskScore == 100

    def test_parse_response_includes_metadata(self, sample_alert):
        """Test response parsing includes correct metadata."""
        agent = AlertTriageAgentV2()
        start_time = 1000.0
        
        with patch('time.time', return_value=1001.5):
            result = agent._parse_response("test response", sample_alert, start_time)
        
        assert result.AlertId == sample_alert.SystemAlertId
        assert result.AgentVersion == "2.0.0-foundry"
        assert result.EnrichmentData["foundry_native"] is True
        assert result.ProcessingTimeMs == 1500  # 1.5 seconds

    def test_reset(self):
        """Test reset method."""
        agent = AlertTriageAgentV2()
        agent._loader = MagicMock()
        
        agent.reset()
        
        agent._loader.reset.assert_called_once()


class TestGetTriageAgentV2:
    """Tests for get_triage_agent_v2 function."""

    def test_get_triage_agent_v2_creates_instance(self):
        """Test that get_triage_agent_v2 creates singleton instance."""
        # Reset global state
        import src.agents.alert_triage_agent_v2 as module
        module._triage_agent_v2 = None
        
        agent1 = get_triage_agent_v2()
        agent2 = get_triage_agent_v2()
        
        assert agent1 is agent2
        assert isinstance(agent1, AlertTriageAgentV2)

    def test_get_triage_agent_v2_custom_dir(self):
        """Test creating agent with custom definitions directory."""
        import src.agents.alert_triage_agent_v2 as module
        module._triage_agent_v2 = None
        
        agent = get_triage_agent_v2(definitions_dir="/custom/dir")
        assert str(agent._loader.definitions_dir) == "/custom/dir"


@pytest.mark.asyncio
class TestAlertTriageAgentV2Async:
    """Async tests for AlertTriageAgentV2."""

    async def test_triage_alert_success(self, sample_alert):
        """Test successful alert triage."""
        agent = AlertTriageAgentV2()
        
        # Mock the loader
        mock_loader = MagicMock()
        mock_loader.run = AsyncMock(return_value="""
            Analysis complete.
            Risk Score: 75
            Decision: Escalate to Incident
            Priority: High
            Rationale: High severity PowerShell execution with MITRE technique.
        """)
        agent._loader = mock_loader
        
        result = await agent.triage_alert(sample_alert)
        
        assert result.AlertId == sample_alert.SystemAlertId
        assert result.RiskScore == 75
        assert result.TriageDecision == TriageDecision.ESCALATE_TO_INCIDENT
        assert result.AgentVersion == "2.0.0-foundry"
        # ProcessingTimeMs might be 0 if execution is very fast
        assert result.ProcessingTimeMs >= 0

    async def test_triage_alert_failure(self, sample_alert):
        """Test alert triage failure handling."""
        agent = AlertTriageAgentV2()
        
        # Mock the loader to raise an exception
        mock_loader = MagicMock()
        mock_loader.run = AsyncMock(side_effect=Exception("Test error"))
        agent._loader = mock_loader
        
        with pytest.raises(Exception) as exc_info:
            await agent.triage_alert(sample_alert)
        
        assert "Test error" in str(exc_info.value)
