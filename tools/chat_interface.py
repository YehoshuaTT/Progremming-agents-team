"""
Chat Interface for Natural User-Agent Conversation

This module provides a conversational interface for users to interact with the
intelligent agent system through natural language. It handles user input parsing,
agent response formatting, and maintains conversation context.

Key Features:
- Natural language processing for user commands
- Context-aware conversation management
- Agent response formatting and display
- Real-time conversation logging
- Multi-turn dialogue support
- Integration with orchestrator for agent consultation

Status: Ready for integration
Dependencies: intelligent_orchestrator.py, certainty_framework.py
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .intelligent_orchestrator import IntelligentOrchestrator, AgentConsultationResult
from .certainty_framework import CertaintyFramework, CertaintyLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages in the conversation"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    CONSULTATION = "consultation"
    APPROVAL_REQUEST = "approval_request"

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation"""
    id: str
    type: MessageType
    content: str
    timestamp: datetime
    agent_id: Optional[str] = None
    certainty_level: Optional[CertaintyLevel] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationContext:
    """Manages conversation context and history"""
    
    def __init__(self, max_history: int = 100):
        self.messages: List[ConversationMessage] = []
        self.max_history = max_history
        self.current_task: Optional[str] = None
        self.user_preferences: Dict[str, Any] = {}
        self.active_agents: List[str] = []
        
    def add_message(self, message: ConversationMessage):
        """Add a message to the conversation history"""
        self.messages.append(message)
        
        # Maintain history limit
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_recent_context(self, count: int = 5) -> List[ConversationMessage]:
        """Get recent conversation messages for context"""
        return self.messages[-count:] if self.messages else []
    
    def get_task_context(self) -> Optional[str]:
        """Get current task context"""
        return self.current_task
    
    def set_task_context(self, task: str):
        """Set current task context"""
        self.current_task = task
    
    def clear_context(self):
        """Clear conversation context"""
        self.messages.clear()
        self.current_task = None
        self.active_agents.clear()

