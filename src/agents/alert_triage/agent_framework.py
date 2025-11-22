"""
Alert Triage Agent using Microsoft Agent Framework and Azure AI Foundry.

This agent uses the Microsoft Agent Framework with custom tools for:
- Risk scoring calculation
- Alert correlation detection
- Triage decision making
- Natural language explanations
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Annotated, List, Dict, Any, Optional
from uuid import UUID, uuid4
import time

from pydantic import Field
from agent_framework import ChatAgent, ai_function
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient

from src.shared.schemas import (
    SecurityAlert,
    TriageResult,
    TriagePriority,
    TriageDecision,
    SeverityLevel
)
from src.shared.logging import get_logger
from src.shared.metrics import counter
from src.shared.audit import get_audit_service, AuditResult
from src.data.datasets import get_attack_loader


logger = get_logger(__name__)


class AlertTriageTools:
    """
    Tools for the Alert Triage Agent.
    
    These are callable functions that the AI agent can invoke to perform
    specific tasks related to alert triage.
    """
    
    def __init__(self):
        """Initialize alert triage tools."""
        self.attack_loader = get_attack_loader()
        self._recent_alerts: List[SecurityAlert] = []
        logger.info("Alert Triage Tools initialized")
    
    @ai_function(description="Calculate risk score for a security alert based on multiple factors")
    async def calculate_risk_score(
        self,
        severity: Annotated[str, Field(description="Alert severity level (High, Medium, Low, Informational)")],
        entity_count: Annotated[int, Field(description="Number of entities involved in the alert")],
        mitre_techniques: Annotated[List[str], Field(description="List of MITRE ATT&CK technique IDs")],
        confidence_score: Annotated[int, Field(description="Detection confidence score (0-100)")]
    ) -> str:
        """
        Calculate a risk score for an alert.
        
        Returns a JSON string with the risk score and explanation.
        """
        score = 0
        
        # Severity contribution (0-30)
        severity_scores = {
            "High": 30,
            "Medium": 20,
            "Low": 10,
            "Informational": 5
        }
        severity_score = severity_scores.get(severity, 10)
        score += severity_score
        
        # Entity count contribution (0-10)
        entity_score = min(entity_count * 2, 10)
        score += entity_score
        
        # MITRE techniques contribution (0-20)
        mitre_score = min(len(mitre_techniques) * 5, 20)
        score += mitre_score
        
        # Asset criticality (0-20) - placeholder for MVP
        asset_score = 15
        score += asset_score
        
        # User risk level (0-10) - placeholder for MVP
        user_score = 5
        score += user_score
        
        # Confidence score (0-10)
        confidence_contribution = int(confidence_score / 10)
        score += confidence_contribution
        
        # Cap at 100
        final_score = min(score, 100)
        
        result = {
            "risk_score": final_score,
            "breakdown": {
                "severity": severity_score,
                "entities": entity_score,
                "mitre_techniques": mitre_score,
                "asset_criticality": asset_score,
                "user_risk": user_score,
                "confidence": confidence_contribution
            },
            "explanation": f"Risk score of {final_score}/100 calculated from {severity} severity, "
                          f"{entity_count} entities, {len(mitre_techniques)} MITRE techniques, "
                          f"and {confidence_score}% confidence."
        }
        
        return str(result)
    
    @ai_function(description="Find related alerts by checking entity overlap")
    async def find_correlated_alerts(
        self,
        alert_entities: Annotated[List[Dict[str, str]], Field(description="List of entities from the current alert (e.g., [{\"type\": \"host\", \"value\": \"WS-001\"}])")]
    ) -> str:
        """
        Find alerts that share entities with the current alert.
        
        Returns a JSON string with correlated alert IDs and overlap details.
        """
        # Extract entity identifiers from current alert
        current_entities = set()
        for entity_dict in alert_entities:
            entity_type = entity_dict.get("type", "")
            entity_value = entity_dict.get("value", "")
            if entity_type and entity_value:
                current_entities.add((entity_type, entity_value))
        
        correlated = []
        
        # Check recent alerts for entity overlap
        for past_alert in self._recent_alerts[-100:]:
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
            overlap = current_entities & past_entities
            if overlap:
                correlated.append({
                    "alert_id": str(past_alert.SystemAlertId),
                    "alert_name": past_alert.AlertName,
                    "shared_entities": [f"{t}:{v}" for t, v in overlap]
                })
        
        result = {
            "correlated_count": len(correlated),
            "correlated_alerts": correlated[:10],  # Top 10
            "has_correlation": len(correlated) > 0
        }
        
        logger.debug(f"Found {len(correlated)} correlated alerts")
        return str(result)
    
    @ai_function(description="Determine triage decision based on risk score and correlation")
    async def make_triage_decision(
        self,
        risk_score: Annotated[int, Field(description="Calculated risk score (0-100)")],
        has_correlation: Annotated[bool, Field(description="Whether the alert correlates with recent alerts")]
    ) -> str:
        """
        Make a triage decision based on risk and correlation.
        
        Returns a JSON string with the decision and rationale.
        """
        if risk_score >= 70:
            decision = "EscalateToIncident"
            priority = "Critical" if risk_score >= 80 else "High"
            rationale = "High risk score indicates potential significant threat requiring immediate incident response."
        elif risk_score >= 40 and has_correlation:
            decision = "CorrelateWithExisting"
            priority = "Medium"
            rationale = "Moderate risk with correlation suggests part of existing incident or campaign."
        elif risk_score < 30:
            decision = "MarkAsFalsePositive"
            priority = "Low"
            rationale = "Low risk indicators suggest benign activity or false positive."
        else:
            decision = "RequireHumanReview"
            priority = "Medium"
            rationale = "Moderate risk without clear correlation requires analyst assessment."
        
        result = {
            "decision": decision,
            "priority": priority,
            "rationale": rationale
        }
        
        return str(result)
    
    @ai_function(description="Get MITRE ATT&CK technique information from the Attack dataset")
    async def get_mitre_context(
        self,
        technique_ids: Annotated[List[str], Field(description="List of MITRE ATT&CK technique IDs (e.g., ['T1059.001'])")]
    ) -> str:
        """
        Retrieve MITRE ATT&CK technique details from the Attack dataset.
        
        Returns a JSON string with technique information.
        """
        techniques = []
        for technique_id in technique_ids:
            scenario = self.attack_loader.get_mitre_mapping(technique_id)
            if scenario:
                techniques.append({
                    "technique_id": technique_id,
                    "name": scenario.get("name", "Unknown"),
                    "tactic": scenario.get("tactic", "Unknown"),
                    "description": scenario.get("description", "No description available")
                })
        
        result = {
            "techniques": techniques,
            "count": len(techniques)
        }
        
        return str(result)
    
    def store_alert(self, alert: SecurityAlert) -> None:
        """Store alert for future correlation (in-memory for MVP)."""
        self._recent_alerts.append(alert)
        if len(self._recent_alerts) > 1000:
            self._recent_alerts.pop(0)


class AlertTriageAgent:
    """
    AI-powered alert triage agent using Microsoft Agent Framework.
    
    This agent analyzes security alerts using AI with custom tools for:
    - Risk scoring
    - Alert correlation
    - Triage decision making
    - Threat intelligence enrichment
    """
    
    def __init__(
        self,
        project_endpoint: Optional[str] = None,
        model_deployment_name: Optional[str] = None,
        agent_version: str = "0.2.0"
    ):
        """
        Initialize Alert Triage Agent.
        
        Args:
            project_endpoint: Azure AI Foundry project endpoint
            model_deployment_name: Model deployment name
            agent_version: Version of the agent
        """
        self.agent_version = agent_version
        self.agent_name = "AlertTriageAgent"
        self.project_endpoint = project_endpoint or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.model_deployment_name = model_deployment_name or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")
        
        # Initialize tools
        self.tools = AlertTriageTools()
        self.audit_service = get_audit_service()
        
        # Agent will be created on demand
        self._agent = None
        self._credential = None
        self._project_client = None
        
        logger.info(f"{self.agent_name} initialized (version: {agent_version})")
    
    async def _get_agent(self) -> ChatAgent:
        """Get or create the agent instance."""
        if self._agent is None:
            # Create credential
            self._credential = AzureCliCredential()
            
            # Build agent instructions
            instructions = """You are an expert security analyst specializing in alert triage.

