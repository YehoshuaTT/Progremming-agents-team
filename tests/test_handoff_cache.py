#!/usr/bin/env python3
"""
Tests for Handoff Packet Caching System
Tests workflow state persistence, resumption, and packet caching
"""

import unittest
import tempfile
import time
import os
import shutil
from unittest.mock import patch, MagicMock

from tools.handoff_cache import (
    HandoffCacheManager, WorkflowSession, WorkflowState,
    create_workflow_session, add_handoff_packet, resume_workflow, get_workflow_history
)
from tools.handoff_system import HandoffPacket, TaskStatus, NextStepSuggestion

class TestHandoffCacheManager(unittest.TestCase):
    """Test cases for HandoffCacheManager"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = HandoffCacheManager(cache_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_workflow_session(self):
        """Test workflow session creation"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.cache_manager.active_sessions)
        
        session = self.cache_manager.active_sessions[session_id]
        self.assertEqual(session.workflow_name, "test_workflow")
        self.assertEqual(session.current_agent, "Architect")
        self.assertEqual(session.state, WorkflowState.ACTIVE)
        self.assertEqual(len(session.handoff_packets), 0)
        self.assertEqual(session.completion_percentage, 0.0)

    def test_add_handoff_packet(self):
        """Test adding handoff packets to session"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
        success = self.cache_manager.add_handoff_packet(session_id, packet)
        self.assertTrue(success)
        
        # Verify packet was added
        session = self.cache_manager.get_session(session_id)
        self.assertEqual(len(session.handoff_packets), 1)
        self.assertEqual(session.handoff_packets[0], packet)
        self.assertEqual(session.current_agent, "Architect")
        self.assertGreater(session.completion_percentage, 0)

    def test_checkpoint_creation(self):
        """Test checkpoint creation and tracking"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
        success = self.cache_manager.add_handoff_packet(session_id, packet, is_checkpoint=True)
        self.assertTrue(success)
        
        # Verify checkpoint was created
        session = self.cache_manager.get_session(session_id)
        self.assertIn("checkpoint_1", session.checkpoints)
        self.assertIn("checkpoint_checkpoint_1", session.metadata)
        self.assertEqual(self.cache_manager.stats["checkpoints_created"], 1)

    def test_workflow_pause_and_resume(self):
        """Test workflow pausing and resuming"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
        
        self.cache_manager.add_handoff_packet(session_id, packet, is_checkpoint=True)
        
        # Pause workflow
        success = self.cache_manager.pause_workflow(session_id)
        self.assertTrue(success)
        
        session = self.cache_manager.get_session(session_id)
        self.assertEqual(session.state, WorkflowState.PAUSED)
        self.assertTrue(session.is_resumable())
        
        # Resume workflow
        last_checkpoint = self.cache_manager.resume_workflow(session_id)
        self.assertIsNotNone(last_checkpoint)
        self.assertEqual(last_checkpoint, packet)
        
        session = self.cache_manager.get_session(session_id)
        self.assertEqual(session.state, WorkflowState.RESUMED)
        self.assertEqual(self.cache_manager.stats["sessions_resumed"], 1)

    def test_workflow_completion(self):
        """Test workflow completion detection"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
            self.cache_manager.add_handoff_packet(session_id, packet)
        
        session = self.cache_manager.get_session(session_id)
        self.assertEqual(session.state, WorkflowState.COMPLETED)
        self.assertEqual(session.completion_percentage, 100.0)
        self.assertEqual(self.cache_manager.stats["workflows_completed"], 1)

    def test_workflow_failure(self):
        """Test workflow failure handling"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
        
        self.cache_manager.add_handoff_packet(session_id, packet)
        
        session = self.cache_manager.get_session(session_id)
        self.assertEqual(session.state, WorkflowState.FAILED)
        self.assertEqual(self.cache_manager.stats["workflows_failed"], 1)

    def test_session_persistence(self):
        """Test session persistence to disk"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
        
        self.cache_manager.add_handoff_packet(session_id, packet)
        
        # Create new cache manager (simulate restart)
        new_cache_manager = HandoffCacheManager(cache_dir=self.temp_dir)
        
        # Verify session was loaded from disk
        session = new_cache_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.workflow_name, "test_workflow")
        self.assertEqual(len(session.handoff_packets), 1)
        self.assertEqual(session.handoff_packets[0].completed_task_id, "task_1")

    def test_workflow_history_retrieval(self):
        """Test workflow history retrieval"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
            self.cache_manager.add_handoff_packet(session_id, packet)
        
        # Get history
        history = self.cache_manager.get_workflow_history(session_id)
        self.assertEqual(len(history), 3)
        
        for i, packet in enumerate(history):
            self.assertEqual(packet.completed_task_id, f"task_{i}")

    def test_active_workflows_tracking(self):
        """Test active workflows tracking"""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = self.cache_manager.create_workflow_session(f"workflow_{i}", "Agent")
            session_ids.append(session_id)
        
        # All should be active
        active_workflows = self.cache_manager.get_active_workflows()
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
        self.cache_manager.add_handoff_packet(session_ids[0], packet)
        
        # Pause one workflow
        self.cache_manager.pause_workflow(session_ids[0])
        
        # Should have 2 active, 1 resumable
        active_workflows = self.cache_manager.get_active_workflows()
        resumable_workflows = self.cache_manager.get_resumable_workflows()
        
        self.assertEqual(len(active_workflows), 2)
        self.assertEqual(len(resumable_workflows), 1)
        self.assertIn(session_ids[0], resumable_workflows)

    def test_session_cleanup(self):
        """Test expired session cleanup"""
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
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
        session = self.cache_manager.get_session(session_id)
        session.completion_percentage = 100.0
        self.cache_manager.add_handoff_packet(session_id, packet)
        
        # Manually set old timestamp
        session.updated_at = time.time() - (31 * 24 * 3600)  # 31 days ago
        
        # Clean up expired sessions
        cleaned_count = self.cache_manager.cleanup_expired_sessions(max_age_days=30)
        self.assertEqual(cleaned_count, 1)
        
        # Session should be removed
        self.assertNotIn(session_id, self.cache_manager.active_sessions)

    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        stats = self.cache_manager.get_statistics()
        initial_sessions = stats["sessions_created"]
        
        # Create sessions and add packets
        session_id = self.cache_manager.create_workflow_session("test_workflow", "Architect")
        
        packet = HandoffPacket(
            completed_task_id="task_1",
            agent_name="Architect",
            status=TaskStatus.SUCCESS,
            artifacts_produced=["architecture.md"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes="Architecture complete",
            timestamp=str(time.time())
        )
        
        self.cache_manager.add_handoff_packet(session_id, packet, is_checkpoint=True)
        
        # Access session to generate cache hits
        session = self.cache_manager.get_session(session_id)
        self.assertIsNotNone(session)
        
        # Get updated stats
        stats = self.cache_manager.get_statistics()
        
        self.assertEqual(stats["sessions_created"], initial_sessions + 1)
        self.assertEqual(stats["packets_cached"], 1)
        self.assertEqual(stats["checkpoints_created"], 1)
        self.assertGreaterEqual(stats["cache_hits"], 1)

class TestHandoffCacheIntegration(unittest.TestCase):
    """Integration tests for handoff cache functions"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        # Reset global instance
        import tools.handoff_cache
        tools.handoff_cache._handoff_cache_manager = None

    def tearDown(self):
        """Clean up test environment"""
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
        
        success = add_handoff_packet(session_id, packet, is_checkpoint=True)
        self.assertTrue(success)
        
        # Pause the workflow to make it resumable
        from tools.handoff_cache import get_handoff_cache_manager
        cache_manager = get_handoff_cache_manager()
        cache_manager.pause_workflow(session_id)
        
        # Test workflow resumption
        last_checkpoint = resume_workflow(session_id)
        self.assertIsNotNone(last_checkpoint)
        self.assertEqual(last_checkpoint.completed_task_id, "task_1")
        
        # Test history retrieval
        history = get_workflow_history(session_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].completed_task_id, "task_1")

if __name__ == '__main__':
    unittest.main()
