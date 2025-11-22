#!/usr/bin/env python3
"""
Demo script for Alert Triage Agent.

This script demonstrates the Alert Triage Agent analyzing security alerts
and making triage decisions with explanations.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.alert_triage.agent import get_triage_agent
from src.data.datasets import get_guide_loader
from src.shared.logging import configure_logging, get_logger
from src.orchestration.orchestrator import get_orchestrator
from src.orchestration.event_handlers import get_event_bus, EventType


logger = get_logger(__name__)


async def demo_alert_triage():
    """Demonstrate alert triage functionality."""
    
    logger.info("=" * 80)
    logger.info("ALERT TRIAGE AGENT DEMONSTRATION")
    logger.info("=" * 80)
    
    # Initialize components
    triage_agent = get_triage_agent()
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
        
        # Triage the alert
        triage_result = await triage_agent.triage_alert(alert)
        
        # Display results
        logger.info(f"✅ Triage completed:")
        logger.info(f"   Risk Score: {triage_result.RiskScore}/100")
        logger.info(f"   Priority: {triage_result.Priority}")
        logger.info(f"   Decision: {triage_result.TriageDecision}")
        logger.info(f"   Correlated Alerts: {len(triage_result.CorrelatedAlertIds)}")
        logger.info(f"   Processing Time: {triage_result.ProcessingTimeMs}ms")
        logger.info(f"\n📝 Explanation:")
        logger.info(f"   {triage_result.Explanation}")
        logger.info("")
    
    event_bus.register(EventType.ALERT_INGESTION, handle_alert_event)
    
    # Load sample alerts
    logger.info("\n🔍 Loading sample alerts from GUIDE dataset...")
    alerts = guide_loader.load_alerts(max_alerts=5)
    logger.info(f"Loaded {len(alerts)} alerts")
    
    # Process each alert through orchestrator
    logger.info("\n🚀 Processing alerts through orchestration pipeline...\n")
    
    for i, alert in enumerate(alerts, 1):
        logger.info(f"--- Alert {i}/{len(alerts)} ---")
        await orchestrator.process_alert(alert)
        await asyncio.sleep(0.5)  # Brief pause for readability
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATION COMPLETE")
    logger.info("=" * 80)
    logger.info("\nKey Features Demonstrated:")
    logger.info("✓ Alert ingestion and triage")
    logger.info("✓ Risk score calculation")
    logger.info("✓ Alert correlation")
    logger.info("✓ Triage decision making")
    logger.info("✓ Natural language explanations")
    logger.info("✓ Audit logging")
    logger.info("✓ Event-driven orchestration")
    logger.info("")


if __name__ == "__main__":
    # Configure logging
    configure_logging(log_level="INFO", json_output=False)
    
    # Run demo
    try:
        asyncio.run(demo_alert_triage())
    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)