Your role is to analyze security alerts and make intelligent triage decisions by:
1. Calculating risk scores based on multiple factors
2. Finding correlated alerts to detect campaigns
3. Making triage decisions with clear rationales
4. Providing actionable recommendations

Always use the provided tools to analyze alerts systematically. Your responses should be:
- Clear and concise
- Based on evidence from the tools
- Include risk scores and correlations
- Provide specific recommendations

When triaging an alert:
1. First, calculate the risk score using all available factors
2. Check for correlated alerts
3. Get MITRE technique context if applicable
4. Make a triage decision based on risk and correlation
5. Explain your reasoning clearly"""
            
            # Create agent with tools
            if self.project_endpoint:
                # Use Azure AI Foundry agent
                self._project_client = AIProjectClient(
                    endpoint=self.project_endpoint,
                    credential=self._credential
                )
                
                self._agent = ChatAgent(
                    chat_client=AzureAIAgentClient(
                        project_client=self._project_client,
                        async_credential=self._credential,
                        model_deployment_name=self.model_deployment_name,
                        agent_name=self.agent_name
                    ),
                    instructions=instructions,
                    tools=[
                        self.tools.calculate_risk_score,
                        self.tools.find_correlated_alerts,
                        self.tools.make_triage_decision,
                        self.tools.get_mitre_context
                    ]
                )
            else:
                # Use OpenAI client for local testing (fallback)
                logger.warning("No Azure AI Foundry endpoint configured, using OpenAI client")
                from agent_framework.openai import OpenAIChatClient
                
                self._agent = ChatAgent(
                    chat_client=OpenAIChatClient(),
                    instructions=instructions,
                    tools=[
                        self.tools.calculate_risk_score,
                        self.tools.find_correlated_alerts,
                        self.tools.make_triage_decision,
                        self.tools.get_mitre_context
                    ]
                )
        
        return self._agent
    
    async def triage_alert(self, alert: SecurityAlert) -> TriageResult:
        """
        Triage a security alert using the AI agent.
        
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
            # Get agent
            agent = await self._get_agent()
            
            # Prepare alert data for the agent
            entities_list = []
            for entity in alert.Entities:
                if "HostName" in entity.Properties:
                    entities_list.append({"type": "host", "value": entity.Properties["HostName"]})
                if "UserName" in entity.Properties:
                    entities_list.append({"type": "user", "value": entity.Properties["UserName"]})
                if "IPAddress" in entity.Properties:
                    entities_list.append({"type": "ip", "value": entity.Properties["IPAddress"]})
            
            mitre_techniques = alert.ExtendedProperties.get("MitreTechniques", [])
            confidence = alert.ExtendedProperties.get("ConfidenceScore", 75)
            
            # Build the triage query for the agent
            query = f"""Analyze this security alert and provide a triage decision:

Alert Name: {alert.AlertName}
Alert Type: {alert.AlertType}
Severity: {alert.Severity}
Description: {alert.Description}
Number of Entities: {len(alert.Entities)}
MITRE Techniques: {', '.join(mitre_techniques) if mitre_techniques else 'None'}
Confidence Score: {confidence}%

Entities involved:
{chr(10).join([f"- {e['type']}: {e['value']}" for e in entities_list])}

Please:
1. Calculate the risk score using the calculate_risk_score tool
2. Check for correlated alerts using the find_correlated_alerts tool
3. Get MITRE technique context if applicable using the get_mitre_context tool
4. Make a triage decision using the make_triage_decision tool
5. Provide a clear explanation of your decision and recommendations"""
            
            # Run the agent
            response = await agent.run(query)
            
            # Parse the agent's response to extract structured data
            # The agent should have called the tools and provided a response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract risk score from tools (we need to track tool calls)
            # For MVP, we'll parse from the response or call tools again
            # In production, we'd track tool call results
            
            # For now, make direct tool calls to get structured data
            risk_result = await self.tools.calculate_risk_score(
                severity=alert.Severity,
                entity_count=len(alert.Entities),
                mitre_techniques=mitre_techniques,
                confidence_score=confidence
            )
            risk_data = json.loads(risk_result)  # Safe JSON parsing
            risk_score = risk_data["risk_score"]
            
            correlation_result = await self.tools.find_correlated_alerts(
                alert_entities=entities_list
            )
            correlation_data = json.loads(correlation_result)  # Safe JSON parsing
            correlated_alert_ids = [UUID(a["alert_id"]) for a in correlation_data.get("correlated_alerts", [])]
            
            decision_result = await self.tools.make_triage_decision(
                risk_score=risk_score,
                has_correlation=correlation_data.get("has_correlation", False)
            )
            decision_data = json.loads(decision_result)  # Safe JSON parsing
            
            # Map decision strings to enums
            priority_map = {
                "Critical": TriagePriority.CRITICAL,
                "High": TriagePriority.HIGH,
                "Medium": TriagePriority.MEDIUM,
                "Low": TriagePriority.LOW
            }
            decision_map = {
                "EscalateToIncident": TriageDecision.ESCALATE_TO_INCIDENT,
                "CorrelateWithExisting": TriageDecision.CORRELATE_WITH_EXISTING,
                "MarkAsFalsePositive": TriageDecision.MARK_AS_FALSE_POSITIVE,
                "RequireHumanReview": TriageDecision.REQUIRE_HUMAN_REVIEW
            }
            
            priority = priority_map.get(decision_data["priority"], TriagePriority.MEDIUM)
            decision = decision_map.get(decision_data["decision"], TriageDecision.REQUIRE_HUMAN_REVIEW)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create triage result with AI-generated explanation
            triage_result = TriageResult(
                AlertId=alert.SystemAlertId,
                TriageId=uuid4(),
                Timestamp=datetime.utcnow(),
                RiskScore=risk_score,
                Priority=priority,
                TriageDecision=decision,
                Explanation=response_text,  # AI-generated explanation
                CorrelatedAlertIds=correlated_alert_ids,
                EnrichmentData=risk_data.get("breakdown", {}),
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
                    "decision": decision,
                    "ai_powered": True
                }
            )
            
            # Update metrics
            counter("alerts_triaged_total").inc()
            
            # Store alert for future correlation
            self.tools.store_alert(alert)
            
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
    
    async def close(self):
        """Clean up resources."""
        if self._credential:
            await self._credential.close()
        if self._project_client:
            await self._project_client.close()
        logger.info(f"{self.agent_name} resources cleaned up")


# Global agent instance
_triage_agent: Optional[AlertTriageAgent] = None


def get_triage_agent(
    project_endpoint: Optional[str] = None,
    model_deployment_name: Optional[str] = None
) -> AlertTriageAgent:
    """
    Get global Alert Triage Agent instance.
    
    Args:
        project_endpoint: Azure AI Foundry project endpoint
        model_deployment_name: Model deployment name
    
    Returns:
        AlertTriageAgent: Global triage agent
    """
    global _triage_agent
    if _triage_agent is None:
        _triage_agent = AlertTriageAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name
        )
    return _triage_agent
