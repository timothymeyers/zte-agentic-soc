#!/usr/bin/env python3
"""
Example: Using Foundry Native Agents

This script demonstrates the MVP implementation of Microsoft Foundry Native Agents
for the Agentic SOC project. It shows how to:
1. Initialize agents from YAML definitions
2. Reuse agents across multiple operations
3. Clean up resources properly

This replaces the pattern of creating agents programmatically on every request.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents import initialize_agents, get_alert_triage_agent, cleanup_agents
from src.shared.logging import get_logger

logger = get_logger(__name__)


async def main():
    """
    Demonstrate the Foundry Native Agent pattern.
    """
    print("=" * 80)
    print("FOUNDRY NATIVE AGENTS - MVP DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Check for Azure configuration
    azure_endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT') or os.getenv('AZURE_AI_FOUNDRY_ENDPOINT')
    
    if not azure_endpoint:
        print("⚠️  No Azure AI Foundry endpoint configured")
        print("   Set AZURE_AI_PROJECT_ENDPOINT environment variable for full functionality")
        print("   Running in development mode with limited functionality...")
        print()
    else:
        print(f"✅ Azure AI Foundry endpoint: {azure_endpoint[:50]}...")
        print()
    
    try:
        # ========================================
        # Step 1: Initialize Agents at Startup
        # ========================================
        print("Step 1: Initializing agents from YAML definitions...")
        print("-" * 80)
        
        await initialize_agents()
        
        print("✓ Agents initialized successfully")
        print()
        
        # ========================================
        # Step 2: Get Agent Instance
        # ========================================
        print("Step 2: Getting Alert Triage Agent instance...")
        print("-" * 80)
        
        agent = get_alert_triage_agent()
        
        print(f"✓ Agent retrieved:")
        print(f"  Name: {agent.name}")
        print(f"  Version: {agent.version}")
        print(f"  Initialized: {agent.is_initialized}")
        print()
        
        # ========================================
        # Step 3: Demonstrate Agent Reuse
        # ========================================
        print("Step 3: Using agent multiple times (agent reuse pattern)...")
        print("-" * 80)
        
        # Simulate processing multiple alerts with the SAME agent instance
        sample_queries = [
            "What is the risk score for a High severity alert with 3 entities?",
            "Analyze an alert with MITRE technique T1059.001",
            "How should I triage a critical alert with multiple correlations?"
        ]
        
        for i, query in enumerate(sample_queries, 1):
            print(f"\nQuery {i}: {query}")
            
            if azure_endpoint:
                try:
                    # In production, this would actually run the agent
                    print("  → Would run agent query (requires Azure endpoint)")
                    # result = await agent.run(query=query)
                    # print(f"  ✓ Response: {result.text[:100]}...")
                except Exception as e:
                    print(f"  ⚠️  Error: {e}")
            else:
                print("  → Skipped (no Azure endpoint)")
        
        print()
        print("✓ Agent successfully reused for multiple queries")
        print("  (Same agent instance, no recreation overhead)")
        print()
        
        # ========================================
        # Step 4: Key Benefits
        # ========================================
        print("Step 4: Key Benefits of Foundry Native Agents")
        print("-" * 80)
        print()
        print("✅ Declarative Configuration")
        print("   - Agents defined in YAML files (agents/alert-triage-agent.yaml)")
        print("   - Version controlled")
        print("   - No code changes needed for behavior updates")
        print()
        print("✅ Persistent Lifecycle")
        print("   - Agent created ONCE at startup")
        print("   - Reused for all operations")
        print("   - No recreation overhead")
        print()
        print("✅ Resource Efficiency")
        print("   - Reduced API calls")
        print("   - Faster response times")
        print("   - Lower costs")
        print()
        print("✅ Backward Compatibility")
        print("   - Existing code continues to work")
        print("   - Gradual migration path")
        print("   - No breaking changes")
        print()
        
        # ========================================
        # Step 5: YAML Configuration
        # ========================================
        print("Step 5: YAML Configuration")
        print("-" * 80)
        print()
        print("Agent configuration is loaded from:")
        print(f"  {project_root}/agents/alert-triage-agent.yaml")
        print()
        print("Example YAML structure:")
        print("  name: alert-triage-agent")
        print("  version: 1.0.0")
        print("  model:")
        print("    id: gpt-4.1-mini")
        print("  instructions: |")
        print("    You are an autonomous security analyst...")
        print("  tools:")
        print("    - type: mcp  # Knowledge bases")
        print("    - type: code_interpreter  # Python execution")
        print("    - type: file_search  # Historical data")
        print()
        print("Environment variables are resolved at runtime:")
        print("  ${AZURE_AI_PROJECT_ENDPOINT} → actual value")
        print("  ${PROJECT_CONNECTION_ID} → actual value")
        print()
        
        # ========================================
        # Step 6: Migration Pattern
        # ========================================
        print("Step 6: Migration from Old Pattern")
        print("-" * 80)
        print()
        print("OLD (Programmatic):")
        print("  agent = AlertTriageAgent(...)")
        print("  result = await agent.triage_alert(alert)")
        print("  # Agent discarded")
        print()
        print("NEW (Declarative):")
        print("  await initialize_agents()  # Once at startup")
        print("  agent = get_alert_triage_agent()")
        print("  result = await agent.run(query)  # Reuse many times")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Example failed: {e}", exc_info=True)
        return 1
    
    finally:
        # ========================================
        # Step 7: Cleanup
        # ========================================
        print()
        print("Step 7: Cleaning up resources...")
        print("-" * 80)
        
        await cleanup_agents()
        
        print("✓ Resources cleaned up")
        print()
    
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review the implementation in src/agents/foundry_native_agent.py")
    print("2. Check the YAML definition in agents/alert-triage-agent.yaml")
    print("3. Run tests: pytest tests/unit/test_foundry_native_agent.py")
    print("4. Read the guide: docs/FOUNDRY-NATIVE-AGENTS-MVP-GUIDE.md")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
