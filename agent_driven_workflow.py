#!/usr/bin/env python3
"""
Agent-Driven Autonomous Workflow System
=======================================

This system allows each agent to make decisions about the next steps in the workflow,
creating a truly autonomous multi-agent system where agents control the flow.

Features:
- Each agent decides the next step using decision tags
- Support for parallel execution, branching, and human review
- Full context preservation between agents
- Comprehensive logging and decision tracking
- Real-time workflow visualization

Author: AI Assistant
Date: 2025
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Import our existing components
from enhanced_orchestrator import EnhancedOrchestrator
from llm_interface import LLMInterface
from smart_workflow_router import SmartWorkflowRouter, ContextAnalysis, AgentRecommendation
from tools.agent_knowledge_integration import get_knowledge_registry, AgentKnowledgeRegistry
from workspace_organizer import WorkspaceOrganizer


@dataclass
class AgentDecision:
    """Structure for agent decisions"""
    action: str
    target: Optional[str] = None
    targets: Optional[List[str]] = None
    condition: Optional[str] = None
    reason: str = ""
    confidence: float = 1.0
    metadata: Optional[Dict] = None

    def to_dict(self):
        """Convert AgentDecision to a dictionary for JSON serialization"""
        return {
            'action': self.action,
            'target': self.target,
            'targets': self.targets,
            'condition': self.condition,
            'reason': self.reason,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


class AgentDrivenWorkflow:
    """
    Agent-Driven Autonomous Workflow System
    
    In this system, each agent makes decisions about how to continue the workflow
    rather than following a predetermined flow.
    """
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.orchestrator = EnhancedOrchestrator()
        self.workspace_organizer = WorkspaceOrganizer()
        self.llm_interface = LLMInterface()
        self.smart_router = SmartWorkflowRouter()  # Add smart router
        self.knowledge_registry: Optional[AgentKnowledgeRegistry] = None  # Will be initialized asynchronously
        
        # Configure orchestrator with workspace organizer immediately
        self.orchestrator.workspace_organizer = self.workspace_organizer
        
        # Workflow state
        self.workflow_state = {
            'current_agent': None,
            'iteration': 0,
            'max_iterations': 15,
            'context': {},
            'decisions': [],
            'artifacts': [],
            'parallel_tasks': [],
            'workflow_id': None,
            'user_request': None,
            'context_analysis': None
        }
    
    async def initialize(self):
        """Initialize the workflow with the knowledge registry"""
        if self.knowledge_registry is None:
            self.knowledge_registry = await get_knowledge_registry()
            self.debug_print("📚 Knowledge registry initialized")
        
        # Configure orchestrator with workspace organizer
        self.orchestrator.workspace_organizer = self.workspace_organizer
    
    async def get_available_agents(self) -> List[str]:
        """Get list of all available agents from the dynamic registry"""
        if self.knowledge_registry is None:
            await self.initialize()
        
        if self.knowledge_registry is not None:
            return list(self.knowledge_registry.agent_profiles.keys())
        return []
    
    async def get_agent_capabilities(self, agent_name: str) -> Dict[str, Any]:
        """Get agent capabilities from the dynamic registry"""
        if self.knowledge_registry is None:
            await self.initialize()
        
        if self.knowledge_registry is not None:
            capabilities = await self.knowledge_registry.get_agent_capabilities(agent_name)
            return capabilities.get('agent_profile', {})
        return {}
    
    async def validate_agent_name(self, agent_name: str) -> bool:
        """Validate if an agent name exists in the system"""
        if self.knowledge_registry is None:
            await self.initialize()
        
        if self.knowledge_registry is not None:
            return self.knowledge_registry.validate_agent_discovery(agent_name)
        return False
    
    async def display_available_agents(self):
        """Display all available agents with their specialties"""
        if self.knowledge_registry is None:
            await self.initialize()
        
        print("\n🤖 AVAILABLE AGENTS IN THE SYSTEM:")
        print("=" * 60)
        
        agents = await self.get_available_agents()
        main_agents = [
            'Product_Analyst', 'UX_UI_Designer', 'Architect', 'Tester', 
            'Coder', 'Code_Reviewer', 'Security_Specialist', 'QA_Guardian',
            'DevOps_Specialist', 'Technical_Writer', 'Debugger', 'Git_Agent', 'Ask_Agent'
        ]
        
        for i, agent in enumerate(main_agents, 1):
            if agent in agents:
                capabilities = await self.get_agent_capabilities(agent)
                specialties = capabilities.get('capabilities', [])[:3]  # Show first 3
                specialties_str = ', '.join(specialties)
                print(f"  {i:2}. {agent:<20} | {specialties_str}")
        
        print("\n💡 Additional agents also available from registry")
        print("=" * 60)
    
    def debug_print(self, message: str):
        """Print debug messages if debug mode is enabled"""
        if self.debug_mode:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] DEBUG: {message}")
    
    async def generate_agent_decision_prompt(self, agent_name: str, user_request: str, context: Dict) -> str:
        """Generate a comprehensive decision prompt for an agent"""
        
        agent_info = await self.get_agent_capabilities(agent_name)
        
        base_prompt = f"""
        AGENT ROLE: {agent_name}
        ====================
        
        ORIGINAL USER REQUEST:
        {user_request}
        
        YOUR SPECIALTIES:
        {', '.join(agent_info.get('capabilities', []))}
        
        CURRENT WORKFLOW CONTEXT:
        {json.dumps(context, indent=2)}
        
        YOUR TASK:
        1. Complete your specialized work for this request
        2. Evaluate the current state and quality of work
        3. Decide on the next step in the workflow
        
        DECISION FRAMEWORK:
        ===================
        
        After completing your work, you MUST end your response with ONE of these decision tags:
        
        🎯 PRIMARY DECISIONS:
        [COMPLETE] - Task is fully completed, no further work needed
        [NEXT_AGENT: AgentName] - Continue to specific agent (e.g., [NEXT_AGENT: Developer])
        [HUMAN_REVIEW] - Need human intervention or approval
        
        🔄 WORKFLOW CONTROL:
        [RETRY] - Retry current task (if quality is insufficient)
        [PARALLEL: Agent1,Agent2] - Execute multiple agents simultaneously
        [BRANCH: condition] - Create conditional workflow branch
        
        🧠 DECISION FACTORS TO CONSIDER:
        """
        
        # Add agent-specific decision factors - derive from capabilities
        capabilities = agent_info.get('capabilities', [])
        if capabilities:
            base_prompt += f"\n        • Quality of {capabilities[0].replace('_', ' ').title()}"
            for capability in capabilities[1:3]:  # Show first 3 capabilities
                base_prompt += f"\n        • {capability.replace('_', ' ').title()} completeness"
        
        # Add typical next agents - derive from integrates_with
        typical_next = agent_info.get('integrates_with', [])
        if typical_next:
            base_prompt += f"\n\n        🔗 TYPICAL NEXT AGENTS FOR {agent_name}:"
            for next_agent in typical_next:
                base_prompt += f"\n        • {next_agent}"
        
        base_prompt += f"""
        
        📊 QUALITY THRESHOLDS:
        • High Quality Work → [COMPLETE] or [NEXT_AGENT: appropriate_agent]
        • Medium Quality Work → [NEXT_AGENT: QA_Guardian] or [RETRY]
        • Low Quality Work → [RETRY] or [HUMAN_REVIEW]
        • Security Concerns → [NEXT_AGENT: Security_Specialist]
        • Performance Issues → [NEXT_AGENT: Performance_Engineer]
        • Deployment Ready → [NEXT_AGENT: DevOps_Specialist]
        
        🤖 ALL AVAILABLE AGENTS IN SYSTEM:
        Main Workflow: Product_Analyst, UX_UI_Designer, Architect, Tester, Coder, 
        Code_Reviewer, Security_Specialist, QA_Guardian, DevOps_Specialist, 
        Technical_Writer, Debugger, Git_Agent, Ask_Agent
        
        🎯 EXAMPLES:
        • "The code is well-tested and secure. [COMPLETE]"
        • "Code needs quality review before deployment. [NEXT_AGENT: Code_Reviewer]"
        • "Security analysis required due to authentication features. [NEXT_AGENT: Security_Specialist]"
        • "Requirements are unclear, need clarification. [HUMAN_REVIEW]"
        • "Multiple aspects need attention simultaneously. [PARALLEL: Tester,Security_Specialist]"
        • "UI design needed for better user experience. [NEXT_AGENT: UX_UI_Designer]"
        • "Architecture review required for scalability. [NEXT_AGENT: Architect]"
        
        Now, complete your specialized work and make your decision!
        """
        
        return base_prompt
    
    def parse_agent_decision(self, response: str) -> AgentDecision:
        """Parse agent decision from response with enhanced pattern matching"""
        
        # Decision patterns with confidence scoring
        decision_patterns = {
            'COMPLETE': r'\[COMPLETE\]',
            'NEXT_AGENT': r'\[NEXT_AGENT:\s*([^\]]+)\]',
            'HUMAN_REVIEW': r'\[HUMAN_REVIEW\]',
            'RETRY': r'\[RETRY\]',
            'PARALLEL': r'\[PARALLEL:\s*([^\]]+)\]',
            'BRANCH': r'\[BRANCH:\s*([^\]]+)\]'
        }
        
        # Look for decision tags
        for decision_type, pattern in decision_patterns.items():
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                # Extract reason from context around the decision
                reason_context = self.extract_decision_reason(response, match.span())
                
                if decision_type == 'COMPLETE':
                    return AgentDecision(
                        action='COMPLETE',
                        reason=reason_context or 'Agent decided task is complete',
                        confidence=self.calculate_decision_confidence(response, decision_type)
                    )
                
                elif decision_type == 'NEXT_AGENT':
                    target = match.group(1).strip()
                    return AgentDecision(
                        action='NEXT_AGENT',
                        target=target,
                        reason=reason_context or f'Agent decided to continue to {target}',
                        confidence=self.calculate_decision_confidence(response, decision_type)
                    )
                
                elif decision_type == 'HUMAN_REVIEW':
                    return AgentDecision(
                        action='HUMAN_REVIEW',
                        reason=reason_context or 'Agent decided human review is needed',
                        confidence=self.calculate_decision_confidence(response, decision_type)
                    )
                
                elif decision_type == 'RETRY':
                    return AgentDecision(
                        action='RETRY',
                        reason=reason_context or 'Agent decided to retry current task',
                        confidence=self.calculate_decision_confidence(response, decision_type)
                    )
                
                elif decision_type == 'PARALLEL':
                    targets = [agent.strip() for agent in match.group(1).split(',')]
                    return AgentDecision(
                        action='PARALLEL',
                        targets=targets,
                        reason=reason_context or f'Agent decided to execute {len(targets)} agents in parallel',
                        confidence=self.calculate_decision_confidence(response, decision_type)
                    )
                
                elif decision_type == 'BRANCH':
                    condition = match.group(1).strip()
                    return AgentDecision(
                        action='BRANCH',
                        condition=condition,
                        reason=reason_context or f'Agent decided to create conditional branch: {condition}',
                        confidence=self.calculate_decision_confidence(response, decision_type)
                    )
        
        # No explicit decision found - use intelligent fallback
        return self.intelligent_fallback_decision(response)
    
    def extract_decision_reason(self, response: str, decision_span: Tuple[int, int]) -> str:
        """Extract reasoning context around the decision tag"""
        start, end = decision_span
        
        # Look for context before the decision tag
        context_start = max(0, start - 200)
        context_before = response[context_start:start]
        
        # Look for sentences that explain the decision
        sentences = re.split(r'[.!?]+', context_before)
        if sentences:
            # Take the last complete sentence as the reason
            reason = sentences[-1].strip()
            if len(reason) > 10:  # Ensure it's meaningful
                return reason
        
        return ""
    
    def calculate_decision_confidence(self, response: str, decision_type: str) -> float:
        """Calculate confidence score for a decision based on response content"""
        confidence = 0.5  # Base confidence
        
        # Factors that increase confidence
        positive_indicators = [
            'confident', 'certain', 'clear', 'obvious', 'definitely',
            'completed', 'tested', 'verified', 'validated', 'ready'
        ]
        
        # Factors that decrease confidence
        negative_indicators = [
            'uncertain', 'maybe', 'possibly', 'might', 'could',
            'unsure', 'unclear', 'incomplete', 'issues', 'problems'
        ]
        
        response_lower = response.lower()
        
        for indicator in positive_indicators:
            if indicator in response_lower:
                confidence += 0.1
        
        for indicator in negative_indicators:
            if indicator in response_lower:
                confidence -= 0.1
        
        # Specific decision type adjustments
        if decision_type == 'COMPLETE' and 'test' in response_lower:
            confidence += 0.2
        elif decision_type == 'HUMAN_REVIEW' and 'complex' in response_lower:
            confidence += 0.2
        
        return max(0.1, min(1.0, confidence))
    
    def intelligent_fallback_decision(self, response: str) -> AgentDecision:
        """Make intelligent decision when no explicit decision tag is found"""
        
        response_lower = response.lower()
        
        # Analyze response content for implicit decisions
        if any(word in response_lower for word in ['complete', 'finished', 'done', 'ready', 'approved']):
            return AgentDecision(
                action='COMPLETE',
                reason='Response indicates task completion',
                confidence=0.7
            )
        
        # Test and Quality Assurance
        if any(word in response_lower for word in ['test', 'verify', 'validate', 'check']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Tester',
                reason='Response suggests need for testing/validation',
                confidence=0.6
            )
        
        # Security concerns
        if any(word in response_lower for word in ['security', 'secure', 'vulnerability', 'auth', 'login', 'password']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Security_Specialist',
                reason='Response indicates security considerations',
                confidence=0.6
            )
        
        # Deployment and Infrastructure
        if any(word in response_lower for word in ['deploy', 'deployment', 'production', 'server', 'infrastructure']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='DevOps_Specialist',
                reason='Response suggests deployment needs',
                confidence=0.6
            )
        
        # Code implementation
        if any(word in response_lower for word in ['code', 'implement', 'develop', 'program', 'function']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Coder',
                reason='Response indicates need for code implementation',
                confidence=0.6
            )
        
        # Architecture and Design
        if any(word in response_lower for word in ['architecture', 'design', 'system', 'structure', 'pattern']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Architect',
                reason='Response suggests architectural considerations',
                confidence=0.6
            )
        
        # UI/UX Design
        if any(word in response_lower for word in ['ui', 'ux', 'interface', 'user', 'design', 'wireframe']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='UX_UI_Designer',
                reason='Response indicates UI/UX design needs',
                confidence=0.6
            )
        
        # Code Review
        if any(word in response_lower for word in ['review', 'quality', 'maintainability', 'refactor']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Code_Reviewer',
                reason='Response suggests need for code review',
                confidence=0.6
            )
        
        # Documentation
        if any(word in response_lower for word in ['document', 'documentation', 'guide', 'manual', 'docs']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Technical_Writer',
                reason='Response indicates documentation needs',
                confidence=0.6
            )
        
        # Debugging and troubleshooting
        if any(word in response_lower for word in ['bug', 'error', 'issue', 'problem', 'debug', 'fix']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Debugger',
                reason='Response indicates debugging needs',
                confidence=0.6
            )
        
        # Version Control
        if any(word in response_lower for word in ['git', 'commit', 'merge', 'branch', 'version']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Git_Agent',
                reason='Response suggests version control operations',
                confidence=0.6
            )
        
        # Final Quality Check
        if any(word in response_lower for word in ['qa', 'guardian', 'final', 'approval', 'gate']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='QA_Guardian',
                reason='Response indicates need for final quality validation',
                confidence=0.6
            )
        
        # Information and Guidance
        if any(word in response_lower for word in ['ask', 'question', 'help', 'guidance', 'advice', 'information']):
            return AgentDecision(
                action='NEXT_AGENT',
                target='Ask_Agent',
                reason='Response suggests need for information or guidance',
                confidence=0.6
            )
        
        # Default: continue with QA review (most common fallback)
        return AgentDecision(
            action='NEXT_AGENT',
            target='QA_Guardian',
            reason='No explicit decision found, defaulting to QA Guardian review',
            confidence=0.3
        )
    
    async def execute_agent_with_decision(self, agent_name: str, user_request: str, context: Dict) -> Dict:
        """Execute an agent and parse its decision"""
        
        # Smart routing check - should we skip this agent?
        should_skip, skip_reason = self.should_skip_agent(agent_name, context)
        if should_skip:
            self.debug_print(f"🚫 Skipping {agent_name}: {skip_reason}")
            
            # Return a mock decision to continue workflow
            decision = AgentDecision(
                action='NEXT_AGENT',
                target=self.get_smart_next_agent(agent_name, context) or 'QA_Guardian',
                reason=f"Agent skipped: {skip_reason}",
                confidence=0.8
            )
            
            return {
                'response': f"Agent {agent_name} was skipped due to smart routing: {skip_reason}",
                'decision': decision,
                'agent_name': agent_name,
                'iteration': self.workflow_state['iteration'],
                'artifacts_created': [],
                'skipped': True
            }
        
        self.debug_print(f"🤖 Executing {agent_name} with decision capability")
        
        # Optimize context for token efficiency
        optimized_context = self.optimize_context_for_next_agent(context)
        
        # Generate decision-enabled prompt
        prompt = await self.generate_agent_decision_prompt(agent_name, user_request, optimized_context)
        
        # Execute agent through orchestrator
        response = await self.orchestrator.execute_llm_call_with_cache(
            agent_name=agent_name,
            prompt=prompt,
            context={'workflow_id': f"{self.workflow_state['workflow_id']}-{agent_name}-{self.workflow_state['iteration']}"}
        )
        
        # Parse decision from response
        decision = self.parse_agent_decision(response)
        
        # If no explicit decision, use smart routing
        if decision.action == 'NEXT_AGENT' and not decision.target:
            smart_target = self.get_smart_next_agent(agent_name, context)
            if smart_target:
                decision.target = smart_target
                decision.reason = f"Smart routing recommendation: {smart_target}"
        
        # Check if the recommended target should be skipped
        if decision.action == 'NEXT_AGENT' and decision.target:
            should_skip_target, skip_reason = self.should_skip_agent(decision.target, context)
            if should_skip_target:
                self.debug_print(f"🚫 Target {decision.target} should be skipped: {skip_reason}")
                # Try to find an alternative
                alternative_target = self.get_smart_next_agent(agent_name, context)
                if alternative_target and alternative_target != decision.target:
                    decision.target = alternative_target
                    decision.reason = f"Redirected to {alternative_target} due to skip: {skip_reason}"
                else:
                    # Force completion if no valid target
                    decision.action = 'COMPLETE'
                    decision.target = None
                    decision.reason = f"No valid next agent available, completing workflow"
                    decision.confidence = 0.7
        
        # Create result dictionary
        result = {
            'response': response,
            'decision': decision,
            'agent_name': agent_name,
            'iteration': self.workflow_state['iteration'],
            'artifacts_created': [],  # Will be populated by orchestrator if files are saved
            'skipped': False
        }
        
        self.debug_print(f"🎯 {agent_name} decision: {decision.action} (confidence: {decision.confidence:.2f})")
        if decision.reason:
            self.debug_print(f"   Reason: {decision.reason}")
        
        return result
    
    async def execute_parallel_agents(self, agent_names: List[str], user_request: str, context: Dict) -> List[Dict]:
        """Execute multiple agents in parallel"""
        
        self.debug_print(f"🔀 Executing {len(agent_names)} agents in parallel: {', '.join(agent_names)}")
        
        # Create tasks for parallel execution
        tasks = []
        for agent_name in agent_names:
            task = self.execute_agent_with_decision(agent_name, user_request, context)
            tasks.append(task)
        
        # Execute in parallel
        results = await asyncio.gather(*tasks)
        
        self.debug_print(f"✅ Parallel execution completed for {len(agent_names)} agents")
        
        return results
    
    async def run_agent_driven_workflow(self, user_request: str) -> Dict:
        """
        Run the agent-driven autonomous workflow
        
        In this workflow, each agent makes decisions about the next steps,
        creating a truly autonomous multi-agent system.
        """
        
        print(f"\n[WORKFLOW] Starting AGENT-DRIVEN AUTONOMOUS WORKFLOW")
        print(f"📝 User Request: {user_request}")
        print("=" * 80)
        
        # Ensure we're initialized
        await self.initialize()
        
        # Initialize workflow state
        self.workflow_state = {
            'workflow_id': f"agent-driven-{int(time.time())}",
            'current_agent': 'Product_Analyst',  # Always start with analysis
            'iteration': 0,
            'max_iterations': 15,
            'user_request': user_request,  # Store user request
            'context': {
                'user_request': user_request,
                'workflow_history': [],
                'artifacts': [],
                'decisions': [],
                'parallel_results': []
            }
        }
        
        # Initialize context analysis
        context_analysis = self.smart_router.analyze_context(user_request, self.workflow_state['context'])
        self.workflow_state['context']['context_analysis'] = context_analysis.to_dict()  # Convert to dict
        
        # Display context analysis
        self.debug_print(f"📊 Context Analysis:")
        self.debug_print(f"   Project Type: {context_analysis.project_type}")
        self.debug_print(f"   Complexity: {context_analysis.complexity_level}")
        self.debug_print(f"   Security Required: {context_analysis.security_requirements}")
        self.debug_print(f"   User Facing: {context_analysis.user_facing}")
        self.debug_print(f"   Testing Required: {context_analysis.testing_required}")
        self.debug_print(f"   Documentation Needed: {context_analysis.documentation_needed}")
        self.debug_print(f"   Deployment Ready: {context_analysis.deployment_ready}")
        
        workflow_result = {
            'workflow_id': self.workflow_state['workflow_id'],
            'user_request': user_request,
            'execution_flow': [],
            'final_status': 'STARTED',
            'total_iterations': 0,
            'artifacts_created': [],
            'decisions_made': [],
            'context_analysis': context_analysis.to_dict()  # Convert to dict
        }
        
        current_agent = self.workflow_state['current_agent']
        
        # Main workflow loop
        while self.workflow_state['iteration'] < self.workflow_state['max_iterations']:
            self.workflow_state['iteration'] += 1
            
            print(f"\n🔄 ITERATION {self.workflow_state['iteration']}: {current_agent}")
            print("-" * 60)
            
            try:
                # Execute current agent with decision capability
                result = await self.execute_agent_with_decision(
                    current_agent, 
                    user_request, 
                    self.workflow_state['context']
                )
                
                # Get decision from result
                decision = result['decision']
                
                # Record execution
                execution_record = {
                    'iteration': self.workflow_state['iteration'],
                    'agent': current_agent,
                    'decision': decision,
                    'success': True,
                    'artifacts': result.get('artifacts_created', []),
                    'response_length': len(result.get('response', '')),
                    'skipped': result.get('skipped', False)
                }
                
                workflow_result['execution_flow'].append(execution_record)
                
                # Create decision record for agent_decisions compatibility
                decision_record = {
                    'agent': current_agent,
                    'decision': decision.action,
                    'next_agent': decision.target if hasattr(decision, 'target') else None,
                    'confidence': decision.confidence if hasattr(decision, 'confidence') else 0.5,
                    'reason': decision.reason if hasattr(decision, 'reason') else '',
                    'iteration': self.workflow_state['iteration']
                }
                
                workflow_result['decisions_made'].append(decision_record)
                
                # Update context
                self.workflow_state['context']['workflow_history'].append({
                    'agent': current_agent,
                    'result': {
                        'response': result['response'],
                        'artifacts_created': result.get('artifacts_created', [])
                    },
                    'decision': {
                        'action': decision.action,
                        'target': decision.target,
                        'targets': decision.targets,
                        'condition': decision.condition,
                        'reason': decision.reason,
                        'confidence': decision.confidence
                    },
                    'iteration': self.workflow_state['iteration']
                })
                
                # Add artifacts
                if result.get('artifacts_created'):
                    workflow_result['artifacts_created'].extend(result['artifacts_created'])
                
                print(f"🎯 AGENT DECISION: {decision.action}")
                if decision.reason:
                    print(f"   💭 Reason: {decision.reason}")
                print(f"   📊 Confidence: {decision.confidence:.2f}")
                
                # Handle different decision types
                if decision.action == 'COMPLETE':
                    print(f"✅ Workflow COMPLETED by {current_agent}")
                    workflow_result['final_status'] = 'COMPLETED'
                    break
                
                elif decision.action == 'NEXT_AGENT':
                    next_agent = decision.target
                    
                    # Validate agent exists
                    if not await self.validate_agent_name(next_agent):
                        print(f"⚠️  Invalid agent '{next_agent}', using QA_Guardian instead")
                        next_agent = 'QA_Guardian'
                    
                    # Check for workflow loops
                    if self.detect_workflow_loop(next_agent, self.workflow_state['context']):
                        loop_breaker = self.break_workflow_loop(current_agent, self.workflow_state['context'])
                        if loop_breaker:
                            print(f"🔄 Loop detected! Breaking loop by moving to {loop_breaker}")
                            current_agent = loop_breaker
                        else:
                            print(f"🔄 Loop detected! Completing workflow to prevent infinite loop")
                            workflow_result['final_status'] = 'COMPLETED'
                            break
                    else:
                        print(f"➡️  Continuing to {next_agent}")
                        current_agent = next_agent
                
                elif decision.action == 'RETRY':
                    print(f"🔄 Retrying {current_agent}")
                    # Keep same agent for next iteration
                
                elif decision.action == 'HUMAN_REVIEW':
                    print(f"👤 Human review needed - pausing workflow")
                    workflow_result['final_status'] = 'NEEDS_HUMAN_REVIEW'
                    break
                
                elif decision.action == 'PARALLEL':
                    print(f"🔀 Executing parallel agents: {', '.join(decision.targets)}")
                    parallel_results = await self.execute_parallel_agents(
                        decision.targets, 
                        user_request, 
                        self.workflow_state['context']
                    )
                    
                    # Process parallel results
                    for parallel_result in parallel_results:
                        execution_record = {
                            'iteration': self.workflow_state['iteration'],
                            'agent': parallel_result['agent_name'],
                            'decision': parallel_result['decision'],
                            'success': True,
                            'artifacts': parallel_result.get('artifacts_created', []),
                            'response_length': len(parallel_result.get('response', ''))
                        }
                        workflow_result['execution_flow'].append(execution_record)
                        
                        # Update context
                        self.workflow_state['context']['parallel_results'].append(parallel_result)
                        
                        # Add artifacts
                        if parallel_result.get('artifacts_created'):
                            workflow_result['artifacts_created'].extend(parallel_result['artifacts_created'])
                    
                    # Choose next agent based on parallel results
                    next_agent = self.choose_next_agent_from_parallel_results(parallel_results)
                    if next_agent:
                        current_agent = next_agent
                        print(f"➡️  Continuing to {next_agent} based on parallel results")
                    else:
                        print(f"✅ Parallel execution completed workflow")
                        workflow_result['final_status'] = 'COMPLETED'
                        break
                
                elif decision.action == 'BRANCH':
                    print(f"🌳 Branching requested: {decision.condition}")
                    # For now, continue with current flow
                    # Advanced branching logic can be implemented later
                    current_agent = self.evaluate_branch_condition(decision.condition)
                
                else:
                    print(f"❓ Unknown decision action: {decision.action}")
                    # Default to QA review
                    current_agent = 'QA_Engineer'
                
            except Exception as e:
                error_msg = f"Error executing {current_agent}: {str(e)}"
                print(f"❌ {error_msg}")
                
                execution_record = {
                    'iteration': self.workflow_state['iteration'],
                    'agent': current_agent,
                    'decision': None,
                    'success': False,
                    'error': error_msg
                }
                workflow_result['execution_flow'].append(execution_record)
                workflow_result['final_status'] = 'ERROR'
                break
        
        # Finalize workflow
        workflow_result['total_iterations'] = self.workflow_state['iteration']
        
        if workflow_result['final_status'] == 'STARTED':
            workflow_result['final_status'] = 'MAX_ITERATIONS_REACHED'
        
        # Add workspace_path for external access to artifacts
        workflow_result['workspace_path'] = str(self.workspace_organizer.get_workflow_folder(workflow_result['workflow_id']))
        
        # Add agent_decisions for backward compatibility with tests
        workflow_result['agent_decisions'] = workflow_result['decisions_made']
        
        # Save and display results
        self.save_workflow_results(workflow_result)
        self.display_workflow_results(workflow_result)
        
        # Finalize with cleanup
        await self.finalize_workflow(workflow_result)
        
        # Clean up old runs (keep last 5 runs, remove older than 7 days)
        await self.cleanup_after_run(keep_recent=5, days_to_keep=7)
        
        return workflow_result
    
    async def finalize_workflow(self, workflow_result: Dict[str, Any], status: str = "completed"):
        """Finalize the workflow with proper cleanup"""
        try:
            # Save final results using workspace organizer
            if self.workspace_organizer:
                self.workspace_organizer.save_workflow_result(workflow_result['workflow_id'], workflow_result)
                
                # Create workflow summary
                summary = {
                    "workflow_id": workflow_result['workflow_id'],
                    "user_request": workflow_result.get('user_request', ''),
                    "final_status": status,
                    "total_iterations": workflow_result.get('total_iterations', 0),
                    "agents_executed": len(workflow_result.get('execution_flow', [])),
                    "artifacts_created": len(workflow_result.get('artifacts_created', [])),
                    "completed_at": datetime.now().isoformat(),
                    "workspace_path": workflow_result.get('workspace_path', '')
                }
                
                self.workspace_organizer.save_workflow_summary(workflow_result['workflow_id'], summary)
                
                # Clean up temporary files
                self.workspace_organizer.cleanup_temp_files()
                
                # Finalize the session
                self.workspace_organizer.finalize_session(status)
                
                print(f"WORKFLOW: Finalized workflow {workflow_result['workflow_id']} with status: {status}")
                
        except Exception as e:
            print(f"WORKFLOW: Error finalizing workflow: {e}")
    
    async def cleanup_after_run(self, keep_recent: int = 5, days_to_keep: int = 7):
        """Clean up old workspace folders after workflow completion"""
        try:
            from cleanup_utility import WorkspaceCleanup
            
            cleanup = WorkspaceCleanup()
            cleanup.full_cleanup(days_to_keep, keep_recent)
            
        except Exception as e:
            print(f"CLEANUP: Error during cleanup: {e}")
    
    def choose_next_agent_from_parallel_results(self, parallel_results: List[Dict]) -> Optional[str]:
        """Choose next agent based on parallel execution results"""
        
        # Analyze decisions from parallel agents
        decisions = [result['decision'] for result in parallel_results]
        
        # If any agent says COMPLETE, we're done
        if any(d.action == 'COMPLETE' for d in decisions):
            return None
        
        # If any agent requests human review, pause
        if any(d.action == 'HUMAN_REVIEW' for d in decisions):
            return None
        
        # Choose the agent with highest confidence for next step
        next_agent_decisions = [d for d in decisions if d.action == 'NEXT_AGENT']
        if next_agent_decisions:
            best_decision = max(next_agent_decisions, key=lambda x: x.confidence)
            return best_decision.target
        
        return 'QA_Engineer'  # Default fallback
    
    def evaluate_branch_condition(self, condition: str) -> str:
        """Evaluate branch condition and return appropriate agent"""
        
        condition_lower = condition.lower()
        
        if 'security' in condition_lower:
            return 'Security_Engineer'
        elif 'test' in condition_lower or 'quality' in condition_lower:
            return 'QA_Engineer'
        elif 'deploy' in condition_lower:
            return 'DevOps_Engineer'
        elif 'performance' in condition_lower:
            return 'Performance_Engineer'
        else:
            return 'Developer'
    
    def save_workflow_results(self, workflow_result: Dict):
        """Save workflow results to file"""
        
        results_dir = f"./workspace/{workflow_result['workflow_id']}"
        os.makedirs(results_dir, exist_ok=True)
        
        # Save detailed results
        results_path = f"{results_dir}/workflow_results.json"
        
        # Convert AgentDecision objects to dictionaries for JSON serialization
        serializable_result = self.make_serializable(workflow_result)
        
        with open(results_path, 'w') as f:
            json.dump(serializable_result, f, indent=2, default=str)
        
        # Save summary
        summary = {
            'workflow_id': workflow_result['workflow_id'],
            'user_request': workflow_result['user_request'],
            'final_status': workflow_result['final_status'],
            'total_iterations': workflow_result['total_iterations'],
            'agents_executed': len(workflow_result['execution_flow']),
            'artifacts_created': len(workflow_result['artifacts_created']),
            'decisions_made': len(workflow_result['decisions_made'])
        }
        
        summary_path = f"{results_dir}/workflow_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.debug_print(f"📁 Workflow results saved to {results_dir}")
    
    def display_workflow_results(self, workflow_result: Dict):
        """Display comprehensive workflow results"""
        
        print(f"\n📊 AGENT-DRIVEN WORKFLOW RESULTS")
        print("=" * 80)
        print(f"🆔 Workflow ID: {workflow_result['workflow_id']}")
        print(f"📝 User Request: {workflow_result['user_request']}")
        print(f"🎯 Final Status: {workflow_result['final_status']}")
        print(f"🔄 Total Iterations: {workflow_result['total_iterations']}")
        print(f"🤖 Agents Executed: {len(workflow_result['execution_flow'])}")
        print(f"📁 Artifacts Created: {len(workflow_result['artifacts_created'])}")
        print(f"⚖️ Decisions Made: {len(workflow_result['decisions_made'])}")
        
        # Display context analysis
        if 'context_analysis' in workflow_result:
            context_analysis = workflow_result['context_analysis']
            print(f"\n🧠 SMART WORKFLOW ANALYSIS:")
            print(f"   📊 Project Type: {context_analysis['project_type']}")
            print(f"   📊 Complexity: {context_analysis['complexity_level']}")
            print(f"   🔒 Security Required: {context_analysis['security_requirements']}")
            print(f"   👤 User Facing: {context_analysis['user_facing']}")
            print(f"   ✅ Testing Required: {context_analysis['testing_required']}")
            print(f"   📝 Documentation Needed: {context_analysis['documentation_needed']}")
            print(f"   � Deployment Ready: {context_analysis['deployment_ready']}")
        
        # Calculate smart routing efficiency
        executed_agents = [exec['agent'] for exec in workflow_result['execution_flow']]
        skipped_agents = [exec for exec in workflow_result['execution_flow'] if exec.get('skipped', False)]
        
        print(f"\n🎯 SMART ROUTING EFFICIENCY:")
        print(f"   ✅ Agents Executed: {len(executed_agents) - len(skipped_agents)}")
        print(f"   🚫 Agents Skipped: {len(skipped_agents)}")
        if skipped_agents:
            print(f"   📋 Skipped Agents: {', '.join([exec['agent'] for exec in skipped_agents])}")
        
        print(f"\n�🔄 EXECUTION FLOW:")
        for i, execution in enumerate(workflow_result['execution_flow'], 1):
            status_icon = "✅" if execution['success'] else "❌"
            if execution.get('skipped', False):
                status_icon = "🚫"
            
            agent = execution['agent']
            decision = execution.get('decision')
            
            print(f"  {i}. {status_icon} {agent} (Iteration {execution['iteration']})")
            
            if execution.get('skipped', False):
                print(f"     🚫 Skipped: {decision.reason if decision else 'Smart routing decision'}")
            elif decision:
                print(f"     🎯 Decision: {decision.action}")
                if decision.target:
                    print(f"     ➡️  Target: {decision.target}")
                if decision.targets:
                    print(f"     🔀 Targets: {', '.join(decision.targets)}")
                print(f"     📊 Confidence: {decision.confidence:.2f}")
                if decision.reason:
                    print(f"     💭 Reason: {decision.reason}")
            
            if execution.get('error'):
                print(f"     ❌ Error: {execution['error']}")
        
        print(f"\n📁 ARTIFACTS CREATED:")
        for artifact in workflow_result['artifacts_created']:
            print(f"  📄 {artifact}")
        
        print(f"\n🎯 NEXT STEPS:")
        if workflow_result['final_status'] == 'COMPLETED':
            print("  ✅ Workflow completed successfully!")
            print("  🔄 All agents have approved the final result")
            print("  [READY] Ready for production or further development")
        elif workflow_result['final_status'] == 'NEEDS_HUMAN_REVIEW':
            print("  👤 Human review required")
            print("  🔄 Check the latest agent's concerns and provide guidance")
        elif workflow_result['final_status'] == 'ERROR':
            print("  ❌ Workflow encountered errors")
            print("  🔧 Review error messages and fix issues")
        elif workflow_result['final_status'] == 'MAX_ITERATIONS_REACHED':
            print("  ⏰ Maximum iterations reached")
            print("  🔄 Consider increasing iteration limit or simplifying the task")
    
    def make_serializable(self, obj):
        """Convert AgentDecision objects to dictionaries for JSON serialization"""
        if isinstance(obj, AgentDecision):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: self.make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.make_serializable(item) for item in obj]
        else:
            return obj
    
    def should_skip_agent(self, agent_name: str, context: Dict) -> Tuple[bool, str]:
        """Determine if an agent should be skipped based on smart routing"""
        
        # Get context analysis
        context_analysis_dict = context.get('context_analysis')
        if not context_analysis_dict:
            # Create context analysis if not exists
            user_request = context.get('user_request', '')
            context_analysis = self.smart_router.analyze_context(user_request, context)
            context_analysis_dict = context_analysis.to_dict()
            context['context_analysis'] = context_analysis_dict
        
        # Reconstruct ContextAnalysis object for smart router
        from smart_workflow_router import ContextAnalysis
        context_analysis = ContextAnalysis(**context_analysis_dict)
        
        # Check if agent should be skipped
        skip, reason = self.smart_router.should_skip_agent(agent_name, context_analysis, context)
        
        if skip:
            self.debug_print(f"🚫 Skipping {agent_name}: {reason}")
            return True, reason
        
        return False, ""
    
    def get_smart_next_agent(self, current_agent: str, context: Dict) -> Optional[str]:
        """Get smart recommendation for next agent"""
        
        # Get context analysis
        context_analysis_dict = context.get('context_analysis')
        if not context_analysis_dict:
            user_request = context.get('user_request', '')
            context_analysis = self.smart_router.analyze_context(user_request, context)
            context_analysis_dict = context_analysis.to_dict()
            context['context_analysis'] = context_analysis_dict
        
        # Reconstruct ContextAnalysis object for smart router
        from smart_workflow_router import ContextAnalysis
        context_analysis = ContextAnalysis(**context_analysis_dict)
        
        # Get recommendation
        next_agent = self.smart_router.get_next_agent_recommendation(
            current_agent, context_analysis, context
        )
        
        if next_agent:
            self.debug_print(f"🎯 Smart router recommends: {next_agent}")
        
        return next_agent
    
    def optimize_context_for_next_agent(self, context: Dict) -> Dict:
        """Optimize context to reduce token usage"""
        return self.smart_router.optimize_workflow_context(context)
    
    def detect_workflow_loop(self, current_agent: str, context: Dict) -> bool:
        """Detect if we're in an infinite loop between agents"""
        
        workflow_history = context.get('workflow_history', [])
        if len(workflow_history) < 4:
            return False
        
        # Check last 4 agents
        last_4_agents = [entry.get('agent') for entry in workflow_history[-4:]]
        
        # If we see the same 2 agents alternating
        if len(set(last_4_agents)) == 2 and len(last_4_agents) == 4:
            self.debug_print(f"🔄 Loop detected between {last_4_agents[0]} and {last_4_agents[1]}")
            return True
        
        # If we see the same agent 3 times in last 4 iterations
        if last_4_agents.count(current_agent) >= 3:
            self.debug_print(f"🔄 Agent {current_agent} executed too frequently")
            return True
        
        return False
    
    def break_workflow_loop(self, current_agent: str, context: Dict) -> Optional[str]:
        """Break workflow loop by choosing a different agent"""
        
        workflow_history = context.get('workflow_history', [])
        recent_agents = [entry.get('agent') for entry in workflow_history[-5:]]
        
        # Get context analysis
        context_analysis_dict = context.get('context_analysis', {})
        if context_analysis_dict:
            from smart_workflow_router import ContextAnalysis
            context_analysis = ContextAnalysis(**context_analysis_dict)
            
            # For simple scripts, force completion after several iterations
            if context_analysis.complexity_level == 'simple' and len(workflow_history) > 5:
                self.debug_print(f"🔄 Breaking loop: Forcing completion for simple project")
                return None  # This will trigger COMPLETE
            
            # For complex projects, try a different agent
            essential_agents = ['Security_Specialist', 'DevOps_Specialist', 'Technical_Writer']
            for agent in essential_agents:
                if agent not in recent_agents:
                    self.debug_print(f"🔄 Breaking loop: Moving to {agent}")
                    return agent
        
        # Default: complete the workflow
        self.debug_print(f"🔄 Breaking loop: No alternatives, completing workflow")
        return None

