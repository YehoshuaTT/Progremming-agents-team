"""
Agent Factory System
Creates and manages agent instances with standardized templates and handoff packet support
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from tools.handoff_system import HandoffPacket, TaskStatus, NextStepSuggestion

class AgentTemplate:
    """Base class for agent templates with handoff packet support"""
    
    def __init__(self, agent_name: str, role_description: str):
        self.agent_name = agent_name
        self.role_description = role_description
        self.template_path = Path(f"documentation/Agents/{agent_name}.md")
    
    def load_template(self) -> str:
        """Load the agent's template from markdown file"""
        if self.template_path.exists():
            return self.template_path.read_text()
        else:
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Get default template if file doesn't exist"""
        return f"""# {self.agent_name}

## Role
{self.role_description}

## Responsibilities
[To be defined]

## Handoff Packet Requirements
All outputs must end with a structured handoff packet in JSON format.
"""
    
    def create_prompt(self, task_description: str, context: Dict[str, Any]) -> str:
        """Create a complete prompt for the agent"""
        template = self.load_template()
        
        # Create safe context for template formatting
        safe_context = {
            "task_description": task_description,
            **context
        }
        
        # Handle template formatting safely
        try:
            prompt = template.format(**safe_context)
        except KeyError as e:
            # If there are missing placeholders, use the template as-is
            prompt = template
            # Add task description at the beginning
            prompt = f"TASK: {task_description}\n\nCONTEXT: {context}\n\n" + prompt
        
        # Add handoff packet requirements
        prompt += "\n\n" + self._get_handoff_instructions()
        
        return prompt
    
    def _get_handoff_instructions(self) -> str:
        """Get standardized handoff packet instructions"""
        return """
CRITICAL: You must end your response with a handoff packet in this exact JSON format:

```json
{
  "completed_task_id": "[your task ID]",
  "agent_name": "[your agent name]",
  "status": "SUCCESS|FAILURE|PENDING|BLOCKED",
  "artifacts_produced": ["list", "of", "files", "created"],
  "next_step_suggestion": "[appropriate suggestion from list]",
  "notes": "Detailed explanation of what was completed",
  "timestamp": "[current timestamp]",
  "dependencies_satisfied": ["list", "of", "dependencies"],
  "blocking_issues": ["list", "of", "issues", "if", "any"]
}
```

Next Step Suggestions:
- CODE_REVIEW: Code written, needs review
- IMPLEMENTATION_NEEDED: Tests written, need code
- TESTING_NEEDED: Code written, needs tests
- MERGE_APPROVED: Ready for merge
- DEPLOY_TO_STAGING: Ready for staging
- DEPLOY_TO_PRODUCTION: Ready for production
- HUMAN_APPROVAL_NEEDED: Requires human decision
- DOCUMENTATION_NEEDED: Needs documentation
- SECURITY_SCAN_NEEDED: Needs security review
- DEBUG_NEEDED: Issues found, debugging required
"""

