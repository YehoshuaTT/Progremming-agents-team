"""
Agent Knowledge Integration System

This module provides a centralized system for ensuring all agents have access to
and knowledge of all relevant tools, workflows, and capabilities in the system.
It serves as a comprehensive knowledge registry and integration point.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import importlib.util
import sys

from .experience_database import ExperienceDatabase
from .knowledge_graph import KnowledgeGraph
from .learning_engine import AdaptiveLearningEngine
from .solutions_archive import SolutionsArchive


class CapabilityType(Enum):
    """Types of agent capabilities"""
    TOOL = "tool"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    KNOWLEDGE = "knowledge"
    PROCESS = "process"


@dataclass
class ToolCapability:
    """Represents a tool capability available to agents"""
    name: str
    description: str
    parameters: Dict[str, Any]
    usage_examples: List[str]
    compatible_agents: List[str]
    integration_points: List[str]
    performance_metrics: Dict[str, float]
    last_updated: datetime


@dataclass
class WorkflowCapability:
    """Represents a workflow capability"""
    name: str
    description: str
    workflow_type: str
    steps: List[Dict[str, Any]]
    agent_sequence: List[str]
    approval_gates: List[str]
    success_criteria: List[str]
    typical_duration: str
    complexity_level: int


@dataclass
class IntegrationCapability:
    """Represents integration capabilities between components"""
    name: str
    description: str
    components: List[str]
    data_flow: Dict[str, Any]
    api_endpoints: List[str]
    configuration: Dict[str, Any]
    monitoring_metrics: List[str]


@dataclass
class KnowledgeCapability:
    """Represents knowledge and learning capabilities"""
    name: str
    description: str
    knowledge_type: str
    data_sources: List[str]
    learning_algorithms: List[str]
    pattern_recognition: Dict[str, Any]
    recommendations: List[str]


class AgentKnowledgeRegistry:
    """
    Central registry for all agent capabilities, tools, and workflows
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.capabilities: Dict[CapabilityType, Dict[str, Any]] = {
            CapabilityType.TOOL: {},
            CapabilityType.WORKFLOW: {},
            CapabilityType.INTEGRATION: {},
            CapabilityType.KNOWLEDGE: {},
            CapabilityType.PROCESS: {}
        }
        self.agent_profiles: Dict[str, Dict[str, Any]] = {}
        self.compatibility_matrix: Dict[str, Dict[str, bool]] = {}
        self.usage_statistics: Dict[str, Dict[str, int]] = {}
        
    async def initialize(self):
        """Initialize the knowledge registry with all system capabilities"""
        await self._discover_tools()
        await self._discover_workflows()
        await self._discover_integrations()
        await self._discover_knowledge_systems()
        await self._build_agent_profiles()
        await self._build_compatibility_matrix()
        self.logger.info("Agent Knowledge Registry initialized successfully")
        
    async def _discover_tools(self):
        """Discover all available tools in the system (dynamic and static)"""
        tool_definitions = {}
        tools_dir = Path(__file__).parent
        for py_file in tools_dir.glob("*.py"):
            if py_file.name in ["__init__.py", "agent_knowledge_integration.py"]:
                continue
            module_name = f"tools.{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    if hasattr(module, "register_tool"):
                        tool_info = module.register_tool()
                        if tool_info and hasattr(tool_info, "name"):
                            tool_definitions[py_file.stem] = tool_info
            except Exception as e:
                self.logger.warning(f"Failed to load tool {py_file.name}: {e}")
        
        tool_definitions.update({
            "experience_database": ToolCapability(
                name="Experience Database",
                description="Advanced experience database for agent learning and pattern recognition",
                parameters={
                    "log_experience": ["experience: ExperienceEntry"],
                    "get_experience": ["experience_id: str"],
                    "search_experiences": ["filters: Dict", "limit: int"],
                    "get_similar_experiences": ["context: Dict", "similarity_threshold: float"],
                    "get_agent_statistics": ["agent_id: str"],
                    "get_recommendations": ["agent_id: str", "task_type: str"]
                },
                usage_examples=[
                    "await experience_db.log_experience(experience_entry)",
                    "similar = await experience_db.get_similar_experiences(context)",
                    "stats = await experience_db.get_agent_statistics('agent_001')"
                ],
                compatible_agents=["ALL"],
                integration_points=["knowledge_graph", "pattern_recognition", "learning_engine"],
                performance_metrics={"cache_hit_rate": 0.85, "avg_response_time": 0.05},
                last_updated=datetime.now()
            ),
            
            "knowledge_graph": ToolCapability(
                name="Knowledge Graph",
                description="Graph-based knowledge representation and semantic search",
                parameters={
                    "add_node": ["node_id: str", "node_type: str", "properties: Dict"],
                    "add_edge": ["source: str", "target: str", "relationship: str"],
                    "query_nodes": ["query: str", "filters: Dict"],
                    "find_path": ["start: str", "end: str"],
                    "get_neighbors": ["node_id: str", "relationship_type: str"],
                    "find_similar_nodes": ["node_id: str", "similarity_threshold: float"]
                },
                usage_examples=[
                    "await kg.add_node('solution_001', 'solution', properties)",
                    "path = await kg.find_path('problem_001', 'solution_001')",
                    "similar = await kg.find_similar_nodes('concept_001', 0.8)"
                ],
                compatible_agents=["ALL"],
                integration_points=["experience_database", "solutions_archive", "learning_engine"],
                performance_metrics={"query_time": 0.02, "accuracy": 0.92},
                last_updated=datetime.now()
            ),
            
            "learning_engine": ToolCapability(
                name="Adaptive Learning Engine",
                description="AI-powered learning and adaptation system",
                parameters={
                    "learn_from_experience": ["experience_data: Dict"],
                    "get_adaptive_strategy": ["context: Dict"],
                    "optimize_performance": ["objective: LearningObjective"],
                    "predict_outcome": ["planned_action: Dict"],
                    "get_learning_dashboard": []
                },
                usage_examples=[
                    "result = await learning_engine.learn_from_experience(experience)",
                    "strategy = await learning_engine.get_adaptive_strategy(context)",
                    "prediction = await learning_engine.predict_outcome(action)"
                ],
                compatible_agents=["ALL"],
                integration_points=["experience_database", "knowledge_graph", "pattern_recognition"],
                performance_metrics={"prediction_accuracy": 0.87, "learning_rate": 0.15},
                last_updated=datetime.now()
            ),
            
            "solutions_archive": ToolCapability(
                name="Solutions Archive",
                description="Persistent knowledge base with semantic search capabilities",
                parameters={
                    "archive_solution": ["solution: Dict"],
                    "search_solutions": ["query: str", "filters: Dict"],
                    "get_solution": ["solution_id: str"],
                    "find_similar_solutions": ["solution: Dict", "threshold: float"],
                    "rate_solution": ["solution_id: str", "rating: float", "feedback: str"]
                },
                usage_examples=[
                    "await archive.archive_solution(solution_data)",
                    "results = await archive.search_solutions('authentication')",
                    "similar = await archive.find_similar_solutions(current_solution)"
                ],
                compatible_agents=["ALL"],
                integration_points=["knowledge_graph", "experience_database"],
                performance_metrics={"search_accuracy": 0.89, "retrieval_time": 0.03},
                last_updated=datetime.now()
            ),
            
            "handoff_system": ToolCapability(
                name="Intelligent Handoff System",
                description="Context-aware routing and task handoff between agents",
                parameters={
                    "process_handoff": ["handoff_packet: HandoffPacket"],
                    "route_to_agent": ["task: Dict", "context: Dict"],
                    "get_next_agent": ["current_agent: str", "task_type: str"],
                    "resolve_blocking_issue": ["issue: Dict"],
                    "get_workflow_state": ["workflow_id: str"]
                },
                usage_examples=[
                    "next_agent = await handoff.get_next_agent('Coder', 'testing')",
                    "result = await handoff.process_handoff(packet)",
                    "state = await handoff.get_workflow_state(workflow_id)"
                ],
                compatible_agents=["ALL"],
                integration_points=["orchestrator", "caching_system", "error_handling"],
                performance_metrics={"routing_accuracy": 0.94, "handoff_time": 0.08},
                last_updated=datetime.now()
            ),
            
            "security_framework": ToolCapability(
                name="Security Framework",
                description="Comprehensive security validation and enforcement",
                parameters={
                    "validate_command": ["command: str"],
                    "validate_file_path": ["path: str", "operation: str"],
                    "validate_network_request": ["url: str"],
                    "log_security_event": ["event: Dict"],
                    "get_security_report": []
                },
                usage_examples=[
                    "is_safe = await security.validate_command('rm -rf /')",
                    "is_allowed = await security.validate_file_path('/etc/passwd', 'read')",
                    "report = await security.get_security_report()"
                ],
                compatible_agents=["ALL"],
                integration_points=["file_tools", "execution_tools", "git_tools"],
                performance_metrics={"threat_detection": 0.98, "false_positive_rate": 0.02},
                last_updated=datetime.now()
            ),
            
            "caching_system": ToolCapability(
                name="Multi-Level Caching System",
                description="Intelligent caching for LLM responses, tools, and handoffs",
                parameters={
                    "get_cached_response": ["key: str"],
                    "cache_response": ["key: str", "value: Any", "ttl: int"],
                    "invalidate_cache": ["pattern: str"],
                    "get_cache_stats": [],
                    "clear_expired_entries": []
                },
                usage_examples=[
                    "cached = await cache.get_cached_response(cache_key)",
                    "await cache.cache_response(key, response, 3600)",
                    "stats = await cache.get_cache_stats()"
                ],
                compatible_agents=["ALL"],
                integration_points=["handoff_system", "tools", "context_optimization"],
                performance_metrics={"hit_rate": 0.78, "memory_efficiency": 0.85},
                last_updated=datetime.now()
            ),
            
            "context_optimization": ToolCapability(
                name="Context Optimization System",
                description="Intelligent context summarization and token management",
                parameters={
                    "optimize_context": ["context: str", "target_tokens: int"],
                    "generate_summary": ["document: str"],
                    "extract_sections": ["document: str", "section_ids: List"],
                    "estimate_tokens": ["text: str"],
                    "get_section_context": ["doc_path: str", "section_id: str"]
                },
                usage_examples=[
                    "optimized = await context.optimize_context(large_context, 2000)",
                    "summary = await context.generate_summary(document)",
                    "tokens = await context.estimate_tokens(text)"
                ],
                compatible_agents=["ALL"],
                integration_points=["document_processing", "caching_system"],
                performance_metrics={"compression_ratio": 0.7, "accuracy_retention": 0.92},
                last_updated=datetime.now()
            ),
            
            "error_handling": ToolCapability(
                name="Advanced Error Handling System",
                description="Error classification, recovery, and checkpoint management",
                parameters={
                    "classify_error": ["error: Exception"],
                    "create_checkpoint": ["workflow_id: str", "state: Dict"],
                    "recover_from_error": ["error_type: str", "context: Dict"],
                    "get_retry_strategy": ["error_type: str"],
                    "log_error_metrics": ["error: Dict"]
                },
                usage_examples=[
                    "error_type = await error_handler.classify_error(exception)",
                    "checkpoint = await error_handler.create_checkpoint(wf_id, state)",
                    "strategy = await error_handler.get_retry_strategy('network_error')"
                ],
                compatible_agents=["ALL"],
                integration_points=["orchestrator", "checkpoint_system", "logging"],
                performance_metrics={"recovery_rate": 0.89, "error_classification_accuracy": 0.93},
                last_updated=datetime.now()
            )
        })
        self.capabilities[CapabilityType.TOOL] = tool_definitions
        
    async def _discover_workflows(self):
        """Discover all available workflows in the system"""
        workflow_definitions = {
            "complex_ui_feature": WorkflowCapability(
                name="Complex UI Feature Development",
                description="End-to-end feature development with full testing and deployment",
                workflow_type="complex_ui_feature",
                steps=[
                    {"step": 1, "agent": "Product_Analyst", "task": "Requirements analysis and specification"},
                    {"step": 2, "agent": "Architect", "task": "System design and architecture"},
                    {"step": 3, "agent": "Coder", "task": "Implementation"},
                    {"step": 4, "agent": "Code_Reviewer", "task": "Code quality review"},
                    {"step": 5, "agent": "Security_Specialist", "task": "Security analysis"},
                    {"step": 6, "agent": "QA_Guardian", "task": "Testing and validation"},
                    {"step": 7, "agent": "Technical_Writer", "task": "Documentation"},
                    {"step": 8, "agent": "DevOps_Specialist", "task": "Deployment"}
                ],
                agent_sequence=["Product_Analyst", "Architect", "Coder", "Code_Reviewer", "Security_Specialist", "QA_Guardian", "Technical_Writer", "DevOps_Specialist"],
                approval_gates=["after_architecture", "before_deployment"],
                success_criteria=["All tests passing", "Security scan clean", "Documentation complete"],
                typical_duration="2-4 hours",
                complexity_level=8
            ),
            
            "bug_fix": WorkflowCapability(
                name="Bug Fix Workflow",
                description="Systematic issue resolution with root cause analysis",
                workflow_type="bug_fix",
                steps=[
                    {"step": 1, "agent": "Debugger", "task": "Issue analysis and diagnosis"},
                    {"step": 2, "agent": "Debugger", "task": "Root cause investigation"},
                    {"step": 3, "agent": "Coder", "task": "Fix implementation"},
                    {"step": 4, "agent": "Code_Reviewer", "task": "Review fix"},
                    {"step": 5, "agent": "QA_Guardian", "task": "Testing"},
                    {"step": 6, "agent": "DevOps_Specialist", "task": "Deployment"}
                ],
                agent_sequence=["Debugger", "Coder", "Code_Reviewer", "QA_Guardian", "DevOps_Specialist"],
                approval_gates=["before_deployment"],
                success_criteria=["Bug reproduced and fixed", "Tests passing", "No regression"],
                typical_duration="30-90 minutes",
                complexity_level=5
            ),
            
            "security_update": WorkflowCapability(
                name="Security Update Workflow",
                description="Security patches and system hardening",
                workflow_type="security_update",
                steps=[
                    {"step": 1, "agent": "Security_Specialist", "task": "Security analysis"},
                    {"step": 2, "agent": "Architect", "task": "Impact assessment"},
                    {"step": 3, "agent": "Coder", "task": "Security fix implementation"},
                    {"step": 4, "agent": "Security_Specialist", "task": "Security review"},
                    {"step": 5, "agent": "QA_Guardian", "task": "Security testing"},
                    {"step": 6, "agent": "DevOps_Specialist", "task": "Secure deployment"}
                ],
                agent_sequence=["Security_Specialist", "Architect", "Coder", "Security_Specialist", "QA_Guardian", "DevOps_Specialist"],
                approval_gates=["after_security_analysis", "before_deployment"],
                success_criteria=["Security vulnerability fixed", "No new vulnerabilities", "Security tests passing"],
                typical_duration="1-3 hours",
                complexity_level=7
            ),
            
            "performance_optimization": WorkflowCapability(
                name="Performance Optimization Workflow",
                description="System performance improvements and optimization",
                workflow_type="performance_optimization",
                steps=[
                    {"step": 1, "agent": "Architect", "task": "Performance analysis"},
                    {"step": 2, "agent": "Coder", "task": "Optimization implementation"},
                    {"step": 3, "agent": "QA_Guardian", "task": "Performance testing"},
                    {"step": 4, "agent": "Code_Reviewer", "task": "Code review"},
                    {"step": 5, "agent": "DevOps_Specialist", "task": "Deployment and monitoring"}
                ],
                agent_sequence=["Architect", "Coder", "QA_Guardian", "Code_Reviewer", "DevOps_Specialist"],
                approval_gates=["after_analysis", "before_deployment"],
                success_criteria=["Performance metrics improved", "No functionality regression", "Monitoring in place"],
                typical_duration="1-2 hours",
                complexity_level=6
            ),
            
            "ui_ux_design": WorkflowCapability(
                name="UI/UX Design Workflow",
                description="User interface and experience design process",
                workflow_type="ui_ux_design",
                steps=[
                    {"step": 1, "agent": "Product_Analyst", "task": "User requirements analysis"},
                    {"step": 2, "agent": "UX_UI_Designer", "task": "User research and analysis"},
                    {"step": 3, "agent": "UX_UI_Designer", "task": "Wireframing and prototyping"},
                    {"step": 4, "agent": "UX_UI_Designer", "task": "Design validation"},
                    {"step": 5, "agent": "Coder", "task": "UI implementation"},
                    {"step": 6, "agent": "Tester", "task": "User experience testing"}
                ],
                agent_sequence=["Product_Analyst", "UX_UI_Designer", "Coder", "Tester"],
                approval_gates=["after_design", "after_implementation"],
                success_criteria=["User-friendly design", "Accessibility compliance", "Positive user feedback"],
                typical_duration="2-3 hours",
                complexity_level=7
            ),
            
            "testing_workflow": WorkflowCapability(
                name="Comprehensive Testing Workflow",
                description="Complete testing strategy and execution",
                workflow_type="testing_workflow",
                steps=[
                    {"step": 1, "agent": "Tester", "task": "Test strategy planning"},
                    {"step": 2, "agent": "Tester", "task": "Test case development"},
                    {"step": 3, "agent": "Tester", "task": "Automated test implementation"},
                    {"step": 4, "agent": "Tester", "task": "Test execution"},
                    {"step": 5, "agent": "QA_Guardian", "task": "Quality validation"},
                    {"step": 6, "agent": "Debugger", "task": "Issue investigation"}
                ],
                agent_sequence=["Tester", "QA_Guardian", "Debugger"],
                approval_gates=["after_test_planning", "after_execution"],
                success_criteria=["All tests passing", "Coverage requirements met", "Quality standards satisfied"],
                typical_duration="1-2 hours",
                complexity_level=6
            ),
            
            "version_control_workflow": WorkflowCapability(
                name="Version Control and Release Management",
                description="Git operations and release management workflow",
                workflow_type="version_control_workflow",
                steps=[
                    {"step": 1, "agent": "Git_Agent", "task": "Branch management"},
                    {"step": 2, "agent": "Git_Agent", "task": "Code integration"},
                    {"step": 3, "agent": "Code_Reviewer", "task": "Pull request review"},
                    {"step": 4, "agent": "Git_Agent", "task": "Merge and tagging"},
                    {"step": 5, "agent": "DevOps_Specialist", "task": "Release deployment"}
                ],
                agent_sequence=["Git_Agent", "Code_Reviewer", "DevOps_Specialist"],
                approval_gates=["before_merge", "before_release"],
                success_criteria=["Clean merge", "No conflicts", "Successful deployment"],
                typical_duration="30-60 minutes",
                complexity_level=4
            ),
            
            "documentation_workflow": WorkflowCapability(
                name="Documentation Creation and Maintenance",
                description="Comprehensive documentation workflow",
                workflow_type="documentation_workflow",
                steps=[
                    {"step": 1, "agent": "Technical_Writer", "task": "Documentation planning"},
                    {"step": 2, "agent": "Technical_Writer", "task": "Content creation"},
                    {"step": 3, "agent": "Technical_Writer", "task": "Review and editing"},
                    {"step": 4, "agent": "Product_Analyst", "task": "Content validation"}
                ],
                agent_sequence=["Technical_Writer", "Product_Analyst"],
                approval_gates=["after_planning", "before_publishing"],
                success_criteria=["Complete documentation", "Accuracy verified", "User-friendly format"],
                typical_duration="1-2 hours",
                complexity_level=3
            ),
            
            "information_workflow": WorkflowCapability(
                name="Information Retrieval and Guidance",
                description="Knowledge search and guidance provision workflow",
                workflow_type="information_workflow",
                steps=[
                    {"step": 1, "agent": "Ask_Agent", "task": "Query analysis"},
                    {"step": 2, "agent": "Ask_Agent", "task": "Information search"},
                    {"step": 3, "agent": "Ask_Agent", "task": "Response compilation"},
                    {"step": 4, "agent": "Ask_Agent", "task": "Guidance provision"}
                ],
                agent_sequence=["Ask_Agent"],
                approval_gates=[],
                success_criteria=["Accurate information", "Relevant guidance", "Clear response"],
                typical_duration="5-15 minutes",
                complexity_level=2
            ),
            
            "guidance_workflow": WorkflowCapability(
                name="Expert Consultation and Guidance",
                description="Expert consultation and decision support workflow",
                workflow_type="guidance_workflow",
                steps=[
                    {"step": 1, "agent": "Ask_Agent", "task": "Problem analysis"},
                    {"step": 2, "agent": "Ask_Agent", "task": "Expert consultation"},
                    {"step": 3, "agent": "Ask_Agent", "task": "Recommendation formulation"},
                    {"step": 4, "agent": "Ask_Agent", "task": "Guidance delivery"}
                ],
                agent_sequence=["Ask_Agent"],
                approval_gates=[],
                success_criteria=["Expert-level guidance", "Actionable recommendations", "Clear direction"],
                typical_duration="10-30 minutes",
                complexity_level=3
            )
        }
        
        self.capabilities[CapabilityType.WORKFLOW] = workflow_definitions
        
    async def _discover_integrations(self):
        """Discover integration capabilities between system components"""
        integration_definitions = {
            "experience_knowledge_graph": IntegrationCapability(
                name="Experience Database + Knowledge Graph Integration",
                description="Seamless integration between experience logging and knowledge representation",
                components=["experience_database", "knowledge_graph"],
                data_flow={
                    "experience_to_graph": "Experience entries automatically create knowledge graph nodes",
                    "pattern_to_graph": "Recognized patterns become graph relationships",
                    "similarity_queries": "Cross-system similarity searches"
                },
                api_endpoints=["/api/experience/graph", "/api/graph/experience"],
                configuration={"auto_sync": True, "similarity_threshold": 0.8},
                monitoring_metrics=["sync_rate", "query_performance", "data_consistency"]
            ),
            
            "learning_pattern_recognition": IntegrationCapability(
                name="Learning Engine + Pattern Recognition Integration",
                description="AI-powered learning enhanced by advanced pattern recognition",
                components=["learning_engine", "pattern_recognition"],
                data_flow={
                    "patterns_to_learning": "Detected patterns feed into learning algorithms",
                    "learning_to_patterns": "Learning insights improve pattern detection",
                    "feedback_loop": "Continuous improvement through pattern-learning feedback"
                },
                api_endpoints=["/api/learning/patterns", "/api/patterns/learning"],
                configuration={"feedback_enabled": True, "learning_rate": 0.1},
                monitoring_metrics=["pattern_accuracy", "learning_effectiveness", "feedback_quality"]
            ),
            
            "caching_optimization": IntegrationCapability(
                name="Multi-Level Caching Integration",
                description="Comprehensive caching across all system components",
                components=["llm_cache", "tool_cache", "handoff_cache", "context_optimization"],
                data_flow={
                    "layered_caching": "Multiple cache levels with intelligent eviction",
                    "context_aware": "Cache keys include context information",
                    "invalidation_cascade": "Smart cache invalidation across levels"
                },
                api_endpoints=["/api/cache/status", "/api/cache/invalidate"],
                configuration={"ttl_default": 3600, "max_memory": "1GB", "compression": True},
                monitoring_metrics=["hit_rate", "memory_usage", "eviction_rate"]
            )
        }
        
        self.capabilities[CapabilityType.INTEGRATION] = integration_definitions
        
    async def _discover_knowledge_systems(self):
        """Discover knowledge and learning capabilities"""
        knowledge_definitions = {
            "pattern_recognition": KnowledgeCapability(
                name="Advanced Pattern Recognition",
                description="ML-based pattern detection and analysis in agent experiences",
                knowledge_type="pattern_analysis",
                data_sources=["experience_database", "solutions_archive", "workflow_history"],
                learning_algorithms=["DBSCAN clustering", "TF-IDF vectorization", "Cosine similarity"],
                pattern_recognition={
                    "success_patterns": "Identification of successful approaches",
                    "anti_patterns": "Detection of failure patterns",
                    "optimization_opportunities": "Performance improvement suggestions"
                },
                recommendations=["Use modular approaches", "Avoid monolithic designs", "Implement caching"]
            ),
            
            "adaptive_learning": KnowledgeCapability(
                name="Adaptive Learning System",
                description="AI-powered continuous learning and improvement",
                knowledge_type="adaptive_learning",
                data_sources=["all_agent_interactions", "performance_metrics", "outcome_data"],
                learning_algorithms=["Random Forest", "Gradient Boosting", "Neural Networks"],
                pattern_recognition={
                    "performance_prediction": "Predict task success probability",
                    "strategy_optimization": "Optimize agent strategies",
                    "outcome_forecasting": "Forecast project outcomes"
                },
                recommendations=["Context-aware strategies", "Performance optimization", "Risk mitigation"]
            ),
            
            "semantic_search": KnowledgeCapability(
                name="Semantic Search and Retrieval",
                description="Intelligent search across all system knowledge",
                knowledge_type="semantic_retrieval",
                data_sources=["solutions_archive", "documentation", "code_repositories"],
                learning_algorithms=["Vector embeddings", "Semantic similarity", "Relevance ranking"],
                pattern_recognition={
                    "concept_similarity": "Find related concepts and solutions",
                    "code_patterns": "Identify reusable code patterns",
                    "documentation_gaps": "Detect missing documentation"
                },
                recommendations=["Reuse existing solutions", "Fill documentation gaps", "Extract common patterns"]
            )
        }
        
        self.capabilities[CapabilityType.KNOWLEDGE] = knowledge_definitions
        
    async def _build_agent_profiles(self):
        """Build comprehensive profiles for each agent"""
        agent_definitions = {
            "Product_Analyst": {
                "primary_role": "Requirements analysis and specification creation",
                "capabilities": ["requirements_gathering", "stakeholder_analysis", "specification_writing", "user_story_creation", "acceptance_criteria"],
                "tools": ["document_analysis", "user_story_creation", "acceptance_criteria", "requirements_validation", "stakeholder_communication"],
                "integrates_with": ["Architect", "UX_UI_Designer", "Technical_Writer"],
                "workflow_participation": ["complex_ui_feature", "performance_optimization", "simple_linear_feature"],
                "knowledge_access": ["domain_knowledge", "user_requirements", "market_research", "business_processes"]
            },
            
            "Architect": {
                "primary_role": "System design and technical architecture",
                "capabilities": ["system_design", "architecture_patterns", "technology_selection", "scalability_planning", "integration_design"],
                "tools": ["design_patterns", "architecture_documentation", "technology_assessment", "system_modeling", "performance_analysis"],
                "integrates_with": ["Product_Analyst", "Coder", "DevOps_Specialist", "Security_Specialist"],
                "workflow_participation": ["complex_ui_feature", "security_update", "performance_optimization", "system_architecture"],
                "knowledge_access": ["architecture_patterns", "best_practices", "technology_trends", "scalability_strategies"]
            },
            
            "Coder": {
                "primary_role": "Code implementation and development",
                "capabilities": ["code_writing", "algorithm_implementation", "debugging", "refactoring", "optimization"],
                "tools": ["development_frameworks", "code_generation", "testing_tools", "debugging_tools", "version_control"],
                "integrates_with": ["Architect", "Code_Reviewer", "QA_Guardian", "Tester"],
                "workflow_participation": ["complex_ui_feature", "bug_fix", "security_update", "performance_optimization"],
                "knowledge_access": ["code_patterns", "implementation_examples", "api_documentation", "coding_standards"]
            },
            
            "Code_Reviewer": {
                "primary_role": "Code quality and security review",
                "capabilities": ["code_analysis", "security_review", "quality_assessment"],
                "tools": ["static_analysis", "security_scanning", "code_metrics"],
                "integrates_with": ["Coder", "Security_Specialist", "QA_Guardian"],
                "workflow_participation": ["complex_ui_feature", "bug_fix", "security_update", "performance_optimization"],
                "knowledge_access": ["coding_standards", "security_guidelines", "quality_metrics"]
            },
            
            "QA_Guardian": {
                "primary_role": "Testing and quality assurance",
                "capabilities": ["test_design", "test_execution", "quality_validation"],
                "tools": ["testing_frameworks", "test_automation", "quality_metrics"],
                "integrates_with": ["Coder", "Code_Reviewer", "DevOps_Specialist"],
                "workflow_participation": ["complex_ui_feature", "bug_fix", "security_update", "performance_optimization"],
                "knowledge_access": ["testing_strategies", "quality_standards", "test_patterns"]
            },
            
            "DevOps_Specialist": {
                "primary_role": "Deployment and infrastructure",
                "capabilities": ["deployment_automation", "infrastructure_management", "monitoring"],
                "tools": ["ci_cd_pipelines", "infrastructure_as_code", "monitoring_systems"],
                "integrates_with": ["Architect", "Security_Specialist", "QA_Guardian"],
                "workflow_participation": ["complex_ui_feature", "bug_fix", "security_update", "performance_optimization"],
                "knowledge_access": ["deployment_patterns", "infrastructure_best_practices", "monitoring_strategies"]
            },
            
            "Technical_Writer": {
                "primary_role": "Documentation and knowledge management",
                "capabilities": ["documentation_writing", "knowledge_organization", "user_guides"],
                "tools": ["documentation_generators", "knowledge_bases", "content_management"],
                "integrates_with": ["Product_Analyst", "Architect", "Coder"],
                "workflow_participation": ["complex_ui_feature", "documentation_workflow"],
                "knowledge_access": ["documentation_standards", "technical_writing", "knowledge_organization"]
            },
            
            "Security_Specialist": {
                "primary_role": "Security analysis and hardening",
                "capabilities": ["security_analysis", "vulnerability_assessment", "security_hardening"],
                "tools": ["security_scanners", "vulnerability_databases", "security_frameworks"],
                "integrates_with": ["Code_Reviewer", "Architect", "DevOps_Specialist"],
                "workflow_participation": ["complex_ui_feature", "security_update", "security_audit"],
                "knowledge_access": ["security_standards", "threat_intelligence", "security_patterns"]
            },
            
            "Debugger": {
                "primary_role": "Issue diagnosis and resolution",
                "capabilities": ["problem_diagnosis", "root_cause_analysis", "troubleshooting", "log_analysis", "performance_debugging"],
                "tools": ["debugging_tools", "log_analysis", "performance_profiling", "diagnostic_tools", "monitoring_systems"],
                "integrates_with": ["Coder", "QA_Guardian", "DevOps_Specialist"],
                "workflow_participation": ["bug_fix", "performance_optimization", "testing_workflow"],
                "knowledge_access": ["debugging_strategies", "common_issues", "diagnostic_techniques", "troubleshooting_guides"]
            },
            
            "UX_UI_Designer": {
                "primary_role": "User experience and interface design",
                "capabilities": ["ui_design", "ux_research", "wireframing", "prototyping", "user_flow_design"],
                "tools": ["design_tools", "wireframing_tools", "prototyping_frameworks", "user_testing", "design_systems"],
                "integrates_with": ["Product_Analyst", "Architect", "Coder"],
                "workflow_participation": ["complex_ui_feature", "ui_ux_design", "user_experience_optimization"],
                "knowledge_access": ["design_patterns", "user_experience_best_practices", "accessibility_guidelines", "design_systems"]
            },
            
            "Tester": {
                "primary_role": "Test development and quality assurance",
                "capabilities": ["test_design", "test_automation", "quality_validation", "test_strategy", "bug_detection"],
                "tools": ["testing_frameworks", "test_automation_tools", "quality_metrics", "bug_tracking", "performance_testing"],
                "integrates_with": ["Coder", "QA_Guardian", "Code_Reviewer"],
                "workflow_participation": ["complex_ui_feature", "bug_fix", "testing_workflow", "ui_ux_design"],
                "knowledge_access": ["testing_strategies", "quality_standards", "test_patterns", "automation_best_practices"]
            },
            
            "Git_Agent": {
                "primary_role": "Version control and code management",
                "capabilities": ["version_control", "branch_management", "merge_management", "code_history", "collaboration_workflows"],
                "tools": ["git_operations", "branch_management", "merge_tools", "version_tracking", "collaboration_tools"],
                "integrates_with": ["Coder", "Code_Reviewer", "DevOps_Specialist"],
                "workflow_participation": ["complex_ui_feature", "bug_fix", "version_control_workflow"],
                "knowledge_access": ["git_workflows", "branching_strategies", "merge_strategies", "collaboration_patterns"]
            },
            
            "Ask_Agent": {
                "primary_role": "Information and guidance provider",
                "capabilities": ["question_answering", "information_retrieval", "guidance_provision", "knowledge_search", "expert_consultation"],
                "tools": ["knowledge_search", "documentation_access", "expert_systems", "information_retrieval", "guidance_systems"],
                "integrates_with": ["ALL"],
                "workflow_participation": ["information_workflow", "guidance_workflow"],
                "knowledge_access": ["comprehensive_knowledge_base", "documentation", "best_practices", "expert_knowledge"]
            }
        }
        
        self.agent_profiles = agent_definitions
        
    async def _build_compatibility_matrix(self):
        """Build compatibility matrix between agents, tools, and workflows"""
        # Tool compatibility matrix
        tools = list(self.capabilities[CapabilityType.TOOL].keys())
        agents = list(self.agent_profiles.keys())
        
        for agent in agents:
            self.compatibility_matrix[agent] = {}
            for tool in tools:
                # All agents can use all tools (designed for universal access)
                self.compatibility_matrix[agent][tool] = True
                
    async def get_agent_capabilities(self, agent_name: str) -> Dict[str, Any]:
        """Get comprehensive capabilities for a specific agent"""
        if agent_name not in self.agent_profiles:
            return {}
            
        profile = self.agent_profiles[agent_name]
        
        # Get available tools
        available_tools = []
        for tool_name, tool_info in self.capabilities[CapabilityType.TOOL].items():
            if agent_name in tool_info.compatible_agents or "ALL" in tool_info.compatible_agents:
                available_tools.append({
                    "name": tool_name,
                    "description": tool_info.description,
                    "usage_examples": tool_info.usage_examples
                })
                
        # Get available workflows
        available_workflows = []
        for workflow_name, workflow_info in self.capabilities[CapabilityType.WORKFLOW].items():
            if agent_name in workflow_info.agent_sequence:
                available_workflows.append({
                    "name": workflow_name,
                    "description": workflow_info.description,
                    "role_in_workflow": f"Step {workflow_info.agent_sequence.index(agent_name) + 1}"
                })
                
        return {
            "agent_profile": profile,
            "available_tools": available_tools,
            "available_workflows": available_workflows,
            "integration_points": self._get_agent_integrations(agent_name),
            "knowledge_access": self._get_agent_knowledge_access(agent_name)
        }
        
    async def get_workflow_requirements(self, workflow_type: str) -> Dict[str, Any]:
        """Get comprehensive requirements for a specific workflow"""
        if workflow_type not in self.capabilities[CapabilityType.WORKFLOW]:
            # Return default workflow requirements for unknown types
            return {
                "workflow_info": {
                    "name": f"Default {workflow_type}",
                    "description": f"Default workflow for {workflow_type}",
                    "workflow_type": workflow_type,
                    "steps": [
                        {"step": 1, "agent": "Product_Analyst", "task": "Requirements analysis"},
                        {"step": 2, "agent": "Coder", "task": "Implementation"},
                        {"step": 3, "agent": "Code_Reviewer", "task": "Code review"}
                    ],
                    "agent_sequence": ["Product_Analyst", "Coder", "Code_Reviewer"],
                    "approval_gates": ["after_requirements"],
                    "success_criteria": ["Requirements met", "Code quality standards met"],
                    "typical_duration": "2-4 hours",
                    "complexity_level": 5
                },
                "required_agents": ["Product_Analyst", "Coder", "Code_Reviewer"],
                "required_tools": ["file_tools", "git_tools", "execution_tools"],
                "integration_requirements": [],
                "success_criteria": ["Requirements met", "Code quality standards met"],
                "approval_gates": ["after_requirements"]
            }
            
        workflow = self.capabilities[CapabilityType.WORKFLOW][workflow_type]
        
        # Get required tools for this workflow
        required_tools = set()
        for agent_name in workflow.agent_sequence:
            agent_tools = await self.get_agent_tools(agent_name)
            required_tools.update(agent_tools)
            
        return {
            "workflow_info": asdict(workflow),
            "required_agents": workflow.agent_sequence,
            "required_tools": list(required_tools),
            "integration_requirements": self._get_workflow_integrations(workflow_type),
            "success_criteria": workflow.success_criteria,
            "approval_gates": workflow.approval_gates
        }
        
    async def get_agent_tools(self, agent_name: str) -> List[str]:
        """Get list of tools available to a specific agent"""
        tools = []
        for tool_name, tool_info in self.capabilities[CapabilityType.TOOL].items():
            if agent_name in tool_info.compatible_agents or "ALL" in tool_info.compatible_agents:
                tools.append(tool_name)
        return tools
        
    async def generate_agent_knowledge_package(self, agent_name: str) -> Dict[str, Any]:
        """Generate comprehensive knowledge package for an agent"""
        capabilities = await self.get_agent_capabilities(agent_name)
        
        knowledge_package = {
            "agent_identity": {
                "name": agent_name,
                "role": capabilities["agent_profile"]["primary_role"],
                "specialization": capabilities["agent_profile"]["capabilities"]
            },
            "available_tools": capabilities["available_tools"],
            "workflow_participation": capabilities["available_workflows"],
            "integration_capabilities": capabilities["integration_points"],
            "knowledge_access": capabilities["knowledge_access"],
            "collaboration_matrix": self._get_collaboration_info(agent_name),
            "best_practices": await self._get_agent_best_practices(agent_name),
            "performance_metrics": await self._get_agent_performance_metrics(agent_name)
        }
        
        return knowledge_package
        
    async def validate_agent_knowledge(self, agent_name: str) -> Dict[str, Any]:
        """Validate that an agent has access to all necessary tools and knowledge"""
        validation_results = {
            "agent_name": agent_name,
            "validation_timestamp": datetime.now(),
            "tools_accessible": True,
            "workflows_understood": True,
            "integrations_functional": True,
            "knowledge_current": True,
            "issues": []
        }
        
        # Validate tool access
        expected_tools = await self.get_agent_tools(agent_name)
        for tool in expected_tools:
            if not self._validate_tool_access(agent_name, tool):
                validation_results["tools_accessible"] = False
                validation_results["issues"].append(f"Cannot access tool: {tool}")
                
        # Validate workflow knowledge
        agent_workflows = [w for w in self.capabilities[CapabilityType.WORKFLOW].values() 
                          if agent_name in w.agent_sequence]
        for workflow in agent_workflows:
            if not self._validate_workflow_knowledge(agent_name, workflow.workflow_type):
                validation_results["workflows_understood"] = False
                validation_results["issues"].append(f"Workflow knowledge incomplete: {workflow.name}")
                
        return validation_results
        
    def _get_agent_integrations(self, agent_name: str) -> List[str]:
        """Get integration points for an agent"""
        integrations = []
        for integration_name, integration_info in self.capabilities[CapabilityType.INTEGRATION].items():
            # Check if any of the agent's tools are part of this integration
            agent_tools = self.agent_profiles[agent_name].get("tools", [])
            if any(tool in integration_info.components for tool in agent_tools):
                integrations.append(integration_name)
        return integrations
        
    def _get_agent_knowledge_access(self, agent_name: str) -> List[str]:
        """Get knowledge systems accessible to an agent"""
        if agent_name in self.agent_profiles:
            return self.agent_profiles[agent_name].get("knowledge_access", [])
        return []
        
    def _get_workflow_integrations(self, workflow_type: str) -> List[str]:
        """Get integration requirements for a workflow"""
        integrations = []
        if workflow_type in self.capabilities[CapabilityType.WORKFLOW]:
            workflow = self.capabilities[CapabilityType.WORKFLOW][workflow_type]
            # All workflows require core integrations
            integrations = ["experience_knowledge_graph", "caching_optimization", "error_handling"]
            
            # Add workflow-specific integrations
            if "Security" in workflow.name:
                integrations.append("security_integration")
            if "Performance" in workflow.name:
                integrations.append("performance_monitoring")
                
        return integrations
        
    def _get_collaboration_info(self, agent_name: str) -> Dict[str, List[str]]:
        """Get collaboration information for an agent"""
        collaboration = {"input_from": [], "output_to": [], "peer_collaboration": []}
        
        if agent_name in self.agent_profiles:
            integrates_with = self.agent_profiles[agent_name].get("integrates_with", [])
            collaboration["peer_collaboration"] = integrates_with
            
            # Determine input/output relationships based on workflows
            for workflow in self.capabilities[CapabilityType.WORKFLOW].values():
                if agent_name in workflow.agent_sequence:
                    agent_index = workflow.agent_sequence.index(agent_name)
                    if agent_index > 0:
                        collaboration["input_from"].append(workflow.agent_sequence[agent_index - 1])
                    if agent_index < len(workflow.agent_sequence) - 1:
                        collaboration["output_to"].append(workflow.agent_sequence[agent_index + 1])
                        
        return collaboration
        
    async def _get_agent_best_practices(self, agent_name: str) -> List[str]:
        """Get best practices for an agent"""
        best_practices = [
            "Always validate inputs before processing",
            "Use appropriate error handling and logging",
            "Follow security guidelines for all operations",
            "Optimize for performance where possible",
            "Document all decisions and implementations",
            "Collaborate effectively with other agents",
            "Use cached results when available",
            "Validate outputs before handoff"
        ]
        
        # Add role-specific best practices
        role_specific = {
            "Coder": [
                "Follow coding standards and conventions",
                "Write unit tests for all new code",
                "Use design patterns appropriately",
                "Optimize for readability and maintainability"
            ],
            "Security_Specialist": [
                "Perform comprehensive security analysis",
                "Follow OWASP guidelines",
                "Implement defense in depth",
                "Regular security audits"
            ],
            "QA_Guardian": [
                "Design comprehensive test cases",
                "Automate regression testing",
                "Validate all edge cases",
                "Maintain test documentation"
            ]
        }
        
        if agent_name in role_specific:
            best_practices.extend(role_specific[agent_name])
            
        return best_practices
        
    async def _get_agent_performance_metrics(self, agent_name: str) -> Dict[str, float]:
        """Get performance metrics for an agent"""
        # Default metrics - in production, these would come from actual monitoring
        return {
            "task_success_rate": 0.92,
            "average_completion_time": 1800,  # 30 minutes
            "quality_score": 0.89,
            "collaboration_effectiveness": 0.91,
            "knowledge_utilization": 0.87,
            "tool_usage_efficiency": 0.85
        }
        
    def _validate_tool_access(self, agent_name: str, tool_name: str) -> bool:
        """Validate that an agent can access a specific tool"""
        # Check if agent exists in compatibility matrix
        if agent_name not in self.compatibility_matrix:
            return False
        return self.compatibility_matrix[agent_name].get(tool_name, False)
        
    def _validate_workflow_knowledge(self, agent_name: str, workflow_name: str) -> bool:
        """Validate that an agent understands a workflow"""
        # Check if agent exists in profiles
        if agent_name not in self.agent_profiles:
            return False
            
        # Get agent's workflow participation
        workflow_participation = self.agent_profiles[agent_name].get("workflow_participation", [])
        
        # Check if agent participates in this workflow (by workflow_type)
        if workflow_name in workflow_participation:
            return True
            
        # Also check if agent is in workflow sequence
        if workflow_name in self.capabilities[CapabilityType.WORKFLOW]:
            workflow = self.capabilities[CapabilityType.WORKFLOW][workflow_name]
            return agent_name in workflow.agent_sequence
            
        return False
        

async def create_knowledge_integration_system() -> AgentKnowledgeRegistry:
    """Factory function to create and initialize the knowledge integration system"""
    registry = AgentKnowledgeRegistry()
    await registry.initialize()
    return registry


# Global instance
_knowledge_registry = None

async def get_knowledge_registry() -> AgentKnowledgeRegistry:
    """Get the global knowledge registry instance"""
    global _knowledge_registry
    if _knowledge_registry is None:
        _knowledge_registry = await create_knowledge_integration_system()
    return _knowledge_registry
