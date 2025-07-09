"""
Test suite for Certainty Framework module
Tests the decision-making framework with certainty levels
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from tools.certainty_framework import (
    CertaintyFramework, AgentDecision, DecisionType, CertaintyLevel,
    EscalationReason, create_decision
)


class TestCertaintyFramework:
    """Test the certainty framework"""
    
    @pytest.fixture
    def framework(self):
        """Create a certainty framework for testing"""
        return CertaintyFramework()
    
    def test_create_decision(self):
        """Test creating a decision with the helper function"""
        decision = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=85.0,
            content="Test decision",
            reasoning="Test reasoning",
            alternatives=["Option A", "Option B"]
        )
        
        assert decision.agent_id == "test_agent"
        assert decision.decision_type == DecisionType.IMPLEMENTATION
        assert decision.decision_content == "Test decision"
        assert decision.certainty_level == 85.0
        assert decision.reasoning == "Test reasoning"
        assert decision.alternative_options == ["Option A", "Option B"]
    
    def test_decision_to_dict(self):
        """Test decision serialization"""
        decision = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=65.0,
            content="Test decision",
            reasoning="Test reasoning"
        )
        
        decision_dict = decision.to_dict()
        
        assert decision_dict['agent_id'] == "test_agent"
        assert decision_dict['decision_type'] == DecisionType.ARCHITECTURE
        assert decision_dict['decision_content'] == "Test decision"
        assert decision_dict['certainty_level'] == 65.0
        assert 'timestamp' in decision_dict
    
    @pytest.mark.asyncio
    async def test_evaluate_decision_high_certainty(self, framework):
        """Test evaluating a high certainty decision"""
        decision = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=95.0,
            content="High certainty decision",
            reasoning="Clear implementation path"
        )
        
        result = await framework.evaluate_decision(decision)
        
        assert 'proceed_with_confidence' in result['next_actions']
        assert result['certainty_category'] == CertaintyLevel.VERY_HIGH.value
        assert not result['requires_consultation']
        assert not result['should_escalate']
    
    @pytest.mark.asyncio
    async def test_evaluate_decision_medium_certainty(self, framework):
        """Test evaluating a medium certainty decision"""
        decision = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=75.0,
            content="Medium certainty decision",
            reasoning="Some uncertainty about approach"
        )
        
        result = await framework.evaluate_decision(decision)
        
        assert 'consult_peers' in result['next_actions'] or 'escalate_to_supervisor' in result['next_actions']
        assert result['certainty_category'] == CertaintyLevel.MEDIUM.value
    
    @pytest.mark.asyncio
    async def test_evaluate_decision_low_certainty(self, framework):
        """Test evaluating a low certainty decision"""
        decision = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=45.0,
            content="Low certainty decision",
            reasoning="Multiple viable options"
        )
        
        result = await framework.evaluate_decision(decision)
        
        # The low certainty may trigger different actions depending on thresholds
        # Either consult_peers or request_user_approval are valid low confidence responses
        assert any(action in ['consult_peers', 'request_user_approval', 'escalate_to_supervisor'] 
                  for action in result['next_actions'])
        assert result['certainty_category'] == CertaintyLevel.LOW.value
        assert result['should_escalate']
    
    @pytest.mark.asyncio
    async def test_evaluate_adds_to_history(self, framework):
        """Test that evaluation adds decision to history"""
        decision = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=80.0,
            content="Test decision",
            reasoning="Good reasoning"
        )
        
        # Decision is added to history during evaluation
        await framework.evaluate_decision(decision)
        
        assert len(framework.decision_history) == 1
        assert framework.decision_history[0] == decision
    
    @pytest.mark.asyncio
    async def test_initiate_consultation(self, framework):
        """Test initiating a consultation"""
        decision = create_decision(
            agent_name="primary_agent",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=65.0,
            content="Need consultation",
            reasoning="Uncertain about approach"
        )
        
        consultation_id = await framework.initiate_consultation(
            decision.agent_id,
            decision,
            ["architect", "senior_dev"]
        )
        
        assert consultation_id is not None
        assert consultation_id.startswith("consultation_")
    
    @pytest.mark.asyncio
    async def test_get_decision_history(self, framework):
        """Test getting decision history"""
        decision1 = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=80.0,
            content="Decision 1",
            reasoning="Reasoning 1"
        )
        decision2 = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=75.0,
            content="Decision 2",
            reasoning="Reasoning 2"
        )
        
        # Add decisions to history via evaluate_decision
        await framework.evaluate_decision(decision1)
        await framework.evaluate_decision(decision2)
        
        # Get the full decision history
        history = await framework.get_decision_history()
        
        assert len(history) >= 2
        assert decision1 in history
        assert decision2 in history
    
    def test_certainty_levels(self):
        """Test certainty level classification"""
        decision_high = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=95.0,
            content="High certainty",
            reasoning="Clear path"
        )
        
        decision_medium = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=75.0,
            content="Medium certainty",
            reasoning="Some uncertainty"
        )
        
        decision_low = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=45.0,
            content="Low certainty",
            reasoning="Multiple options"
        )
        
        assert decision_high.get_certainty_category() == CertaintyLevel.VERY_HIGH
        assert decision_medium.get_certainty_category() == CertaintyLevel.MEDIUM
        assert decision_low.get_certainty_category() == CertaintyLevel.LOW
    
    def test_should_escalate(self):
        """Test escalation logic"""
        decision_high = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=95.0,
            content="High certainty",
            reasoning="Clear path"
        )
        
        decision_low = create_decision(
            agent_name="test_agent",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=45.0,
            content="Low certainty",
            reasoning="Multiple options"
        )
        
        assert decision_high.should_escalate() is False
        assert decision_low.should_escalate() is True
    
    @pytest.mark.asyncio
    async def test_filter_decision_history(self, framework):
        """Test filtering decision history"""
        # Add multiple decisions
        decision1 = create_decision(
            agent_name="agent1",
            decision_type=DecisionType.IMPLEMENTATION,
            certainty=80.0,
            content="Implementation decision",
            reasoning="Implementation reasoning"
        )
        decision2 = create_decision(
            agent_name="agent2",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=90.0,
            content="Architecture decision",
            reasoning="Architecture reasoning"
        )
        
        await framework.evaluate_decision(decision1)
        await framework.evaluate_decision(decision2)
        
        # Filter by agent name
        history_agent1 = await framework.get_decision_history(agent_name="agent1")
        assert len(history_agent1) == 1
        assert history_agent1[0].agent_id == "agent1"
        
        # Filter by decision type
        history_arch = await framework.get_decision_history(decision_type=DecisionType.ARCHITECTURE)
        assert len(history_arch) >= 1
        assert history_arch[0].decision_type == DecisionType.ARCHITECTURE
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_consultation(self, framework):
        """Test storing and retrieving consultation data"""
        decision = create_decision(
            agent_name="agent1",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=70.0,
            content="Architecture decision",
            reasoning="Need consultation"
        )
        
        # Initiate consultation
        consultation_id = await framework.initiate_consultation(
            "agent1", decision, ["architect", "senior_dev"]
        )
        
        # Verify consultation was recorded
        assert consultation_id in framework.agent_consultations
        assert framework.agent_consultations[consultation_id][0] == decision
    
    @pytest.mark.asyncio
    async def test_add_consultation_response(self, framework):
        """Test adding consultation response"""
        # Create initial decision and consultation
        initial_decision = create_decision(
            agent_name="junior_dev",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=60.0,
            content="Architecture decision",
            reasoning="Need expert input"
        )
        
        consultation_id = await framework.initiate_consultation(
            "junior_dev", initial_decision, ["architect"]
        )
        
        # Create response from architect
        response_decision = create_decision(
            agent_name="architect",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=90.0,
            content="Improved architecture decision",
            reasoning="Expert perspective"
        )
        
        # Add response to consultation
        result = await framework.add_consultation_response(consultation_id, response_decision)
        
        # Verify response was added
        assert len(framework.agent_consultations[consultation_id]) == 2
        assert framework.agent_consultations[consultation_id][1] == response_decision
        assert result["response_added"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
