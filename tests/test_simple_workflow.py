#!/usr/bin/env python3
"""
Simple test script to verify the workflow components are working
"""

import asyncio
from agent_driven_workflow import AgentDrivenWorkflow, AgentDecision
from smart_workflow_router import SmartWorkflowRouter, ContextAnalysis

async def test_basic_functionality():
    """Test basic functionality without complex mocks"""
    print("🔄 Testing basic functionality...")
    
    # Test 1: SmartWorkflowRouter initialization
    try:
        router = SmartWorkflowRouter()
        assert router is not None
        assert hasattr(router, 'agent_rules')
        print("✅ SmartWorkflowRouter initialization OK")
    except Exception as e:
        print(f"❌ SmartWorkflowRouter initialization failed: {e}")
        return False
    
    # Test 2: Context analysis
    try:
        context = {"user_request": "Build a calculator", "execution_history": []}
        analysis = router.analyze_context("Build a calculator", context)
        assert isinstance(analysis, ContextAnalysis)
        assert analysis.complexity_level in ["simple", "medium", "complex"]
        print("✅ Context analysis OK")
    except Exception as e:
        print(f"❌ Context analysis failed: {e}")
        return False
    
    # Test 3: Agent recommendations
    try:
        recommendations = router.get_agent_recommendations(analysis, "Product_Analyst", context)
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 0
        print("✅ Agent recommendations OK")
    except Exception as e:
        print(f"❌ Agent recommendations failed: {e}")
        return False
    
    # Test 4: Agent skipping logic
    try:
        should_skip, reason = router.should_skip_agent("Product_Analyst", analysis, context)
        assert isinstance(should_skip, bool)
        assert isinstance(reason, str)
        print("✅ Agent skipping logic OK")
    except Exception as e:
        print(f"❌ Agent skipping logic failed: {e}")
        return False
    
    # Test 5: Context optimization
    try:
        large_context = {
            "user_request": "Build something",
            "execution_history": ["Agent1"] * 50,
            "artifacts": ["file1.py"] * 20
        }
        optimized = router.optimize_workflow_context(large_context)
        assert isinstance(optimized, dict)
        print("✅ Context optimization OK")
    except Exception as e:
        print(f"❌ Context optimization failed: {e}")
        return False
    
    # Test 6: AgentDrivenWorkflow initialization
    try:
        workflow = AgentDrivenWorkflow(debug_mode=False)
        assert workflow is not None
        assert hasattr(workflow, 'orchestrator')
        assert hasattr(workflow, 'smart_router')
        assert len(workflow.agent_capabilities) >= 13
        print("✅ AgentDrivenWorkflow initialization OK")
    except Exception as e:
        print(f"❌ AgentDrivenWorkflow initialization failed: {e}")
        return False
    
    # Test 7: Agent decision parsing
    try:
        response = "Task completed successfully. [COMPLETE]"
        decision = workflow.parse_agent_decision(response)
        assert isinstance(decision, AgentDecision)
        assert decision.action == "COMPLETE"
        print("✅ Agent decision parsing OK")
    except Exception as e:
        print(f"❌ Agent decision parsing failed: {e}")
        return False
    
    # Test 8: Agent validation
    try:
        valid_agent = workflow.validate_agent_name("Product_Analyst")
        invalid_agent = workflow.validate_agent_name("NonExistentAgent")
        assert valid_agent is True
        assert invalid_agent is False
        print("✅ Agent validation OK")
    except Exception as e:
        print(f"❌ Agent validation failed: {e}")
        return False
    
    print("\n🎉 All basic functionality tests passed!")
    return True

async def test_workflow_mock_execution():
    """Test workflow execution with minimal mocking"""
    print("🔄 Testing workflow execution...")
    
    try:
        workflow = AgentDrivenWorkflow(debug_mode=False)
        
        # Mock the orchestrator method
        original_method = workflow.orchestrator.execute_llm_call_with_cache
        
        async def mock_execute(agent_name, prompt, context):
            return f"Task completed by {agent_name}. [COMPLETE]"
        
        workflow.orchestrator.execute_llm_call_with_cache = mock_execute
        
        # Run a simple workflow
        result = await workflow.run_agent_driven_workflow("Create a simple calculator")
        
        # Restore original method
        workflow.orchestrator.execute_llm_call_with_cache = original_method
        
        assert result is not None
        assert "workflow_id" in result
        assert "final_status" in result
        assert result["final_status"] in ["COMPLETED", "MAX_ITERATIONS_REACHED"]
        
        print("✅ Workflow execution test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow execution test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Simple Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    basic_success = await test_basic_functionality()
    print()
    
    # Test workflow execution
    workflow_success = await test_workflow_mock_execution()
    print()
    
    if basic_success and workflow_success:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("✅ The workflow system is working correctly!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
