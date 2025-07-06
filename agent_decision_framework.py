"""
Agent Decision Framework Configuration
=====================================

This file contains the centralized decision-making logic for all agents
in the autonomous workflow system.

Author: AI Assistant
Date: 2025-07-06
"""

import json
import yaml
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict


class DecisionType(Enum):
    """Types of decisions an agent can make"""
    COMPLETE = "COMPLETE"
    NEXT_AGENT = "NEXT_AGENT"
    RETRY = "RETRY"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    PARALLEL = "PARALLEL"
    BRANCH = "BRANCH"
    DELEGATE = "DELEGATE"
    ESCALATE = "ESCALATE"
    PAUSE = "PAUSE"
    ROLLBACK = "ROLLBACK"


@dataclass
class DecisionCriteria:
    """Criteria for making decisions"""
    min_confidence: float = 0.7
    max_iterations: int = 3
    require_human_approval: bool = False
    allowed_next_agents: List[str] = None
    blocked_agents: List[str] = None
    quality_threshold: float = 0.8
    security_check_required: bool = False


@dataclass
class DecisionRule:
    """A single decision rule"""
    condition: str  # Python expression to evaluate
    action: DecisionType
    target_agent: Optional[str] = None
    target_agents: Optional[List[str]] = None
    priority: int = 1
    reason: str = ""
    confidence_modifier: float = 0.0


