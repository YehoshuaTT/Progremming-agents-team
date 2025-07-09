"""
Intelligent Agent Communication and Orchestration System

This module provides sophisticated agent-to-agent communication, consultation,
and collaborative decision-making capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import yaml
from datetime import datetime
import uuid

from .certainty_framework import (
    CertaintyFramework, AgentDecision, DecisionType, 
    EscalationReason, CertaintyLevel, create_decision
)

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Roles that agents can take in the system"""
    ORCHESTRATOR = "orchestrator"
    PRODUCT_ANALYST = "product_analyst"
    ARCHITECT = "architect"
    CODER = "coder"
    CODE_REVIEWER = "code_reviewer"
    QA_GUARDIAN = "qa_guardian"
    SECURITY_SPECIALIST = "security_specialist"
    DEVOPS = "devops"
    TECHNICAL_WRITER = "technical_writer"
    TESTER = "tester"
    UX_UI_DESIGNER = "ux_ui_designer"
    GIT_AGENT = "git_agent"
    DEBUGGER = "debugger"
    LIBRARIAN = "librarian"
    ASK_AGENT = "ask_agent"

class CommunicationType(Enum):
    """Types of communication between agents"""
    CONSULTATION = "consultation"
    HANDOFF = "handoff"
    REVIEW_REQUEST = "review_request"
    NOTIFICATION = "notification"
    ESCALATION = "escalation"
    FEEDBACK = "feedback"
    QUESTION = "question"
    ANSWER = "answer"

class WorkflowPhase(Enum):
    """Phases of the development workflow"""
    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    TESTING = "testing"
    SECURITY = "security"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"
    COMPLETE = "complete"

