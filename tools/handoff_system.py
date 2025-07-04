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
    dependencies_satisfied: List[str] = None
    blocking_issues: List[str] = None
    
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
    
    def __init__(self):
        self.routing_rules = self._initialize_routing_rules()
    
    def _initialize_routing_rules(self) -> Dict[NextStepSuggestion, callable]:
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
    
    def route_next_task(self, handoff_packet: HandoffPacket) -> List[Dict[str, Any]]:
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
            return self.routing_rules[suggestion](handoff_packet)
        else:
            return self._handle_unknown_suggestion(handoff_packet)
    
    def _handle_code_review_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle code review routing"""
        return [
            {
                "task_type": "code_review",
                "agent": "Code_Reviewer",
                "title": "Review Code Quality",
                "description": f"Review code from task {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "high"
            },
            {
                "task_type": "security_scan",
                "agent": "Security_Specialist",
                "title": "Scan for Vulnerabilities",
                "description": f"Security scan for task {packet.completed_task_id}",
                "artifacts": packet.artifacts_produced,
                "priority": "high"
            }
        ]
    
    def _handle_implementation_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle implementation routing"""
        return [
            {
                "task_type": "implementation",
                "agent": "Coder",
                "title": "Implement Code to Pass Test",
                "description": f"Implement code for failing tests from {packet.completed_task_id}",
                "context": packet.notes,
                "priority": "high"
            }
        ]
    
    def _handle_testing_needed(self, packet: HandoffPacket) -> List[Dict[str, Any]]:
        """Handle testing routing"""
        return [
            {
                "task_type": "testing",
                "agent": "Tester",
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