async def main():
    """Main function to demonstrate agent-driven workflow"""
    
    print("🎮 AGENT-DRIVEN AUTONOMOUS WORKFLOW DEMO")
    print("=" * 80)
    
    # Create workflow
    workflow = AgentDrivenWorkflow(debug_mode=True)
    
    # Initialize workflow with dynamic registry
    await workflow.initialize()
    
    # Display all available agents
    await workflow.display_available_agents()
    
    # Test different types of requests
    test_requests = [
        "Create a simple calculator with basic operations",
        "Build a secure user authentication system with registration and login",
        "Develop a REST API for a blog with CRUD operations and tests",
        "Create a task management web application with user interface",
        "Build a data analysis pipeline with error handling and logging",
        "Design and implement a microservices architecture",
        "Create comprehensive documentation for the project",
        "Debug performance issues in the application",
        "Set up CI/CD pipeline for deployment"
    ]
    
    print("\n📝 Choose a request to test:")
    for i, request in enumerate(test_requests, 1):
        print(f"{i}. {request}")
    print(f"{len(test_requests) + 1}. Custom request")
    
    try:
        choice = int(input(f"\nEnter your choice (1-{len(test_requests) + 1}): "))
        
        if choice <= len(test_requests):
            request = test_requests[choice - 1]
        else:
            request = input("Enter your custom request: ")
        
        print(f"\n[PROCESSING] Processing: '{request}'")
        print("=" * 80)
        
        # Execute agent-driven workflow
        result = await workflow.run_agent_driven_workflow(request)
        
        print(f"\n🎯 Agent-driven workflow '{result['workflow_id']}' completed!")
        print(f"📊 Status: {result['final_status']}")
        
        # Show agents that participated
        agents_used = set(exec_flow['agent'] for exec_flow in result['execution_flow'])
        print(f"🤖 Agents participated: {', '.join(sorted(agents_used))}")
        print(f"📈 Agent utilization: {len(agents_used)}/13 agents ({len(agents_used)/13*100:.1f}%)")
        
    except KeyboardInterrupt:
        print("\n👋 Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