class ChatInterface:
    """Main chat interface for user-agent conversation"""
    
    def __init__(self, orchestrator: IntelligentOrchestrator):
        self.orchestrator = orchestrator
        self.certainty_framework = CertaintyFramework()
        self.context = ConversationContext()
        self.is_running = False
        self.approval_pending = False
        self.pending_actions: List[Dict[str, Any]] = []
        
    async def start_conversation(self):
        """Start the interactive conversation"""
        self.is_running = True
        
        welcome_message = ConversationMessage(
            id=self._generate_message_id(),
            type=MessageType.SYSTEM,
            content="Welcome to the Intelligent Agent System! How can I help you today?",
            timestamp=datetime.now()
        )
        
        self.context.add_message(welcome_message)
        self._display_message(welcome_message)
        
        while self.is_running:
            try:
                user_input = await self._get_user_input()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    await self._handle_exit()
                    break
                
                await self._process_user_input(user_input)
                
            except KeyboardInterrupt:
                await self._handle_exit()
                break
            except Exception as e:
                logger.error(f"Error in conversation: {e}")
                await self._handle_error(str(e))
    
    async def _get_user_input(self) -> str:
        """Get user input with proper prompting"""
        if self.approval_pending:
            prompt = "\n🔄 Approval needed (approve/deny/modify): "
        else:
            prompt = "\n💬 You: "
        
        return input(prompt).strip()
    
    async def _process_user_input(self, user_input: str):
        """Process user input and generate appropriate responses"""
        # Add user message to context
        user_message = ConversationMessage(
            id=self._generate_message_id(),
            type=MessageType.USER,
            content=user_input,
            timestamp=datetime.now()
        )
        self.context.add_message(user_message)
        
        # Handle approval responses
        if self.approval_pending:
            await self._handle_approval_response(user_input)
            return
        
        # Parse user intent and generate response
        intent = await self._parse_user_intent(user_input)
        
        # Consult agents based on intent
        consultation_result = await self._consult_agents(intent)
        
        # Handle the consultation result
        await self._handle_consultation_result(consultation_result)
    
    async def _parse_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Parse user input to understand intent"""
        # Simple intent parsing - can be enhanced with NLP
        intent = {
            "type": "general_query",
            "content": user_input,
            "keywords": user_input.lower().split(),
            "context": self.context.get_task_context()
        }
        
        # Detect specific intent types
        if any(word in user_input.lower() for word in ['create', 'build', 'make', 'generate']):
            intent["type"] = "creation_request"
        elif any(word in user_input.lower() for word in ['fix', 'debug', 'error', 'problem']):
            intent["type"] = "problem_solving"
        elif any(word in user_input.lower() for word in ['explain', 'how', 'what', 'why']):
            intent["type"] = "information_request"
        elif any(word in user_input.lower() for word in ['test', 'verify', 'check']):
            intent["type"] = "validation_request"
        
        return intent
    
    async def _consult_agents(self, intent: Dict[str, Any]) -> AgentConsultationResult:
        """Consult relevant agents based on user intent"""
        # Determine relevant agents based on intent
        relevant_agents = self._get_relevant_agents(intent)
        
        # Prepare consultation request
        consultation_request = {
            "query": intent["content"],
            "intent_type": intent["type"],
            "context": self.context.get_recent_context(5),
            "current_task": intent.get("context")
        }
        
        # Consult agents through orchestrator
        result = await self.orchestrator.consult_agents(
            query=consultation_request["query"],
            agents=relevant_agents,
            context=consultation_request
        )
        
        return result
    
    def _get_relevant_agents(self, intent: Dict[str, Any]) -> List[str]:
        """Determine which agents are relevant for the given intent"""
        all_agents = self.orchestrator.get_available_agents()
        
        # Simple relevance matching - can be enhanced
        relevant_agents = []
        
        intent_type = intent["type"]
        keywords = intent["keywords"]
        
        for agent_id in all_agents:
            agent_info = self.orchestrator.get_agent_info(agent_id)
            if agent_info:
                capabilities = agent_info.get("capabilities", [])
                
                # Match based on intent type
                if intent_type == "creation_request" and "creation" in capabilities:
                    relevant_agents.append(agent_id)
                elif intent_type == "problem_solving" and "debugging" in capabilities:
                    relevant_agents.append(agent_id)
                elif intent_type == "information_request" and "analysis" in capabilities:
                    relevant_agents.append(agent_id)
                elif intent_type == "validation_request" and "testing" in capabilities:
                    relevant_agents.append(agent_id)
                
                # Match based on keywords
                for keyword in keywords:
                    if keyword in str(capabilities).lower():
                        if agent_id not in relevant_agents:
                            relevant_agents.append(agent_id)
        
        # If no specific agents found, include general agents
        if not relevant_agents:
            relevant_agents = all_agents[:3]  # Top 3 agents
        
        return relevant_agents
    
    async def _handle_consultation_result(self, result: AgentConsultationResult):
        """Handle the result of agent consultation"""
        if not result.responses:
            await self._handle_no_responses()
            return
        
        # Display consultation results
        await self._display_consultation_results(result)
        
        # Check if user approval is needed
        if result.requires_approval:
            await self._request_user_approval(result)
        else:
            await self._execute_actions(result)
    
    async def _execute_actions(self, result: AgentConsultationResult):
        """Execute actions from consultation result"""
        actions = self._extract_actions(result)
        
        if not actions:
            print("\n✅ No actions to execute.")
            return
        
        print(f"\n⚡ Executing {len(actions)} actions...")
        
        for action in actions:
            try:
                await self._execute_single_action(action)
                print(f"✅ Completed: {action.get('description', 'Action')}")
            except Exception as e:
                print(f"❌ Failed: {action.get('description', 'Action')} - {e}")
        
        print("\n🎉 All actions completed!")
    
    async def _display_consultation_results(self, result: AgentConsultationResult):
        """Display consultation results to user"""
        print(f"\n🤖 Agent Consultation Results (Certainty: {result.consensus_certainty.value})")
        print("=" * 60)
        
        for agent_id, response in result.responses.items():
            certainty_emoji = self._get_certainty_emoji(response.certainty_level)
            print(f"\n{certainty_emoji} Agent {agent_id}:")
            print(f"   Response: {response.content}")
            print(f"   Certainty: {response.certainty_level.value}")
            
            if response.actions:
                print(f"   Proposed Actions: {len(response.actions)}")
        
        if result.consensus_response:
            print(f"\n✅ Consensus: {result.consensus_response}")
        
        if result.escalation_needed:
            print(f"\n⚠️  Escalation Required: {result.escalation_reason}")
    
    async def _request_user_approval(self, result: AgentConsultationResult):
        """Request user approval for proposed actions"""
        self.approval_pending = True
        self.pending_actions = self._extract_actions(result)
        
        print(f"\n🔄 Approval Required")
        print("=" * 30)
        print(f"Proposed Actions: {len(self.pending_actions)}")
        
        for i, action in enumerate(self.pending_actions, 1):
            print(f"{i}. {action.get('description', 'Unknown action')}")
        
        print("\nOptions: approve, deny, modify, or ask questions")
        
        approval_message = ConversationMessage(
            id=self._generate_message_id(),
            type=MessageType.APPROVAL_REQUEST,
            content="User approval required for proposed actions",
            timestamp=datetime.now(),
            metadata={"actions": self.pending_actions}
        )
        
        self.context.add_message(approval_message)
    
    async def _handle_approval_response(self, response: str):
        """Handle user's approval response"""
        response_lower = response.lower()
        
        if response_lower in ['approve', 'yes', 'y', 'ok']:
            await self._execute_approved_actions()
        elif response_lower in ['deny', 'no', 'n', 'cancel']:
            await self._cancel_actions()
        elif response_lower in ['modify', 'change', 'edit']:
            await self._modify_actions()
        else:
            # Treat as a question about the actions
            await self._handle_approval_question(response)
    
    async def _execute_approved_actions(self):
        """Execute approved actions"""
        self.approval_pending = False
        
        print("\n✅ Executing approved actions...")
        
        for action in self.pending_actions:
            try:
                await self._execute_single_action(action)
                print(f"✅ Completed: {action.get('description', 'Action')}")
            except Exception as e:
                print(f"❌ Failed: {action.get('description', 'Action')} - {e}")
        
        self.pending_actions.clear()
        print("\n🎉 All actions completed!")
    
    async def _cancel_actions(self):
        """Cancel pending actions"""
        self.approval_pending = False
        self.pending_actions.clear()
        
        print("\n❌ Actions cancelled. How else can I help you?")
    
    async def _modify_actions(self):
        """Allow user to modify actions"""
        print("\n🔧 Action modification not yet implemented.")
        print("Please approve or deny the current actions, or ask specific questions.")
    
    async def _handle_approval_question(self, question: str):
        """Handle questions about pending actions"""
        print(f"\n💭 Question about actions: {question}")
        print("For detailed information, please ask specific questions about the actions.")
        print("Available actions:")
        
        for i, action in enumerate(self.pending_actions, 1):
            print(f"{i}. {action.get('description', 'Unknown action')}")
    
    async def _execute_single_action(self, action: Dict[str, Any]):
        """Execute a single action"""
        action_type = action.get("type", "unknown")
        
        # Route to appropriate execution method
        if action_type == "create_file":
            await self._execute_create_file(action)
        elif action_type == "modify_file":
            await self._execute_modify_file(action)
        elif action_type == "run_command":
            await self._execute_run_command(action)
        else:
            logger.warning(f"Unknown action type: {action_type}")
    
    async def _execute_create_file(self, action: Dict[str, Any]):
        """Execute file creation action"""
        filepath = action.get("filepath", "")
        content = action.get("content", "")
        
        if filepath and content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    async def _execute_modify_file(self, action: Dict[str, Any]):
        """Execute file modification action"""
        # Implementation depends on modification type
        pass
    
    async def _execute_run_command(self, action: Dict[str, Any]):
        """Execute command action"""
        # Implementation for running commands
        pass
    
    def _extract_actions(self, result: AgentConsultationResult) -> List[Dict[str, Any]]:
        """Extract actions from consultation result"""
        actions = []
        
        for agent_id, response in result.responses.items():
            if response.actions:
                actions.extend(response.actions)
        
        return actions
    
    async def _handle_no_responses(self):
        """Handle case when no agent responses are available"""
        message = ConversationMessage(
            id=self._generate_message_id(),
            type=MessageType.SYSTEM,
            content="I'm sorry, but I couldn't get any responses from the agents. Please try rephrasing your request.",
            timestamp=datetime.now()
        )
        
        self.context.add_message(message)
        self._display_message(message)
    
    async def _handle_error(self, error: str):
        """Handle conversation errors"""
        error_message = ConversationMessage(
            id=self._generate_message_id(),
            type=MessageType.SYSTEM,
            content=f"An error occurred: {error}. Please try again.",
            timestamp=datetime.now()
        )
        
        self.context.add_message(error_message)
        self._display_message(error_message)
    
    async def _handle_exit(self):
        """Handle conversation exit"""
        self.is_running = False
        
        exit_message = ConversationMessage(
            id=self._generate_message_id(),
            type=MessageType.SYSTEM,
            content="Thank you for using the Intelligent Agent System. Goodbye!",
            timestamp=datetime.now()
        )
        
        self.context.add_message(exit_message)
        self._display_message(exit_message)
    
    def _display_message(self, message: ConversationMessage):
        """Display a message to the user"""
        timestamp = message.timestamp.strftime("%H:%M:%S")
        
        if message.type == MessageType.SYSTEM:
            print(f"\n🤖 [{timestamp}] {message.content}")
        elif message.type == MessageType.AGENT:
            agent_emoji = self._get_agent_emoji(message.agent_id)
            print(f"\n{agent_emoji} [{timestamp}] Agent {message.agent_id}: {message.content}")
        elif message.type == MessageType.CONSULTATION:
            print(f"\n🔍 [{timestamp}] {message.content}")
    
    def _get_certainty_emoji(self, certainty: CertaintyLevel) -> str:
        """Get emoji representation of certainty level"""
        emoji_map = {
            CertaintyLevel.VERY_LOW: "🔴",
            CertaintyLevel.LOW: "🟠",
            CertaintyLevel.MEDIUM: "🟡",
            CertaintyLevel.HIGH: "🟢",
            CertaintyLevel.VERY_HIGH: "🔵"
        }
        return emoji_map.get(certainty, "⚪")
    
    def _get_agent_emoji(self, agent_id: Optional[str]) -> str:
        """Get emoji representation for agent"""
        if not agent_id:
            return "🤖"
        
        # Simple mapping - can be enhanced
        if "creator" in agent_id.lower():
            return "🛠️"
        elif "analyzer" in agent_id.lower():
            return "🔍"
        elif "tester" in agent_id.lower():
            return "🧪"
        else:
            return "🤖"
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        return f"msg_{datetime.now().timestamp()}"
    
    def save_conversation(self, filepath: str):
        """Save conversation to file"""
        conversation_data = {
            "messages": [asdict(msg) for msg in self.context.messages],
            "task_context": self.context.current_task,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, default=str)
    
    def load_conversation(self, filepath: str):
        """Load conversation from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.context.messages = [
            ConversationMessage(**msg) for msg in data["messages"]
        ]
        self.context.current_task = data.get("task_context")

# Example usage
async def main():
    """Example usage of the chat interface"""
    orchestrator = IntelligentOrchestrator()
    
    # Register some example agents
    orchestrator.register_agent(
        agent_id="creator_agent",
        capabilities=["creation", "file_generation"],
        weight=0.8
    )
    
    orchestrator.register_agent(
        agent_id="analyzer_agent", 
        capabilities=["analysis", "debugging"],
        weight=0.7
    )
    
    # Start chat interface
    chat = ChatInterface(orchestrator)
    await chat.start_conversation()

if __name__ == "__main__":
    asyncio.run(main())