class AgentDecisionFramework:
    """Central decision-making framework for all agents"""
    
    def __init__(self, config_file: str = "agent_decisions.yaml"):
        self.config_file = config_file
        self.agent_rules = {}
        self.global_rules = {}
        self.quality_metrics = {}
        self.escalation_rules = {}
        self.load_configuration()
    
    def load_configuration(self):
        """Load decision configuration from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            self.agent_rules = config.get('agent_rules', {})
            self.global_rules = config.get('global_rules', {})
            self.quality_metrics = config.get('quality_metrics', {})
            self.escalation_rules = config.get('escalation_rules', {})
            
        except FileNotFoundError:
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Create default configuration file"""
        default_config = {
            'agent_rules': {
                'Product_Analyst': {
                    'criteria': {
                        'min_confidence': 0.7,
                        'max_iterations': 2,
                        'require_human_approval': False,
                        'allowed_next_agents': ['Developer', 'Architect', 'Designer'],
                        'quality_threshold': 0.8
                    },
                    'rules': [
                        {
                            'condition': 'response_length < 500',
                            'action': 'RETRY',
                            'reason': 'Response too short for proper analysis',
                            'priority': 1
                        },
                        {
                            'condition': 'security_keywords_found and complexity_high',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'Security_Engineer',
                            'reason': 'Security analysis required',
                            'priority': 2
                        },
                        {
                            'condition': 'requirements_clear and scope_defined',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'Developer',
                            'reason': 'Ready for development',
                            'priority': 3
                        }
                    ]
                },
                'Developer': {
                    'criteria': {
                        'min_confidence': 0.8,
                        'max_iterations': 3,
                        'allowed_next_agents': ['QA_Engineer', 'Security_Engineer', 'DevOps_Engineer'],
                        'quality_threshold': 0.9
                    },
                    'rules': [
                        {
                            'condition': 'code_generated and tests_included',
                            'action': 'COMPLETE',
                            'reason': 'Code complete with tests',
                            'priority': 1
                        },
                        {
                            'condition': 'code_generated and not tests_included',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'QA_Engineer',
                            'reason': 'Code needs testing',
                            'priority': 2
                        },
                        {
                            'condition': 'security_concerns_identified',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'Security_Engineer',
                            'reason': 'Security review required',
                            'priority': 3
                        },
                        {
                            'condition': 'deployment_ready',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'DevOps_Engineer',
                            'reason': 'Ready for deployment',
                            'priority': 4
                        }
                    ]
                },
                'QA_Engineer': {
                    'criteria': {
                        'min_confidence': 0.85,
                        'max_iterations': 2,
                        'allowed_next_agents': ['Developer', 'Performance_Engineer', 'Security_Engineer'],
                        'quality_threshold': 0.9
                    },
                    'rules': [
                        {
                            'condition': 'all_tests_pass and coverage_high',
                            'action': 'COMPLETE',
                            'reason': 'All tests pass with high coverage',
                            'priority': 1
                        },
                        {
                            'condition': 'tests_fail or bugs_found',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'Developer',
                            'reason': 'Bugs found, need fixes',
                            'priority': 2
                        },
                        {
                            'condition': 'performance_issues_detected',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'Performance_Engineer',
                            'reason': 'Performance optimization needed',
                            'priority': 3
                        },
                        {
                            'condition': 'security_vulnerabilities_found',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'Security_Engineer',
                            'reason': 'Security vulnerabilities detected',
                            'priority': 4
                        }
                    ]
                },
                'Security_Engineer': {
                    'criteria': {
                        'min_confidence': 0.9,
                        'max_iterations': 2,
                        'allowed_next_agents': ['Developer', 'QA_Engineer'],
                        'quality_threshold': 0.95,
                        'security_check_required': True
                    },
                    'rules': [
                        {
                            'condition': 'security_approved and no_vulnerabilities',
                            'action': 'COMPLETE',
                            'reason': 'Security approved',
                            'priority': 1
                        },
                        {
                            'condition': 'critical_vulnerabilities_found',
                            'action': 'HUMAN_REVIEW',
                            'reason': 'Critical security issues require human review',
                            'priority': 2
                        },
                        {
                            'condition': 'minor_security_issues',
                            'action': 'NEXT_AGENT',
                            'target_agent': 'Developer',
                            'reason': 'Minor security fixes needed',
                            'priority': 3
                        }
                    ]
                },
                'DevOps_Engineer': {
                    'criteria': {
                        'min_confidence': 0.8,
                        'max_iterations': 3,
                        'allowed_next_agents': ['Monitoring_Engineer', 'Performance_Engineer'],
                        'quality_threshold': 0.9
                    },
                    'rules': [
                        {
                            'condition': 'deployment_successful and monitoring_setup',
                            'action': 'COMPLETE',
                            'reason': 'Deployment successful with monitoring',
                            'priority': 1
                        },
                        {
                            'condition': 'deployment_failed',
                            'action': 'RETRY',
                            'reason': 'Deployment failed, retry needed',
                            'priority': 2
                        },
                        {
                            'condition': 'infrastructure_issues',
                            'action': 'ESCALATE',
                            'reason': 'Infrastructure issues need escalation',
                            'priority': 3
                        }
                    ]
                }
            },
            'global_rules': {
                'max_workflow_iterations': 15,
                'emergency_stop_conditions': [
                    'critical_security_breach',
                    'data_loss_detected',
                    'system_compromise'
                ],
                'human_approval_required': [
                    'production_deployment',
                    'security_critical_changes',
                    'data_migration'
                ]
            },
            'quality_metrics': {
                'code_quality_factors': [
                    'readability',
                    'maintainability',
                    'test_coverage',
                    'documentation',
                    'error_handling'
                ],
                'security_factors': [
                    'authentication',
                    'authorization',
                    'input_validation',
                    'encryption',
                    'audit_logging'
                ],
                'performance_factors': [
                    'response_time',
                    'throughput',
                    'resource_usage',
                    'scalability',
                    'reliability'
                ]
            },
            'escalation_rules': {
                'levels': [
                    {
                        'level': 1,
                        'conditions': ['low_confidence', 'repeated_failures'],
                        'actions': ['retry', 'different_agent']
                    },
                    {
                        'level': 2,
                        'conditions': ['security_issues', 'quality_concerns'],
                        'actions': ['specialist_review', 'additional_testing']
                    },
                    {
                        'level': 3,
                        'conditions': ['critical_failures', 'system_risks'],
                        'actions': ['human_review', 'workflow_pause']
                    }
                ]
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        self.agent_rules = default_config['agent_rules']
        self.global_rules = default_config['global_rules']
        self.quality_metrics = default_config['quality_metrics']
        self.escalation_rules = default_config['escalation_rules']
    
    def evaluate_decision(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate decision based on agent rules and context"""
        
        if agent_name not in self.agent_rules:
            return self._default_decision(agent_name, context)
        
        agent_config = self.agent_rules[agent_name]
        criteria = agent_config.get('criteria', {})
        rules = agent_config.get('rules', [])
        
        # Sort rules by priority
        sorted_rules = sorted(rules, key=lambda x: x.get('priority', 99))
        
        # Evaluate each rule
        for rule in sorted_rules:
            if self._evaluate_condition(rule['condition'], context):
                return {
                    'action': rule['action'],
                    'target_agent': rule.get('target_agent'),
                    'target_agents': rule.get('target_agents'),
                    'reason': rule.get('reason', 'Rule matched'),
                    'confidence': self._calculate_confidence(context, criteria),
                    'rule_matched': rule['condition']
                }
        
        # No rule matched, return default
        return self._default_decision(agent_name, context)
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string against context"""
        try:
            # Create safe evaluation environment
            safe_dict = {
                'response_length': len(context.get('response', '')),
                'iteration': context.get('iteration', 0),
                'confidence': context.get('confidence', 0.5),
                'security_keywords_found': self._check_security_keywords(context.get('response', '')),
                'complexity_high': self._assess_complexity(context.get('response', '')),
                'requirements_clear': self._check_requirements_clarity(context.get('response', '')),
                'scope_defined': self._check_scope_definition(context.get('response', '')),
                'code_generated': self._check_code_generation(context.get('response', '')),
                'tests_included': self._check_tests_included(context.get('response', '')),
                'security_concerns_identified': self._check_security_concerns(context.get('response', '')),
                'deployment_ready': self._check_deployment_readiness(context.get('response', '')),
                'all_tests_pass': self._check_test_results(context.get('response', '')),
                'coverage_high': self._check_test_coverage(context.get('response', '')),
                'tests_fail': self._check_test_failures(context.get('response', '')),
                'bugs_found': self._check_bugs_found(context.get('response', '')),
                'performance_issues_detected': self._check_performance_issues(context.get('response', '')),
                'security_vulnerabilities_found': self._check_security_vulnerabilities(context.get('response', '')),
                'security_approved': self._check_security_approval(context.get('response', '')),
                'no_vulnerabilities': self._check_no_vulnerabilities(context.get('response', '')),
                'critical_vulnerabilities_found': self._check_critical_vulnerabilities(context.get('response', '')),
                'minor_security_issues': self._check_minor_security_issues(context.get('response', '')),
                'deployment_successful': self._check_deployment_success(context.get('response', '')),
                'monitoring_setup': self._check_monitoring_setup(context.get('response', '')),
                'deployment_failed': self._check_deployment_failure(context.get('response', '')),
                'infrastructure_issues': self._check_infrastructure_issues(context.get('response', ''))
            }
            
            return eval(condition, {"__builtins__": {}}, safe_dict)
            
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _check_security_keywords(self, response: str) -> bool:
        """Check if security keywords are present"""
        security_keywords = ['security', 'auth', 'login', 'password', 'encrypt', 'secure', 'vulnerability']
        return any(keyword in response.lower() for keyword in security_keywords)
    
    def _assess_complexity(self, response: str) -> bool:
        """Assess if the response indicates high complexity"""
        complexity_indicators = ['complex', 'complicated', 'advanced', 'multiple', 'integration']
        return any(indicator in response.lower() for indicator in complexity_indicators)
    
    def _check_requirements_clarity(self, response: str) -> bool:
        """Check if requirements are clearly defined"""
        clarity_indicators = ['requirement', 'specification', 'defined', 'clear', 'documented']
        return any(indicator in response.lower() for indicator in clarity_indicators)
    
    def _check_scope_definition(self, response: str) -> bool:
        """Check if scope is well defined"""
        scope_indicators = ['scope', 'boundary', 'feature', 'functionality', 'objective']
        return any(indicator in response.lower() for indicator in scope_indicators)
    
    def _check_code_generation(self, response: str) -> bool:
        """Check if code was generated"""
        return 'def ' in response or 'class ' in response or 'function' in response.lower()
    
    def _check_tests_included(self, response: str) -> bool:
        """Check if tests are included"""
        test_indicators = ['test', 'assert', 'unittest', 'pytest', 'testing']
        return any(indicator in response.lower() for indicator in test_indicators)
    
    def _check_security_concerns(self, response: str) -> bool:
        """Check if security concerns are identified"""
        security_concerns = ['security', 'vulnerability', 'risk', 'threat', 'unsafe']
        return any(concern in response.lower() for concern in security_concerns)
    
    def _check_deployment_readiness(self, response: str) -> bool:
        """Check if ready for deployment"""
        deployment_indicators = ['deploy', 'production', 'release', 'ready', 'complete']
        return any(indicator in response.lower() for indicator in deployment_indicators)
    
    def _check_test_results(self, response: str) -> bool:
        """Check if all tests pass"""
        return 'pass' in response.lower() and 'fail' not in response.lower()
    
    def _check_test_coverage(self, response: str) -> bool:
        """Check if test coverage is high"""
        coverage_indicators = ['coverage', '100%', '95%', 'high coverage']
        return any(indicator in response.lower() for indicator in coverage_indicators)
    
    def _check_test_failures(self, response: str) -> bool:
        """Check if tests fail"""
        return 'fail' in response.lower() or 'error' in response.lower()
    
    def _check_bugs_found(self, response: str) -> bool:
        """Check if bugs are found"""
        bug_indicators = ['bug', 'issue', 'problem', 'error', 'defect']
        return any(indicator in response.lower() for indicator in bug_indicators)
    
    def _check_performance_issues(self, response: str) -> bool:
        """Check if performance issues are detected"""
        performance_indicators = ['slow', 'performance', 'bottleneck', 'optimization']
        return any(indicator in response.lower() for indicator in performance_indicators)
    
    def _check_security_vulnerabilities(self, response: str) -> bool:
        """Check if security vulnerabilities are found"""
        vulnerability_indicators = ['vulnerability', 'exploit', 'breach', 'unsafe', 'insecure']
        return any(indicator in response.lower() for indicator in vulnerability_indicators)
    
    def _check_security_approval(self, response: str) -> bool:
        """Check if security is approved"""
        approval_indicators = ['approved', 'secure', 'safe', 'no issues']
        return any(indicator in response.lower() for indicator in approval_indicators)
    
    def _check_no_vulnerabilities(self, response: str) -> bool:
        """Check if no vulnerabilities found"""
        return 'no vulnerabilities' in response.lower() or 'secure' in response.lower()
    
    def _check_critical_vulnerabilities(self, response: str) -> bool:
        """Check if critical vulnerabilities found"""
        critical_indicators = ['critical', 'severe', 'high risk', 'dangerous']
        return any(indicator in response.lower() for indicator in critical_indicators)
    
    def _check_minor_security_issues(self, response: str) -> bool:
        """Check if minor security issues found"""
        minor_indicators = ['minor', 'small', 'low risk', 'recommendation']
        return any(indicator in response.lower() for indicator in minor_indicators)
    
    def _check_deployment_success(self, response: str) -> bool:
        """Check if deployment was successful"""
        success_indicators = ['successful', 'deployed', 'live', 'running']
        return any(indicator in response.lower() for indicator in success_indicators)
    
    def _check_monitoring_setup(self, response: str) -> bool:
        """Check if monitoring is set up"""
        monitoring_indicators = ['monitoring', 'alerts', 'metrics', 'dashboard']
        return any(indicator in response.lower() for indicator in monitoring_indicators)
    
    def _check_deployment_failure(self, response: str) -> bool:
        """Check if deployment failed"""
        failure_indicators = ['failed', 'error', 'broken', 'not working']
        return any(indicator in response.lower() for indicator in failure_indicators)
    
    def _check_infrastructure_issues(self, response: str) -> bool:
        """Check if infrastructure issues exist"""
        infrastructure_indicators = ['infrastructure', 'server', 'network', 'hardware']
        return any(indicator in response.lower() for indicator in infrastructure_indicators)
    
    def _calculate_confidence(self, context: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate confidence score based on context and criteria"""
        base_confidence = 0.7
        
        response_length = len(context.get('response', ''))
        if response_length > 1000:
            base_confidence += 0.1
        elif response_length < 200:
            base_confidence -= 0.2
        
        iteration = context.get('iteration', 0)
        max_iterations = criteria.get('max_iterations', 3)
        if iteration > max_iterations:
            base_confidence -= 0.1
        
        return max(0.1, min(1.0, base_confidence))
    
    def _default_decision(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return default decision when no rules match"""
        return {
            'action': 'NEXT_AGENT',
            'target_agent': 'QA_Engineer',
            'reason': 'No specific rules matched, defaulting to QA review',
            'confidence': 0.5,
            'rule_matched': 'default'
        }
    
    def get_agent_capabilities(self, agent_name: str) -> Dict[str, Any]:
        """Get agent capabilities and allowed actions"""
        if agent_name not in self.agent_rules:
            return {}
        
        return self.agent_rules[agent_name].get('criteria', {})
    
    def validate_decision(self, agent_name: str, decision: Dict[str, Any]) -> bool:
        """Validate if a decision is allowed for an agent"""
        capabilities = self.get_agent_capabilities(agent_name)
        
        if 'allowed_next_agents' in capabilities:
            allowed_agents = capabilities['allowed_next_agents']
            target_agent = decision.get('target_agent')
            
            if target_agent and target_agent not in allowed_agents:
                return False
        
        return True


def main():
    """Demo of the decision framework"""
    framework = AgentDecisionFramework()
    
    # Example context
    context = {
        'response': 'I have created a secure login system with authentication and password encryption. The code includes proper error handling and input validation.',
        'iteration': 1,
        'confidence': 0.8,
        'agent': 'Developer'
    }
    
    # Evaluate decision
    decision = framework.evaluate_decision('Developer', context)
    print(f"Decision: {decision}")
    
    # Validate decision
    is_valid = framework.validate_decision('Developer', decision)
    print(f"Decision valid: {is_valid}")


if __name__ == "__main__":
    main()
