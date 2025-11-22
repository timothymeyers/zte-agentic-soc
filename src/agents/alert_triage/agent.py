"""
Alert Triage Agent - AI-powered alert analysis and prioritization.

This agent analyzes security alerts, assigns risk scores, correlates related alerts,
and makes triage decisions with natural language explanations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
import time

from src.shared.schemas import (
    SecurityAlert,
    TriageResult,
    TriagePriority,
    TriageDecision,
    SeverityLevel
)
from src.shared.logging import get_logger
from src.shared.metrics import measure_time, counter
from src.shared.audit import get_audit_service, AuditResult
from src.data.datasets import get_attack_loader


logger = get_logger(__name__)


class AlertTriageAgent:
    """
    AI-powered alert triage agent.
    
    This agent:
    - Analyzes incoming security alerts
    - Calculates risk scores based on multiple factors
    - Correlates related alerts
    - Makes triage decisions
    - Provides natural language explanations
    """
    
    def __init__(
        self,
        agent_version: str = "0.1.0",
        # TODO: Add Azure AI Foundry client parameters
    ):
        """
        Initialize Alert Triage Agent.
        
        Args:
            agent_version: Version of the agent
        """
        self.agent_version = agent_version
        self.agent_name = "AlertTriageAgent"
        
        # Load threat intelligence for enrichment
        self.attack_loader = get_attack_loader()
        self.audit_service = get_audit_service()
        
        # Historical alerts for correlation (in-memory for MVP)
        self._recent_alerts: List[SecurityAlert] = []
        
        logger.info(f"{self.agent_name} initialized (version: {agent_version})")
    
    async def triage_alert(self, alert: SecurityAlert) -> TriageResult:
        """
        Triage a security alert.
        
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
            severity=alert.Severity
        )
        
        try:
            with measure_time("triage_duration_ms"):
                # Calculate risk score
                risk_score = await self._calculate_risk_score(alert)
                
                # Determine priority
                priority = self._determine_priority(risk_score, alert.Severity)
                
                # Find correlated alerts
                correlated_alerts = await self._correlate_alerts(alert)
                
                # Make triage decision
                decision = self._make_triage_decision(risk_score, correlated_alerts)
                
                # Generate explanation
                explanation = await self._generate_explanation(
                    alert, risk_score, priority, decision, correlated_alerts
                )
                
                # Enrich with threat intelligence
                enrichment_data = await self._enrich_with_threat_intel(alert)
                
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Create triage result
                triage_result = TriageResult(
                    AlertId=alert.SystemAlertId,
                    TriageId=uuid4(),
                    Timestamp=datetime.utcnow(),
                    RiskScore=risk_score,
                    Priority=priority,
                    TriageDecision=decision,
                    Explanation=explanation,
                    CorrelatedAlertIds=[a.SystemAlertId for a in correlated_alerts],
                    EnrichmentData=enrichment_data,
                    ProcessingTimeMs=processing_time_ms,
                    AgentVersion=self.agent_version
                )
                
                # Log to audit trail
                await self.audit_service.log_agent_action(
                    agent_name=self.agent_name,
                    action="TriagedAlert",
                    target_entity_type="SecurityAlert",
                    target_entity_id=str(alert.SystemAlertId),
                    result=AuditResult.SUCCESS,
                    details={
                        "risk_score": risk_score,
                        "priority": priority,
                        "decision": decision
                    }
                )
                
                # Update metrics
                counter("alerts_triaged_total").inc()
                
                # Store alert for future correlation
                self._recent_alerts.append(alert)
                if len(self._recent_alerts) > 1000:  # Keep last 1000 alerts
                    self._recent_alerts.pop(0)
                
                logger.info(
                    "alert_triage_completed",
                    alert_id=str(alert.SystemAlertId),
                    triage_id=str(triage_result.TriageId),
                    risk_score=risk_score,
                    priority=priority,
                    decision=decision,
                    processing_time_ms=processing_time_ms
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
                agent_name=self.agent_name,
                action="TriagedAlert",
                target_entity_type="SecurityAlert",
                target_entity_id=str(alert.SystemAlertId),
                result=AuditResult.FAILURE,
                error_message=str(e)
            )
            
            counter("alerts_triage_failed_total").inc()
            raise
    
    async def _calculate_risk_score(self, alert: SecurityAlert) -> int:
        """
        Calculate risk score for an alert.
        
        Args:
            alert: Security alert
        
        Returns:
            int: Risk score (0-100)
        
        Factors:
        - Alert severity (30%)
        - Entity count (10%)
        - MITRE techniques (20%)
        - Asset criticality (20%)
        - User risk level (10%)
        - Confidence score (10%)
        """
        score = 0
        
        # Severity contribution (0-30)
        severity_scores = {
            SeverityLevel.HIGH: 30,
            SeverityLevel.MEDIUM: 20,
            SeverityLevel.LOW: 10,
            SeverityLevel.INFORMATIONAL: 5
        }
        score += severity_scores.get(alert.Severity, 10)
        
        # Entity count contribution (0-10)
        entity_count = len(alert.Entities)
        score += min(entity_count * 2, 10)
        
        # MITRE techniques contribution (0-20)
        mitre_techniques = alert.ExtendedProperties.get("MitreTechniques", [])
        if mitre_techniques:
            score += min(len(mitre_techniques) * 5, 20)
        
        # Asset criticality (0-20) - placeholder
        # TODO: Lookup actual asset criticality from asset inventory
        score += 15  # Assume medium criticality
        
        # User risk level (0-10) - placeholder
        # TODO: Lookup user risk from identity protection
        score += 5  # Assume low risk
        
        # Confidence score (0-10)
        confidence = alert.ExtendedProperties.get("ConfidenceScore", 0)
        score += int(confidence / 10)
        
        # Cap at 100
        return min(score, 100)
    
    def _determine_priority(
        self,
        risk_score: int,
        severity: SeverityLevel
    ) -> TriagePriority:
        """
        Determine priority based on risk score and severity.
        
        Args:
            risk_score: Calculated risk score
            severity: Alert severity
        
        Returns:
            TriagePriority: Priority level
        """
        if risk_score >= 80:
            return TriagePriority.CRITICAL
        elif risk_score >= 60:
            return TriagePriority.HIGH
        elif risk_score >= 40:
            return TriagePriority.MEDIUM
        else:
            return TriagePriority.LOW
    
    async def _correlate_alerts(
        self,
        alert: SecurityAlert
    ) -> List[SecurityAlert]:
        """
        Find related alerts by entity overlap.
        
        Args:
            alert: Security alert
        
        Returns:
            List[SecurityAlert]: Correlated alerts
        """
        correlated = []
        
        # Extract entity identifiers from current alert
        current_entities = set()
        for entity in alert.Entities:
            if "HostName" in entity.Properties:
                current_entities.add(("host", entity.Properties["HostName"]))
            if "UserName" in entity.Properties:
                current_entities.add(("user", entity.Properties["UserName"]))
            if "IPAddress" in entity.Properties:
                current_entities.add(("ip", entity.Properties["IPAddress"]))
        
        # Check recent alerts for entity overlap
        for past_alert in self._recent_alerts[-100:]:  # Check last 100 alerts
            if past_alert.SystemAlertId == alert.SystemAlertId:
                continue
            
            # Extract entities from past alert
            past_entities = set()
            for entity in past_alert.Entities:
                if "HostName" in entity.Properties:
                    past_entities.add(("host", entity.Properties["HostName"]))
                if "UserName" in entity.Properties:
                    past_entities.add(("user", entity.Properties["UserName"]))
                if "IPAddress" in entity.Properties:
                    past_entities.add(("ip", entity.Properties["IPAddress"]))
            
            # Check for overlap
            if current_entities & past_entities:
                correlated.append(past_alert)
        
        logger.debug(
            "alert_correlation_complete",
            alert_id=str(alert.SystemAlertId),
            correlated_count=len(correlated)
        )
        
        return correlated
    
    def _make_triage_decision(
        self,
        risk_score: int,
        correlated_alerts: List[SecurityAlert]
    ) -> TriageDecision:
        """
        Make triage decision based on risk and correlation.
        
        Args:
            risk_score: Calculated risk score
            correlated_alerts: List of correlated alerts
        
        Returns:
            TriageDecision: Triage decision
        """
        # High risk → escalate to incident
        if risk_score >= 70:
            return TriageDecision.ESCALATE_TO_INCIDENT
        
        # Medium risk with correlation → correlate with existing
        if risk_score >= 40 and correlated_alerts:
            return TriageDecision.CORRELATE_WITH_EXISTING
        
        # Low risk → likely false positive
        if risk_score < 30:
            return TriageDecision.MARK_AS_FALSE_POSITIVE
        
        # Medium risk without correlation → needs human review
        return TriageDecision.REQUIRE_HUMAN_REVIEW
    
    async def _generate_explanation(
        self,
        alert: SecurityAlert,
        risk_score: int,
        priority: TriagePriority,
        decision: TriageDecision,
        correlated_alerts: List[SecurityAlert]
    ) -> str:
        """
        Generate natural language explanation for triage decision.
        
        Args:
            alert: Security alert
            risk_score: Risk score
            priority: Priority level
            decision: Triage decision
            correlated_alerts: Correlated alerts
        
        Returns:
            str: Natural language explanation
        """
        # TODO: Use Azure OpenAI GPT-4 for explanation generation
        # For MVP, use template-based explanation
        
        explanation_parts = [
            f"This alert has been assigned a risk score of {risk_score}/100 and {priority} priority."
        ]
        
        # Add severity context
        explanation_parts.append(
            f"The alert severity is {alert.Severity}, which contributes to the overall risk assessment."
        )
        
        # Add correlation context
        if correlated_alerts:
            explanation_parts.append(
                f"This alert is correlated with {len(correlated_alerts)} recent alert(s) "
                f"involving the same entities, indicating potential attack campaign."
            )
        
        # Add MITRE context
        mitre_techniques = alert.ExtendedProperties.get("MitreTechniques", [])
        if mitre_techniques:
            techniques_str = ", ".join(mitre_techniques)
            explanation_parts.append(
                f"The alert maps to MITRE ATT&CK techniques: {techniques_str}."
            )
        
        # Add decision rationale
        decision_rationales = {
            TriageDecision.ESCALATE_TO_INCIDENT: (
                "This alert should be escalated to a security incident due to high risk score "
                "and potential impact to critical assets."
            ),
            TriageDecision.CORRELATE_WITH_EXISTING: (
                "This alert should be correlated with existing incidents due to entity overlap "
                "with recent alerts."
            ),
            TriageDecision.MARK_AS_FALSE_POSITIVE: (
                "This alert appears to be a false positive based on low risk indicators "
                "and benign patterns."
            ),
            TriageDecision.REQUIRE_HUMAN_REVIEW: (
                "This alert requires human analyst review to determine appropriate action "
                "due to moderate risk and insufficient context."
            )
        }
        explanation_parts.append(decision_rationales[decision])
        
        return " ".join(explanation_parts)
    
    async def _enrich_with_threat_intel(
        self,
        alert: SecurityAlert
    ) -> Dict[str, Any]:
        """
        Enrich alert with threat intelligence.
        
        Args:
            alert: Security alert
        
        Returns:
            Dict: Enrichment data
        """
        enrichment = {}
        
        # Lookup MITRE techniques in Attack dataset
        mitre_techniques = alert.ExtendedProperties.get("MitreTechniques", [])
        for technique_id in mitre_techniques:
            scenario = self.attack_loader.get_mitre_mapping(technique_id)
            if scenario:
                enrichment[technique_id] = scenario
        
        return enrichment


# Global agent instance
_triage_agent: Optional[AlertTriageAgent] = None


def get_triage_agent() -> AlertTriageAgent:
    """
    Get global Alert Triage Agent instance.
    
    Returns:
        AlertTriageAgent: Global triage agent
    """
    global _triage_agent
    if _triage_agent is None:
        _triage_agent = AlertTriageAgent()
    return _triage_agent
