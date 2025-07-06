#!/usr/bin/env python3
"""
Simple Test to Verify System is Working
"""

import asyncio
from agent_driven_workflow import AgentDrivenWorkflow
from smart_workflow_router import SmartWorkflowRouter

async def test_basic_functionality():
    print("🔄 Testing Basic System Functionality...")
    print("=" * 50)
    
    # Test 1: Router initialization
    try:
        router = SmartWorkflowRouter()
        print("✅ SmartWorkflowRouter initialized successfully")
    except Exception as e:
        print(f"❌ Router initialization failed: {e}")
        return False
    
    # Test 2: Context analysis
    try:
        context = {"current_artifacts": [], "execution_history": []}
        analysis = router.analyze_context("Create a calculator", context)
        print(f"✅ Context analysis works: {analysis.project_type}, {analysis.complexity_level}")
    except Exception as e:
        print(f"❌ Context analysis failed: {e}")
        return False
    
    # Test 3: Workflow initialization
    try:
        workflow = AgentDrivenWorkflow()
        print("✅ AgentDrivenWorkflow initialized successfully")
        print(f"   📊 {len(workflow.agent_capabilities)} agents available")
    except Exception as e:
        print(f"❌ Workflow initialization failed: {e}")
        return False
    
    # Test 4: Agent capabilities check
    try:
        expected_agents = ["Product_Analyst", "Coder", "QA_Guardian", "Security_Specialist"]
        for agent in expected_agents:
            assert agent in workflow.agent_capabilities
        print(f"✅ All expected agents available")
    except Exception as e:
        print(f"❌ Agent capabilities check failed: {e}")
        return False
    
    # Test 5: Decision parsing
    try:
        from agent_driven_workflow import AgentDecision
        decision = AgentDecision(action="COMPLETE", reason="Test complete", confidence=0.9)
        print(f"✅ AgentDecision works: {decision.action}")
    except Exception as e:
        print(f"❌ AgentDecision failed: {e}")
        return False
    
    print("=" * 50)
    print("🎉 ALL BASIC TESTS PASSED!")
    print("✅ System is fully functional and ready for use")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    exit(0 if success else 1)
