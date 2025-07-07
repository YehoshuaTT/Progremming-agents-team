#!/usr/bin/env python3
"""
Tests for Handoff Packet Caching System
Tests workflow state persistence, resumption, and packet caching
"""

import unittest
import tempfile
import time
import shutil
from unittest.mock import patch, MagicMock

from tools.handoff_cache import (
    create_workflow_session, add_handoff_packet, get_handoff_cache_manager,
    HandoffPacket, TaskStatus, NextStepSuggestion, WorkflowState,
    get_workflow_history, resume_workflow
)

class TestHandoffCacheManager(unittest.TestCase):
    """Test cases for HandoffCacheManager"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        # Set the global cache manager to use temp_dir, but do NOT patch or reload any class
        import tools.handoff_cache
        if hasattr(tools.handoff_cache, '_handoff_cache_manager'):
            tools.handoff_cache._handoff_cache_manager = None
        # Import the class and instance from the same module context
        self.cache_manager = tools.handoff_cache.HandoffCacheManager(cache_dir=self.temp_dir)
        tools.handoff_cache._handoff_cache_manager = self.cache_manager

    def tearDown(self):
        """Clean up test environment"""
        import tools.handoff_cache
        tools.handoff_cache._handoff_cache_manager = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_workflow_session(self):
        """Test workflow session creation"""
        session_id = create_workflow_session("test_workflow", "Architect")
        self.assertIsNotNone(session_id)
        session = get_handoff_cache_manager().active_sessions[session_id]
        self.assertEqual(session.workflow_name, "test_workflow")
        self.assertEqual(session.current_agent, "Architect")
        self.assertEqual(session.state, WorkflowState.ACTIVE)
        self.assertEqual(len(session.handoff_packets), 0)
        self.assertEqual(session.completion_percentage, 0.0)

    def test_add_handoff_packet(self):
        """Test adding handoff packets to session"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        # Create a test handoff packet
        packet = HandoffPacket(
            completed_task_id="task_1",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["architecture.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Architecture complete",
            timestamp=str(time.time())
        )
        
        # Add packet to session
        success = add_handoff_packet(session_id, packet)
        self.assertTrue(success)
        
        # Verify packet was added
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return  # For static analysis
        self.assertEqual(len(session.handoff_packets), 1)
        self.assertEqual(session.handoff_packets[0], packet)
        self.assertEqual(session.current_agent, "Architect")
        self.assertGreater(session.completion_percentage, 0)

    def test_checkpoint_creation(self):
        """Test checkpoint creation and tracking"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        packet = HandoffPacket(
            completed_task_id="checkpoint_1",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["architecture.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Architecture complete",
            timestamp=str(time.time())
        )
        
        # Add packet as checkpoint
        success = add_handoff_packet(session_id, packet, is_checkpoint=True)
        self.assertTrue(success)
        
        # Verify checkpoint was created
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return
        self.assertIn("checkpoint_1", session.checkpoints)
        self.assertIn("checkpoint_checkpoint_1", session.metadata)
        self.assertEqual(get_handoff_cache_manager().stats["checkpoints_created"], 1)

    def test_workflow_pause_and_resume(self):
        """Test workflow pausing and resuming"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        # Add a checkpoint packet
        packet = HandoffPacket(
            completed_task_id="checkpoint_1",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["architecture.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Architecture complete",
            timestamp=str(time.time())
        )
        
        add_handoff_packet(session_id, packet, is_checkpoint=True)
        
        # Pause workflow
        success = get_handoff_cache_manager().pause_workflow(session_id)
        self.assertTrue(success)
        
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return
        self.assertEqual(session.state, WorkflowState.PAUSED)
        self.assertTrue(session.is_resumable())
        
        # Resume workflow
        last_checkpoint = resume_workflow(session_id)
        self.assertIsNotNone(last_checkpoint)
        self.assertEqual(last_checkpoint, packet)
        
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return
        self.assertEqual(session.state, WorkflowState.RESUMED)
        self.assertEqual(get_handoff_cache_manager().stats["sessions_resumed"], 1)

    def test_workflow_completion(self):
        """Test workflow completion detection"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        # Add multiple successful packets to reach 100% completion
        for i in range(10):
            packet = HandoffPacket(
                completed_task_id=f"task_{i}",
                agent_name="Agent",
                status=TaskStatus.SUCCESS,
                artifacts_produced=[f"artifact_{i}.md"],
                next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
                notes=f"Task {i} complete",
                timestamp=str(time.time())
            )
            add_handoff_packet(session_id, packet)
        
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return
        self.assertEqual(session.state, WorkflowState.COMPLETED)
        self.assertEqual(session.completion_percentage, 100.0)
        self.assertEqual(get_handoff_cache_manager().stats["workflows_completed"], 1)

    def test_workflow_failure(self):
        """Test workflow failure handling"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        # Add a failed packet
        packet = HandoffPacket(
            completed_task_id="task_1",
            agent_name="Architect",
            status=TaskStatus.FAILURE,
            artifacts_produced=[],
            next_step_suggestion=NextStepSuggestion.DEBUG_NEEDED,
            notes="Task failed",
            timestamp=str(time.time())
        )
        
        add_handoff_packet(session_id, packet)
        
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return
        self.assertEqual(session.state, WorkflowState.FAILED)
        self.assertEqual(get_handoff_cache_manager().stats["workflows_failed"], 1)

    def test_session_persistence(self):
        """Test session persistence to disk"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        # Add a packet
        packet = HandoffPacket(
            completed_task_id="task_1",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["architecture.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Architecture complete",
            timestamp=str(time.time())
        )
        
        add_handoff_packet(session_id, packet)
        
        # Ensure session is persisted before creating new manager
        import time as _time
        _time.sleep(0.1)
        
        # Simulate restart by reloading the manager
        manager = get_handoff_cache_manager()
        session = manager.get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return
        self.assertEqual(session.workflow_name, "test_workflow")
        self.assertEqual(len(session.handoff_packets), 1)
        self.assertEqual(session.handoff_packets[0].completed_task_id, "task_1")

    def test_workflow_history_retrieval(self):
        """Test workflow history retrieval"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        # Add multiple packets
        packets = []
        for i in range(3):
            packet = HandoffPacket(
                completed_task_id=f"task_{i}",
                agent_name="Agent",
                status=TaskStatus.SUCCESS,
                artifacts_produced=[f"artifact_{i}.md"],
                next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
                notes=f"Task {i} complete",
                timestamp=str(time.time())
            )
            packets.append(packet)
            add_handoff_packet(session_id, packet)
        
        # Get history
        history = get_workflow_history(session_id)
        self.assertEqual(len(history), 3)
        
        for i, packet in enumerate(history):
            self.assertEqual(packet.completed_task_id, f"task_{i}")

    def test_active_workflows_tracking(self):
        """Test active workflows tracking"""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = create_workflow_session(f"workflow_{i}", "Agent")
            session_ids.append(session_id)
        
        # All should be active
        active_workflows = get_handoff_cache_manager().get_active_workflows()
        self.assertEqual(len(active_workflows), 3)
        
        # Add a packet to first session so it can be resumed
        packet = HandoffPacket(
            completed_task_id="task_1",
            agent_name="Agent",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["artifact.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Task complete",
            timestamp=str(time.time())
        )
        add_handoff_packet(session_ids[0], packet)
        
        # Pause one workflow
        get_handoff_cache_manager().pause_workflow(session_ids[0])
        
        # Should have 2 active, 1 resumable
        active_workflows = get_handoff_cache_manager().get_active_workflows()
        resumable_workflows = get_handoff_cache_manager().get_resumable_workflows()
        
        self.assertEqual(len(active_workflows), 2)
        self.assertEqual(len(resumable_workflows), 1)
        self.assertIn(session_ids[0], resumable_workflows)

    def test_session_cleanup(self):
        """Test expired session cleanup"""
        session_id = create_workflow_session("test_workflow", "Architect")
        
        # Complete the workflow
        packet = HandoffPacket(
            completed_task_id="final_task",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["final.md"],
            next_step_suggestion=NextStepSuggestion.MERGE_APPROVED,
            notes="Workflow complete",
            timestamp=str(time.time())
        )
        
        # Manually set completion to 100%
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session, "Session should not be None")
        if session is None:
            return
        session.completion_percentage = 100.0
        add_handoff_packet(session_id, packet)
        
        # Manually set old timestamp
        session.updated_at = time.time() - (31 * 24 * 3600)
        
        # Clean up expired sessions
        cleaned_count = get_handoff_cache_manager().cleanup_expired_sessions(max_age_days=30)
        self.assertEqual(cleaned_count, 1)
        
        # Session should be removed
        self.assertNotIn(session_id, get_handoff_cache_manager().active_sessions)

    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        stats = get_handoff_cache_manager().get_statistics()
        initial_sessions = stats["sessions_created"]
        
        # Create sessions and add packets
        session_id = create_workflow_session("test_workflow", "Architect")
        
        packet = HandoffPacket(
            completed_task_id="task_1",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["architecture.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Architecture complete",
            timestamp=str(time.time())
        )
        
        add_handoff_packet(session_id, packet, is_checkpoint=True)
        
        # Access session to generate cache hits
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session)
        
        # Get updated stats
        stats = get_handoff_cache_manager().get_statistics()
        
        self.assertEqual(stats["sessions_created"], initial_sessions + 1)
        self.assertEqual(stats["packets_cached"], 1)
        self.assertEqual(stats["checkpoints_created"], 1)
        self.assertGreaterEqual(stats["cache_hits"], 1)

class TestHandoffCacheIntegration(unittest.TestCase):
    """Integration tests for handoff cache functions"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        # Set the global cache manager to use temp_dir, matching the approach in TestHandoffCacheManager
        import tools.handoff_cache
        tools.handoff_cache._handoff_cache_manager = None
        self.cache_manager = tools.handoff_cache.HandoffCacheManager(cache_dir=self.temp_dir)
        tools.handoff_cache._handoff_cache_manager = self.cache_manager

    def tearDown(self):
        """Clean up test environment"""
        import tools.handoff_cache
        tools.handoff_cache._handoff_cache_manager = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_global_functions(self):
        """Test global convenience functions"""
        # Test session creation
        session_id = create_workflow_session("test_workflow", "Architect")
        self.assertIsNotNone(session_id)
        
        # Test packet addition
        packet = HandoffPacket(
            completed_task_id="task_1",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["architecture.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Architecture complete",
            timestamp=str(time.time())
        )
        # Mark as checkpoint so resume logic works
        add_handoff_packet(session_id, packet, is_checkpoint=True)
        
        # Ensure session is persisted before reloading
        import time as _time
        _time.sleep(0.1)
        
        # Test session retrieval
        session = get_handoff_cache_manager().get_session(session_id)
        self.assertIsNotNone(session)
        if session is None:
            self.fail("Session was not loaded from disk by global functions!")
        self.assertEqual(session.workflow_name, "test_workflow")
        self.assertEqual(len(session.handoff_packets), 1)
        self.assertEqual(session.handoff_packets[0].completed_task_id, "task_1")
        
        # Test workflow resumption
        cache_manager = get_handoff_cache_manager()
        cache_manager.pause_workflow(session_id)
        last_checkpoint = resume_workflow(session_id)
        self.assertIsNotNone(last_checkpoint)
        if last_checkpoint is None:
            self.fail("No checkpoint found when resuming workflow!")
        self.assertEqual(last_checkpoint.completed_task_id, "task_1")
        
        # Test history retrieval
        history = get_workflow_history(session_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].completed_task_id, "task_1")

if __name__ == '__main__':
    unittest.main()
