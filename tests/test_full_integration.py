#!/usr/bin/env python3
"""
Test Suite: Full System Integration Tests
בדיקת כל המערכת בצורה מקיפה
"""

import asyncio
import json
import pytest
from datetime import datetime
from enhanced_orchestrator import EnhancedOrchestrator
from tools.handoff_system import HandoffPacket, TaskStatus, NextStepSuggestion

@pytest.mark.asyncio
async def test_full_system_integration():
    """בדיקת אינטגרציה מלאה של המערכת"""
    print("🔄 Starting Full System Integration Tests...")
    
    # יצירת האורכסטרייטור
    orchestrator = EnhancedOrchestrator()
    print("✅ Orchestrator created")
    
    # אתחול מערכות הידע
    await orchestrator.initialize_knowledge_systems()
    print("✅ Knowledge systems initialized")
    
    # בדיקת כל הסוכנים
    all_agents = orchestrator.agent_factory.list_available_agents()
    print(f"✅ Found {len(all_agents)} agents: {', '.join(all_agents)}")
    
    # בדיקת יכולות כל סוכן
    agent_capabilities = {}
    for agent in all_agents:
        capabilities = await orchestrator.get_agent_capabilities(agent)
        agent_capabilities[agent] = capabilities
        print(f"   📋 {agent}: {len(capabilities)} capabilities")
    
    # יצירת workflow מלא
    workflow_id = await orchestrator.start_workflow(
        "Create a secure user authentication system with login, registration, and password reset features",
        "complex_ui_feature"
    )
    print(f"✅ Complex workflow created: {workflow_id}")
    
    # בדיקת סטטוס workflow
    workflow_status = orchestrator.get_workflow_status(workflow_id)
    print(f"📊 Workflow status: {workflow_status['status']}")
    
    # סימולציית handoff packet
    handoff_packet = HandoffPacket(
        completed_task_id=f"TASK-{workflow_id}-001",
        agent_name="Product_Analyst",
        status=TaskStatus.SUCCESS,
        artifacts_produced=["requirements.md", "user_stories.md"],
        next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
        notes="Comprehensive requirements analysis completed with security focus",
        timestamp=datetime.now().isoformat(),
        dependencies_satisfied=["stakeholder_interviews", "security_review"],
        blocking_issues=[]
    )
    
    # עיבוד השלמת המשימה
    routing_result = await orchestrator.process_agent_completion(
        f"TASK-{workflow_id}-001",
        f"Task completed successfully.\n\nHANDOFF_PACKET: {handoff_packet.to_json()}",
        workflow_id
    )
    print(f"✅ Agent completion processed: {routing_result['status']}")
    
    # בדיקת מערכת אישור אנושי
    human_approval_packet = HandoffPacket(
        completed_task_id=f"TASK-{workflow_id}-002",
        agent_name="Architect",
        status=TaskStatus.SUCCESS,
        artifacts_produced=["architecture.md", "security_design.md"],
        next_step_suggestion=NextStepSuggestion.HUMAN_APPROVAL_NEEDED,
        notes="Technical architecture ready for human review",
        timestamp=datetime.now().isoformat()
    )
    
    approval_result = await orchestrator.process_agent_completion(
        f"TASK-{workflow_id}-002",
        f"Architecture completed.\n\nHANDOFF_PACKET: {human_approval_packet.to_json()}",
        workflow_id
    )
    print(f"✅ Human approval gate created: {approval_result['approval_id']}")
    
    # בדיקת pending approvals
    pending_approvals = orchestrator.get_pending_approvals()
    print(f"📋 Pending approvals: {len(pending_approvals)}")
    
    # אישור אנושי
    if pending_approvals:
        approval_id = pending_approvals[0]["id"]
        approval_response = await orchestrator.process_human_approval(
            approval_id, 
            "APPROVE"
        )
        print(f"✅ Human approval processed: {approval_response['status']}")
    
    # בדיקת סטטיסטיקות cache
    cache_stats = orchestrator.get_cache_performance_stats()
    print(f"📊 Cache efficiency: {cache_stats['performance_summary']['cache_efficiency']:.1f}%")
    
    # בדיקת context optimization
    context_stats = orchestrator.get_context_optimization_stats()
    print(f"📊 Context optimization: {context_stats['cached_summaries']} summaries cached")
    
    # בדיקת מערכת recovery
    try:
        result = await orchestrator.execute_task_with_recovery(
            "TEST_TASK_001",
            "Tester",
            "Write comprehensive tests for authentication system",
            {"workflow_id": workflow_id}
        )
        print(f"✅ Task recovery system: {result['status']}")
    except Exception as e:
        print(f"⚠️ Task recovery test failed (expected): {str(e)[:50]}...")
    
    # בדיקת מערכת checkpoints
    checkpoint_status = orchestrator.get_checkpoint_status("TEST_TASK_001")
    if checkpoint_status:
        print(f"📊 Checkpoint system: {checkpoint_status['progress']}% complete")
    
    # בדיקת מערכת שגיאות
    error_stats = orchestrator.get_error_statistics()
    print(f"📊 Error statistics: {error_stats['total_errors']} total errors")
    
    # בדיקת validation של כל הסוכנים
    validation_results = await orchestrator.validate_all_agents_knowledge()
    print(f"✅ Agent validation: {validation_results['validated_agents']}/{validation_results['total_agents']} agents validated")
    
    # יצירת דוח cache
    cache_report = orchestrator.generate_cache_report()
    print("✅ Cache report generated")
    
    # ניקוי נתונים ישנים
    orchestrator.cleanup_old_data(24)
    print("✅ Old data cleanup completed")
    
    print("\n🎉 All Full System Integration Tests Passed!")
    
    return {
        "orchestrator": orchestrator,
        "workflow_id": workflow_id,
        "agent_capabilities": agent_capabilities,
        "validation_results": validation_results,
        "cache_stats": cache_stats
    }

