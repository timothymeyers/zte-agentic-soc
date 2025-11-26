#!/usr/bin/env python3
"""
Demo: Foundry Declarative Alert Triage Agent.

Shows agent loaded from YAML with Foundry IQ integration.
Uses the new declarative agent framework approach.

Reference: https://github.com/microsoft/agent-framework/tree/main/agent-samples/foundry
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.alert_triage_agent_v2 import AlertTriageAgentV2
from src.data.datasets import get_guide_loader
from src.shared.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def demo():
    """Run Foundry declarative agent demo."""

    print("=" * 80)
    print("FOUNDRY DECLARATIVE ALERT TRIAGE AGENT DEMO")
    print("=" * 80)
    print()
    print("Features:")
    print("  ✓ Declarative YAML definition")
    print("  ✓ Foundry IQ for MITRE ATT&CK knowledge (via MCP)")
    print("  ✓ No custom tools - LLM handles all reasoning")
    print("  ✓ AgentFactory for YAML parsing and agent creation")
    print()

    # Initialize agent (one-time)
    print("🔄 Initializing Foundry agent from YAML...")
    agent = AlertTriageAgentV2()
    try:
        agent.initialize()
        print("✅ Agent ready\n")
    except Exception as e:
        print(f"⚠️  Agent initialization note: {e}")
        print("   (This is expected if Foundry IQ is not configured)")
        print("   Continuing with demo to show the architecture...\n")

    # Load sample alerts
    print("📥 Loading sample alerts...")
    loader = get_guide_loader()
    alerts = loader.load_alerts(max_alerts=3)
    print(f"✅ Loaded {len(alerts)} alerts\n")

    # Process alerts (reusing same agent)
    for i, alert in enumerate(alerts, 1):
        print(f"{'─' * 80}")
        print(f"📋 ALERT {i}/{len(alerts)}: {alert.AlertName}")
        print(f"{'─' * 80}")
        print(f"   Severity: {alert.Severity}")
        print(f"   Type: {alert.AlertType}")
        print(f"   Description: {alert.Description[:100]}...")
        print()

        try:
            result = await agent.triage_alert(alert)

            print(f"✅ Triage Complete:")
            print(f"   Risk Score: {result.RiskScore}/100")
            print(f"   Priority: {result.Priority.value}")
            print(f"   Decision: {result.TriageDecision.value}")
            print(f"   Time: {result.ProcessingTimeMs}ms")
            print(f"\n   Explanation (first 300 chars):")
            print(f"   {result.Explanation[:300]}...")
            print()
        except Exception as e:
            print(f"❌ Triage failed: {e}")
            print("   (This is expected if Azure AI Foundry is not configured)")
            print()

    # Summary
    print(f"{'=' * 80}")
    print("✨ Demo Complete")
    print("   • Agent loaded from YAML definition")
    print("   • Used Foundry IQ for MITRE context (if configured)")
    print("   • Declarative approach - no custom tools needed")
    print(f"{'=' * 80}\n")

    print("📚 Architecture:")
    print("  YAML Definition (alert_triage_agent.yaml)")
    print("    ↓")
    print("  AgentFactory (agent-framework-declarative)")
    print("    ├─ Resolves =Env.Variable PowerFx references")
    print("    ├─ Configures MCP tools (Foundry IQ)")
    print("    └─ Creates ChatAgent")
    print("    ↓")
    print("  ChatAgent with Foundry IQ")
    print("    ↓")
    print("  AI Model (Azure AI Foundry)")
    print("    ↓")
    print("  Structured Output (TriageResult)")
    print()


if __name__ == "__main__":
    # Configure logging
    configure_logging(log_level="INFO", json_output=False)

    # Suppress verbose logging
    import logging
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Run demo
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)
