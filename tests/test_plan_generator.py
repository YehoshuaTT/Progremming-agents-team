"""
Test suite for Plan Generator module
Tests project planning, feature analysis, and task breakdown functionality
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from tools.plan_generator import (
    PlanGenerator, ProjectPlan, Feature, Task, Milestone,
    ProjectType, TechStack, Priority, TaskStatus
)
from tools.intelligent_orchestrator import IntelligentOrchestrator
from tools.certainty_framework import CertaintyLevel


class TestProjectPlan:
    """Test the project plan data structures"""
    
    def test_feature_creation(self):
        """Test creating a feature"""
        feature = Feature(
            id="f1",
            name="User Authentication",
            description="Allow users to register and login",
            priority=Priority.HIGH,
            estimated_hours=12
        )
        
        assert feature.id == "f1"
        assert feature.name == "User Authentication"
        assert feature.priority == Priority.HIGH
        assert feature.estimated_hours == 12
    
    def test_task_creation(self):
        """Test creating a task"""
        task = Task(
            id="t1",
            feature_id="f1",
            title="Implement login form",
            description="Create UI for login screen",
            assigned_agent=None,
            estimated_hours=3,
            priority=Priority.MEDIUM,
            status=TaskStatus.PENDING
        )
        
        assert task.id == "t1"
        assert task.feature_id == "f1"
        assert task.title == "Implement login form"
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.MEDIUM
        assert task.estimated_hours == 3
    
    def test_milestone_creation(self):
        """Test creating a milestone"""
        milestone = Milestone(
            id="m1",
            name="Alpha Release",
            description="First testable version",
            due_date=datetime.now(),
            deliverables=["feature1", "feature2"]
        )
        
        assert milestone.id == "m1"
        assert milestone.name == "Alpha Release"
        assert len(milestone.deliverables) == 2
    
    def test_project_plan_creation(self):
        """Test creating a project plan"""
        plan = ProjectPlan(
            project_name="Web Application",
            project_type=ProjectType.WEB_APPLICATION,
            tech_stack=TechStack.REACT_NODE,
            features=[],
            tasks=[],
            milestones=[],
            estimated_duration_weeks=4,
            team_size=3
        )
        
        assert plan.project_name == "Web Application"
        assert plan.project_type == ProjectType.WEB_APPLICATION
        assert plan.tech_stack == TechStack.REACT_NODE
        assert len(plan.features) == 0
        assert len(plan.tasks) == 0
        assert len(plan.milestones) == 0


class TestPlanGenerator:
    """Test the plan generator"""
    
    @pytest.fixture
    def orchestrator_mock(self):
        """Create a mock orchestrator"""
        mock = AsyncMock(spec=IntelligentOrchestrator)
        return mock
    
    @pytest.fixture
    def plan_generator(self, orchestrator_mock):
        """Create a plan generator for testing"""
        generator = PlanGenerator(orchestrator=orchestrator_mock)
        return generator
    
    def test_initialization(self, plan_generator, orchestrator_mock):
        """Test plan generator initialization"""
        assert plan_generator.orchestrator == orchestrator_mock
    
    @pytest.mark.asyncio
    async def test_generate_plan(self, plan_generator, orchestrator_mock):
        """Test generating a project plan"""
        # Mock the orchestrator's consult_agents method
        orchestrator_mock.consult_agents.return_value = AsyncMock(
            consensus_certainty=CertaintyLevel.HIGH,
            consensus_response=json.dumps({
                "project_type": "web_application",
                "tech_stack": "react_node",
                "features": [
                    {
                        "name": "User Authentication",
                        "priority": "high"
                    }
                ]
            })
        )
        
        plan = await plan_generator.generate_plan(
            project_description="A test project for unit testing",
            requirements={
                "features": ["user authentication", "dashboard"],
                "constraints": {"budget": 10000, "timeline": "3 months"}
            }
        )
        
        assert plan is not None
        assert isinstance(plan, ProjectPlan)
        assert orchestrator_mock.consult_agents.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