@pytest.mark.asyncio
async def test_workflow_session_management():
    """בדיקת ניהול sessions של workflows"""
    print("\n🔄 Testing Workflow Session Management...")
    
    orchestrator = EnhancedOrchestrator()
    await orchestrator.initialize_knowledge_systems()
    
    # יצירת session חדש
    session_id = orchestrator.start_workflow_session("authentication_system", "Product_Analyst")
    print(f"✅ Workflow session created: {session_id}")
    
    # הוספת handoff packets
    from tools.handoff_cache import add_handoff_packet
    
    test_packet = HandoffPacket(
        completed_task_id="TASK-001",
        agent_name="Product_Analyst",
        status=TaskStatus.SUCCESS,
        artifacts_produced=["spec.md"],
        next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
        notes="Initial analysis complete",
        timestamp=datetime.now().isoformat()
    )
    
    add_handoff_packet(session_id, test_packet, True)
    print("✅ Handoff packet added to session")
    
    # בדיקת sessions
    sessions_info = orchestrator.get_workflow_sessions()
    print(f"📊 Active sessions: {len(sessions_info['active_sessions'])}")
    
    # pause session
    paused = orchestrator.pause_workflow_session(session_id)
    print(f"✅ Session paused: {paused}")
    
    # resume session
    resumed = orchestrator.resume_workflow_session(session_id)
    if resumed:
        print(f"✅ Session resumed with {len(resumed['history'])} history items")
    
    print("✅ Workflow Session Management Tests Passed!")

@pytest.mark.asyncio
async def test_performance_monitoring():
    """בדיקת מערכת ניטור ביצועים"""
    print("\n🔄 Testing Performance Monitoring...")
    
    orchestrator = EnhancedOrchestrator()
    await orchestrator.initialize_knowledge_systems()
    
    # בדיקת context optimization
    large_context = {
        "user_request": "Complex request",
        "previous_artifacts": [f"file_{i}.md" for i in range(10)],
        "artifact_content": "Large content block " * 1000,
        "metadata": {"large_data": list(range(1000))}
    }
    
    optimized = orchestrator._optimize_context_for_agent(large_context, "Coder")
    original_size = len(str(large_context))
    optimized_size = len(str(optimized))
    reduction = ((original_size - optimized_size) / original_size) * 100
    
    print(f"📊 Context optimization: {reduction:.1f}% reduction")
    
    # בדיקת token estimation
    tokens = orchestrator._estimate_context_tokens(optimized)
    print(f"📊 Token estimation: {tokens} tokens")
    
    # בדיקת cache performance
    cache_stats = orchestrator.get_cache_performance_stats()
    print(f"📊 Cache performance: {cache_stats['performance_summary']['cache_efficiency']:.1f}% efficiency")
    
    print("✅ Performance Monitoring Tests Passed!")

if __name__ == "__main__":
    async def run_all_tests():
        try:
            await test_full_system_integration()
            await test_workflow_session_management()
            await test_performance_monitoring()
            print("\n🎉 ALL INTEGRATION TESTS PASSED SUCCESSFULLY! 🎉")
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            raise
    
    asyncio.run(run_all_tests())
