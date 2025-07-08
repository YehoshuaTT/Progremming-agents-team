#!/usr/bin/env python3
"""
Comprehensive test suite for the migrated agent workflow system.
This test suite focuses on the actual working functionality of the system.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from agent_driven_workflow import AgentDrivenWorkflow, AgentDecision
from workspace_organizer import WorkspaceOrganizer
from cleanup_utility import WorkspaceCleanup
from enhanced_orchestrator import EnhancedOrchestrator
from llm_interface import LLMInterface


class TestActualSystemFunctionality:
    """Test the actual working functionality of the migrated system"""
    
    def test_agent_decision_creation(self):
        """Test creating AgentDecision with correct parameters"""
        decision = AgentDecision(
            action="NEXT_AGENT",
            target="Coder",
            reason="Need to implement the solution",
            confidence=0.8
        )
        
        assert decision.action == "NEXT_AGENT"
        assert decision.target == "Coder"
        assert decision.reason == "Need to implement the solution"
        assert decision.confidence == 0.8
        
        # Test to_dict method
        decision_dict = decision.to_dict()
        assert decision_dict['action'] == "NEXT_AGENT"
        assert decision_dict['target'] == "Coder"
        assert decision_dict['reason'] == "Need to implement the solution"
        assert decision_dict['confidence'] == 0.8
    
    def test_workspace_organizer_functionality(self):
        """Test workspace organizer actual functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            organizer = WorkspaceOrganizer(temp_dir)
            
            # Check session creation
            assert organizer.session_id is not None
            assert len(organizer.session_id) > 0
            assert organizer.main_folder.exists()
            
            # Check subfolders creation
            assert organizer.artifacts_folder.exists()
            assert organizer.logs_folder.exists()
            assert organizer.results_folder.exists()
            assert organizer.temp_folder.exists()
            
            # Test workflow folder creation
            workflow_folder = organizer.get_workflow_folder("TEST-001")
            assert workflow_folder.exists()
            
            # Test artifact creation
            artifact_path = organizer.create_agent_artifact(
                "TEST-001", "Product_Analyst", 1, "test.md", "# Test Content"
            )
            assert artifact_path.exists()
            assert artifact_path.read_text() == "# Test Content"
            
            # Test workflow result saving
            result_path = organizer.save_workflow_result("TEST-001", {
                "status": "completed",
                "agents": ["Product_Analyst", "Coder"]
            })
            assert result_path.exists()
            
            # Test session summary
            summary = organizer.get_session_summary()
            assert summary['session_id'] == organizer.session_id
            assert 'created_at' in summary
    
    def test_cleanup_utility_functionality(self):
        """Test cleanup utility actual functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cleanup = WorkspaceCleanup(temp_dir)
            
            # Test workspace stats
            stats = cleanup.get_workspace_stats()
            assert isinstance(stats, dict)
            assert 'total_folders' in stats
            assert 'total_files' in stats
            assert 'total_size_mb' in stats
            
            # Test full cleanup - returns stats after cleanup
            result = cleanup.full_cleanup(days_to_keep=0, keep_recent=0)
            assert isinstance(result, dict)
            assert 'total_folders' in result
            assert 'total_files' in result
            assert 'total_size_mb' in result
    
    def test_enhanced_orchestrator_workspace_integration(self):
        """Test enhanced orchestrator workspace integration"""
        orchestrator = EnhancedOrchestrator()
        
        # Test that orchestrator has workspace_organizer attribute
        assert hasattr(orchestrator, 'workspace_organizer')
        
        # Test workspace organizer assignment
        organizer = WorkspaceOrganizer()
        orchestrator.workspace_organizer = organizer
        
        assert orchestrator.workspace_organizer is not None
        assert orchestrator.workspace_organizer.session_id == organizer.session_id
    
    def test_agent_driven_workflow_integration(self):
        """Test agent driven workflow integration"""
        workflow = AgentDrivenWorkflow()
        
        # Test that workflow has required components
        assert hasattr(workflow, 'orchestrator')
        assert hasattr(workflow, 'workspace_organizer')
        assert isinstance(workflow.orchestrator, EnhancedOrchestrator)
        assert isinstance(workflow.workspace_organizer, WorkspaceOrganizer)
        
        # Test that orchestrator has workspace organizer assigned
        assert workflow.orchestrator.workspace_organizer is not None
        assert workflow.orchestrator.workspace_organizer.session_id == workflow.workspace_organizer.session_id
    
    def test_llm_interface_functionality(self):
        """Test LLM interface functionality"""
        # Test that LLMInterface can be imported and initialized
        # This will use mock responses since we don't have API keys in tests
        interface = LLMInterface()
        
        # Test system prompt generation
        prompt = interface._get_system_prompt("Product_Analyst")
        assert prompt is not None
        assert len(prompt) > 50
        assert "Product Analyst" in prompt
    
    @pytest.mark.asyncio
    async def test_workflow_execution_basics(self):
        """Test basic workflow execution without full complexity"""
        workflow = AgentDrivenWorkflow()
        
        # Test that workflow has main run method
        assert hasattr(workflow, 'run_agent_driven_workflow')
        assert callable(workflow.run_agent_driven_workflow)
        
        # Test that workflow has agent execution methods
        assert hasattr(workflow, 'execute_agent_with_decision')
        assert callable(workflow.execute_agent_with_decision)
    
    def test_concurrent_workspace_organizers(self):
        """Test that multiple workspace organizers can coexist"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            organizer1 = WorkspaceOrganizer(temp_dir)
            time.sleep(1)  # Ensure different timestamp
            organizer2 = WorkspaceOrganizer(temp_dir)
            
            # Sessions should be different (if created at different times)
            assert organizer1.session_id is not None
            assert organizer2.session_id is not None
            assert organizer1.session_id != organizer2.session_id
            
            # Main folders should be different
            assert organizer1.main_folder != organizer2.main_folder
    
    def test_folder_statistics(self):
        """Test folder statistics functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            organizer = WorkspaceOrganizer(temp_dir)
            
            # Create some test content
            organizer.create_agent_artifact(
                "TEST-001", "Product_Analyst", 1, "test.md", "# Test"
            )
            
            # Test folder stats
            stats = organizer._get_folder_stats()
            assert isinstance(stats, dict)
            assert 'total_files' in stats
            assert 'total_size_mb' in stats
            assert 'workflow_count' in stats
            assert stats['workflow_count'] >= 1
    
    def test_system_components_integration(self):
        """Test that all system components work together"""
        # Create workflow
        workflow = AgentDrivenWorkflow()
        
        # Test that all components are properly initialized
        assert workflow.orchestrator is not None
        assert workflow.workspace_organizer is not None
        assert workflow.orchestrator.workspace_organizer is not None
        
        # Test that workspace organizer is properly configured
        assert workflow.workspace_organizer.main_folder.exists()
        assert workflow.workspace_organizer.artifacts_folder.exists()
        assert workflow.workspace_organizer.logs_folder.exists()
        assert workflow.workspace_organizer.results_folder.exists()
        assert workflow.workspace_organizer.temp_folder.exists()
    
    def test_cleanup_integration(self):
        """Test cleanup integration with workspace organizer"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some workspace content
            organizer = WorkspaceOrganizer(temp_dir)
            organizer.create_agent_artifact(
                "TEST-001", "Product_Analyst", 1, "test.md", "# Test"
            )
            
            # Create cleanup utility
            cleanup = WorkspaceCleanup(temp_dir)
            
            # Test that cleanup can see the workspace
            stats = cleanup.get_workspace_stats()
            assert stats['total_files'] > 0
            
            # Test cleanup doesn't break workspace
            cleanup.cleanup_empty_folders()
            
            # Workspace should still be intact
            assert organizer.main_folder.exists()
            assert len(list(organizer.main_folder.rglob('*'))) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
