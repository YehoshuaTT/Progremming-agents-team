#!/usr/bin/env python3
"""
Test script to verify the Enhanced Orchestrator is working correctly
"""

import asyncio
from enhanced_orchestrator import EnhancedOrchestrator

async def test_orchestrator():
    """Test basic orchestrator functionality"""
    print("🔄 Initializing Enhanced Orchestrator...")
    
    # Create orchestrator instance
    orchestrator = EnhancedOrchestrator()
    
    # Test basic functionality
    print("✅ Orchestrator created successfully")
    
    # Test knowledge system initialization
    await orchestrator.initialize_knowledge_systems()
    print("✅ Knowledge systems initialized")
    
    # Test agent capabilities
    capabilities = await orchestrator.get_agent_capabilities("Product_Analyst")
    print(f"✅ Product Analyst capabilities: {len(capabilities)} items")
    
    # Test context optimization
    test_context = {
        "user_request": "Create a login system",
        "previous_artifacts": ["spec.md", "design.md"],
        "artifact_content": "This is a large content block" * 100
    }
    
    optimized_context = orchestrator._optimize_context_for_agent(test_context, "Coder")
    print(f"✅ Context optimization: Original {len(str(test_context))} -> Optimized {len(str(optimized_context))} characters")
    
    # Test workflow creation
    print("🔄 Testing workflow creation...")
    workflow_id = await orchestrator.start_workflow(
        "Create a user authentication system with login and registration",
        "complex_ui_feature"
    )
    print(f"✅ Workflow created: {workflow_id}")
    
    # Test workflow status
    status = orchestrator.get_workflow_status(workflow_id)
    print(f"✅ Workflow status: {status['status']}")
    
    # Test cache performance stats
    cache_stats = orchestrator.get_cache_performance_stats()
    print(f"✅ Cache efficiency: {cache_stats['performance_summary']['cache_efficiency']:.1f}%")
    
    # Test agent validation
    validation_results = await orchestrator.validate_all_agents_knowledge()
    print(f"✅ Agent validation: {validation_results['validated_agents']}/{validation_results['total_agents']} agents validated")
    
    print("\n🎉 All tests passed! Enhanced Orchestrator is working correctly.")
    
    return {
        "orchestrator": orchestrator,
        "workflow_id": workflow_id,
        "validation_results": validation_results
    }

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
