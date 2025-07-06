#!/usr/bin/env python3
"""
Test Agent Knowledge Integration
Verify all agents have proper access to tools and workflows
"""
import asyncio
import pytest
from tools.agent_knowledge_integration import get_knowledge_registry

@pytest.mark.asyncio
async def test_agent_knowledge():
    """Test agent knowledge integration"""
    print("🔄 Testing Agent Knowledge Integration...")
    
    # Get knowledge registry
    registry = await get_knowledge_registry()
    
    # Get all agents from agent factory
    from tools.agent_factory import AgentFactory
    agent_factory = AgentFactory()
    all_agents = agent_factory.list_available_agents()
    
    print(f"✅ Found {len(all_agents)} agents: {', '.join(all_agents)}")
    
    # Test each agent's capabilities
    for agent_name in all_agents:
        print(f"\n📋 Testing {agent_name}:")
        
        # Get agent capabilities
        capabilities = await registry.get_agent_capabilities(agent_name)
        
        if not capabilities:
            print(f"   ❌ No capabilities found for {agent_name}")
            continue
            
        agent_profile = capabilities.get("agent_profile", {})
        available_tools = capabilities.get("available_tools", [])
        available_workflows = capabilities.get("available_workflows", [])
        
        print(f"   📊 Role: {agent_profile.get('primary_role', 'Unknown')}")
        print(f"   🛠️  Capabilities: {len(agent_profile.get('capabilities', []))} items")
        print(f"   🔧 Available Tools: {len(available_tools)} tools")
        print(f"   🔄 Workflows: {len(available_workflows)} workflows")
        
        # Show some tool details
        if available_tools:
            print(f"   📝 Sample tools: {', '.join([t['name'] for t in available_tools[:3]])}...")
        else:
            print(f"   ⚠️  No tools available!")
            
        # Show workflow participation
        if available_workflows:
            print(f"   📝 Sample workflows: {', '.join([w['name'] for w in available_workflows[:3]])}...")
        else:
            print(f"   ⚠️  No workflow participation!")
    
    # Test agent knowledge package generation
    print(f"\n🔄 Testing Knowledge Package Generation...")
    for agent_name in ["Product_Analyst", "Coder", "UX_UI_Designer", "Tester", "Git_Agent"]:
        knowledge_package = await registry.generate_agent_knowledge_package(agent_name)
        tools_count = len(knowledge_package.get("available_tools", []))
        workflows_count = len(knowledge_package.get("workflow_participation", []))
        
        print(f"   📦 {agent_name}: {tools_count} tools, {workflows_count} workflows")
    
    # Test workflow requirements
    print(f"\n🔄 Testing Workflow Requirements...")
    workflows = ["complex_ui_feature", "simple_linear_feature", "bug_fix", "unknown_workflow"]
    
    for workflow_type in workflows:
        requirements = await registry.get_workflow_requirements(workflow_type)
        required_agents = requirements.get("required_agents", [])
        required_tools = requirements.get("required_tools", [])
        
        print(f"   🔄 {workflow_type}: {len(required_agents)} agents, {len(required_tools)} tools")
        if required_agents:
            print(f"      👥 Agents: {', '.join(required_agents[:3])}...")
        if required_tools:
            print(f"      🔧 Tools: {', '.join(required_tools[:3])}...")
    
    # Test validation for each agent
    validation_passed = 0
    print(f"\n🔄 Testing Agent Validation...")
    
    for agent_name in all_agents:
        validation_result = await registry.validate_agent_knowledge(agent_name)
        
        if (validation_result.get("tools_accessible", False) and 
            validation_result.get("workflows_understood", False)):
            validation_passed += 1
            print(f"   ✅ {agent_name}: Validated successfully")
        else:
            print(f"   ❌ {agent_name}: Validation failed - {validation_result.get('issues', [])}")
    
    print(f"\n✅ Agent validation: {validation_passed}/{len(all_agents)} agents validated")
    
    print(f"\n🎉 Agent Knowledge Integration Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_agent_knowledge())
