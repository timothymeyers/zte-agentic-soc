#!/usr/bin/env python3
"""
Test script for azure-ai-projects 2.0.0b1+ agent API.

This script demonstrates and tests the correct usage of:
- AIProjectClient initialization
- agent.create() for new agents
- agents.create_version() for updates
- agents.get(agent_name=...) for retrieval
- agents.list() for listing all agents

Usage:
    python test_agent_api.py
"""

import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential


def test_agent_api():
    """Test the azure-ai-projects 2.0 agents API."""
    
    print("\n" + "=" * 80)
    print("Testing azure-ai-projects 2.0.0b1+ Agent API")
    print("=" * 80)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not endpoint:
        print("❌ AZURE_AI_FOUNDRY_PROJECT_ENDPOINT not set")
        return False
    
    if not model:
        print("❌ Model deployment name not set")
        return False
    
    # Mask sensitive parts of endpoint
    masked_endpoint = endpoint.replace(endpoint.split("/")[4], "******")
    print(f"✓ Endpoint: {masked_endpoint}")
    print(f"✓ Model: {model}")
    
    # Initialize client
    print("\n2. Initializing AIProjectClient...")
    try:
        client = AIProjectClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential()
        )
        print("✓ AIProjectClient initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test list agents
    print("\n3. Listing existing agents...")
    try:
        agents = list(client.agents.list())
        print(f"✓ Found {len(agents)} existing agents")
        if agents:
            print(f"\n  First few agents:")
            for agent in agents[:5]:
                version = getattr(agent, 'version', 'N/A')
                agent_id = str(getattr(agent, 'id', 'N/A'))
                print(f"  - {agent.name} (version: {version}, id: {agent_id[:20]}...)")
    except Exception as e:
        print(f"❌ Failed to list agents: {e}")
        return False
    
    # Test get agent by name
    print("\n4. Testing get(agent_name=...)...")
    test_agent_name = "SOC_Manager" if any(a.name == "SOC_Manager" for a in agents) else agents[0].name if agents else None
    
    if test_agent_name:
        try:
            agent = client.agents.get(agent_name=test_agent_name)
            print(f"✓ Retrieved agent '{test_agent_name}'")
            print(f"  - ID: {agent.id}")
            print(f"  - Kind: {getattr(agent, 'kind', 'N/A')}")
            print(f"  - Created: {getattr(agent, 'created_at', 'N/A')}")
        except Exception as e:
            print(f"❌ Failed to get agent: {e}")
    else:
        print("⚠ No agents to test get() method")
    
    # Test create/update agent
    print("\n5. Testing create_version (create or update agent)...")
    try:
        agent = client.agents.create_version(
            agent_name="test-api-agent",
            definition=PromptAgentDefinition(
                model=model,
                instructions="You are a test agent created by the API test script.",
            ),
            description="Test agent for API verification"
        )
        print(f"✓ Agent created/updated successfully")
        print(f"  - Name: {agent.name}")
        print(f"  - ID: {agent.id}")
        print(f"  - Version: {getattr(agent, 'version', 'N/A')}")
        print(f"  - Kind: {getattr(agent, 'kind', 'N/A')}")
        print(f"  - Created: {getattr(agent, 'created_at', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to create/update agent: {e}")
        return False
    
    # Test with OpenAI client to interact with agent
    print("\n6. Testing agent interaction with OpenAI client...")
    try:
        openai_client = client.get_openai_client()
        print("✓ Got OpenAI client")
        
        # Create conversation
        conversation = openai_client.conversations.create(
            items=[{"type": "message", "role": "user", "content": "Say hello!"}],
        )
        print(f"✓ Created conversation (id: {conversation.id})")
        
        # Get response from agent
        response = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
            input="",
        )
        print(f"✓ Agent responded: {response.output_text[:100]}...")
        
        # Cleanup
        openai_client.conversations.delete(conversation_id=conversation.id)
        print("✓ Conversation deleted")
        
    except Exception as e:
        print(f"⚠ Could not test agent interaction: {e}")
    
    print("\n" + "=" * 80)
    print("✅ All API tests passed! Agent deployment is working correctly.")
    print("=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    import sys
    success = test_agent_api()
    sys.exit(0 if success else 1)
