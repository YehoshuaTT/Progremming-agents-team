"""
Test suite for Chat Interface module
Tests the user-agent conversation handling capabilities
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from tools.chat_interface import (
    ChatInterface, ConversationManager, ConversationSession,
    MessageType, ConversationMessage
)
from tools.intelligent_orchestrator import IntelligentOrchestrator, AgentConsultationResult


class TestConversationMessage:
    """Test the conversation message dataclass"""
    
    def test_message_creation(self):
        """Test creating a conversation message"""
        message = ConversationMessage(
            id="123",
            type=MessageType.USER,
            content="Hello agents",
            timestamp=datetime.now()
        )
        
        assert message.id == "123"
        assert message.type == MessageType.USER
        assert message.content == "Hello agents"
        assert message.agent_id is None
    
    def test_message_with_agent_id(self):
        """Test creating a message with agent ID"""
        message = ConversationMessage(
            id="456",
            type=MessageType.AGENT,
            content="I'm the coder agent",
            timestamp=datetime.now(),
            agent_id="coder"
        )
        
        assert message.id == "456"
        assert message.type == MessageType.AGENT
        assert message.content == "I'm the coder agent"
        assert message.agent_id == "coder"
    
    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        now = datetime.now()
        message = ConversationMessage(
            id="789",
            type=MessageType.SYSTEM,
            content="System notification",
            timestamp=now
        )
        
        message_dict = message.to_dict()
        
        assert message_dict["id"] == "789"
        assert message_dict["type"] == "system"
        assert message_dict["content"] == "System notification"
        assert message_dict["timestamp"] == now.isoformat()
        assert "agent_id" not in message_dict or message_dict["agent_id"] is None


class TestConversationSession:
    """Test the conversation session"""
    
    @pytest.fixture
    def session(self):
        """Create a conversation session for testing"""
        return ConversationSession(
            session_id="test-session",
            user_id="test-user"
        )
    
    def test_session_initialization(self, session):
        """Test conversation session initialization"""
        assert session.session_id == "test-session"
        assert session.user_id == "test-user"
        assert session.start_time is not None
        assert len(session.messages) == 0
        assert session.active is True
        assert session.context == {}
    
    def test_add_message(self, session):
        """Test adding a message to a session"""
        message = ConversationMessage(
            id="123",
            type=MessageType.USER,
            content="Test message",
            timestamp=datetime.now()
        )
        
        session.add_message(message)
        
        assert len(session.messages) == 1
        assert session.messages[0] == message
    
    def test_get_message_history(self, session):
        """Test getting message history"""
        # Add multiple messages
        message1 = ConversationMessage(
            id="1",
            type=MessageType.USER,
            content="First message",
            timestamp=datetime.now()
        )
        message2 = ConversationMessage(
            id="2",
            type=MessageType.AGENT,
            content="Second message",
            timestamp=datetime.now(),
            agent_id="agent1"
        )
        
        session.add_message(message1)
        session.add_message(message2)
        
        history = session.get_message_history()
        
        assert len(history) == 2
        assert history[0].id == "1"
        assert history[1].id == "2"
    
    def test_update_context(self, session):
        """Test updating context"""
        session.update_context({"project": "test-project"})
        
        assert "project" in session.context
        assert session.context["project"] == "test-project"
        
        # Update with additional context
        session.update_context({"language": "python"})
        
        assert "project" in session.context
        assert "language" in session.context
        assert session.context["language"] == "python"


class TestConversationManager:
    """Test the conversation manager"""
    
    @pytest.fixture
    def manager(self):
        """Create a conversation manager for testing"""
        return ConversationManager()
    
    def test_create_session(self, manager):
        """Test creating a new conversation session"""
        session = manager.create_session("user1")
        
        assert session.user_id == "user1"
        assert session.session_id in manager.sessions
        assert manager.sessions[session.session_id] == session
    
    def test_get_session(self, manager):
        """Test getting a conversation session"""
        # Create a session first
        session = manager.create_session("user2")
        session_id = session.session_id
        
        # Get the session
        retrieved_session = manager.get_session(session_id)
        
        assert retrieved_session == session
    
    def test_get_active_sessions(self, manager):
        """Test getting active sessions"""
        # Create multiple sessions
        session1 = manager.create_session("user3")
        session2 = manager.create_session("user4")
        
        # Deactivate one session
        session1.active = False
        
        active_sessions = manager.get_active_sessions()
        
        assert len(active_sessions) == 1
        assert session2.session_id in [s.session_id for s in active_sessions]
    
    def test_close_session(self, manager):
        """Test closing a session"""
        # Create a session
        session = manager.create_session("user5")
        session_id = session.session_id
        
        # Close the session
        manager.close_session(session_id)
        
        # Get the session and check if it's inactive
        closed_session = manager.get_session(session_id)
        assert closed_session.active is False


class TestChatInterface:
    """Test the chat interface"""
    
    @pytest.fixture
    def orchestrator_mock(self):
        """Create a mock orchestrator"""
        mock = AsyncMock(spec=IntelligentOrchestrator)
        return mock
    
    @pytest.fixture
    def chat_interface(self, orchestrator_mock):
        """Create a chat interface for testing"""
        interface = ChatInterface(orchestrator=orchestrator_mock)
        return interface
    
    @pytest.mark.asyncio
    async def test_initialization(self, chat_interface, orchestrator_mock):
        """Test chat interface initialization"""
        assert chat_interface.orchestrator == orchestrator_mock
        assert chat_interface.conversation_manager is not None
        
    @pytest.mark.asyncio
    async def test_start_conversation(self, chat_interface):
        """Test starting a new conversation"""
        result = await chat_interface.start_conversation("user123")
        
        assert "session_id" in result
        assert "message" in result
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_send_message(self, chat_interface, orchestrator_mock):
        """Test sending a message"""
        # First create a session
        session_info = await chat_interface.start_conversation("user456")
        session_id = session_info["session_id"]
        
        # Set up orchestrator mock to return a response
        from tools.certainty_framework import CertaintyLevel
        orchestrator_mock.consult_agents.return_value = AgentConsultationResult(
            query="Can you help me build an app?",
            responses={},
            consensus_response="I'll help you with that",
            consensus_certainty=CertaintyLevel.HIGH
        )
        
        # Send a message
        response = await chat_interface.send_message(
            session_id=session_id,
            message="Can you help me build an app?"
        )
        
        assert response["status"] == "success"
        assert "message_id" in response
        assert "response" in response
        
        # Note: The orchestrator may or may not be called depending on the implementation
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, chat_interface):
        """Test retrieving conversation history"""
        # Create a session and add some messages
        session_info = await chat_interface.start_conversation("user789")
        session_id = session_info["session_id"]
        
        # Get the session and add messages manually
        session = chat_interface.conversation_manager.get_session(session_id)
        message1 = ConversationMessage(
            id="test1",
            type=MessageType.USER,
            content="User question",
            timestamp=datetime.now()
        )
        message2 = ConversationMessage(
            id="test2",
            type=MessageType.AGENT,
            content="Agent response",
            timestamp=datetime.now(),
            agent_id="agent1"
        )
        session.add_message(message1)
        session.add_message(message2)
        
        # Get the history
        history = await chat_interface.get_conversation_history(session_id)
        
        # The history should include the manual messages plus any system messages
        assert len(history["messages"]) >= 2
    
    @pytest.mark.asyncio
    async def test_end_conversation(self, chat_interface):
        """Test ending a conversation"""
        # Create a session
        session_info = await chat_interface.start_conversation("user999")
        session_id = session_info["session_id"]
        
        # End the conversation
        result = await chat_interface.end_conversation(session_id)
        
        assert result["status"] == "success"
        assert result["session_id"] == session_id
        assert result["ended"] is True
        
        # Check that session is marked inactive
        session = chat_interface.conversation_manager.get_session(session_id)
        assert session.active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
