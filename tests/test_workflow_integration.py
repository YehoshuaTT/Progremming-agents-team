"""
Test suite for Workflow Integration module
Tests the integration between different workflow components and context management
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import os
import tempfile

from tools.workflow_integration import (
    IntegratedWorkflowSystem, WorkflowContext
)
from tools.intelligent_orchestrator import IntelligentOrchestrator, WorkflowPhase
from tools.plan_generator import ProjectPlan
from tools.progress_tracker import ProgressTracker


class TestWorkflowContext:
    """Test the workflow context"""
    
    def test_context_initialization(self):
        """Test initializing a workflow context"""
        context = WorkflowContext(
            workflow_id="workflow123",
            user_prompt="Create a web application",
            current_phase=WorkflowPhase.PLANNING
        )
        
        assert context.workflow_id == "workflow123"
        assert context.user_prompt == "Create a web application"
        assert context.current_phase == WorkflowPhase.PLANNING
        assert context.project_plan is None
        assert context.chat_session_id is None
        assert context.progress_tracker_id is None
        assert context.active_agents == []
        assert context.decisions_made == []
        assert context.pending_approvals == []
        assert context.created_files == []
    
    def test_context_to_dict(self):
        """Test converting context to dictionary"""
        context = WorkflowContext(
            workflow_id="workflow123",
            user_prompt="Create a web application",
            current_phase=WorkflowPhase.PLANNING
        )
        
        context_dict = context.to_dict()
        
        assert context_dict["workflow_id"] == "workflow123"
        assert context_dict["user_prompt"] == "Create a web application"
        assert context_dict["current_phase"] == WorkflowPhase.PLANNING.value


class TestIntegratedWorkflowSystem:
    """Test the integrated workflow system"""
    
    @pytest.fixture
    def workflow_system(self):
        """Create a workflow system for testing"""
        return IntegratedWorkflowSystem(workspace_path="test_workspace")
    
    def test_initialization(self, workflow_system):
        """Test workflow system initialization"""
        assert workflow_system.orchestrator is not None
        assert workflow_system.certainty_framework is not None
        assert workflow_system.chat_interface is not None
        assert workflow_system.plan_generator is not None
        assert workflow_system.progress_tracker is not None
        assert workflow_system.active_workflows == {}
        assert workflow_system.workflow_history == []
    
    @pytest.mark.asyncio
    async def test_start_workflow(self, workflow_system):
        """Test starting a new workflow"""
        user_prompt = "Create a simple web application"
        
        context = await workflow_system.start_workflow(user_prompt)
        
        assert context is not None
        assert context.user_prompt == user_prompt
        assert context.current_phase == WorkflowPhase.PLANNING
        assert context.workflow_id in workflow_system.active_workflows
        assert workflow_system.active_workflows[context.workflow_id] == context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
