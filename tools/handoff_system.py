"""
Handoff Packet System for Agent Communication
Implements the intelligent routing mechanism defined in Future Steps document
"""

import json
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

class TaskStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"

class NextStepSuggestion(Enum):
    CODE_REVIEW = "CODE_REVIEW"
    IMPLEMENTATION_NEEDED = "IMPLEMENTATION_NEEDED"
    TESTING_NEEDED = "TESTING_NEEDED"
    MERGE_APPROVED = "MERGE_APPROVED"
    DEPLOY_TO_STAGING = "DEPLOY_TO_STAGING"
    DEPLOY_TO_PRODUCTION = "DEPLOY_TO_PRODUCTION"
    HUMAN_APPROVAL_NEEDED = "HUMAN_APPROVAL_NEEDED"
    DOCUMENTATION_NEEDED = "DOCUMENTATION_NEEDED"
    SECURITY_SCAN_NEEDED = "SECURITY_SCAN_NEEDED"
    DEBUG_NEEDED = "DEBUG_NEEDED"

@dataclass
class HandoffPacket:
    """Structured communication packet between agents"""
    completed_task_id: str
    agent_name: str
    status: TaskStatus
    artifacts_produced: List[str]
    next_step_suggestion: NextStepSuggestion
    notes: str
    timestamp: str
    dependencies_satisfied: Optional[List[str]] = None
    blocking_issues: Optional[List[str]] = None
    
    def to_json(self) -> str:
        """Convert handoff packet to JSON string"""
        packet_dict = asdict(self)
        packet_dict['status'] = self.status.value
        packet_dict['next_step_suggestion'] = self.next_step_suggestion.value
        return json.dumps(packet_dict, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HandoffPacket':
        """Create handoff packet from JSON string"""
        data = json.loads(json_str)
        data['status'] = TaskStatus(data['status'])
        data['next_step_suggestion'] = NextStepSuggestion(data['next_step_suggestion'])
        return cls(**data)

class ConductorRouter:
    """Intelligent routing system for the Conductor agent"""
    
    def __init__(self, knowledge_registry=None):
        self.routing_rules = self._initialize_routing_rules()
        self.knowledge_registry = knowledge_registry
        
    def set_knowledge_registry(self, registry):
        """Set the knowledge registry for dynamic agent selection"""
        self.knowledge_registry = registry
    
    async def select_best_agent_for_task(self, task_type: str, task_description: str, context: Dict[str, Any]) -> str:
        """
        Dynamically select the best agent for a given task using knowledge registry
        """
        if not self.knowledge_registry:
            # Fallback to static mapping if no registry available
            return self._get_static_agent_for_task(task_type)
        
        # Query registry for agents capable of handling this task type
        suitable_agents = []
        
        for agent_name, agent_profile in self.knowledge_registry.agent_profiles.items():
            # Check if agent has the required capabilities
            agent_capabilities = agent_profile.get("capabilities", [])
            
            # Match task type to agent capabilities
            if self._matches_task_requirements(task_type, agent_capabilities, task_description):
                # Calculate suitability score
                score = self._calculate_agent_suitability(agent_name, task_type, context)
                suitable_agents.append((agent_name, score))
        
        if not suitable_agents:
            # Fallback to static assignment
            return self._get_static_agent_for_task(task_type)
        
        # Sort by score (highest first) and return best agent
        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        return suitable_agents[0][0]
    
    def _matches_task_requirements(self, task_type: str, agent_capabilities: List[str], task_description: str) -> bool:
        """Check if agent capabilities match task requirements"""
        task_capability_map = {
            "code_review": ["code_analysis", "security_review", "quality_assessment"],
            "implementation": ["code_writing", "algorithm_implementation", "debugging"],
            "testing": ["test_design", "test_execution", "quality_validation"],
            "security_scan": ["security_review", "vulnerability_assessment", "code_analysis"],
            "documentation": ["documentation_writing", "knowledge_organization", "user_guides"],
            "deployment": ["deployment_automation", "infrastructure_management", "monitoring"],
            "debugging": ["debugging", "code_analysis", "problem_solving"],
            "architecture": ["system_design", "architecture_patterns", "technology_selection"]
        }
        
        required_capabilities = task_capability_map.get(task_type, [])
        
        # Check if agent has any of the required capabilities
        return any(capability in agent_capabilities for capability in required_capabilities)
    
    def _calculate_agent_suitability(self, agent_name: str, task_type: str, context: Dict[str, Any]) -> float:
        """Calculate suitability score for an agent for a specific task"""
        if not self.knowledge_registry:
            return 0.5
            
        agent_profile = self.knowledge_registry.agent_profiles.get(agent_name, {})
        
        base_score = 0.5
        
        # Boost score based on agent's primary role matching task
        primary_role = agent_profile.get("primary_role", "").lower()
        if task_type in primary_role:
            base_score += 0.3
        
        # Boost score based on workflow participation
        workflow_participation = agent_profile.get("workflow_participation", [])
        current_workflow = context.get("workflow_type", "")
        if current_workflow in workflow_participation:
            base_score += 0.2
        
        # Boost score based on tool availability
        agent_tools = agent_profile.get("tools", [])
        if len(agent_tools) > 0:
            base_score += 0.1
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def _get_static_agent_for_task(self, task_type: str) -> str:
        """Fallback static agent mapping"""
        static_mapping = {
            "code_review": "Code_Reviewer",
            "implementation": "Coder",
            "testing": "QA_Guardian",
            "security_scan": "Security_Specialist",
            "documentation": "Technical_Writer",
            "deployment": "DevOps_Specialist",
            "debugging": "Debugger",
            "architecture": "Architect"
        }
        return static_mapping.get(task_type, "Coder")
    
    def _initialize_routing_rules(self) -> Dict[NextStepSuggestion, Any]:
        """Initialize routing rules mapping suggestions to actions"""
        return {
            NextStepSuggestion.CODE_REVIEW: self._handle_code_review_needed,
            NextStepSuggestion.IMPLEMENTATION_NEEDED: self._handle_implementation_needed,
            NextStepSuggestion.TESTING_NEEDED: self._handle_testing_needed,
            NextStepSuggestion.MERGE_APPROVED: self._handle_merge_approved,
            NextStepSuggestion.DEPLOY_TO_STAGING: self._handle_deploy_staging,
            NextStepSuggestion.DEPLOY_TO_PRODUCTION: self._handle_deploy_production,
            NextStepSuggestion.HUMAN_APPROVAL_NEEDED: self._handle_human_approval_needed,
            NextStepSuggestion.DOCUMENTATION_NEEDED: self._handle_documentation_needed,
            NextStepSuggestion.SECURITY_SCAN_NEEDED: self._handle_security_scan_needed,
            NextStepSuggestion.DEBUG_NEEDED: self._handle_debug_needed,
        }
    
    async def route_next_task(self, handoff_packet: HandoffPacket) -> List[Dict[str, Any]]:
        """
        Route the next task based on handoff packet
        Returns list of tasks to be created
        """
        # Handle failure cases first
        if handoff_packet.status == TaskStatus.FAILURE:
            return self._handle_failure(handoff_packet)
        
        # Route based on next step suggestion
        suggestion = handoff_packet.next_step_suggestion
        if suggestion in self.routing_rules:
            routing_method = self.routing_rules[suggestion]
            # Handle async methods
            if suggestion in [NextStepSuggestion.CODE_REVIEW, NextStepSuggestion.IMPLEMENTATION_NEEDED, NextStepSuggestion.TESTING_NEEDED]:
                return await routing_method(handoff_packet)
            else:
                return routing_method(handoff_packet)
        else:
            return self._handle_unknown_suggestion(handoff_packet)
    
    async def _handle_code_review_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle code review routing with dynamic agent selection"""
        # Select best agents for code review and security scan
        code_reviewer = await self.select_best_agent_for_task("code_review", "Code quality review", {"workflow_type": "code_review"})
        security_specialist = await self.select_best_agent_for_task("security_scan", "Security vulnerability scan", {"workflow_type": "security_scan"})
        
        return [
            {
                "task_type": "code_review",
                "agent": code_reviewer,
                "title": "Review Code Quality",
                "description": f"Review code from task {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "high"
            },
            {
                "task_type": "security_scan",
                "agent": security_specialist,
                "title": "Scan for Vulnerabilities",
                "description": f"Security scan for task {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "high"
            }
        ]
    
    async def _handle_implementation_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle implementation routing with dynamic agent selection"""
        # Select best agent for implementation
        implementation_agent = await self.select_best_agent_for_task("implementation", "Code implementation", {"workflow_type": "implementation"})
        
        return [
            {
                "task_type": "implementation",
                "agent": implementation_agent,
                "title": "Implement Solution",
                "description": f"Implement solution for task {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "high"
            }
        ]
    
    async def _handle_testing_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle testing routing with dynamic agent selection"""
        # Select best agent for testing
        testing_agent = await self.select_best_agent_for_task("testing", "Test implementation", {"workflow_type": "testing"})
        
        return [
            {
                "task_type": "testing",
                "agent": testing_agent,
                "title": "Write Tests",
                "description": f"Write tests for implementation from {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "high"
            }
        ]
    
    def _handle_merge_approved(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle merge approval routing"""
        return [
            {
                "task_type": "git_merge",
                "agent": "Git_Agent",
                "title": "Merge Feature Branch",
                "description": f"Merge feature branch for {packet.completed_task_id}",
                "priority": "high"
            },
            {
                "task_type": "documentation",
                "agent": "Technical_Writer",
                "title": "Write Documentation",
                "description": f"Write documentation for completed feature {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "medium"
            },
            {
                "task_type": "deployment",
                "agent": "DevOps_Specialist",
                "title": "Deploy to Staging",
                "description": f"Deploy feature {packet.completed_task_id} to staging environment",
                "priority": "high"
            }
        ]
    
    def _handle_deploy_staging(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle staging deployment routing"""
        return [
            {
                "task_type": "deployment",
                "agent": "DevOps_Specialist",
                "title": "Deploy to Staging",
                "description": f"Deploy to staging environment for {packet.completed_task_id}",
                "priority": "high"
            }
        ]
    
    def _handle_deploy_production(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle production deployment routing"""
        return [
            {
                "task_type": "deployment",
                "agent": "DevOps_Specialist",
                "title": "Deploy to Production",
                "description": f"Deploy to production environment for {packet.completed_task_id}",
                "priority": "critical"
            }
        ]
    
    def _handle_human_approval_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle human approval routing"""
        return [
            {
                "task_type": "human_approval",
                "agent": "Conductor",
                "title": "Request Human Approval",
                "description": f"Human approval needed for {packet.completed_task_id}",
                "notes": packet.notes,
                "priority": "high"
            }
        ]
    
    def _handle_documentation_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle documentation routing"""
        return [
            {
                "task_type": "documentation",
                "agent": "Technical_Writer",
                "title": "Write Documentation",
                "description": f"Write documentation for {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "medium"
            }
        ]
    
    def _handle_security_scan_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle security scan routing"""
        return [
            {
                "task_type": "security_scan",
                "agent": "Security_Specialist",
                "title": "Security Scan",
                "description": f"Perform security scan for {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "high"
            }
        ]
    
    def _handle_debug_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle debugging routing"""
        return [
            {
                "task_type": "debugging",
                "agent": "Debugger",
                "title": "Diagnose Issues",
                "description": f"Debug issues in {packet.completed_task_id}",
                "error_context": packet.notes,
                "priority": "critical"
            }
        ]
    
    def _handle_failure(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle failure cases"""
        return [
            {
                "task_type": "debugging",
                "agent": "Debugger",
                "title": "Diagnose Failure",
                "description": f"Diagnose failure in {packet.completed_task_id}",
                "error_context": packet.notes,
                "blocking_issues": packet.blocking_issues,
                "priority": "critical"
            }
        ]
    
    def _handle_unknown_suggestion(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle unknown suggestions"""
        return [
            {
                "task_type": "human_clarification",
                "agent": "Conductor",
                "title": "Request Clarification",
                "description": f"Unknown next step for {packet.completed_task_id}",
                "context": packet.notes,
                "suggestion": packet.next_step_suggestion.value,
                "priority": "high"
            }
        ]
