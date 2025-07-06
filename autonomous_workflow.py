"""
Autonomous Multi-Agent Workflow System
======================================
This system automatically decides which agents to use and how to flow between them.
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enhanced_orchestrator import EnhancedOrchestrator

class WorkflowDecisionEngine:
    """Decides which agents to use and how to flow between them"""
    
    def __init__(self):
        self.decision_rules = {
            # Keywords that indicate which type of work is needed
            'analysis_keywords': ['analyze', 'requirements', 'specs', 'plan', 'design', 'architecture'],
            'development_keywords': ['code', 'implement', 'build', 'create', 'develop', 'function', 'class'],
            'qa_keywords': ['test', 'validate', 'verify', 'check', 'quality', 'bugs'],
            'devops_keywords': ['deploy', 'infrastructure', 'server', 'docker', 'cloud', 'production'],
            'security_keywords': ['secure', 'auth', 'login', 'password', 'encrypt', 'safety']
        }
        
        # Workflow patterns
        self.workflow_patterns = {
            'simple_code': ['Developer'],
            'full_product': ['Product_Analyst', 'Developer', 'QA_Engineer'],
            'secure_system': ['Product_Analyst', 'Security_Engineer', 'Developer', 'QA_Engineer'],
            'deployment': ['Developer', 'DevOps_Engineer', 'QA_Engineer'],
            'analysis_only': ['Product_Analyst']
        }
    
    def analyze_request(self, request: str) -> Dict:
        """Analyze the request and determine the appropriate workflow"""
        request_lower = request.lower()
        
        # Count keyword matches
        analysis_score = sum(1 for keyword in self.decision_rules['analysis_keywords'] 
                           if keyword in request_lower)
        development_score = sum(1 for keyword in self.decision_rules['development_keywords'] 
                              if keyword in request_lower)
        qa_score = sum(1 for keyword in self.decision_rules['qa_keywords'] 
                      if keyword in request_lower)
        devops_score = sum(1 for keyword in self.decision_rules['devops_keywords'] 
                          if keyword in request_lower)
        security_score = sum(1 for keyword in self.decision_rules['security_keywords'] 
                           if keyword in request_lower)
        
        # Determine complexity
        total_words = len(request.split())
        complexity = 'simple' if total_words < 10 else 'medium' if total_words < 20 else 'complex'
        
        # Determine workflow pattern
        if security_score > 0 and analysis_score > 0:
            pattern = 'secure_system'
        elif devops_score > 0:
            pattern = 'deployment'
        elif analysis_score > 0 and development_score > 0 and qa_score > 0:
            pattern = 'full_product'
        elif analysis_score > 0 and development_score == 0:
            pattern = 'analysis_only'
        elif development_score > 0 and analysis_score == 0 and qa_score == 0:
            pattern = 'simple_code'
        else:
            pattern = 'full_product'  # default
        
        return {
            'pattern': pattern,
            'complexity': complexity,
            'scores': {
                'analysis': analysis_score,
                'development': development_score,
                'qa': qa_score,
                'devops': devops_score,
                'security': security_score
            },
            'agents': self.workflow_patterns[pattern]
        }
    
    def generate_agent_decision_rules(self, agent_name: str) -> str:
        """Generate decision rules for each agent to decide next steps"""
        
        base_rules = """
        DECISION RULES FOR NEXT STEPS:
        ================================
        
        As an autonomous agent, you must decide how to proceed after completing your work.
        Please end your response with one of these decision tags:
        
        [NEXT_AGENT: AgentName] - Continue to specific agent
        [COMPLETE] - Task is fully completed
        [RETRY] - Need to retry current task
        [HUMAN_REVIEW] - Need human intervention
        [PARALLEL: Agent1,Agent2] - Execute multiple agents in parallel
        [BRANCH: condition] - Create conditional flow
        
        Consider these factors in your decision:
        - Quality of your output
        - Completeness of the task
        - Dependencies on other agents
        - Risk level of the work
        - Need for validation/testing
        """
        
        agent_specific_rules = {
            'Product_Analyst': """
            PRODUCT ANALYST DECISION RULES:
            - If requirements are clear and complete → [NEXT_AGENT: Developer]
            - If requirements need security focus → [NEXT_AGENT: Security_Engineer]
            - If requirements are unclear → [HUMAN_REVIEW]
            - If analysis reveals high complexity → [NEXT_AGENT: Architect]
            """,
            
            'Developer': """
            DEVELOPER DECISION RULES:
            - If code is simple and well-tested → [COMPLETE]
            - If code needs quality assurance → [NEXT_AGENT: QA_Engineer]
            - If code has security implications → [NEXT_AGENT: Security_Engineer]
            - If code needs deployment → [NEXT_AGENT: DevOps_Engineer]
            - If code has bugs or issues → [RETRY]
            """,
            
            'QA_Engineer': """
            QA ENGINEER DECISION RULES:
            - If all tests pass and quality is high → [COMPLETE]
            - If tests reveal bugs → [NEXT_AGENT: Developer]
            - If performance issues found → [NEXT_AGENT: Performance_Engineer]
            - If security issues found → [NEXT_AGENT: Security_Engineer]
            - If ready for deployment → [NEXT_AGENT: DevOps_Engineer]
            """,
            
            'Security_Engineer': """
            SECURITY ENGINEER DECISION RULES:
            - If security is sufficient → [NEXT_AGENT: Developer]
            - If major security issues → [HUMAN_REVIEW]
            - If needs security testing → [NEXT_AGENT: QA_Engineer]
            - If security approved → [COMPLETE]
            """,
            
            'DevOps_Engineer': """
            DEVOPS ENGINEER DECISION RULES:
            - If deployment successful → [COMPLETE]
            - If deployment issues → [NEXT_AGENT: Developer]
            - If monitoring needed → [NEXT_AGENT: Monitoring_Engineer]
            - If infrastructure issues → [RETRY]
            """,
            
            'Architect': """
            ARCHITECT DECISION RULES:
            - If architecture is solid → [NEXT_AGENT: Developer]
            - If needs specialized agents → [PARALLEL: Developer,QA_Engineer]
            - If architecture needs review → [HUMAN_REVIEW]
            - If complex system → [NEXT_AGENT: Product_Analyst]
            """
        }
        
        return base_rules + agent_specific_rules.get(agent_name, "")
    
    def parse_agent_decision(self, response: str) -> Dict:
        """Parse agent decision from response"""
        import re
        
        # Look for decision tags
        decision_patterns = {
            'NEXT_AGENT': r'\[NEXT_AGENT:\s*([^\]]+)\]',
            'COMPLETE': r'\[COMPLETE\]',
            'RETRY': r'\[RETRY\]',
            'HUMAN_REVIEW': r'\[HUMAN_REVIEW\]',
            'PARALLEL': r'\[PARALLEL:\s*([^\]]+)\]',
            'BRANCH': r'\[BRANCH:\s*([^\]]+)\]'
        }
        
        for decision_type, pattern in decision_patterns.items():
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                if decision_type == 'NEXT_AGENT':
                    return {
                        'action': 'NEXT_AGENT',
                        'target': match.group(1).strip(),
                        'reason': 'Agent decided to continue workflow'
                    }
                elif decision_type == 'COMPLETE':
                    return {
                        'action': 'COMPLETE',
                        'reason': 'Agent decided task is complete'
                    }
                elif decision_type == 'RETRY':
                    return {
                        'action': 'RETRY',
                        'reason': 'Agent decided to retry current task'
                    }
                elif decision_type == 'HUMAN_REVIEW':
                    return {
                        'action': 'HUMAN_REVIEW',
                        'reason': 'Agent decided human review is needed'
                    }
                elif decision_type == 'PARALLEL':
                    agents = [agent.strip() for agent in match.group(1).split(',')]
                    return {
                        'action': 'PARALLEL',
                        'targets': agents,
                        'reason': 'Agent decided to execute multiple agents in parallel'
                    }
                elif decision_type == 'BRANCH':
                    return {
                        'action': 'BRANCH',
                        'condition': match.group(1).strip(),
                        'reason': 'Agent decided to create conditional flow'
                    }
        
        # Default: continue with original workflow
        return {
            'action': 'CONTINUE',
            'reason': 'No explicit decision found, continuing with original workflow'
        }


class SmartAgentWorkflow:
    """Agents decide their own next steps based on intelligent rules"""
    
    def __init__(self):
        self.orchestrator = EnhancedOrchestrator()
        self.workflow_history = []
        
        # Agent decision rules - each agent knows what to do
        self.agent_rules = {
            'Product_Analyst': {
                'capabilities': ['requirements', 'analysis', 'specifications', 'user_stories'],
                'next_agent_rules': {
                    'needs_security': 'Security_Engineer',
                    'needs_code': 'Developer', 
                    'needs_design': 'UI_Designer',
                    'complex_system': 'System_Architect'
                },
                'decision_prompt': """
                Based on your analysis, decide what should happen next:
                - If security/authentication mentioned → recommend Security_Engineer
                - If ready for coding → recommend Developer
                - If needs UI/UX work → recommend UI_Designer
                - If system is complex → recommend System_Architect
                - If analysis complete and simple → recommend Developer
                
                Respond with: NEXT_AGENT: [agent_name] | REASON: [why] | CONFIDENCE: [1-10]
                Or: COMPLETE | REASON: [why this task is done]
                """
            },
            
            'Developer': {
                'capabilities': ['coding', 'implementation', 'bug_fixes', 'integration'],
                'next_agent_rules': {
                    'needs_testing': 'QA_Engineer',
                    'needs_security_review': 'Security_Engineer',
                    'needs_deployment': 'DevOps_Engineer',
                    'needs_optimization': 'Performance_Engineer'
                },
                'decision_prompt': """
                Based on the code you created, decide what should happen next:
                - If code needs testing → recommend QA_Engineer
                - If security-sensitive features → recommend Security_Engineer  
                - If ready for deployment → recommend DevOps_Engineer
                - If performance critical → recommend Performance_Engineer
                - If code is simple and complete → COMPLETE
                
                Respond with: NEXT_AGENT: [agent_name] | REASON: [why] | CONFIDENCE: [1-10]
                Or: COMPLETE | REASON: [why this task is done]
                """
            },
            
            'QA_Engineer': {
                'capabilities': ['testing', 'validation', 'quality_assurance', 'bug_detection'],
                'next_agent_rules': {
                    'found_bugs': 'Developer',
                    'security_issues': 'Security_Engineer', 
                    'performance_issues': 'Performance_Engineer',
                    'ready_for_production': 'DevOps_Engineer'
                },
                'decision_prompt': """
                Based on your testing results, decide what should happen next:
                - If bugs found → recommend Developer (with bug details)
                - If security vulnerabilities → recommend Security_Engineer
                - If performance issues → recommend Performance_Engineer
                - If all tests pass → recommend DevOps_Engineer or COMPLETE
                
                Respond with: NEXT_AGENT: [agent_name] | REASON: [why] | CONFIDENCE: [1-10]
                Or: COMPLETE | REASON: [why this task is done]
                """
            },
            
            'Security_Engineer': {
                'capabilities': ['security_audit', 'vulnerability_assessment', 'auth_systems'],
                'next_agent_rules': {
                    'needs_code_changes': 'Developer',
                    'needs_testing': 'QA_Engineer',
                    'security_approved': 'DevOps_Engineer'
                },
                'decision_prompt': """
                Based on your security analysis, decide what should happen next:
                - If security issues found → recommend Developer (with security requirements)
                - If need security testing → recommend QA_Engineer
                - If security approved → recommend DevOps_Engineer or COMPLETE
                
                Respond with: NEXT_AGENT: [agent_name] | REASON: [why] | CONFIDENCE: [1-10]
                Or: COMPLETE | REASON: [why this task is done]
                """
            },
            
            'DevOps_Engineer': {
                'capabilities': ['deployment', 'infrastructure', 'monitoring', 'scaling'],
                'next_agent_rules': {
                    'deployment_issues': 'Developer',
                    'needs_testing': 'QA_Engineer',
                    'performance_tuning': 'Performance_Engineer'
                },
                'decision_prompt': """
                Based on deployment analysis, decide what should happen next:
                - If deployment issues → recommend Developer
                - If needs production testing → recommend QA_Engineer  
                - If performance concerns → recommend Performance_Engineer
                - If successfully deployed → COMPLETE
                
                Respond with: NEXT_AGENT: [agent_name] | REASON: [why] | CONFIDENCE: [1-10]
                Or: COMPLETE | REASON: [why this task is done]
                """
            }
        }
    
    def debug_print(self, message: str):
        """Print debug message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🧠 {message}")
    
    def parse_agent_decision(self, response: str) -> Dict:
        """Parse agent's decision from response"""
        decision = {
            'action': 'UNKNOWN',
            'next_agent': None,
            'reason': 'No decision found',
            'confidence': 5
        }
        
        # Look for decision patterns
        response_upper = response.upper()
        
        if 'COMPLETE' in response_upper:
            decision['action'] = 'COMPLETE'
            # Extract reason
            if 'REASON:' in response_upper:
                reason_part = response.split('REASON:')[1].split('|')[0].strip()
                decision['reason'] = reason_part
        
        elif 'NEXT_AGENT:' in response_upper:
            decision['action'] = 'CONTINUE'
            
            # Extract next agent
            try:
                next_agent_part = response.split('NEXT_AGENT:')[1].split('|')[0].strip()
                decision['next_agent'] = next_agent_part
            except:
                decision['next_agent'] = 'Developer'  # fallback
            
            # Extract reason
            if 'REASON:' in response_upper:
                try:
                    reason_part = response.split('REASON:')[1].split('|')[0].strip()
                    decision['reason'] = reason_part
                except:
                    decision['reason'] = 'Agent recommendation'
            
            # Extract confidence
            if 'CONFIDENCE:' in response_upper:
                try:
                    confidence_part = response.split('CONFIDENCE:')[1].split('|')[0].strip()
                    decision['confidence'] = int(confidence_part)
                except:
                    decision['confidence'] = 7
        
        return decision
        
    def debug_print(self, message: str):
        """Print debug message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🤖 {message}")
    
    async def execute_autonomous_workflow(self, request: str) -> Dict:
        """Execute a fully autonomous workflow"""
        
        print("🚀 Autonomous Multi-Agent Workflow")
        print("=" * 60)
        print(f"📝 Request: '{request}'")
        print("=" * 60)
        
        # Analyze request
        self.debug_print("Analyzing request...")
        analysis = self.decision_engine.analyze_request(request)
        
        print(f"🧠 WORKFLOW ANALYSIS:")
        print(f"   Pattern: {analysis['pattern']}")
        print(f"   Complexity: {analysis['complexity']}")
        print(f"   Agents: {' → '.join(analysis['agents'])}")
        print(f"   Scores: {analysis['scores']}")
        print()
        
        # Generate unique workflow ID
        workflow_id = f"autonomous-{int(time.time())}"
        
        # Execute workflow
        workflow_result = {
            'workflow_id': workflow_id,
            'request': request,
            'analysis': analysis,
            'agents_executed': [],
            'artifacts': [],
            'decisions': [],
            'status': 'STARTED'
        }
        
        agents = analysis['agents']
        context = request
        
        for i, agent in enumerate(agents):
            print(f"🔄 PHASE {i+1}/{len(agents)}: {agent.upper()}")
            print("-" * 40)
            
            # Execute agent
            self.debug_print(f"Executing {agent}...")
            
            try:
                result = await self.orchestrator.execute_llm_call_with_cache(
                    agent_name=agent,
                    prompt=context,
                    workflow_id=f"{workflow_id}-{i+1:03d}"
                )
                
                workflow_result['agents_executed'].append({
                    'agent': agent,
                    'phase': i+1,
                    'status': 'SUCCESS',
                    'result_length': len(result.get('response', '')),
                    'artifacts_created': result.get('artifacts_created', [])
                })
                
                # Add artifacts
                if 'artifacts_created' in result:
                    workflow_result['artifacts'].extend(result['artifacts_created'])
                
                print(f"✅ {agent} completed ({len(result.get('response', ''))} characters)")
                
                # Check if we should continue to next agent
                if i < len(agents) - 1:
                    next_agent = agents[i + 1]
                    should_continue, reason = self.decision_engine.should_continue_to_next_agent(
                        result, agent, next_agent
                    )
                    
                    decision = {
                        'from_agent': agent,
                        'to_agent': next_agent,
                        'should_continue': should_continue,
                        'reason': reason,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    workflow_result['decisions'].append(decision)
                    
                    if should_continue:
                        self.debug_print(f"✅ Continuing to {next_agent}: {reason}")
                        # Update context for next agent
                        context = f"""
                        Based on the previous work from {agent}:
                        {result.get('response', '')}
                        
                        Please continue with the next phase for the original request: {request}
                        """
                    else:
                        self.debug_print(f"❌ Stopping workflow: {reason}")
                        workflow_result['status'] = 'STOPPED'
                        break
                        
            except Exception as e:
                error_msg = f"Error executing {agent}: {str(e)}"
                self.debug_print(error_msg)
                
                workflow_result['agents_executed'].append({
                    'agent': agent,
                    'phase': i+1,
                    'status': 'ERROR',
                    'error': error_msg
                })
                
                workflow_result['status'] = 'ERROR'
                break
        
        if workflow_result['status'] == 'STARTED':
            workflow_result['status'] = 'COMPLETED'
        
        # Save workflow summary
        self.save_workflow_summary(workflow_result)
        
        # Display summary
        self.display_workflow_summary(workflow_result)
        
        return workflow_result
    
    def save_workflow_summary(self, workflow_result: Dict):
        """Save workflow summary to file"""
        summary_path = f"./workspace/{workflow_result['workflow_id']}/workflow_summary.json"
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(workflow_result, f, indent=2)
        
        self.debug_print(f"Workflow summary saved to {summary_path}")
    
    def display_workflow_summary(self, workflow_result: Dict):
        """Display workflow summary"""
        print("\n📊 AUTONOMOUS WORKFLOW SUMMARY")
        print("=" * 60)
        print(f"🆔 Workflow ID: {workflow_result['workflow_id']}")
        print(f"📝 Request: {workflow_result['request']}")
        print(f"🎯 Pattern: {workflow_result['analysis']['pattern']}")
        print(f"📊 Status: {workflow_result['status']}")
        print(f"🤖 Agents: {len(workflow_result['agents_executed'])}")
        print(f"📁 Artifacts: {len(workflow_result['artifacts'])}")
        print(f"⚖️ Decisions: {len(workflow_result['decisions'])}")
        
        print("\n🔄 EXECUTION FLOW:")
        for i, agent_result in enumerate(workflow_result['agents_executed']):
            status_icon = "✅" if agent_result['status'] == 'SUCCESS' else "❌"
            print(f"  {i+1}. {status_icon} {agent_result['agent']} - {agent_result['status']}")
            if agent_result['status'] == 'SUCCESS':
                print(f"     📊 Generated {agent_result['result_length']} characters")
                if agent_result.get('artifacts_created'):
                    print(f"     📁 Created {len(agent_result['artifacts_created'])} artifacts")
            elif agent_result['status'] == 'ERROR':
                print(f"     ❌ Error: {agent_result.get('error', 'Unknown error')}")
        
        print("\n⚖️ DECISION POINTS:")
        for decision in workflow_result['decisions']:
            icon = "✅" if decision['should_continue'] else "❌"
            print(f"  {icon} {decision['from_agent']} → {decision['to_agent']}")
            print(f"     Reason: {decision['reason']}")
        
        print("\n📁 GENERATED ARTIFACTS:")
        for artifact in workflow_result['artifacts']:
            print(f"  📄 {artifact}")
        
        print("\n🎯 Next Steps:")
        if workflow_result['status'] == 'COMPLETED':
            print("  ✅ Workflow completed successfully!")
            print("  🔄 You can now review the generated artifacts")
            print("  🚀 Ready for deployment or further development")
        elif workflow_result['status'] == 'STOPPED':
            print("  ⚠️ Workflow stopped - may need human intervention")
            print("  🔄 Consider addressing blocking issues and retrying")
        elif workflow_result['status'] == 'ERROR':
            print("  ❌ Workflow encountered errors")
            print("  🔧 Check logs and fix issues before retrying")


def main():
    """Main function to demonstrate autonomous workflow"""
    
    async def run_workflow():
        # Create workflow
        workflow = AutonomousWorkflow()
        
        # Test different types of requests
        test_requests = [
            "Create a simple calculator function",
            "Build a secure user authentication system with login and registration",
            "Analyze requirements for a task management application",
            "Create a REST API for a blog platform with tests",
            "Deploy a web application to production"
        ]
        
        print("🎮 AUTONOMOUS WORKFLOW DEMO")
        print("=" * 60)
        print("Choose a request to test:")
        for i, request in enumerate(test_requests, 1):
            print(f"{i}. {request}")
        print(f"{len(test_requests) + 1}. Custom request")
        
        try:
            choice = int(input("\nEnter your choice (1-6): "))
            
            if choice <= len(test_requests):
                request = test_requests[choice - 1]
            else:
                request = input("Enter your custom request: ")
            
            print(f"\n🚀 Processing: '{request}'")
            print("=" * 60)
            
            # Execute autonomous workflow
            result = await workflow.execute_autonomous_workflow(request)
            
            print(f"\n🎯 Workflow '{result['workflow_id']}' completed!")
            
        except KeyboardInterrupt:
            print("\n👋 Workflow interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    # Run the async workflow
    asyncio.run(run_workflow())


if __name__ == "__main__":
    main()