class AgentFactory:
    """Factory for creating agent instances with proper templates"""
    
    def __init__(self):
        self.agent_configs = self._load_agent_configs()
        self.templates = {}
        self.knowledge_registry = None  # Will be injected by orchestrator
        self._initialize_templates()
    
    def _load_agent_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load agent configurations"""
        return {
            "Product_Analyst": {
                "role": "Specification Writer",
                "description": "Defines functional requirements and user stories",
                "default_next_step": "DESIGN_NEEDED"
            },
            "UX_UI_Designer": {
                "role": "User Experience Designer",
                "description": "Creates user interface designs using Mermaid.js",
                "default_next_step": "ARCHITECTURE_NEEDED"
            },
            "Architect": {
                "role": "Technical Architect",
                "description": "Creates technical architecture and system design",
                "default_next_step": "HUMAN_APPROVAL_NEEDED"
            },
            "Tester": {
                "role": "Test Engineer",
                "description": "Writes and executes automated tests following TDD",
                "default_next_step": "IMPLEMENTATION_NEEDED"
            },
            "Coder": {
                "role": "Software Developer",
                "description": "Writes clean, efficient code that passes tests",
                "default_next_step": "CODE_REVIEW"
            },
            "Code_Reviewer": {
                "role": "Code Quality Reviewer",
                "description": "Reviews code for quality, logic, and maintainability",
                "default_next_step": "SECURITY_SCAN_NEEDED"
            },
            "Security_Specialist": {
                "role": "Security Engineer",
                "description": "Identifies and mitigates security risks",
                "default_next_step": "QA_APPROVAL_NEEDED"
            },
            "QA_Guardian": {
                "role": "Quality Assurance Guardian",
                "description": "Final quality validation before deployment",
                "default_next_step": "MERGE_APPROVED"
            },
            "DevOps_Specialist": {
                "role": "DevOps Engineer",
                "description": "Manages deployment and infrastructure",
                "default_next_step": "HUMAN_APPROVAL_NEEDED"
            },
            "Technical_Writer": {
                "role": "Technical Documentation Writer",
                "description": "Creates clear user and developer documentation",
                "default_next_step": "DOCUMENTATION_COMPLETE"
            },
            "Debugger": {
                "role": "Debugging Specialist",
                "description": "Diagnoses and resolves technical issues",
                "default_next_step": "DEBUG_NEEDED"
            },
            "Git_Agent": {
                "role": "Version Control Manager",
                "description": "Manages Git operations and version control",
                "default_next_step": "MERGE_COMPLETE"
            }
        }
    
    def _initialize_templates(self):
        """Initialize agent templates"""
        for agent_name, config in self.agent_configs.items():
            self.templates[agent_name] = AgentTemplate(
                agent_name=agent_name,
                role_description=config["description"]
            )
    
    async def create_agent_prompt(self, agent_name: str, task_description: str, 
                          context: Dict[str, Any]) -> str:
        """Create a complete prompt for an agent"""
        if agent_name not in self.templates:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        template = self.templates[agent_name]
        
        # If knowledge registry is available, enrich context with agent knowledge
        if self.knowledge_registry:
            try:
                agent_knowledge = await self.knowledge_registry.generate_agent_knowledge_package(agent_name)
                
                # Add agent-specific knowledge to context
                enriched_context = {
                    **context,
                    "agent_capabilities": agent_knowledge.get("agent_identity", {}),
                    "available_tools": agent_knowledge.get("available_tools", []),
                    "workflow_participation": agent_knowledge.get("workflow_participation", []),
                    "integration_capabilities": agent_knowledge.get("integration_capabilities", []),
                    "best_practices": agent_knowledge.get("best_practices", []),
                    "collaboration_matrix": agent_knowledge.get("collaboration_matrix", {}),
                    "performance_metrics": agent_knowledge.get("performance_metrics", {})
                }
                
                return template.create_prompt(task_description, enriched_context)
                
            except Exception as e:
                # If knowledge retrieval fails, fall back to basic prompt
                print(f"Warning: Failed to retrieve agent knowledge for {agent_name}: {e}")
                return template.create_prompt(task_description, context)
        else:
            return template.create_prompt(task_description, context)
    
    def create_agent_prompt_sync(self, agent_name: str, task_description: str, 
                          context: Dict[str, Any]) -> str:
        """Create a complete prompt for an agent (synchronous version)"""
        if agent_name not in self.templates:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        template = self.templates[agent_name]
        return template.create_prompt(task_description, context)
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for an agent"""
        return self.agent_configs.get(agent_name, {})
    
    def list_available_agents(self) -> List[str]:
        """List all available agent types"""
        return list(self.agent_configs.keys())
    
    def validate_handoff_packet(self, packet_json: str) -> bool:
        """Validate that a handoff packet is properly formatted"""
        try:
            packet = json.loads(packet_json)
            required_fields = [
                "completed_task_id", "agent_name", "status", 
                "artifacts_produced", "next_step_suggestion", "notes"
            ]
            return all(field in packet for field in required_fields)
        except json.JSONDecodeError:
            return False

