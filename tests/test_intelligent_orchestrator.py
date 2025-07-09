"""
Test suite for Intelligent Orchestrator module
Tests the agent communication and orchestration system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from tools.intelligent_orchestrator import (
    IntelligentOrchestrator, AgentRegistry, CommunicationHub, 
    WorkflowPhase, AgentRole, AgentInfo, AgentMessage, CommunicationType
)
from tools.certainty_framework import create_decision, DecisionType


class TestAgentRegistry:
    """Test the agent registry"""
    
    @pytest.fixture
    def registry(self):
        """Create an agent registry for testing"""
        registry = AgentRegistry()
        # Clear default agents for clean testing
        registry.agents = {}
        registry.role_mappings = {}
        return registry
    
    def test_register_agent(self, registry):
        """Test registering an agent"""
        agent = AgentInfo(
            name="test_agent",
            role=AgentRole.CODER,
            specialties=["python", "testing"],
            workload=2
        )
        
        registry.register_agent(agent)
        
        assert "test_agent" in registry.agents
        assert registry.agents["test_agent"] == agent
    
    def test_get_agents_by_role(self, registry):
        """Test getting agents by role"""
        agent1 = AgentInfo(
            name="coder1",
            role=AgentRole.CODER,
            specialties=["python"],
            workload=1
        )
        agent2 = AgentInfo(
            name="coder2", 
            role=AgentRole.CODER,
            specialties=["javascript"],
            workload=3
        )
        agent3 = AgentInfo(
            name="architect1",
            role=AgentRole.ARCHITECT,
            specialties=["system_design"],
            workload=2
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        registry.register_agent(agent3)
        
        coders = registry.get_agents_by_role(AgentRole.CODER)
        architects = registry.get_agents_by_role(AgentRole.ARCHITECT)
        
        assert len(coders) == 2
        assert len(architects) == 1
        assert agent1 in coders
        assert agent2 in coders
        assert agent3 in architects
    
    def test_get_agents_by_specialty(self, registry):
        """Test getting agents by specialty"""
        agent1 = AgentInfo(
            name="python_expert",
            role=AgentRole.CODER,
            specialties=["python", "testing"],
            workload=1
        )
        agent2 = AgentInfo(
            name="js_expert",
            role=AgentRole.CODER,
            specialties=["javascript", "react"],
            workload=2
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        python_agents = registry.get_agents_by_specialty("python")
        js_agents = registry.get_agents_by_specialty("javascript")
        
        assert len(python_agents) == 1
        assert len(js_agents) == 1
        assert agent1 in python_agents
        assert agent2 in js_agents
    
    def test_get_available_agents(self, registry):
        """Test getting available agents"""
        agent1 = AgentInfo(
            name="available_agent",
            role=AgentRole.CODER,
            specialties=["python"],
            workload=1
        )
        agent2 = AgentInfo(
            name="busy_agent",
            role=AgentRole.CODER,
            specialties=["python"],
            workload=4  # High workload
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        available = registry.get_available_agents(workload_threshold=0.8)
        
        assert len(available) == 1
        assert agent1 in available
        assert agent2 not in available


class TestCommunicationHub:
    """Test the communication hub"""
    
    @pytest.fixture
    def registry(self):
        """Create registry with test agents"""
        registry = AgentRegistry()
        # Clear default agents for clean testing
        registry.agents = {}
        registry.role_mappings = {}
        
        agent1 = AgentInfo(
            name="agent1",
            role=AgentRole.CODER,
            specialties=["python"],
            workload=1
        )
        agent2 = AgentInfo(
            name="agent2",
            role=AgentRole.ARCHITECT,
            specialties=["design"],
            workload=2
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        return registry
    
    @pytest.fixture
    def comm_hub(self, registry):
        """Create a communication hub for testing"""
        return CommunicationHub(registry)
    
    @pytest.mark.asyncio
    async def test_send_message(self, comm_hub):
        """Test sending a message"""
        message = AgentMessage()
        message.sender = "agent1"
        message.recipient = "agent2"
        message.message_type = CommunicationType.HANDOFF
        message.content = "Test message"
        message.context = {"test": "context"}
        
        await comm_hub.send_message(message)
        
        # Check message was stored
        messages = await comm_hub.get_conversation_history("agent1", "agent2")
        assert len(messages) == 1
        assert messages[0].content == "Test message"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_broadcast_message(self, comm_hub):
        """Test broadcasting a message"""
        sender = "orchestrator"
        message_content = "Broadcast message"
        target_roles = [AgentRole.CODER, AgentRole.ARCHITECT]
        
        sent_count = await comm_hub.broadcast_message(
            sender=sender,
            message_content=message_content,
            message_type=CommunicationType.NOTIFICATION,
            target_roles=target_roles
        )
        
        # Should send to both agents but not sender
        assert sent_count == 2
        
        # Check all agents received the message
        agent1_messages = await comm_hub.get_messages("agent1")
        agent2_messages = await comm_hub.get_messages("agent2")
        
        assert len(agent1_messages) == 1
        assert len(agent2_messages) == 1
        assert agent1_messages[0].content == message_content
        assert agent2_messages[0].content == message_content
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, comm_hub):
        """Test getting conversation history"""
        message1 = AgentMessage()
        message1.sender = "agent1"
        message1.recipient = "agent2"
        message1.message_type = CommunicationType.CONSULTATION
        message1.content = "First message"
        message1.context = {}
        
        message2 = AgentMessage()
        message2.sender = "agent2"
        message2.recipient = "agent1"
        message2.message_type = CommunicationType.ANSWER  # Using ANSWER instead of CONSULTATION_RESPONSE
        message2.content = "Response message"
        message2.context = {}
        
        await comm_hub.send_message(message1)
        await comm_hub.send_message(message2)
        
        history = await comm_hub.get_conversation_history("agent1", "agent2")
        
        assert len(history) == 2
        assert history[0].content == "First message"
        assert history[1].content == "Response message"


class TestIntelligentOrchestrator:
    """Test the intelligent orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator for testing"""
        return IntelligentOrchestrator()
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.agent_registry is not None
        assert orchestrator.communication_hub is not None
        assert orchestrator.current_phase == WorkflowPhase.PLANNING
        assert isinstance(orchestrator.project_context, dict)
        assert isinstance(orchestrator.task_queue, list)
        assert isinstance(orchestrator.completed_tasks, list)
        assert isinstance(orchestrator.user_approvals_needed, list)
    
    @pytest.mark.asyncio
    async def test_start_project(self, orchestrator):
        """Test starting a new project"""
        # Mock agent registry to have required agents
        mock_product_analyst = AgentInfo(
            name="product_analyst",
            role=AgentRole.PRODUCT_ANALYST,
            specialties=["requirements"],
            workload=0
        )
        mock_ask_agent = AgentInfo(
            name="ask_agent",
            role=AgentRole.ASK_AGENT,
            specialties=["questions"],
            workload=0
        )
        
        orchestrator.agent_registry.register_agent(mock_product_analyst)
        orchestrator.agent_registry.register_agent(mock_ask_agent)
        
        result = await orchestrator.start_project(
            "Create a web application",
            {"features": ["login", "dashboard"]}
        )
        
        assert result['project_started'] is True
        assert result['current_phase'] == WorkflowPhase.PLANNING.value
        assert 'assigned_agents' in result
        assert len(result['assigned_agents']) == 2
    
    @pytest.mark.asyncio
    async def test_process_agent_decision(self, orchestrator):
        """Test processing an agent decision"""
        decision = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=85.0,
            content="Implement feature X",
            reasoning="Clear requirements"
        )
        
        result = await orchestrator.process_agent_decision("test_agent", decision)
        
        assert 'decision_id' in result
        assert 'actions_taken' in result  # Fixed: should be actions_taken (list) not action_taken
        assert 'decision_processed' in result
        assert result['decision_processed'] == True
    
    @pytest.mark.asyncio
    async def test_register_agent(self, orchestrator):
        """Test registering an agent with capabilities"""
        result = orchestrator.register_agent(
            agent_id="new_agent",
            capabilities=["python", "testing"],
            weight=0.8
        )
        
        assert result['registered'] is True
        assert result['agent_id'] == "new_agent"
        
        # Verify agent was added to registry
        agents = orchestrator.agent_registry.get_agents_by_specialty("python")
        assert len(agents) > 0
        assert any(agent.name == "new_agent" for agent in agents)
    
    @pytest.mark.asyncio
    async def test_get_consultation_targets(self, orchestrator):
        """Test getting consultation targets"""
        decision = create_decision(
            agent_name="junior_dev",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=60.0,
            content="Architecture decision",
            reasoning="Need expert input"
        )
        
        targets = await orchestrator._identify_consultation_targets("junior_dev", decision)
        
        assert isinstance(targets, list)
        # Should return relevant agents for architecture decisions
    
    @pytest.mark.asyncio
    async def test_get_pending_user_approvals(self, orchestrator):
        """Test getting pending user approvals"""
        # Add a mock approval
        orchestrator.user_approvals_needed.append({
            'approval_id': 'test_approval',
            'decision_type': 'implementation',
            'description': 'Test approval needed',
            'timestamp': datetime.now().isoformat()
        })
        
        approvals = await orchestrator.get_pending_user_approvals()
        
        assert len(approvals) == 1
        assert approvals[0]['approval_id'] == 'test_approval'
    
    @pytest.mark.asyncio
    async def test_phase_transitions(self, orchestrator):
        """Test workflow phase transitions"""
        initial_phase = orchestrator.current_phase
        
        # Test transitioning to next phase
        orchestrator.current_phase = WorkflowPhase.REQUIREMENTS
        assert orchestrator.current_phase == WorkflowPhase.REQUIREMENTS
        
        orchestrator.current_phase = WorkflowPhase.ARCHITECTURE
        assert orchestrator.current_phase == WorkflowPhase.ARCHITECTURE
    
    @pytest.mark.asyncio
    async def test_task_queue_management(self, orchestrator):
        """Test task queue management"""
        task = {
            'task_id': 'test_task',
            'description': 'Test task',
            'assigned_agent': 'test_agent',
            'priority': 'high'
        }
        
        orchestrator.task_queue.append(task)
        
        assert len(orchestrator.task_queue) == 1
        assert orchestrator.task_queue[0]['task_id'] == 'test_task'
        
        # Move task to completed
        completed_task = orchestrator.task_queue.pop(0)
        completed_task['status'] = 'completed'
        orchestrator.completed_tasks.append(completed_task)
        
        assert len(orchestrator.task_queue) == 0
        assert len(orchestrator.completed_tasks) == 1
        assert orchestrator.completed_tasks[0]['status'] == 'completed'
    
    def test_agent_data_structures(self, orchestrator):
        """Test agent-related data structures"""
        # Test Agent dataclass
        agent = AgentInfo(
            name="test_agent",
            role=AgentRole.CODER,
            specialties=["python", "testing"],
            workload=2
        )
        
        assert agent.name == "test_agent"
        assert agent.role == AgentRole.CODER
        assert "python" in agent.specialties
        assert agent.workload == 2
        
        # Test AgentMessage dataclass
        message = AgentMessage()
        message.sender = "agent1"
        message.recipient = "agent2"
        message.message_type = CommunicationType.HANDOFF
        message.content = "Test message"
        message.context = {"key": "value"}
        
        assert message.sender == "agent1"
        assert message.recipient == "agent2"
        assert message.message_type == CommunicationType.HANDOFF
        assert message.content == "Test message"
        assert message.context["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_agent_workload_management(self, orchestrator):
        """Test agent workload management"""
        agent = AgentInfo(
            name="workload_test_agent",
            role=AgentRole.CODER,
            specialties=["python"],
            workload=1
        )
        
        orchestrator.agent_registry.register_agent(agent)
        
        # Test getting available agents
        available = orchestrator.agent_registry.get_available_agents(workload_threshold=0.5)
        assert len(available) >= 1
        assert any(a.name == "workload_test_agent" for a in available)
        
        # Test workload update
        agent.workload = 4  # High workload (80% of max capacity)
        available_high_threshold = orchestrator.agent_registry.get_available_agents(workload_threshold=0.7)  # Only 70% threshold
        assert not any(a.name == "workload_test_agent" for a in available_high_threshold)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
