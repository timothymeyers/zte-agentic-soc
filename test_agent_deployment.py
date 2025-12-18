#!/usr/bin/env python3
"""
Test script to verify agent deployment to Microsoft Foundry.
"""

import os
import sys
from src.deployment.deploy_agents import AgentDeployer, AGENT_DEFINITIONS

def test_agent_deployment():
    """Test deploying the manager agent to Foundry."""
    print("=" * 80)
    print("Testing Agent Deployment to Microsoft Foundry")
    print("=" * 80)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not endpoint:
        print("❌ AZURE_AI_FOUNDRY_PROJECT_ENDPOINT not set")
        return False
    
    if not model:
        print("❌ Model deployment name not set (AZURE_AI_MODEL_DEPLOYMENT_NAME or AZURE_OPENAI_DEPLOYMENT_NAME)")
        return False
    
    print(f"✓ Endpoint: {endpoint}")
    print(f"✓ Model: {model}")
    
    # Initialize deployer
    print("\n2. Initializing AgentDeployer...")
    try:
        deployer = AgentDeployer()
        print("✓ AgentDeployer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AgentDeployer: {e}")
        return False
    
    # Test listing agents
    print("\n3. Listing existing agents...")
    try:
        agents = deployer.list_agents()
        print(f"✓ Found {len(agents)} existing agents")
        for agent in agents:
            print(f"  - {agent.name} (id: {agent.id})")
    except Exception as e:
        print(f"❌ Failed to list agents: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test deploying manager agent
    print("\n4. Deploying SOC_Manager agent...")
    manager_def = AGENT_DEFINITIONS["manager"]
    try:
        agent = deployer.deploy_agent(
            name=manager_def["name"],
            instructions_file=manager_def["instructions_file"],
            description=manager_def["description"],
        )
        print(f"✓ Agent deployed successfully!")
        print(f"  - Name: {agent.name}")
        print(f"  - ID: {agent.id}")
        print(f"  - Model: {agent.model}")
        if hasattr(agent, 'created_at'):
            print(f"  - Created: {agent.created_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to deploy agent: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_deployment()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ All tests passed! Agent deployment is working correctly.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ Tests failed! Please check the errors above.")
        print("=" * 80)
        sys.exit(1)
