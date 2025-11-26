"""
Alert Triage Agent V2 - Foundry Declarative Implementation.

Uses declarative YAML definition with Foundry IQ and Enterprise Memory.
No custom tools - all reasoning handled by LLM.

Reference: https://github.com/microsoft/agent-framework/tree/main/agent-samples/foundry
"""

import re
import time
from datetime import datetime
from typing import Optional
from uuid import uuid4

from src.agents.foundry_agent_loader import FoundryAgentLoader
from src.shared.schemas import (
    SecurityAlert,
    TriageResult,
    TriagePriority,
    TriageDecision,
)
from src.shared.logging import get_logger
from src.shared.metrics import counter
from src.shared.audit import get_audit_service, AuditResult

logger = get_logger(__name__)


class AlertTriageAgentV2:
    """
    Alert Triage Agent using Foundry declarative approach.

    Key differences from V1:
    - No custom @ai_function tools
    - Foundry IQ for MITRE knowledge (via MCP)
    - Agent loaded once, reused for session
    - All reasoning handled by LLM instructions
    """

    AGENT_VERSION = "2.0.0-foundry"
    YAML_FILE = "alert_triage_agent.yaml"

    def __init__(self, definitions_dir: str = "src/agents/definitions"):
        """
        Initialize Alert Triage Agent V2.

        Args:
            definitions_dir: Directory containing agent YAML definitions
        """
        self._loader = FoundryAgentLoader(definitions_dir=definitions_dir)
        self.audit_service = get_audit_service()

    def initialize(self) -> None:
        """Initialize agent from YAML (one-time at startup)."""
        logger.info("Initializing Foundry declarative agent...")
        self._loader.create_agent(self.YAML_FILE)
        logger.info(f"✅ Agent ready (v{self.AGENT_VERSION})")

    async def triage_alert(self, alert: SecurityAlert) -> TriageResult:
        """
        Triage a security alert.

        All reasoning is handled by the LLM with:
        - Foundry IQ for MITRE context
        - Built-in agent instructions for decision making

        Args:
            alert: Security alert to triage

        Returns:
            TriageResult: Triage analysis result
        """
        start_time = time.time()

        logger.info(
            "alert_triage_started",
            alert_id=str(alert.SystemAlertId),
            alert_name=alert.AlertName,
            severity=alert.Severity,
            agent_version=self.AGENT_VERSION
        )

        try:
            # Build alert context for the agent
            alert_context = self._format_alert(alert)

            # Run agent (uses Foundry IQ internally via MCP)
            response = await self._loader.run(input_text=alert_context)

            # Parse structured response
            triage_result = self._parse_response(response, alert, start_time)

            # Audit log
            await self.audit_service.log_agent_action(
                agent_name="AlertTriageAgentV2",
                action="TriagedAlert",
                target_entity_type="SecurityAlert",
                target_entity_id=str(alert.SystemAlertId),
                result=AuditResult.SUCCESS,
                details={
                    "version": self.AGENT_VERSION,
                    "foundry_native": True,
                    "custom_tools": False,
                    "risk_score": triage_result.RiskScore,
                    "decision": triage_result.TriageDecision.value,
                    "priority": triage_result.Priority.value,
                }
            )

            counter("alerts_triaged_total").inc()

            logger.info(
                "alert_triage_completed",
                alert_id=str(alert.SystemAlertId),
                triage_id=str(triage_result.TriageId),
                risk_score=triage_result.RiskScore,
                priority=triage_result.Priority,
                decision=triage_result.TriageDecision,
                processing_time_ms=triage_result.ProcessingTimeMs
            )

            return triage_result

        except Exception as e:
            logger.error(
                "alert_triage_failed",
                alert_id=str(alert.SystemAlertId),
                error=str(e),
                exc_info=True
            )

            # Log failure to audit trail
            await self.audit_service.log_agent_action(
                agent_name="AlertTriageAgentV2",
                action="TriagedAlert",
                target_entity_type="SecurityAlert",
                target_entity_id=str(alert.SystemAlertId),
                result=AuditResult.FAILURE,
                error_message=str(e)
            )

            counter("alerts_triage_failed_total").inc()
            raise

    def _format_alert(self, alert: SecurityAlert) -> str:
        """
        Format alert for agent input.

        Args:
            alert: Security alert to format

        Returns:
            str: Formatted alert context for the agent
        """
        entities = []
        for entity in alert.Entities:
            props = entity.Properties
            if "HostName" in props:
                entities.append(f"Host: {props['HostName']}")
            if "UserName" in props:
                entities.append(f"User: {props['UserName']}")
            if "IPAddress" in props:
                entities.append(f"IP: {props['IPAddress']}")

        mitre = alert.ExtendedProperties.get("MitreTechniques", [])
        confidence = alert.ExtendedProperties.get("ConfidenceScore", 75)

        return f"""
Analyze and triage this security alert:

**Alert Name**: {alert.AlertName}
**Alert Type**: {alert.AlertType}
**Severity**: {alert.Severity.value}
**Description**: {alert.Description}
**Confidence**: {confidence}%

**Entities**:
{chr(10).join(f'- {e}' for e in entities) if entities else '- None identified'}

**MITRE Techniques**: {', '.join(mitre) if mitre else 'None tagged'}

Please:
1. Query the MITRE knowledge base for technique context
2. Assess risk and make a triage decision
3. Provide remediation recommendations

Respond with:
- Risk Score: [0-100]
- Decision: [EscalateToIncident/CorrelateWithExisting/MarkAsFalsePositive/RequireHumanReview]
- Priority: [Critical/High/Medium/Low]
- Rationale: [Your reasoning]
- Remediation: [Specific actions to take]
"""

    def _parse_response(
        self,
        response: str,
        alert: SecurityAlert,
        start_time: float
    ) -> TriageResult:
        """
        Parse agent response into TriageResult.

        Args:
            response: Agent response text
            alert: Original security alert
            start_time: Processing start time

        Returns:
            TriageResult: Parsed triage result
        """
        response_lower = response.lower()

        # Determine decision from response text
        if "escalate" in response_lower and "incident" in response_lower:
            decision = TriageDecision.ESCALATE_TO_INCIDENT
            priority = TriagePriority.HIGH
        elif "correlate" in response_lower:
            decision = TriageDecision.CORRELATE_WITH_EXISTING
            priority = TriagePriority.MEDIUM
        elif "false positive" in response_lower:
            decision = TriageDecision.MARK_AS_FALSE_POSITIVE
            priority = TriagePriority.LOW
        else:
            decision = TriageDecision.REQUIRE_HUMAN_REVIEW
            priority = TriagePriority.MEDIUM

        # Extract priority if explicitly mentioned
        if "critical" in response_lower:
            priority = TriagePriority.CRITICAL
        elif "high" in response_lower and "priority" in response_lower:
            priority = TriagePriority.HIGH
        elif "low" in response_lower and "priority" in response_lower:
            priority = TriagePriority.LOW

        # Extract risk score if mentioned
        risk_score = 50  # default
        score_match = re.search(r'risk\s*score[:\s]*(\d+)', response_lower)
        if score_match:
            risk_score = min(100, max(0, int(score_match.group(1))))
        else:
            # Alternative pattern: "75/100" or "85 / 100" format
            score_match = re.search(r'(\d+)\s*/\s*100', response_lower)
            if score_match:
                risk_score = min(100, max(0, int(score_match.group(1))))

        return TriageResult(
            AlertId=alert.SystemAlertId,
            TriageId=uuid4(),
            Timestamp=datetime.utcnow(),
            RiskScore=risk_score,
            Priority=priority,
            TriageDecision=decision,
            Explanation=response,
            CorrelatedAlertIds=[],  # Can be populated from Enterprise Memory in future
            EnrichmentData={"foundry_native": True, "agent_version": self.AGENT_VERSION},
            ProcessingTimeMs=int((time.time() - start_time) * 1000),
            AgentVersion=self.AGENT_VERSION
        )

    def reset(self) -> None:
        """Reset the agent loader."""
        self._loader.reset()


# Global agent instance
_triage_agent_v2: Optional[AlertTriageAgentV2] = None


def get_triage_agent_v2(
    definitions_dir: str = "src/agents/definitions"
) -> AlertTriageAgentV2:
    """
    Get global Alert Triage Agent V2 instance.

    Args:
        definitions_dir: Directory containing agent YAML definitions

    Returns:
        AlertTriageAgentV2: Global triage agent
    """
    global _triage_agent_v2
    if _triage_agent_v2 is None:
        _triage_agent_v2 = AlertTriageAgentV2(definitions_dir=definitions_dir)
    return _triage_agent_v2
