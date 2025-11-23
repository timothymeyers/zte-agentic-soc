#!/usr/bin/env python3
"""
Demo script for Alert Triage Agent using Microsoft Agent Framework.

This script demonstrates the Alert Triage Agent analyzing security alerts
using the Microsoft Agent Framework with Azure AI Foundry.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.alert_triage.agent_framework import get_triage_agent
from src.data.datasets import get_guide_loader
from src.shared.logging import configure_logging, get_logger
from src.orchestration.orchestrator import get_orchestrator
from src.orchestration.event_handlers import get_event_bus, OrchestrationEventType


logger = get_logger(__name__)


async def demo_agent_framework():
    """Demonstrate alert triage functionality using Microsoft Agent Framework."""
    
    logger.info("=" * 80)
    logger.info("ALERT TRIAGE AGENT - MICROSOFT AGENT FRAMEWORK DEMO")
    logger.info("=" * 80)
    
    # Check for required environment variables
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")
    
    if not project_endpoint:
        logger.error("\n❌ AZURE_AI_PROJECT_ENDPOINT not set!")
        logger.error("Azure AI Foundry endpoint is required for the agent to function.")
        logger.error("Local LLM support (Ollama) is planned but not yet implemented.")
        logger.error("\nTo run this demo, configure Azure AI Foundry:")
        logger.error("  export AZURE_AI_PROJECT_ENDPOINT='https://your-project.services.ai.azure.com/api/projects/project-id'")
        logger.error("  export AZURE_AI_MODEL_DEPLOYMENT_NAME='gpt-4.1-mini'\n")
        logger.error("See README.md for setup instructions.")
        return
    else:
        logger.info(f"\n✓ Using Azure AI Foundry")
        logger.info(f"  Project: {project_endpoint}")
        logger.info(f"  Model: {model_deployment}\n")
    
    # Initialize components
    triage_agent = get_triage_agent(
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment
    )
    guide_loader = get_guide_loader()
    orchestrator = get_orchestrator()
    event_bus = get_event_bus()
    
    # Register triage agent with orchestrator
    orchestrator.register_agent("AlertTriageAgent", triage_agent)
    
    # Register triage event handler
    async def handle_alert_event(event_data):
        """Handle alert ingestion events."""
        from src.shared.schemas import SecurityAlert
        alert_dict = event_data["alert"]
        alert = SecurityAlert(**alert_dict)
        
        logger.info(f"\n📬 Processing alert: {alert.AlertName}")
        logger.info(f"   Severity: {alert.Severity}")
        logger.info(f"   Entities: {len(alert.Entities)}")
        
        # Triage the alert using the agent framework
        triage_result = await triage_agent.triage_alert(alert)
        
        # Display results
        logger.info(f"\n✅ Triage completed:")
        logger.info(f"   Risk Score: {triage_result.RiskScore}/100")
        logger.info(f"   Priority: {triage_result.Priority}")
        logger.info(f"   Decision: {triage_result.TriageDecision}")
        logger.info(f"   Correlated Alerts: {len(triage_result.CorrelatedAlertIds)}")
        logger.info(f"   Processing Time: {triage_result.ProcessingTimeMs}ms")
        logger.info(f"\n🤖 AI Agent Explanation:")
        logger.info(f"   {triage_result.Explanation[:500]}...")  # First 500 chars
        logger.info("")
    
    event_bus.register(OrchestrationEventType.ALERT_INGESTION, handle_alert_event)
    
    # Load sample alerts
    logger.info("\n🔍 Loading sample alerts from GUIDE dataset...")
    alerts = guide_loader.load_alerts(max_alerts=3)  # Start with just 3 for demo
    logger.info(f"Loaded {len(alerts)} alerts\n")
    
    # Process each alert through orchestrator
    logger.info("🚀 Processing alerts through orchestration pipeline...\n")
    
    try:
        for i, alert in enumerate(alerts, 1):
            logger.info(f"--- Alert {i}/{len(alerts)} ---")
            await orchestrator.process_alert(alert)
            await asyncio.sleep(1)  # Brief pause for readability
    finally:
        # Clean up agent resources
        await triage_agent.close()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATION COMPLETE")
    logger.info("=" * 80)
    logger.info("\n✨ Key Features Demonstrated:")
    logger.info("✓ Microsoft Agent Framework integration")
    logger.info("✓ Custom AI function tools (@ai_function)")
    logger.info("✓ Azure AI Foundry SDK (when configured)")
    logger.info("✓ Agent-powered risk scoring")
    logger.info("✓ Agent-powered correlation detection")
    logger.info("✓ Agent-powered triage decisions")
    logger.info("✓ AI-generated natural language explanations")
    logger.info("✓ Audit logging and metrics")
    logger.info("✓ Event-driven orchestration")
    logger.info("")
    
    logger.info("📚 Architecture:")
    logger.info("  ChatAgent (Microsoft Agent Framework)")
    logger.info("    ↓")
    logger.info("  Custom Tools (@ai_function decorators)")
    logger.info("    ├─ calculate_risk_score")
    logger.info("    ├─ find_correlated_alerts")
    logger.info("    ├─ make_triage_decision")
    logger.info("    └─ get_mitre_context")
    logger.info("    ↓")
    logger.info("  AI Model (GPT-4.1-mini via Azure AI Foundry)")
    logger.info("    ↓")
    logger.info("  Structured Output (TriageResult)")
    logger.info("")


if __name__ == "__main__":
    # Configure logging
    configure_logging(log_level="INFO", json_output=False)
    
    # Run demo
    try:
        asyncio.run(demo_agent_framework())
    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)