class AgentOrchestrationPipeline:
    """Pipeline for orchestrating agent workflows with handoff packets"""
    
    def __init__(self, agent_factory: AgentFactory):
        self.agent_factory = agent_factory
        self.active_tasks = {}
        self.completed_handoffs = []
    
    def create_agent_workflow(self, workflow_type: str, initial_context: Dict[str, Any]) -> str:
        """Create a new agent workflow"""
        workflow_id = f"WORKFLOW-{len(self.active_tasks) + 1:03d}"
        
        if workflow_type == "complex_ui_feature":
            return self._create_complex_ui_workflow(workflow_id, initial_context)
        elif workflow_type == "simple_linear_feature":
            return self._create_simple_linear_workflow(workflow_id, initial_context)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
    
    def _create_complex_ui_workflow(self, workflow_id: str, context: Dict[str, Any]) -> str:
        """Create complex UI feature workflow as defined in master document"""
        workflow = {
            "id": workflow_id,
            "type": "complex_ui_feature",
            "context": context,
            "phases": [
                {
                    "name": "planning",
                    "agents": ["Product_Analyst", "UX_UI_Designer", "Architect"],
                    "parallel": False
                },
                {
                    "name": "human_approval",
                    "agents": ["Conductor"],
                    "parallel": False
                },
                {
                    "name": "development",
                    "agents": ["Tester", "Coder"],
                    "parallel": False,
                    "repeat": True
                },
                {
                    "name": "quality_assurance",
                    "agents": ["Code_Reviewer", "Security_Specialist"],
                    "parallel": True
                },
                {
                    "name": "final_validation",
                    "agents": ["QA_Guardian"],
                    "parallel": False
                },
                {
                    "name": "deployment",
                    "agents": ["Git_Agent", "DevOps_Specialist", "Technical_Writer"],
                    "parallel": True
                }
            ],
            "current_phase": 0,
            "status": "active"
        }
        
        self.active_tasks[workflow_id] = workflow
        return workflow_id
    
    def _create_simple_linear_workflow(self, workflow_id: str, context: Dict[str, Any]) -> str:
        """Create simple linear feature workflow"""
        workflow = {
            "id": workflow_id,
            "type": "simple_linear_feature",
            "context": context,
            "phases": [
                {
                    "name": "planning",
                    "agents": ["Product_Analyst", "Architect"],
                    "parallel": False
                },
                {
                    "name": "human_approval",
                    "agents": ["Conductor"],
                    "parallel": False
                },
                {
                    "name": "tdd_development",
                    "agents": ["Tester", "Coder", "Code_Reviewer"],
                    "parallel": False
                },
                {
                    "name": "integration",
                    "agents": ["QA_Guardian", "Git_Agent"],
                    "parallel": False
                }
            ],
            "current_phase": 0,
            "status": "active"
        }
        
        self.active_tasks[workflow_id] = workflow
        return workflow_id
    
    def process_handoff(self, workflow_id: str, handoff_packet: HandoffPacket) -> Dict[str, Any]:
        """Process a handoff packet and advance workflow"""
        if workflow_id not in self.active_tasks:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        workflow = self.active_tasks[workflow_id]
        self.completed_handoffs.append(handoff_packet)
        
        # Advance workflow based on handoff packet
        result = self._advance_workflow(workflow, handoff_packet)
        
        return result
    
    def _advance_workflow(self, workflow: Dict[str, Any], handoff_packet: HandoffPacket) -> Dict[str, Any]:
        """Advance workflow based on handoff packet"""
        current_phase = workflow["phases"][workflow["current_phase"]]
        
        # Check if current phase is complete
        if self._is_phase_complete(current_phase, handoff_packet):
            workflow["current_phase"] += 1
            
            if workflow["current_phase"] >= len(workflow["phases"]):
                workflow["status"] = "complete"
                return {"status": "workflow_complete", "workflow_id": workflow["id"]}
            else:
                next_phase = workflow["phases"][workflow["current_phase"]]
                return {"status": "phase_advanced", "next_phase": next_phase["name"]}
        
        return {"status": "phase_continuing", "current_phase": current_phase["name"]}
    
    def _is_phase_complete(self, phase: Dict[str, Any], handoff_packet: HandoffPacket) -> bool:
        """Check if a phase is complete based on handoff packet"""
        # Simple logic - can be enhanced based on specific requirements
        completion_indicators = [
            NextStepSuggestion.HUMAN_APPROVAL_NEEDED,
            NextStepSuggestion.MERGE_APPROVED,
            NextStepSuggestion.DEPLOY_TO_STAGING,
            NextStepSuggestion.DEPLOY_TO_PRODUCTION
        ]
        
        return handoff_packet.next_step_suggestion in completion_indicators
    
    async def enrich_agent_template(self, agent_name: str, template_content: str) -> str:
        """Enrich an agent template with knowledge integration information"""
        if not self.knowledge_registry:
            return template_content
        
        try:
            # Get agent knowledge package
            knowledge_package = await self.knowledge_registry.generate_agent_knowledge_package(agent_name)
            
            # Create knowledge section
            knowledge_section = f"""

## 🧠 AGENT KNOWLEDGE INTEGRATION

### Available Tools
{self._format_tools_list(knowledge_package.get('available_tools', []))}

### Workflow Participation
{self._format_workflows_list(knowledge_package.get('workflow_participation', []))}

### Integration Capabilities
{self._format_integrations_list(knowledge_package.get('integration_capabilities', []))}

### Collaboration Matrix
{self._format_collaboration_matrix(knowledge_package.get('collaboration_matrix', {}))}

### Best Practices
{self._format_best_practices_list(knowledge_package.get('best_practices', []))}

### Performance Metrics
{self._format_performance_metrics(knowledge_package.get('performance_metrics', {}))}

## 🔧 TOOL USAGE GUIDELINES

Each tool you have access to comes with specific usage patterns and best practices. 
Always validate tool availability before use and follow the established patterns for consistency.

## 🤝 COLLABORATION GUIDELINES

Your role in workflows is well-defined. Always:
- Provide clear handoff information to the next agent
- Document your decisions and rationale
- Use the established communication patterns
- Validate your outputs before handoff

"""
            
            # Insert knowledge section before handoff instructions
            if "CRITICAL: You must end your response" in template_content:
                parts = template_content.split("CRITICAL: You must end your response")
                enhanced_template = parts[0] + knowledge_section + "\n\nCRITICAL: You must end your response" + parts[1]
            else:
                enhanced_template = template_content + knowledge_section
            
            return enhanced_template
            
        except Exception as e:
            print(f"Warning: Failed to enrich template for {agent_name}: {e}")
            return template_content
    
    def _format_tools_list(self, tools: List[Dict]) -> str:
        """Format tools list for template"""
        if not tools:
            return "No specific tools assigned."
        
        formatted = []
        for tool in tools:
            formatted.append(f"- **{tool['name']}**: {tool['description']}")
        return "\n".join(formatted)
    
    def _format_workflows_list(self, workflows: List[Dict]) -> str:
        """Format workflows list for template"""
        if not workflows:
            return "No specific workflows assigned."
        
        formatted = []
        for workflow in workflows:
            formatted.append(f"- **{workflow['name']}**: {workflow['description']}")
        return "\n".join(formatted)
    
    def _format_integrations_list(self, integrations: List[str]) -> str:
        """Format integrations list for template"""
        if not integrations:
            return "No specific integrations assigned."
        
        return "\n".join([f"- {integration}" for integration in integrations])
    
    def _format_collaboration_matrix(self, matrix: Dict) -> str:
        """Format collaboration matrix for template"""
        if not matrix:
            return "No collaboration information available."
        
        formatted = []
        if matrix.get('input_from'):
            formatted.append(f"**Receives input from**: {', '.join(matrix['input_from'])}")
        if matrix.get('output_to'):
            formatted.append(f"**Provides output to**: {', '.join(matrix['output_to'])}")
        if matrix.get('peer_collaboration'):
            formatted.append(f"**Collaborates with**: {', '.join(matrix['peer_collaboration'])}")
        
        return "\n".join(formatted) if formatted else "No collaboration information available."
    
    def _format_best_practices_list(self, practices: List[str]) -> str:
        """Format best practices list for template"""
        if not practices:
            return "No specific best practices defined."
        
        return "\n".join([f"- {practice}" for practice in practices])
    
    def _format_performance_metrics(self, metrics: Dict) -> str:
        """Format performance metrics for template"""
        if not metrics:
            return "No performance metrics available."
        
        formatted = []
        for key, value in metrics.items():
            if isinstance(value, float):
                formatted.append(f"- **{key.replace('_', ' ').title()}**: {value:.2f}")
            else:
                formatted.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        return "\n".join(formatted)
