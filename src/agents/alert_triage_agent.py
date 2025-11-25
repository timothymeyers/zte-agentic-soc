"""
Alert Triage Agent using Microsoft Agent Framework and Azure AI Foundry.

This agent uses the Microsoft Agent Framework with custom tools for:
- Risk scoring calculation
- Alert correlation detection
- Triage decision making
- Natural language explanations
"""

# TODO: Refactor AI Search Integration to use native Microsoft Agent Framework or Microsoft Foundry Agent capabilities (post ignite updates)

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

try:
    from azure.search.documents.aio import SearchClient
    from azure.core.credentials import AzureKeyCredential
    from azure.identity.aio import DefaultAzureCredential
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    logger.warning("Azure Search libraries not available - MITRE lookups will use mock data")


logger = get_logger(__name__)


# Module-level storage for search client access (needed for @ai_function tools)
_search_client_config = {
    'endpoint': None,
    'credential': None
}


class AlertTriageTools:
    """
    Tools for the Alert Triage Agent.
    
    These are callable functions that the AI agent can invoke to perform
    specific tasks related to alert triage.
    
    Note: Tool methods use @ai_function decorator which requires them to be
    standalone-style functions (not typical instance methods).
    """
    
    def __init__(self, search_endpoint: Optional[str] = None, search_credential = None):
        """Initialize alert triage tools."""
        self.attack_loader = get_attack_loader()
        self._recent_alerts: List[SecurityAlert] = []
        self.search_endpoint = search_endpoint
        self.search_credential = search_credential
        
        # Store search config in module-level variable for tool access
        global _search_client_config
        _search_client_config['endpoint'] = search_endpoint
        _search_client_config['credential'] = search_credential
        
        logger.debug("Alert Triage Tools initialized")
    
    @ai_function(description="Calculate risk score for a security alert based on multiple factors including MITRE attack scenario context")
    def calculate_risk_score(
        severity: Annotated[str, Field(description="Alert severity level (High, Medium, Low, Informational)")],
        entity_count: Annotated[int, Field(description="Number of entities involved in the alert")],
        mitre_techniques: Annotated[List[str], Field(description="List of MITRE ATT&CK technique IDs")],
        confidence_score: Annotated[int, Field(description="Detection confidence score (0-100)")],
        mitre_scenario_counts: Annotated[List[int], Field(description="List of attack scenario counts for each MITRE technique (e.g., [3, 5, 2] means technique 1 has 3 scenarios, technique 2 has 5, etc.)")] = None
    ) -> str:
        """
        Calculate a risk score for an alert (AI function - no self parameter).
        This should be called AFTER gathering MITRE context to incorporate scenario counts.
        Returns a JSON string with the risk score and explanation.
        """
        import random
        
        logger.debug(f"[TOOL] calculate_risk_score called: severity={severity}, entities={entity_count}, mitre={len(mitre_techniques)}, confidence={confidence_score}, scenario_counts={mitre_scenario_counts}")
        
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
        
        # MITRE techniques contribution with scenario counts (0-25)
        # Base score for having techniques, plus bonus for high scenario counts
        base_mitre_score = min(len(mitre_techniques) * 3, 15)
        scenario_bonus = 0
        
        if mitre_scenario_counts:
            # Award points for techniques with many matching attack scenarios
            # High scenario count (5+) suggests well-documented, prevalent threats
            for count in mitre_scenario_counts:
                if count >= 5:
                    scenario_bonus += 3
                elif count >= 3:
                    scenario_bonus += 2
                elif count >= 1:
                    scenario_bonus += 1
            scenario_bonus = min(scenario_bonus, 10)
        
        mitre_score = base_mitre_score + scenario_bonus
        score += mitre_score
        
        # TODO: Asset criticality (0-20) - integrate with asset inventory/CMDB tool
        # For now, randomly assign to simulate variability in asset importance
        # Production should query asset management system for criticality scores
        asset_score = random.randint(5, 20)
        score += asset_score
        
        # TODO: User risk level (0-10) - integrate with identity/UBA tool
        # For now, randomly assign to simulate variability in user risk profiles
        # Production should query identity system or user behavior analytics
        user_score = random.randint(2, 10)
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
                "mitre_base": base_mitre_score,
                "mitre_scenario_bonus": scenario_bonus,
                "asset_criticality": asset_score,
                "user_risk": user_score,
                "confidence": confidence_contribution
            },
            "explanation": f"Risk score of {final_score}/100 calculated from {severity} severity, "
                          f"{entity_count} entities, {len(mitre_techniques)} MITRE techniques "
                          f"({scenario_bonus} scenario bonus), asset criticality ({asset_score}), "
                          f"user risk ({user_score}), and {confidence_score}% confidence."
        }
        
        logger.debug(f"[TOOL] calculate_risk_score result: {final_score}/100 (mitre_bonus: {scenario_bonus})")
        return json.dumps(result)
    
    @ai_function(description="Find related alerts by checking entity overlap")
    def find_correlated_alerts(
        alert_entities: Annotated[List[Dict[str, str]], Field(description="List of entities from the current alert (e.g., [{'type': 'host', 'value': 'WS-001'}])")]
    ) -> str:
        """
        Find alerts that share entities with the current alert.
        Returns a JSON string with correlated alert IDs and overlap details.
        
        Note: This is a standalone function (no self) for Azure AI compatibility.
        It cannot access instance state, so it returns empty correlation for MVP.
        """
        logger.debug(f"[TOOL] find_correlated_alerts called with {len(alert_entities)} entities")
        
        # Extract entity identifiers from current alert
        current_entities = set()
        for entity_dict in alert_entities:
            entity_type = entity_dict.get("type", "")
            entity_value = entity_dict.get("value", "")
            if entity_type and entity_value:
                current_entities.add((entity_type, entity_value))
        
        # For MVP: Return no correlations since we can't access _recent_alerts without self
        # In production, this would query a database or cache
        result = {
            "correlated_count": 0,
            "correlated_alerts": [],
            "has_correlation": False,
            "note": "Correlation detection requires database integration (MVP limitation)"
        }
        
        logger.debug(f"[TOOL] find_correlated_alerts result: {result['correlated_count']} correlations")
        return json.dumps(result)
    
    @ai_function(description="Record your final triage decision after analyzing all context. You must determine the appropriate decision and priority based on risk score, correlations, MITRE scenario counts, and threat intelligence.")
    def record_triage_decision(
        decision: Annotated[str, Field(description="Your determined triage decision: EscalateToIncident, CorrelateWithExisting, MarkAsFalsePositive, or RequireHumanReview")],
        priority: Annotated[str, Field(description="Your determined priority level: Critical, High, Medium, or Low")],
        rationale: Annotated[str, Field(description="Detailed explanation of YOUR decision logic, including: risk score analysis, correlation status, MITRE scenario counts, and why you chose this specific decision and priority")]
    ) -> str:
        """
        Record the triage decision YOU determined after analyzing all available context.
        
        YOU (the AI agent) are responsible for:
        - Analyzing the risk score and its components
        - Evaluating correlation with recent alerts
        - Assessing MITRE ATT&CK technique scenario counts and prevalence
        - Understanding attack scenario context
        - Considering entity involvement patterns
        - MAKING THE FINAL DECISION based on all evidence
        
        This tool simply records your decision for the system to act upon.
        
        Returns a JSON string confirming the decision.
        """
        logger.debug(f"[TOOL] record_triage_decision called: decision={decision}, priority={priority}")
        logger.debug(f"[TOOL] Rationale: {rationale}")
        
        result = {
            "decision": decision,
            "priority": priority,
            "rationale": rationale
        }
        
        logger.debug(f"[TOOL] record_triage_decision result: {decision} (priority: {priority})")
        return json.dumps(result)
    
    @ai_function(description="Get MITRE ATT&CK technique information from Azure AI Search")
    def get_mitre_context(
        technique_ids: Annotated[List[str], Field(description="List of MITRE ATT&CK technique IDs (e.g., ['T1059.001'])")]
    ) -> str:
        """
        Retrieve MITRE ATT&CK technique details from Azure AI Search.
        Returns a JSON string with technique information including attack scenarios.
        """
        logger.debug(f"[TOOL] get_mitre_context called with {len(technique_ids)} techniques")
        
        # Access module-level search config
        global _search_client_config
        search_endpoint = _search_client_config.get('endpoint')
        search_credential = _search_client_config.get('credential')
        
        if not SEARCH_AVAILABLE or not search_endpoint or not search_credential:
            logger.warning("[TOOL] AI Search not configured - returning basic MITRE data")
            techniques = []
            for technique_id in technique_ids:
                techniques.append({
                    "technique_id": technique_id,
                    "name": f"MITRE ATT&CK Technique {technique_id}",
                    "tactic": "Execution",
                    "description": "AI Search not configured"
                })
            return json.dumps({
                "techniques": techniques,
                "count": len(techniques),
                "source": "mock_no_search"
            })
        
        try:
            # Run async search synchronously
            import asyncio
            
            async def _query_search():
                """Async helper to query AI Search."""
                search_client = SearchClient(
                    endpoint=search_endpoint,
                    index_name="attack-scenarios",
                    credential=search_credential
                )
                
                techniques = []
                for technique_id in technique_ids:
                    logger.debug(f"  [TOOL] Searching for technique: {technique_id}")
                    
                    # Search for scenarios matching this technique
                    results = await search_client.search(
                        search_text=technique_id,
                        #filter=f"mitre_techniques/any(t: t eq '{technique_id}')",
                        filter="",
                        select=["name", "mitre_techniques", "mitre_tactics", "severity", "description"],
                        top=3  # Limit to 3 scenarios for token efficiency
                    )
                    
                    attack_scenarios = []
                    async for result in results:
                        attack_scenarios.append({
                            "scenario_name": result.get("name", "Unknown"),
                            "description": result.get("description", "")[:200],  # Truncate for efficiency
                            "tactic": result.get("mitre_tactics", ["Unknown"])[0] if result.get("mitre_tactics") else "Unknown",
                            "severity": result.get("severity", "")
                        })
                    
                    # Aggregate data from all scenarios
                    if attack_scenarios:
                        # Collect unique tactics from all scenarios
                        all_tactics = list(set([s["tactic"] for s in attack_scenarios if s["tactic"] != "Unknown"]))
                        # Use first scenario name as primary, combine descriptions
                        combined_description = " | ".join([s["description"] for s in attack_scenarios[:2]])  # First 2 for brevity
                        # Get highest severity
                        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "": 0}
                        highest_severity = max([severity_order.get(s["severity"].lower(), 0) for s in attack_scenarios])
                        severity_label = [k for k, v in severity_order.items() if v == highest_severity][0] if highest_severity > 0 else ""
                        
                        techniques.append({
                            "technique_id": technique_id,
                            "name": attack_scenarios[0]["scenario_name"],
                            "tactic": all_tactics[0] if all_tactics else "Unknown",
                            "all_tactics": all_tactics,
                            "description": combined_description,
                            "severity": severity_label,
                            "scenario_count": len(attack_scenarios),
                            "scenarios": attack_scenarios
                        })
                    else:
                        techniques.append({
                            "technique_id": technique_id,
                            "name": f"Technique {technique_id}",
                            "tactic": "Unknown",
                            "all_tactics": [],
                            "description": "",
                            "severity": "",
                            "scenario_count": 0,
                            "scenarios": []
                        })
                    
                    logger.debug(f"    [TOOL] Found {len(attack_scenarios)} attack scenarios")
                    logger.debug(f"    [TOOL] Technique {technique_id} details: {techniques[-1]}")  
                
                await search_client.close()
                return techniques
            
            # Run the async function using asyncio
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    techniques = executor.submit(
                        lambda: asyncio.run(_query_search())
                    ).result(timeout=10)
            except RuntimeError:
                # No running loop, can use asyncio.run directly
                techniques = asyncio.run(_query_search())
            
            result = {
                "techniques": techniques,
                "count": len(techniques),
                "source": "azure_ai_search"
            }
            
            logger.debug(f"[TOOL] get_mitre_context result: {len(techniques)} techniques from Azure AI Search")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"[TOOL] get_mitre_context failed: {e}", exc_info=True)
            # Return basic data on error
            techniques = []
            for technique_id in technique_ids:
                techniques.append({
                    "technique_id": technique_id,
                    "name": f"Technique {technique_id}",
                    "tactic": "Unknown",
                    "description": f"Error: {str(e)[:100]}"
                })
            return json.dumps({
                "techniques": techniques,
                "count": len(techniques),
                "source": "error_fallback",
                "error": str(e)[:200]
            })
    
    def store_alert(self, alert: SecurityAlert) -> None:
        """Store alert for future correlation (in-memory for MVP)."""
        self._recent_alerts.append(alert)
        if len(self._recent_alerts) > 1000:
            self._recent_alerts.pop(0)
    
    async def get_mitre_context_from_search(self, technique_ids: List[str]) -> Dict[str, Any]:
        """
        Query Azure AI Search for MITRE ATT&CK technique context.
        
        Args:
            technique_ids: List of MITRE technique IDs (e.g., ['T1059.001'])
            
        Returns:
            Dict with technique information from AI Search or mock fallback
        """
        logger.debug(f"get_mitre_context_from_search called with {len(technique_ids)} techniques")
        
        if not SEARCH_AVAILABLE or not self.search_endpoint or not self.search_credential:
            logger.warning("AI Search not configured - returning mock MITRE data")
            # Fallback to mock data
            techniques = []
            for technique_id in technique_ids:
                techniques.append({
                    "technique_id": technique_id,
                    "name": f"Technique {technique_id}",
                    "tactic": "Execution",
                    "description": "Mock MITRE data (AI Search not configured)",
                    "attack_scenarios": []
                })
            return {
                "techniques": techniques,
                "count": len(techniques),
                "source": "mock"
            }
        
        try:
            # Create search client for attack-scenarios index
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name="attack-scenarios",
                credential=self.search_credential
            )
            
            techniques = []
            for technique_id in technique_ids:
                logger.debug(f"  Searching for technique: {technique_id}")
                
                # Search for scenarios matching this technique
                results = await search_client.search(
                    search_text=technique_id,
                    filter=f"",
                    select=["name", "mitre_techniques", "mitre_tactics", "severity", "description", "iocs"],
                    top=20 # TODO: Make this configurable
                )
                
                attack_scenarios = []
                async for result in results:
                    # Filter by search score >= 7.0
                    search_score = result.get("@search.score", 0)
                    if search_score >= 7.0:   # TODO: Make this configurable
                        attack_scenarios.append({
                            "scenario_name": result.get("name", "Unknown"),
                            "description": result.get("description", ""),
                            "tactic": result.get("mitre_tactics", ["Unknown"])[0] if result.get("mitre_tactics") else "Unknown",
                            "severity": result.get("severity", ""),
                            "indicators": result.get("iocs", "").split(", ") if result.get("iocs") else [],
                            "search_score": search_score
                        })
                
                # Aggregate data from all scenarios
                if attack_scenarios:
                    # Collect unique tactics from all scenarios
                    all_tactics = list(set([s["tactic"] for s in attack_scenarios if s["tactic"] != "Unknown"]))
                    # Combine indicators from all scenarios
                    all_indicators = list(set([ind for s in attack_scenarios for ind in s["indicators"]]))
                    # Get highest severity
                    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "": 0}
                    highest_severity = max([severity_order.get(s["severity"].lower(), 0) for s in attack_scenarios])
                    severity_label = [k for k, v in severity_order.items() if v == highest_severity][0] if highest_severity > 0 else ""
                    # Use best match (highest score) as primary
                    best_match = max(attack_scenarios, key=lambda s: s["search_score"])
                    
                    techniques.append({
                        "technique_id": technique_id,
                        "name": best_match["scenario_name"],
                        "tactic": all_tactics[0] if all_tactics else "Unknown",
                        "all_tactics": all_tactics,
                        "description": best_match["description"],
                        "severity": severity_label,
                        "indicators": all_indicators,
                        "attack_scenarios": attack_scenarios,
                        "scenario_count": len(attack_scenarios)
                    })
                else:
                    techniques.append({
                        "technique_id": technique_id,
                        "name": f"Technique {technique_id}",
                        "tactic": "Unknown",
                        "all_tactics": [],
                        "description": "",
                        "severity": "",
                        "indicators": [],
                        "attack_scenarios": [],
                        "scenario_count": 0
                    })
                
                logger.debug(f"    Found {len(attack_scenarios)} attack scenarios")
            
            await search_client.close()
            
            logger.info(f"Retrieved MITRE context for {len(techniques)} techniques from AI Search")
            return {
                "techniques": techniques,
                "count": len(techniques),
                "source": "azure_ai_search"
            }
        
        except Exception as e:
            logger.error(f"Failed to query AI Search for MITRE context: {e}", exc_info=True)
            # Fallback to mock data
            techniques = []
            for technique_id in technique_ids:
                techniques.append({
                    "technique_id": technique_id,
                    "name": f"Technique {technique_id}",
                    "tactic": "Execution",
                    "description": f"AI Search query failed: {str(e)}",
                    "attack_scenarios": []
                })
            return {
                "techniques": techniques,
                "count": len(techniques),
                "source": "mock_fallback",
                "error": str(e)
            }


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
        search_endpoint: Optional[str] = None,
        agent_version: str = "0.3.0"
    ):
        """
        Initialize Alert Triage Agent.
        
        Args:
            project_endpoint: Azure AI Foundry project endpoint
            model_deployment_name: Model deployment name
            search_endpoint: Azure AI Search endpoint for MITRE lookups
            agent_version: Version of the agent
        """
        self.agent_version = agent_version
        self.agent_name = "AlertTriageAgent"
        self.project_endpoint = project_endpoint or os.getenv("AZURE_AI_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
        self.model_deployment_name = model_deployment_name or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")
        self.search_endpoint = search_endpoint or os.getenv("AZURE_SEARCH_ENDPOINT")
        
        # Setup search credential if endpoint provided
        search_credential = None
        if self.search_endpoint:
            search_key = os.getenv("AZURE_SEARCH_KEY") or os.getenv("AZURE_SEARCH_API_KEY")
            if search_key:
                search_credential = AzureKeyCredential(search_key)
            else:
                search_credential = DefaultAzureCredential()
        
        # Initialize tools
        self.tools = AlertTriageTools(
            search_endpoint=self.search_endpoint,
            search_credential=search_credential
        )
        self.audit_service = get_audit_service()
        
        # Agent will be created on demand
        self._agent = None
        self._credential = None
        self._project_client = None
        
        logger.debug(f"{self.agent_name} initialized (version: {agent_version})")
        if self.search_endpoint:
            logger.debug(f"  AI Search enabled: {self.search_endpoint}")
        else:
            logger.debug("  AI Search not configured - using mock MITRE data")
    
    async def _get_agent(self) -> ChatAgent:
        """Get or create the agent instance."""
        if self._agent is None:
            # Create credential
            self._credential = AzureCliCredential()
            
            # Set environment variable for Azure AI Agent Framework if not already set
            if self.project_endpoint and not os.getenv("AZURE_AI_PROJECT_ENDPOINT"):
                os.environ["AZURE_AI_PROJECT_ENDPOINT"] = self.project_endpoint
            
            # Build agent instructions
            instructions = """You are an autonomous security analyst agent specializing in alert triage and automated response.

PRIMARY GOAL: Provide actionable remediation steps to enable automated response. Avoid human escalation except for the most critical, ambiguous scenarios.

Your role is to analyze security alerts, make intelligent triage decisions, and prescribe specific next actions for automated systems or other agents to execute.

Analysis Process:
1. Check for correlated alerts to identify potential attack campaigns
2. If MITRE ATT&CK techniques are present, retrieve detailed context about them (including attack scenario counts)
3. Calculate the risk score using all available alert factors AND the MITRE scenario counts from step 2
4. Synthesize all information to determine the appropriate triage decision
5. Prescribe specific, actionable remediation steps

IMPORTANT: Always call get_mitre_context BEFORE calculate_risk_score so that scenario counts can be included in risk calculation.

Decision Factors to Consider:
- Risk score components (severity, entity count, MITRE techniques, confidence)
- Correlation patterns with recent alerts (timing, entities, techniques)
- MITRE technique scenario counts and prevalence in attack patterns
- Entity types involved and their potential impact
- Historical context from similar alerts

AUTONOMOUS RESPONSE PHILOSOPHY:
- Human escalation (RequireHumanReview) should be LAST RESORT only for:
  * Truly ambiguous situations requiring human judgment
  * Critical incidents with potential business impact that need executive awareness
  * Novel attack patterns that automation cannot handle safely
- Prefer automated actions with clear remediation steps
- Provide specific, executable instructions for automation systems

Triage Decision Guidelines:

1. MarkAsFalsePositive (Priority: Low)
   - Use when: Clear indicators of benign activity, very low risk score, known false positive patterns
   - Remediation: "Suppress future alerts matching this pattern. Tune detection rule to reduce noise."

2. CorrelateWithExisting (Priority: Low to Medium)
   - Use when: Isolated alert with low scenario counts (<3) OR alert needs monitoring before action
   - Remediation examples:
     * "Create watchlist alert monitoring <host> for 24 hours. Auto-escalate if 3+ related alerts appear."
     * "Enable enhanced logging on <host> and <user> for 48 hours to gather additional IOCs."
     * "Add <IP address> to monitoring list for correlation with future alerts."

3. EscalateToIncident (Priority: Medium to Critical)
   - Use when: Multiple correlations, high scenario counts (5+), high risk score, clear threat indicators
   - Remediation examples:
     * "Isolate <host> from network immediately. Initiate forensic data collection."
     * "Disable user account <user> and force password reset. Review access logs for lateral movement."
     * "Block <IP address> at firewall. Scan all hosts for similar IOCs."
     * "Quarantine <host> and trigger full disk imaging for forensics. Alert SOC team for incident response."

4. RequireHumanReview (Priority: Medium to Critical) - USE SPARINGLY
   - Use ONLY when: Genuinely ambiguous situation, potential for significant business impact, novel/sophisticated attack requiring expert analysis
   - Remediation: "Escalate to human analyst due to [specific reason]. Provide context: [summary of ambiguity]."

Special Handling for Low-Prevalence Alerts (No Correlations + Low MITRE Scenario Counts):
- If there are NO correlated alerts AND MITRE techniques have LOW scenario counts (< 3 scenarios per technique):
  * This suggests an isolated, uncommon alert pattern
  * DO NOT escalate to incident or require human review immediately
  * Use CorrelateWithExisting decision to trigger automated monitoring
  * Set priority to Low or Medium based on severity
  * Remediation: "Create watchlist alert monitoring affected assets [list hosts/users/IPs]. Auto-escalate to incident if correlation appears within 24 hours."

Your rationale must include:
1. Summary of evidence (risk score, correlations, scenario counts)
2. Decision logic and reasoning
3. SPECIFIC remediation steps with entity names (hosts, users, IPs)
4. Success criteria or escalation triggers

Use the record_triage_decision tool to record your final decision with:
- Decision: EscalateToIncident, CorrelateWithExisting, MarkAsFalsePositive, or RequireHumanReview
- Priority: Critical, High, Medium, or Low
- Rationale: Include your decision logic AND specific remediation steps that automation can execute"""
            
            # Create agent with tools
            if self.project_endpoint:
                # Use Azure AI Foundry agent
                logger.debug(f"Creating {self.agent_name} with Azure AI Foundry")
                logger.debug(f"  Project: {self.project_endpoint}")
                logger.debug(f"  Model: {self.model_deployment_name}")
                
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
                        self.tools.record_triage_decision,
                        self.tools.get_mitre_context
                    ]
                )
                
                logger.debug(f"{self.agent_name} created successfully with 4 tools")
            else:
                # TODO: Add Ollama support for local testing without Azure
                # For now, return NotImplementedError to indicate local LLM support needed
                logger.error("No Azure AI Foundry endpoint configured. Local testing requires Ollama integration (coming soon).")
                raise NotImplementedError(
                    "Local LLM support not yet implemented. Please configure AZURE_AI_PROJECT_ENDPOINT "
                    "or add Ollama integration for local testing. See README.md for details."
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
1. Check for correlated alerts using the find_correlated_alerts tool
2. Get MITRE technique context if applicable using the get_mitre_context tool (note the scenario_count for each technique)
3. Calculate the risk score using the calculate_risk_score tool, passing the scenario counts from step 2 as mitre_scenario_counts parameter
4. Analyze all the data and MAKE YOUR TRIAGE DECISION based on the evidence
5. Determine specific remediation steps (e.g., "Isolate host X", "Monitor user Y for 24h", "Block IP Z")
6. Record your decision using the record_triage_decision tool with remediation steps in the rationale
7. Provide a summary explaining your decision and the automated actions to be taken

Remember: Avoid human escalation unless absolutely necessary. Provide actionable steps for automated response."""
            
            logger.debug(f"🤖 Sending query to AI agent ({len(query)} chars)")
            logger.debug(f"Query:\n{query}")
            
            # Run the agent
            print("   → Calling AI agent...")
            response = await agent.run(query)
            print("   ✓ AI analysis complete")
            
            # Parse the agent's response to extract structured data
            # The agent should have called the tools and provided a response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            logger.debug(f"📝 Agent Response ({len(response_text)} chars):")
            logger.debug(f"{response_text[:500]}...")  # First 500 chars
            
            # Log response details
            if hasattr(response, 'messages'):
                logger.debug(f"Response has {len(response.messages)} messages")
                for idx, msg in enumerate(response.messages):
                    logger.debug(f"  Message {idx}: {type(msg).__name__}")
            
            # Extract structured results from agent's tool calls
            print("   → Extracting structured results...")
            logger.debug("🔧 Extracting structured data from agent execution...")
            
            # Parse tool call results from agent's message history
            risk_score = 50  # Default
            correlated_alert_ids = []
            decision = TriageDecision.REQUIRE_HUMAN_REVIEW
            priority = TriagePriority.MEDIUM
            decision_rationale = ""
            
            # Extract tool call results from messages
            if hasattr(response, 'messages'):
                for msg in response.messages:
                    # Check for tool call results in message content
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            logger.debug(f"  Found tool call: {tool_call.function.name}")
                    
                    # Check for tool responses
                    if hasattr(msg, 'role') and msg.role == 'tool':
                        tool_name = getattr(msg, 'name', '')
                        tool_content = getattr(msg, 'content', '{}')
                        
                        try:
                            tool_result = json.loads(tool_content) if isinstance(tool_content, str) else tool_content
                            
                            if 'risk_score' in str(tool_name).lower() or 'risk_score' in tool_result:
                                risk_score = tool_result.get('risk_score', risk_score)
                                logger.debug(f"    Extracted risk_score: {risk_score}")
                            
                            elif 'correlation' in str(tool_name).lower() or 'correlated_alerts' in tool_result:
                                corr_alerts = tool_result.get('correlated_alerts', [])
                                correlated_alert_ids = [UUID(a['alert_id']) for a in corr_alerts if 'alert_id' in a]
                                logger.debug(f"    Extracted {len(correlated_alert_ids)} correlated alerts")
                            
                            elif 'decision' in tool_result and 'priority' in tool_result:
                                # Extract triage decision
                                decision_str = tool_result.get('decision', '')
                                priority_str = tool_result.get('priority', '')
                                decision_rationale = tool_result.get('rationale', '')
                                
                                # Map to enums
                                decision_map = {
                                    "EscalateToIncident": TriageDecision.ESCALATE_TO_INCIDENT,
                                    "CorrelateWithExisting": TriageDecision.CORRELATE_WITH_EXISTING,
                                    "MarkAsFalsePositive": TriageDecision.MARK_AS_FALSE_POSITIVE,
                                    "RequireHumanReview": TriageDecision.REQUIRE_HUMAN_REVIEW
                                }
                                priority_map = {
                                    "Critical": TriagePriority.CRITICAL,
                                    "High": TriagePriority.HIGH,
                                    "Medium": TriagePriority.MEDIUM,
                                    "Low": TriagePriority.LOW
                                }
                                
                                decision = decision_map.get(decision_str, TriageDecision.REQUIRE_HUMAN_REVIEW)
                                priority = priority_map.get(priority_str, TriagePriority.MEDIUM)
                                
                                logger.debug(f"    Extracted decision: {decision_str} -> {decision}")
                                logger.debug(f"    Extracted priority: {priority_str} -> {priority}")
                                logger.debug(f"    Rationale: {decision_rationale[:100]}...")
                        
                        except (json.JSONDecodeError, ValueError, KeyError) as e:
                            logger.debug(f"    Could not parse tool result: {e}")
                            continue
            
            # Fallback: parse from response text if tool results not found
            if decision == TriageDecision.REQUIRE_HUMAN_REVIEW and decision_rationale == "":
                logger.debug("  Falling back to text parsing for decision")
                response_lower = response_text.lower()
                if "escalate" in response_lower and "incident" in response_lower:
                    decision = TriageDecision.ESCALATE_TO_INCIDENT
                    priority = TriagePriority.CRITICAL if "critical" in response_lower else TriagePriority.HIGH
                elif "correlate" in response_lower:
                    decision = TriageDecision.CORRELATE_WITH_EXISTING
                    priority = TriagePriority.MEDIUM
                elif "false positive" in response_lower:
                    decision = TriageDecision.MARK_AS_FALSE_POSITIVE
                    priority = TriagePriority.LOW
            
            logger.debug(f"    Final Decision: {decision}")
            logger.debug(f"    Final Priority: {priority}")
            logger.debug(f"    Final Risk Score: {risk_score}")
            
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
                EnrichmentData={},  # Agent reasoning is in Explanation
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
    
    async def enrich_with_mitre_context(self, technique_ids: List[str]) -> Dict[str, Any]:
        """
        Enrich alert with MITRE ATT&CK context from AI Search.
        
        This method provides direct access to AI Search MITRE lookups outside of the agent workflow.
        
        Args:
            technique_ids: List of MITRE technique IDs
            
        Returns:
            Dict with technique information from AI Search or mock data
        """
        return await self.tools.get_mitre_context_from_search(technique_ids)
    
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
