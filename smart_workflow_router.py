#!/usr/bin/env python3
"""
Smart Workflow Router
====================

This module provides intelligent agent routing and decision-making capabilities
for the autonomous workflow system. It reduces unnecessary agent calls and
optimizes the workflow flow based on context and project requirements.

Features:
- Context-aware agent selection
- Skip agents when not needed
- Enforce project conventions
- Optimize token usage
- Smart decision confidence handling
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from workflow_config import (
    CONFIDENCE_THRESHOLDS, QUALITY_THRESHOLDS, ROUTING_PREFERENCES,
    CONTEXT_OPTIMIZATION, EXECUTION_PATTERNS, TOKEN_OPTIMIZATION
)


class AgentPriority(Enum):
    """Priority levels for agent execution"""
    CRITICAL = 1      # Must be executed (security, quality gates)
    HIGH = 2          # Should be executed (code review, testing)
    MEDIUM = 3        # Can be executed (optimization, documentation)
    LOW = 4           # Optional (nice-to-have features)
    SKIP = 5          # Skip this iteration


@dataclass
class ContextAnalysis:
    """Analysis of current workflow context"""
    project_type: str
    complexity_level: str
    security_requirements: bool
    performance_critical: bool
    user_facing: bool
    testing_required: bool
    documentation_needed: bool
    deployment_ready: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'project_type': self.project_type,
            'complexity_level': self.complexity_level,
            'security_requirements': self.security_requirements,
            'performance_critical': self.performance_critical,
            'user_facing': self.user_facing,
            'testing_required': self.testing_required,
            'documentation_needed': self.documentation_needed,
            'deployment_ready': self.deployment_ready
        }
    
    
@dataclass
class AgentRecommendation:
    """Recommendation for agent execution"""
    agent_name: str
    priority: AgentPriority
    reason: str
    confidence: float
    skip_reason: Optional[str] = None
    prerequisites: List[str] = None


class SmartWorkflowRouter:
    """
    Smart router that decides which agents to call based on context and efficiency
    """
    
    def __init__(self):
        # Agent execution rules and patterns
        self.agent_rules = {
            'Product_Analyst': {
                'required_for': ['new_project', 'unclear_requirements'],
                'skip_if': ['clear_requirements', 'existing_specifications'],
                'triggers': ['requirements', 'planning', 'analysis', 'specifications']
            },
            'UX_UI_Designer': {
                'required_for': ['user_interface', 'user_experience', 'frontend'],
                'skip_if': ['backend_only', 'api_only', 'cli_tool'],
                'triggers': ['ui', 'interface', 'user', 'design', 'frontend']
            },
            'Architect': {
                'required_for': ['complex_system', 'scalability', 'integration'],
                'skip_if': ['simple_script', 'single_function'],
                'triggers': ['architecture', 'system', 'scalability', 'integration']
            },
            'Tester': {
                'required_for': ['quality_assurance', 'testing_needed'],
                'skip_if': ['already_tested', 'simple_function'],
                'triggers': ['test', 'testing', 'validation', 'qa']
            },
            'Coder': {
                'required_for': ['implementation_needed', 'coding_required'],
                'skip_if': ['code_complete', 'no_implementation'],
                'triggers': ['code', 'implement', 'develop', 'build']
            },
            'Code_Reviewer': {
                'required_for': ['code_quality', 'best_practices'],
                'skip_if': ['simple_script', 'already_reviewed'],
                'triggers': ['review', 'quality', 'refactor', 'optimize']
            },
            'Security_Specialist': {
                'required_for': ['security_critical', 'authentication', 'data_protection'],
                'skip_if': ['simple_calculation', 'offline_tool'],
                'triggers': ['security', 'auth', 'encrypt', 'vulnerability']
            },
            'QA_Guardian': {
                'required_for': ['final_validation', 'quality_gate'],
                'skip_if': ['early_stage', 'incomplete_work'],
                'triggers': ['quality', 'final', 'validate', 'approve']
            },
            'DevOps_Specialist': {
                'required_for': ['deployment', 'infrastructure', 'production'],
                'skip_if': ['development_only', 'local_script'],
                'triggers': ['deploy', 'infrastructure', 'ci', 'production']
            },
            'Technical_Writer': {
                'required_for': ['documentation', 'user_guides', 'api_docs'],
                'skip_if': ['simple_script', 'internal_tool'],
                'triggers': ['documentation', 'docs', 'guide', 'manual']
            },
            'Debugger': {
                'required_for': ['issues_found', 'errors_detected'],
                'skip_if': ['no_issues', 'working_correctly'],
                'triggers': ['debug', 'error', 'issue', 'problem', 'bug']
            },
            'Git_Agent': {
                'required_for': ['version_control', 'merge_conflicts'],
                'skip_if': ['single_file', 'no_git'],
                'triggers': ['git', 'version', 'merge', 'commit']
            },
            'Ask_Agent': {
                'required_for': ['unclear_requirements', 'need_guidance'],
                'skip_if': ['clear_path', 'standard_implementation'],
                'triggers': ['question', 'clarify', 'guidance', 'help']
            }
        }
        
        # Project type patterns
        self.project_patterns = {
            'simple_script': ['calculator', 'converter', 'simple', 'basic'],
            'web_application': ['web', 'app', 'frontend', 'backend', 'api'],
            'security_critical': ['auth', 'login', 'password', 'secure', 'encryption'],
            'enterprise_system': ['enterprise', 'scalable', 'microservices', 'distributed'],
            'data_processing': ['data', 'analysis', 'processing', 'pipeline'],
            'cli_tool': ['cli', 'command', 'terminal', 'console']
        }
        
        # Quality thresholds - use configuration
        self.quality_thresholds = CONFIDENCE_THRESHOLDS
        
        # Routing preferences
        self.routing_preferences = ROUTING_PREFERENCES
        
        # Execution patterns
        self.execution_patterns = EXECUTION_PATTERNS
    
    def analyze_context(self, user_request: str, workflow_context: Dict) -> ContextAnalysis:
        """Analyze the current context to understand project requirements"""
        
        request_lower = user_request.lower()
        
        # Determine project type
        project_type = 'unknown'
        for ptype, patterns in self.project_patterns.items():
            if any(pattern in request_lower for pattern in patterns):
                project_type = ptype
                break
        
        # Analyze complexity
        complexity_indicators = {
            'simple': ['simple', 'basic', 'calculator', 'converter'],
            'medium': ['web', 'api', 'application', 'system'],
            'complex': ['enterprise', 'scalable', 'distributed', 'microservices']
        }
        
        complexity_level = 'medium'  # default
        for level, indicators in complexity_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                complexity_level = level
                break
        
        # Check specific requirements
        security_requirements = any(word in request_lower for word in 
                                  ['auth', 'login', 'secure', 'password', 'encryption'])
        
        performance_critical = any(word in request_lower for word in 
                                 ['performance', 'fast', 'optimize', 'scale'])
        
        user_facing = any(word in request_lower for word in 
                         ['ui', 'interface', 'user', 'frontend', 'web'])
        
        testing_required = complexity_level != 'simple' or 'test' in request_lower
        
        documentation_needed = complexity_level == 'complex' or 'document' in request_lower
        
        deployment_ready = any(word in request_lower for word in 
                             ['deploy', 'production', 'release'])
        
        return ContextAnalysis(
            project_type=project_type,
            complexity_level=complexity_level,
            security_requirements=security_requirements,
            performance_critical=performance_critical,
            user_facing=user_facing,
            testing_required=testing_required,
            documentation_needed=documentation_needed,
            deployment_ready=deployment_ready
        )
    
    def get_agent_recommendations(self, context_analysis: ContextAnalysis, 
                                current_agent: str, workflow_context: Dict) -> List[AgentRecommendation]:
        """Get prioritized recommendations for next agents"""
        
        recommendations = []
        
        # Get agents that have already been executed
        executed_agents = set()
        for decision in workflow_context.get('decisions', []):
            if 'agent' in decision:
                executed_agents.add(decision['agent'])
        
        # Analyze each agent
        for agent_name, rules in self.agent_rules.items():
            if agent_name == current_agent:
                continue  # Skip current agent
            
            recommendation = self._analyze_agent_need(
                agent_name, rules, context_analysis, executed_agents, workflow_context
            )
            
            if recommendation:
                recommendations.append(recommendation)
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda x: (x.priority.value, -x.confidence))
        
        return recommendations
    
    def _analyze_agent_need(self, agent_name: str, rules: Dict, 
                           context_analysis: ContextAnalysis, 
                           executed_agents: Set[str], 
                           workflow_context: Dict) -> Optional[AgentRecommendation]:
        """Analyze if an agent should be executed"""
        
        # Check if agent has been executed too many times
        executed_agents_list = workflow_context.get('workflow_history', [])
        agent_execution_count = sum(1 for entry in executed_agents_list if entry.get('agent') == agent_name)
        
        execution_pattern = self.execution_patterns.get(agent_name, {})
        max_executions = execution_pattern.get('max_executions', 3)
        
        if agent_execution_count >= max_executions:
            return AgentRecommendation(
                agent_name=agent_name,
                priority=AgentPriority.SKIP,
                reason=f"Maximum executions reached ({agent_execution_count}/{max_executions})",
                confidence=0.9,
                skip_reason="Maximum executions reached"
            )
        
        # Check iteration-based skip
        current_iteration = workflow_context.get('iteration', 0)
        skip_after_iteration = execution_pattern.get('skip_after_iteration')
        
        if skip_after_iteration and current_iteration > skip_after_iteration:
            return AgentRecommendation(
                agent_name=agent_name,
                priority=AgentPriority.SKIP,
                reason=f"Iteration limit reached (iteration {current_iteration} > {skip_after_iteration})",
                confidence=0.8,
                skip_reason="Iteration limit reached"
            )
        
        # Check project-specific routing preferences
        project_preferences = self.routing_preferences.get(context_analysis.project_type, {})
        skip_agents = project_preferences.get('skip_agents', [])
        
        if agent_name in skip_agents:
            return AgentRecommendation(
                agent_name=agent_name,
                priority=AgentPriority.SKIP,
                reason=f"Agent not needed for {context_analysis.project_type} projects",
                confidence=0.8,
                skip_reason="Project-specific skip"
            )
        
        # Check skip conditions
        skip_conditions = rules.get('skip_if', [])
        for condition in skip_conditions:
            if self._check_condition(condition, context_analysis, workflow_context):
                return AgentRecommendation(
                    agent_name=agent_name,
                    priority=AgentPriority.SKIP,
                    reason=f"Skip condition met: {condition}",
                    confidence=0.8,
                    skip_reason=condition
                )
        
        # Check required conditions
        required_conditions = rules.get('required_for', [])
        priority = AgentPriority.MEDIUM
        confidence = 0.5
        reason = f"Standard workflow inclusion for {agent_name}"
        
        for condition in required_conditions:
            if self._check_condition(condition, context_analysis, workflow_context):
                priority = AgentPriority.HIGH
                confidence = 0.8
                reason = f"Required for: {condition}"
                break
        
        # Check triggers in workflow context
        triggers = rules.get('triggers', [])
        context_text = json.dumps(workflow_context).lower()
        
        for trigger in triggers:
            if trigger in context_text:
                if priority == AgentPriority.MEDIUM:
                    priority = AgentPriority.HIGH
                    confidence = min(confidence + 0.2, 0.9)
                    reason = f"Triggered by context: {trigger}"
                break
        
        # Special logic for specific agents
        if agent_name == 'QA_Guardian':
            # QA Guardian should only run when work is ready for final validation
            recent_decisions = workflow_context.get('decisions', [])[-3:]
            if not any('complete' in str(d).lower() or 'quality' in str(d).lower() 
                      for d in recent_decisions):
                priority = AgentPriority.SKIP
                skip_reason = "Work not ready for final QA"
                confidence = 0.7
        
        elif agent_name == 'Security_Specialist':
            if not context_analysis.security_requirements:
                priority = AgentPriority.LOW
                confidence = 0.3
                reason = "No security requirements detected"
        
        elif agent_name == 'DevOps_Specialist':
            if not context_analysis.deployment_ready:
                priority = AgentPriority.SKIP
                skip_reason = "Not ready for deployment"
                confidence = 0.8
        
        return AgentRecommendation(
            agent_name=agent_name,
            priority=priority,
            reason=reason,
            confidence=confidence,
            skip_reason=skip_reason if priority == AgentPriority.SKIP else None
        )
    
    def _check_condition(self, condition: str, context_analysis: ContextAnalysis, 
                        workflow_context: Dict) -> bool:
        """Check if a condition is met"""
        
        # Map conditions to context analysis
        condition_mapping = {
            'new_project': lambda: workflow_context.get('iteration', 0) <= 1,
            'unclear_requirements': lambda: context_analysis.complexity_level == 'simple',
            'clear_requirements': lambda: context_analysis.project_type != 'unknown',
            'existing_specifications': lambda: len(workflow_context.get('artifacts', [])) > 0,
            'user_interface': lambda: context_analysis.user_facing,
            'user_experience': lambda: context_analysis.user_facing,
            'frontend': lambda: context_analysis.user_facing,
            'backend_only': lambda: not context_analysis.user_facing,
            'api_only': lambda: context_analysis.project_type == 'web_application' and not context_analysis.user_facing,
            'cli_tool': lambda: context_analysis.project_type == 'cli_tool',
            'complex_system': lambda: context_analysis.complexity_level == 'complex',
            'scalability': lambda: context_analysis.performance_critical,
            'integration': lambda: context_analysis.complexity_level in ['medium', 'complex'],
            'simple_script': lambda: context_analysis.complexity_level == 'simple',
            'single_function': lambda: context_analysis.complexity_level == 'simple',
            'quality_assurance': lambda: context_analysis.testing_required,
            'testing_needed': lambda: context_analysis.testing_required,
            'already_tested': lambda: 'test' in str(workflow_context.get('artifacts', [])).lower(),
            'implementation_needed': lambda: 'code' not in str(workflow_context.get('artifacts', [])).lower(),
            'coding_required': lambda: True,  # Most projects need coding
            'code_complete': lambda: 'code' in str(workflow_context.get('artifacts', [])).lower(),
            'no_implementation': lambda: False,  # Rarely true
            'code_quality': lambda: 'code' in str(workflow_context.get('artifacts', [])).lower(),
            'best_practices': lambda: context_analysis.complexity_level != 'simple',
            'already_reviewed': lambda: 'review' in str(workflow_context.get('decisions', [])).lower(),
            'security_critical': lambda: context_analysis.security_requirements,
            'authentication': lambda: context_analysis.security_requirements,
            'data_protection': lambda: context_analysis.security_requirements,
            'simple_calculation': lambda: context_analysis.project_type == 'simple_script',
            'offline_tool': lambda: context_analysis.project_type in ['simple_script', 'cli_tool'],
            'final_validation': lambda: workflow_context.get('iteration', 0) > 3,
            'quality_gate': lambda: workflow_context.get('iteration', 0) > 3,
            'early_stage': lambda: workflow_context.get('iteration', 0) <= 2,
            'incomplete_work': lambda: workflow_context.get('iteration', 0) <= 2,
            'deployment': lambda: context_analysis.deployment_ready,
            'infrastructure': lambda: context_analysis.deployment_ready,
            'production': lambda: context_analysis.deployment_ready,
            'development_only': lambda: not context_analysis.deployment_ready,
            'local_script': lambda: context_analysis.project_type == 'simple_script',
            'documentation': lambda: context_analysis.documentation_needed,
            'user_guides': lambda: context_analysis.user_facing,
            'api_docs': lambda: context_analysis.project_type == 'web_application',
            'internal_tool': lambda: not context_analysis.user_facing,
            'issues_found': lambda: 'error' in str(workflow_context.get('context', {})).lower(),
            'errors_detected': lambda: 'error' in str(workflow_context.get('context', {})).lower(),
            'no_issues': lambda: 'error' not in str(workflow_context.get('context', {})).lower(),
            'working_correctly': lambda: 'success' in str(workflow_context.get('context', {})).lower(),
            'version_control': lambda: context_analysis.complexity_level != 'simple',
            'merge_conflicts': lambda: 'conflict' in str(workflow_context.get('context', {})).lower(),
            'single_file': lambda: context_analysis.complexity_level == 'simple',
            'no_git': lambda: context_analysis.project_type == 'simple_script',
            'unclear_requirements': lambda: context_analysis.project_type == 'unknown',
            'need_guidance': lambda: context_analysis.complexity_level == 'complex',
            'clear_path': lambda: context_analysis.project_type != 'unknown',
            'standard_implementation': lambda: context_analysis.complexity_level == 'simple'
        }
        
        condition_func = condition_mapping.get(condition)
        if condition_func:
            try:
                return condition_func()
            except:
                return False
        
        return False
    
    def should_skip_agent(self, agent_name: str, context_analysis: ContextAnalysis, 
                         workflow_context: Dict) -> Tuple[bool, str]:
        """Determine if an agent should be skipped"""
        
        recommendations = self.get_agent_recommendations(
            context_analysis, agent_name, workflow_context
        )
        
        for rec in recommendations:
            if rec.agent_name == agent_name:
                if rec.priority == AgentPriority.SKIP:
                    return True, rec.skip_reason or rec.reason
                break
        
        return False, ""
    
    def get_next_agent_recommendation(self, current_agent: str, 
                                    context_analysis: ContextAnalysis,
                                    workflow_context: Dict) -> Optional[str]:
        """Get the best next agent recommendation"""
        
        recommendations = self.get_agent_recommendations(
            context_analysis, current_agent, workflow_context
        )
        
        # Filter out skipped agents
        valid_recommendations = [r for r in recommendations if r.priority != AgentPriority.SKIP]
        
        if not valid_recommendations:
            return None
        
        # Return the highest priority agent
        best_recommendation = valid_recommendations[0]
        
        # Apply confidence threshold
        if best_recommendation.confidence < self.quality_thresholds['MINIMUM']:
            return None
        
        return best_recommendation.agent_name
    
    def optimize_workflow_context(self, context: Dict) -> Dict:
        """Optimize context to reduce token usage while preserving critical information"""
        
        if not context:
            return context
        
        optimized = {}
        
        # Keep critical information
        critical_keys = ['iteration', 'current_agent', 'workflow_id', 'user_request', 'context_analysis']
        for key in critical_keys:
            if key in context:
                optimized[key] = context[key]
        
        # Compress decisions - use configuration
        if 'decisions' in context:
            decisions = context['decisions']
            max_decisions = CONTEXT_OPTIMIZATION['max_decisions_history']
            if len(decisions) > max_decisions:
                optimized['decisions'] = decisions[-max_decisions:]
            else:
                optimized['decisions'] = decisions
        
        # Compress artifacts - use configuration
        if 'artifacts' in context:
            artifacts = context['artifacts']
            max_artifacts = CONTEXT_OPTIMIZATION['max_artifacts_history']
            if len(artifacts) > max_artifacts:
                optimized['artifacts'] = artifacts[-max_artifacts:]
            else:
                optimized['artifacts'] = artifacts
        
        # Compress context - remove verbose information
        if 'context' in context:
            ctx = context['context']
            if isinstance(ctx, dict):
                # Keep only essential context
                essential_ctx = {}
                for key, value in ctx.items():
                    if key in ['quality_score', 'security_score', 'completion_status', 'user_request', 'context_analysis']:
                        essential_ctx[key] = value
                    elif isinstance(value, str) and len(value) > CONTEXT_OPTIMIZATION['max_response_length']:
                        # Truncate long strings
                        essential_ctx[key] = value[:CONTEXT_OPTIMIZATION['max_response_length']] + "..."
                    elif not isinstance(value, (dict, list)):
                        essential_ctx[key] = value
                optimized['context'] = essential_ctx
        
        return optimized