@dataclass
class AgentMessage:
    """Represents a message between agents"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    message_type: CommunicationType = CommunicationType.NOTIFICATION
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    decision: Optional[AgentDecision] = None
    requires_response: bool = False
    response_deadline: Optional[datetime] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'message_type': self.message_type.value,
            'content': self.content,
            'context': self.context,
            'decision': self.decision.to_dict() if self.decision else None,
            'requires_response': self.requires_response,
            'response_deadline': self.response_deadline.isoformat() if self.response_deadline else None,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class AgentInfo:
    """Information about an agent in the system"""
    name: str
    role: AgentRole
    specialties: List[str] = field(default_factory=list)
    is_available: bool = True
    current_task: Optional[str] = None
    workload: int = 0
    max_workload: int = 5
    consultation_history: List[str] = field(default_factory=list)
    
    def can_take_task(self) -> bool:
        """Check if agent can take on more work"""
        return self.is_available and self.workload < self.max_workload

@dataclass
class AgentResponse:
    """Response from an agent during consultation"""
    agent_id: str
    content: str
    certainty_level: CertaintyLevel
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentConsultationResult:
    """Result of consulting multiple agents"""
    query: str
    responses: Dict[str, AgentResponse]
    consensus_response: Optional[str] = None
    consensus_certainty: CertaintyLevel = CertaintyLevel.MEDIUM
    requires_approval: bool = False
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'responses': {k: asdict(v) for k, v in self.responses.items()},
            'consensus_response': self.consensus_response,
            'consensus_certainty': self.consensus_certainty.value,
            'requires_approval': self.requires_approval,
            'escalation_needed': self.escalation_needed,
            'escalation_reason': self.escalation_reason
        }

class AgentRegistry:
    """Registry for managing all agents in the system"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.role_mappings: Dict[AgentRole, List[str]] = {}
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agents from configuration"""
        default_agents = [
            AgentInfo("orchestrator", AgentRole.ORCHESTRATOR, ["coordination", "workflow_management"]),
            AgentInfo("product_analyst", AgentRole.PRODUCT_ANALYST, ["requirements", "user_stories", "analysis"]),
            AgentInfo("architect", AgentRole.ARCHITECT, ["system_design", "architecture", "scalability"]),
            AgentInfo("coder", AgentRole.CODER, ["implementation", "coding", "algorithms"]),
            AgentInfo("code_reviewer", AgentRole.CODE_REVIEWER, ["code_quality", "best_practices", "review"]),
            AgentInfo("qa_guardian", AgentRole.QA_GUARDIAN, ["quality_assurance", "testing_strategy"]),
            AgentInfo("security_specialist", AgentRole.SECURITY_SPECIALIST, ["security", "vulnerabilities", "compliance"]),
            AgentInfo("devops", AgentRole.DEVOPS, ["deployment", "infrastructure", "ci_cd"]),
            AgentInfo("technical_writer", AgentRole.TECHNICAL_WRITER, ["documentation", "guides", "api_docs"]),
            AgentInfo("tester", AgentRole.TESTER, ["testing", "automation", "bug_finding"]),
            AgentInfo("ux_ui_designer", AgentRole.UX_UI_DESIGNER, ["user_experience", "interface_design", "usability"]),
            AgentInfo("git_agent", AgentRole.GIT_AGENT, ["version_control", "branching", "merging"]),
            AgentInfo("debugger", AgentRole.DEBUGGER, ["debugging", "troubleshooting", "error_analysis"]),
            AgentInfo("librarian", AgentRole.LIBRARIAN, ["documentation", "knowledge_management", "progress_tracking"]),
            AgentInfo("ask_agent", AgentRole.ASK_AGENT, ["user_communication", "clarification", "requirements_gathering"])
        ]
        
        for agent in default_agents:
            self.register_agent(agent)
    
    def register_agent(self, agent: AgentInfo):
        """Register an agent in the system"""
        self.agents[agent.name] = agent
        
        if agent.role not in self.role_mappings:
            self.role_mappings[agent.role] = []
        self.role_mappings[agent.role].append(agent.name)
        
        logger.info(f"Registered agent: {agent.name} ({agent.role.value})")
    
    def get_agent(self, agent_name: str) -> Optional[AgentInfo]:
        """Get agent information by name"""
        return self.agents.get(agent_name)
    
    def get_agents_by_role(self, role: AgentRole) -> List[AgentInfo]:
        """Get all agents with a specific role"""
        agent_names = self.role_mappings.get(role, [])
        return [self.agents[name] for name in agent_names if name in self.agents]
    
    def get_agents_by_specialty(self, specialty: str) -> List[AgentInfo]:
        """Get all agents with a specific specialty"""
        return [agent for agent in self.agents.values() 
                if specialty in agent.specialties]

    def get_available_agents(self, role: Optional[AgentRole] = None, 
                           workload_threshold: Optional[float] = None) -> List[AgentInfo]:
        """Get all available agents, optionally filtered by role and workload threshold"""
        agents = self.agents.values()
        
        if role:
            agents = [a for a in agents if a.role == role]
        
        # Filter by workload threshold if provided
        if workload_threshold is not None:
            # workload_threshold is a percentage (0.8 = 80% of max capacity)
            # Filter agents whose workload is below this threshold
            agents = [a for a in agents if (a.workload / a.max_workload) < workload_threshold]
        
        return [a for a in agents if a.can_take_task()]
    
    def find_best_agent_for_task(self, 
                                task_type: str, 
                                required_specialties: Optional[List[str]] = None,
                                exclude_agents: Optional[List[str]] = None) -> Optional[AgentInfo]:
        """Find the best available agent for a specific task"""
        available_agents = self.get_available_agents()
        
        if exclude_agents:
            available_agents = [a for a in available_agents if a.name not in exclude_agents]
        
        # Score agents based on specialties match
        scored_agents = []
        for agent in available_agents:
            score = 0
            
            # Base score for availability
            score += 10 - agent.workload
            
            # Bonus for matching specialties
            if required_specialties:
                matching_specialties = set(agent.specialties) & set(required_specialties)
                score += len(matching_specialties) * 5
            
            # Bonus for specific task type matching
            if task_type in agent.specialties:
                score += 10
            
            scored_agents.append((agent, score))
        
        # Return agent with highest score
        if scored_agents:
            return max(scored_agents, key=lambda x: x[1])[0]
        
        return None

class CommunicationHub:
    """Central hub for agent communication and message routing"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.message_queue: Dict[str, List[AgentMessage]] = {}
        self.message_history: List[AgentMessage] = []
        self.active_conversations: Dict[str, List[AgentMessage]] = {}
        self.certainty_framework = CertaintyFramework()
        
        # Initialize message queues for all agents
        for agent_name in self.agent_registry.agents:
            self.message_queue[agent_name] = []
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to an agent"""
        if message.recipient not in self.agent_registry.agents:
            logger.error(f"Recipient {message.recipient} not found")
            return False
        
        # Add to recipient's queue
        self.message_queue[message.recipient].append(message)
        self.message_history.append(message)
        
        # Track conversations
        conversation_id = f"{message.sender}_{message.recipient}"
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = []
        self.active_conversations[conversation_id].append(message)
        
        logger.info(f"Message sent from {message.sender} to {message.recipient}: {message.message_type.value}")
        return True
    
    async def get_messages(self, agent_name: str, mark_as_read: bool = True) -> List[AgentMessage]:
        """Get all messages for an agent"""
        if agent_name not in self.message_queue:
            return []
        
        messages = self.message_queue[agent_name].copy()
        
        if mark_as_read:
            self.message_queue[agent_name].clear()
        
        return messages
    
    async def request_consultation(self, 
                                 initiating_agent: str,
                                 decision: AgentDecision,
                                 target_agents: List[str],
                                 context: Optional[Dict[str, Any]] = None) -> str:
        """Request consultation from other agents"""
        consultation_id = str(uuid.uuid4())
        
        # Start consultation in certainty framework
        consultation = await self.certainty_framework.initiate_consultation(
            initiating_agent, decision, target_agents
        )
        
        # Send consultation messages to target agents
        for target_agent in target_agents:
            message = AgentMessage(
                sender=initiating_agent,
                recipient=target_agent,
                message_type=CommunicationType.CONSULTATION,
                content=f"Consultation request: {decision.decision_content}",
                context=context or {},
                decision=decision,
                requires_response=True
            )
            
            await self.send_message(message)
        
        return consultation_id
    
    async def respond_to_consultation(self,
                                    consultation_id: str,
                                    responding_agent: str,
                                    response_decision: AgentDecision) -> Dict[str, Any]:
        """Respond to a consultation request"""
        # Add response to certainty framework
        result = await self.certainty_framework.add_consultation_response(
            consultation_id, response_decision
        )
        
        # Send response message back to initiating agent
        # (This would be implemented based on the consultation tracking)
        
        return result
    
    async def escalate_decision(self,
                              agent_name: str,
                              decision: AgentDecision,
                              escalation_reason: EscalationReason) -> Dict[str, Any]:
        """Escalate a decision to a higher authority"""
        # Find appropriate escalation target
        escalation_target = await self._find_escalation_target(agent_name, decision)
        
        if escalation_target:
            message = AgentMessage(
                sender=agent_name,
                recipient=escalation_target,
                message_type=CommunicationType.ESCALATION,
                content=f"Escalation: {decision.decision_content}",
                context={'escalation_reason': escalation_reason.value},
                decision=decision,
                requires_response=True
            )
            
            await self.send_message(message)
            
            return {
                'escalated': True,
                'escalation_target': escalation_target,
                'escalation_reason': escalation_reason.value
            }
        else:
            # Escalate to user
            return {
                'escalated': True,
                'escalation_target': 'user',
                'escalation_reason': escalation_reason.value,
                'requires_user_input': True
            }
    
    async def _find_escalation_target(self, agent_name: str, decision: AgentDecision) -> Optional[str]:
        """Find the appropriate escalation target for a decision"""
        agent = self.agent_registry.get_agent(agent_name)
        if not agent:
            return None
        
        # Define escalation hierarchy
        escalation_hierarchy = {
            AgentRole.CODER: [AgentRole.CODE_REVIEWER, AgentRole.ARCHITECT],
            AgentRole.TESTER: [AgentRole.QA_GUARDIAN],
            AgentRole.CODE_REVIEWER: [AgentRole.ARCHITECT],
            AgentRole.UX_UI_DESIGNER: [AgentRole.ARCHITECT, AgentRole.PRODUCT_ANALYST],
            AgentRole.SECURITY_SPECIALIST: [AgentRole.ARCHITECT],
            AgentRole.DEVOPS: [AgentRole.ARCHITECT],
        }
        
        # Find escalation options
        escalation_roles = escalation_hierarchy.get(agent.role, [AgentRole.ORCHESTRATOR])
        
        for role in escalation_roles:
            available_agents = self.agent_registry.get_available_agents(role)
            if available_agents:
                return available_agents[0].name
        
        return None
    
    async def broadcast_notification(self, 
                                   sender: str,
                                   message: str,
                                   recipients: Optional[List[str]] = None,
                                   context: Optional[Dict[str, Any]] = None) -> int:
        """Broadcast a notification to multiple agents"""
        if not recipients:
            recipients = list(self.agent_registry.agents.keys())
        
        sent_count = 0
        for recipient in recipients:
            if recipient != sender:  # Don't send to self
                notification = AgentMessage(
                    sender=sender,
                    recipient=recipient,
                    message_type=CommunicationType.NOTIFICATION,
                    content=message,
                    context=context or {}
                )
                
                if await self.send_message(notification):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast_message(self, 
                             sender: str, 
                             message_content: str, 
                             message_type: CommunicationType = CommunicationType.NOTIFICATION,
                             target_roles: Optional[List[AgentRole]] = None,
                             exclude_agents: Optional[List[str]] = None) -> int:
        """Broadcast a message to multiple agents"""
        recipients = []
        
        if target_roles:
            # Send to specific roles
            for role in target_roles:
                agents = self.agent_registry.get_agents_by_role(role)
                recipients.extend([agent.name for agent in agents])
        else:
            # Send to all agents
            recipients = list(self.agent_registry.agents.keys())
        
        # Remove excluded agents
        if exclude_agents:
            recipients = [r for r in recipients if r not in exclude_agents]
        
        # Remove sender from recipients
        if sender in recipients:
            recipients.remove(sender)
        
        # Send messages
        sent_count = 0
        for recipient in recipients:
            message = AgentMessage(
                sender=sender,
                recipient=recipient,
                message_type=message_type,
                content=message_content,
                requires_response=False
            )
            
            if await self.send_message(message):
                sent_count += 1
        
        return sent_count
    
    async def get_conversation_history(self, agent1: str, agent2: str) -> List[AgentMessage]:
        """Get conversation history between two agents"""
        conversations = []
        
        # Check both directions
        conv_id1 = f"{agent1}_{agent2}"
        conv_id2 = f"{agent2}_{agent1}"
        
        if conv_id1 in self.active_conversations:
            conversations.extend(self.active_conversations[conv_id1])
        if conv_id2 in self.active_conversations:
            conversations.extend(self.active_conversations[conv_id2])
        
        # Sort by timestamp
        conversations.sort(key=lambda x: x.timestamp)
        return conversations
    
    async def get_system_communication_stats(self) -> Dict[str, Any]:
        """Get statistics about system communication"""
        stats = {
            'total_messages': len(self.message_history),
            'active_conversations': len(self.active_conversations),
            'message_types': {},
            'most_active_agents': {},
            'consultation_stats': {}
        }
        
        # Count message types
        for message in self.message_history:
            msg_type = message.message_type.value
            stats['message_types'][msg_type] = stats['message_types'].get(msg_type, 0) + 1
        
        # Count agent activity
        for message in self.message_history:
            sender = message.sender
            stats['most_active_agents'][sender] = stats['most_active_agents'].get(sender, 0) + 1
        
        # Consultation statistics
        active_consultations = await self.certainty_framework.get_active_consultations()
        stats['consultation_stats'] = {
            'active_consultations': len(active_consultations),
            'total_decisions': len(self.certainty_framework.decision_history)
        }
        
        return stats

class IntelligentOrchestrator:
    """Intelligent orchestrator that manages the entire workflow"""
    
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.communication_hub = CommunicationHub(self.agent_registry)
        self.current_phase = WorkflowPhase.PLANNING
        self.project_context: Dict[str, Any] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        self.user_approvals_needed: List[Dict[str, Any]] = []
        
    async def start_project(self, project_description: str, user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new project with intelligent agent collaboration"""
        self.project_context = {
            'description': project_description,
            'requirements': user_requirements,
            'start_time': datetime.now().isoformat(),
            'current_phase': WorkflowPhase.PLANNING.value
        }
        
        # Initiate planning phase
        logger.info(f"Starting new project: {project_description}")
        
        # Get Product Analyst to start requirements gathering
        product_analyst = self.agent_registry.get_agents_by_role(AgentRole.PRODUCT_ANALYST)[0]
        ask_agent = self.agent_registry.get_agents_by_role(AgentRole.ASK_AGENT)[0]
        
        # Send initial project message
        initial_message = AgentMessage(
            sender="orchestrator",
            recipient=product_analyst.name,
            message_type=CommunicationType.HANDOFF,
            content="Please analyze the project requirements and work with Ask Agent to gather any missing information",
            context=self.project_context,
            requires_response=True
        )
        
        await self.communication_hub.send_message(initial_message)
        
        return {
            'project_started': True,
            'current_phase': self.current_phase.value,
            'assigned_agents': [product_analyst.name, ask_agent.name]
        }
    
    async def process_agent_decision(self, agent_name: str, decision: AgentDecision) -> Dict[str, Any]:
        """Process a decision made by an agent"""
        # Evaluate decision using certainty framework
        evaluation = await self.communication_hub.certainty_framework.evaluate_decision(decision)
        
        # Generate a decision ID from agent and timestamp
        decision_id = f"{agent_name}_{decision.timestamp}"
        
        result = {
            'decision_processed': True,
            'decision_id': decision_id,  # Use generated decision_id
            'agent': agent_name,
            'certainty_level': decision.certainty_level,
            'actions_taken': []
        }
        
        # Handle based on evaluation
        if 'proceed_with_decision' in evaluation['next_actions']:
            result['actions_taken'].append('decision_approved')
            await self._execute_decision(decision)
            
        elif 'consult_peer_agents' in evaluation['next_actions']:
            result['actions_taken'].append('consultation_initiated')
            target_agents = await self._identify_consultation_targets(agent_name, decision)
            consultation_id = await self.communication_hub.request_consultation(
                agent_name, decision, target_agents
            )
            result['consultation_id'] = consultation_id
            
        elif 'escalate_to_supervisor' in evaluation['next_actions']:
            result['actions_taken'].append('escalated_to_supervisor')
            escalation_result = await self.communication_hub.escalate_decision(
                agent_name, decision, EscalationReason.LOW_CONFIDENCE
            )
            result['escalation_result'] = escalation_result
            
        elif 'escalate_to_user' in evaluation['next_actions']:
            result['actions_taken'].append('escalated_to_user')
            self.user_approvals_needed.append({
                'agent': agent_name,
                'decision': decision.to_dict(),
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    async def _identify_consultation_targets(self, agent_name: str, decision: AgentDecision) -> List[str]:
        """Identify which agents should be consulted for a decision"""
        agent = self.agent_registry.get_agent(agent_name)
        if not agent:
            return []
        
        # Define consultation relationships
        consultation_map = {
            AgentRole.ARCHITECT: [AgentRole.SECURITY_SPECIALIST, AgentRole.DEVOPS, AgentRole.CODER],
            AgentRole.CODER: [AgentRole.CODE_REVIEWER, AgentRole.ARCHITECT],
            AgentRole.UX_UI_DESIGNER: [AgentRole.PRODUCT_ANALYST, AgentRole.ARCHITECT],
            AgentRole.SECURITY_SPECIALIST: [AgentRole.ARCHITECT, AgentRole.DEVOPS],
            AgentRole.QA_GUARDIAN: [AgentRole.TESTER, AgentRole.CODE_REVIEWER],
        }
        
        target_roles = consultation_map.get(agent.role, [])
        target_agents = []
        
        for role in target_roles:
            available_agents = self.agent_registry.get_available_agents(role)
            if available_agents:
                target_agents.append(available_agents[0].name)
        
        return target_agents
    
    async def _execute_decision(self, decision: AgentDecision):
        """Execute an approved decision"""
        # Log decision execution
        logger.info(f"Executing decision: {decision.decision_content}")
        
        # Update project context
        if 'decisions' not in self.project_context:
            self.project_context['decisions'] = []
        
        self.project_context['decisions'].append({
            'agent': decision.agent_id,
            'decision': decision.decision_content,
            'timestamp': decision.timestamp
        })
        
        # Notify Librarian to update documentation
        librarian = self.agent_registry.get_agents_by_role(AgentRole.LIBRARIAN)[0]
        notification = AgentMessage(
            sender="orchestrator",
            recipient=librarian.name,
            message_type=CommunicationType.NOTIFICATION,
            content=f"Decision executed: {decision.decision_content}",
            context={'decision': decision.to_dict()}
        )
        
        await self.communication_hub.send_message(notification)
    
    async def get_pending_user_approvals(self) -> List[Dict[str, Any]]:
        """Get all decisions that need user approval"""
        return self.user_approvals_needed.copy()
    
    async def process_user_approval(self, approval_id: int, approved: bool, feedback: str = "") -> Dict[str, Any]:
        """Process user approval of a decision"""
        if approval_id >= len(self.user_approvals_needed):
            return {'error': 'Invalid approval ID'}
        
        approval_item = self.user_approvals_needed[approval_id]
        
        result = {
            'approval_processed': True,
            'approved': approved,
            'feedback': feedback
        }
        
        if approved:
            # Execute the decision
            decision = AgentDecision(**approval_item['decision'])
            await self._execute_decision(decision)
            result['action'] = 'decision_executed'
        else:
            # Send feedback to the agent
            agent_name = approval_item['agent']
            feedback_message = AgentMessage(
                sender="user",
                recipient=agent_name,
                message_type=CommunicationType.FEEDBACK,
                content=f"Decision not approved: {feedback}",
                context={'original_decision': approval_item['decision']}
            )
            await self.communication_hub.send_message(feedback_message)
            result['action'] = 'feedback_sent'
        
        # Remove from pending approvals
        self.user_approvals_needed.pop(approval_id)
        
        return result
    
    async def get_project_status(self) -> Dict[str, Any]:
        """Get current project status"""
        communication_stats = await self.communication_hub.get_system_communication_stats()
        
        return {
            'current_phase': self.current_phase.value,
            'project_context': self.project_context,
            'pending_approvals': len(self.user_approvals_needed),
            'completed_tasks': len(self.completed_tasks),
            'pending_tasks': len(self.task_queue),
            'communication_stats': communication_stats,
            'active_agents': len([a for a in self.agent_registry.agents.values() if a.is_available])
        }
    
    async def consult_agents(self, query: str, agents: List[str], context: Optional[Dict[str, Any]] = None) -> AgentConsultationResult:
        """Consult multiple agents about a query"""
        responses = {}
        
        for agent_id in agents:
            agent_info = self.agent_registry.get_agent(agent_id)
            if agent_info and agent_info.is_available:
                # Simulate agent response - in real implementation, this would call actual agent
                response = AgentResponse(
                    agent_id=agent_id,
                    content=f"Agent {agent_id} response to: {query}",
                    certainty_level=CertaintyLevel.MEDIUM,
                    actions=[],
                    metadata={"specialties": agent_info.specialties}
                )
                responses[agent_id] = response
        
        # Analyze consensus
        consensus_response = None
        consensus_certainty = CertaintyLevel.MEDIUM
        requires_approval = False
        escalation_needed = False
        
        if responses:
            # Simple consensus logic - can be enhanced
            consensus_response = f"Consensus from {len(responses)} agents on: {query}"
            
            # Check if approval is needed based on certainty levels
            low_certainty_count = sum(1 for r in responses.values() if r.certainty_level in [CertaintyLevel.LOW, CertaintyLevel.VERY_LOW])
            if low_certainty_count > len(responses) / 2:
                requires_approval = True
                escalation_needed = True
        
        return AgentConsultationResult(
            query=query,
            responses=responses,
            consensus_response=consensus_response,
            consensus_certainty=consensus_certainty,
            requires_approval=requires_approval,
            escalation_needed=escalation_needed,
            escalation_reason="Low confidence consensus" if escalation_needed else None
        )
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent IDs"""
        return [name for name, agent in self.agent_registry.agents.items() if agent.is_available]
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent"""
        agent = self.agent_registry.get_agent(agent_id)
        if agent:
            return {
                "name": agent.name,
                "role": agent.role.value,
                "specialties": agent.specialties,
                "capabilities": agent.specialties,  # Alias for compatibility
                "is_available": agent.is_available,
                "workload": agent.workload,
                "max_workload": agent.max_workload
            }
        return None
    
    def register_agent(self, agent_id: str, capabilities: List[str], weight: float = 1.0):
        """Register a new agent in the system"""
        # Map capabilities to specialties and determine role
        role = AgentRole.CODER  # Default role
        if "creation" in capabilities:
            role = AgentRole.CODER
        elif "analysis" in capabilities:
            role = AgentRole.ARCHITECT
        elif "testing" in capabilities:
            role = AgentRole.TESTER
        elif "debugging" in capabilities:
            role = AgentRole.DEBUGGER
        
        agent_info = AgentInfo(
            name=agent_id,
            role=role,
            specialties=capabilities,
            is_available=True,
            workload=0,
            max_workload=5
        )
        
        self.agent_registry.register_agent(agent_info)
        
        # Store weight for future use
        if not hasattr(self, 'agent_weights'):
            self.agent_weights = {}
        self.agent_weights[agent_id] = weight
        
        logger.info(f"Registered agent {agent_id} with role {role.value} and capabilities {capabilities}")
        
        # Return agent information
        return {
            "agent_id": agent_id,
            "role": role.value,
            "capabilities": capabilities,
            "weight": weight,
            "registered": True
        }

# Example usage and testing
if __name__ == "__main__":
    async def demo_orchestrator():
        orchestrator = IntelligentOrchestrator()
        
        # Start a project
        project_result = await orchestrator.start_project(
            "Task Management System",
            {
                'users': 'multiple',
                'features': ['task_creation', 'assignment', 'tracking'],
                'tech_preference': 'modern_web_stack'
            }
        )
        
        print(f"Project started: {project_result}")
        
        # Simulate agent decision
        decision = create_decision(
            agent_name="architect",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=75.0,
            content="Use microservices architecture",
            reasoning="Better scalability for multi-user system",
            alternatives=["Monolithic", "Serverless"]
        )
        
        decision_result = await orchestrator.process_agent_decision("architect", decision)
        print(f"Decision processed: {decision_result}")
        
        # Get project status
        status = await orchestrator.get_project_status()
        print(f"Project status: {status}")
    
    asyncio.run(demo_orchestrator())
