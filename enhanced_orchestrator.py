"""
Enhanced Orchestrator with Intelligent Agent Integration
Implements the full autonomous multi-agent system as defined in master documents
"""

import os
import json
import asyncio
import logging
import re
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from tools.handoff_system import HandoffPacket, ConductorRouter, TaskStatus, NextStepSuggestion
from tools.agent_factory import AgentFactory, AgentOrchestrationPipeline
from tools.checkpoint_system import checkpoint_manager, TaskCheckpoint
from tools.error_handling import error_classifier, retry_manager, recovery_strategy, ErrorInfo
from tools.document_summary_generator import DocumentSummaryGenerator
from tools.section_extraction import get_document_section
from tools.llm_cache import llm_cache, LLMCacheManager
from tools import task_tools
from tools import log_tools
from tools import indexing_tools
from tools import file_tools
from tools import git_tools
from tools import execution_tools
from tools import text_replacement
from tools.handoff_cache import get_handoff_cache_manager, create_workflow_session, add_handoff_packet
from tools.agent_knowledge_integration import AgentKnowledgeRegistry, get_knowledge_registry
from llm_interface import llm_interface

# Debug configuration
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
VERBOSE_OUTPUT = os.getenv('VERBOSE_OUTPUT', 'false').lower() == 'true'

def debug_print(message: str, level: str = "INFO"):
    """Print debug messages if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

def verbose_print(message: str):
    """Print verbose messages if VERBOSE_OUTPUT is enabled"""
    if VERBOSE_OUTPUT or DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] VERBOSE: {message}")

class EnhancedOrchestrator:
    """Enhanced orchestrator with full agent integration and intelligent routing"""
    
    def __init__(self):
        # Initialize workspace organizer (will be set by workflow)
        self.workspace_organizer = None
        
        # Initialize core tools (as modules, not classes)
        self.task_tools = task_tools
        self.log_tools = log_tools
        self.indexing_tools = indexing_tools
        self.file_tools = file_tools
        self.git_tools = git_tools
        self.execution_tools = execution_tools
        
        # Initialize context optimization system
        self.document_summary_generator = DocumentSummaryGenerator()
        
        # Initialize intelligent systems
        self.router = ConductorRouter()
        self.agent_factory = AgentFactory()
        self.orchestration_pipeline = AgentOrchestrationPipeline(self.agent_factory)
        
        # Initialize error handling and recovery systems
        self.checkpoint_manager = checkpoint_manager
        self.error_classifier = error_classifier
        self.retry_manager = retry_manager
        self.recovery_strategy = recovery_strategy
        
        # Initialize knowledge integration system
        self.knowledge_registry = AgentKnowledgeRegistry()  # Will be initialized asynchronously
        self.agent_factory.set_knowledge_registry(self.knowledge_registry)
        self.router.set_knowledge_registry(self.knowledge_registry)

        # State management
        self.active_workflows = {}
        self.agent_sessions = {}
        self.handoff_history = []
        self.human_approval_queue = []
        self.error_history = []  # Track error patterns
        
        # Context optimization settings
        self.context_optimization_enabled = True
        self.max_context_tokens = 16000  # Conservative limit for context
        self.summary_cache = {}  # Cache for document summaries
        
        # Initialize LLM caching system
        self.llm_cache = llm_cache
        self.caching_enabled = True
        
        # Initialize handoff caching system
        self.handoff_cache_manager = get_handoff_cache_manager()
        
        # Configuration
        self.config = self._load_configuration()
        
        self.log_tools.record_log(
            task_id="ORCHESTRATOR_INIT",
            event="ORCHESTRATOR_INITIALIZED",
            data={
                "timestamp": datetime.now().isoformat(),
                "available_agents": self.agent_factory.list_available_agents(),
                "context_optimization_enabled": self.context_optimization_enabled
            }
        )
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load orchestrator configuration"""
        return {
            "max_concurrent_workflows": 5,
            "max_retry_attempts": 3,
            "human_approval_timeout": 3600,  # 1 hour
            "auto_approve_low_risk": False,
            "semantic_indexing_enabled": True,
            "git_auto_push": True,
            "caching_enabled": True,
            "cache_performance_monitoring": True
        }
    
    def _optimize_context_for_agent(self, context: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Optimize context for specific agent using multi-layered approach"""
        # Validate parameters
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        if not agent_name or not isinstance(agent_name, str):
            raise ValueError("agent_name must be a non-empty string")
        
        if not self.context_optimization_enabled:
            return context.copy()
        
        try:
            optimized_context = context.copy()
            
            # Generate or load summaries for relevant documents
            if "previous_artifacts" in context:
                # Replace full artifacts with summaries
                optimized_context["artifact_summaries"] = self._get_artifact_summaries(
                    context["previous_artifacts"], agent_name
                )
                # Remove the original full artifacts to save tokens
                del optimized_context["previous_artifacts"]
            
            # Remove full document content if present (simulates real scenario)
            if "artifact_content" in optimized_context:
                del optimized_context["artifact_content"]
            
            # Add context tools instructions
            optimized_context["context_tools"] = {
                "summary_available": True,
                "drill_down_available": True,
                "instructions": (
                    "Use document summaries first for overview. "
                    "Request specific sections using get_document_section() only when needed. "
                    "This optimizes token usage and improves performance."
                )
            }
            
            return optimized_context
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="CONTEXT_OPTIMIZATION_ERROR",
                event="CONTEXT_OPTIMIZATION_ERROR",
                data={
                    "agent": agent_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            # Return original context if optimization fails
            return context.copy()
    
    def _get_artifact_summaries(self, artifact_paths: List[str], agent_name: str) -> List[Dict[str, Any]]:
        """Get summaries of artifacts for context optimization"""
        summaries = []
        
        for artifact_path in artifact_paths:
            try:
                # Check cache first
                cache_key = f"{artifact_path}_{agent_name}"
                if cache_key in self.summary_cache:
                    summaries.append(self.summary_cache[cache_key])
                    continue
                
                # Generate or load summary
                summary = self.document_summary_generator.generate_summary(artifact_path)
                
                if summary:
                    # Create agent-specific summary entry
                    summary_entry = {
                        "document_path": artifact_path,
                        "summary": summary,
                        "agent_context": agent_name,
                        "generated_at": datetime.now().isoformat()
                    }
                    
                    # Cache the summary
                    self.summary_cache[cache_key] = summary_entry
                    summaries.append(summary_entry)
                    
                    self.log_tools.record_log(
                        task_id="CONTEXT_OPTIMIZATION",
                        event="SUMMARY_GENERATED",
                        data={
                            "document": artifact_path,
                            "agent": agent_name,
                            "summary_size": len(json.dumps(summary))
                        }
                    )
                
            except Exception as e:
                self.log_tools.record_log(
                    task_id="CONTEXT_OPTIMIZATION_ERROR",
                    event="SUMMARY_GENERATION_ERROR",
                    data={
                        "document": artifact_path,
                        "agent": agent_name,
                        "error": str(e)
                    }
                )
        
        return summaries
    
    def _estimate_context_tokens(self, context: Dict[str, Any]) -> int:
        """Estimate total tokens in context"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            context_str = json.dumps(context, indent=2)
            return len(encoding.encode(context_str))
        except Exception:
            # Fallback estimation
            context_str = json.dumps(context, indent=2)
            return len(context_str) // 4
    
    async def get_section_for_agent(self, document_path: str, section_id: str, agent_id: str) -> Dict[str, Any]:
        """Get specific document section for agent (drill-down functionality)"""
        try:
            result = get_document_section(document_path, section_id, agent_id)
            
            # Log the drill-down request
            self.log_tools.record_log(
                task_id="CONTEXT_DRILL_DOWN",
                event="SECTION_REQUESTED",
                data={
                    "document": document_path,
                    "section_id": section_id,
                    "agent": agent_id,
                    "success": result["success"]
                }
            )
            
            return result
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="CONTEXT_DRILL_DOWN_ERROR",
                event="SECTION_REQUEST_ERROR",
                data={
                    "document": document_path,
                    "section_id": section_id,
                    "agent": agent_id,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "content": "",
                "error": f"Failed to extract section: {str(e)}",
                "section_id": section_id,
                "agent_id": agent_id
            }
    
    async def execute_llm_call_with_cache(self, agent_name: str, prompt: str, 
                                        context: Optional[Dict[str, Any]] = None) -> str:
        """Execute LLM call with intelligent caching"""
        # Validate parameters
        if not agent_name or not isinstance(agent_name, str):
            raise ValueError("agent_name must be a non-empty string")
        
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt must be a non-empty string")
        
        if context is None:
            context = {}
        
        if not self.caching_enabled:
            return await self._execute_llm_call_direct(agent_name, prompt, context)
        
        # Try to get cached response
        try:
            cached_response = self.llm_cache.get_llm_response(agent_name, prompt, context)
            if cached_response:
                self.log_tools.record_log(
                    task_id="LLM_CACHE_HIT",
                    event="LLM_CACHE_HIT",
                    data={
                        "agent": agent_name,
                        "prompt_size": len(prompt),
                        "cached_response_size": len(cached_response),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                return cached_response
        except Exception as e:
            # Log cache error but continue with direct call
            self.log_tools.record_log(
                task_id="LLM_CACHE_ERROR",
                event="LLM_CACHE_GET_ERROR",
                data={
                    "agent": agent_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Execute LLM call
        response = await self._execute_llm_call_direct(agent_name, prompt, context)
        
        # Cache the response
        if response:
            try:
                success = self.llm_cache.cache_llm_response(agent_name, prompt, response, context)
                if success:
                    self.log_tools.record_log(
                        task_id="LLM_CACHE_STORE",
                        event="LLM_CACHE_STORE",
                        data={
                            "agent": agent_name,
                            "prompt_size": len(prompt),
                            "response_size": len(response),
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                else:
                    self.log_tools.record_log(
                        task_id="LLM_CACHE_STORE_FAILED",
                        event="LLM_CACHE_STORE_FAILED",
                        data={
                            "agent": agent_name,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
            except Exception as e:
                # Log cache error but don't fail the call
                self.log_tools.record_log(
                    task_id="LLM_CACHE_ERROR",
                    event="LLM_CACHE_STORE_ERROR",
                    data={
                        "agent": agent_name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Save any code artifacts from the response
            if context and isinstance(context, dict) and context.get('workflow_id'):
                workflow_id = context['workflow_id']
                saved_files = await self._save_agent_artifacts(response, workflow_id)
                if saved_files:
                    self.log_tools.record_log(
                        task_id=f"ARTIFACTS_SAVED_{workflow_id}",
                        event="ARTIFACTS_SAVED",
                        data={
                            "agent": agent_name,
                            "files_saved": saved_files,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
        
        return response
    
    async def _execute_llm_call_direct(self, agent_name: str, prompt: str, 
                                     context: Optional[Dict[str, Any]] = None) -> str:
        """Execute direct LLM call using the real LLM interface"""
        # Validate parameters
        if not agent_name or not isinstance(agent_name, str):
            raise ValueError("agent_name must be a non-empty string")
        
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt must be a non-empty string")
        
        if context is None:
            context = {}
        
        debug_print(f"Executing LLM call for {agent_name}")
        verbose_print(f"Prompt preview: {prompt[:100]}...")
        
        self.log_tools.record_log(
            task_id="LLM_CALL_DIRECT",
            event="LLM_CALL_DIRECT",
            data={
                "agent": agent_name,
                "prompt_size": len(prompt),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Use the real LLM interface
        try:
            debug_print("Calling LLM interface...")
            response = await llm_interface.call_llm(agent_name, prompt, context)
            
            debug_print(f"LLM response received: {len(response)} characters")
            verbose_print(f"Response preview: {response[:200]}...")
            
            # Log successful call
            self.log_tools.record_log(
                task_id="LLM_CALL_SUCCESS",
                event="LLM_CALL_SUCCESS",
                data={
                    "agent": agent_name,
                    "response_size": len(response),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return response
            
        except Exception as e:
            debug_print(f"LLM call failed: {str(e)}", "ERROR")
            # Log error and return fallback
            self.log_tools.record_log(
                task_id="LLM_CALL_ERROR",
                event="LLM_CALL_ERROR",
                data={
                    "agent": agent_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return a basic fallback response
            return f"Task completed by {agent_name}: {prompt[:100]}... [Note: LLM call failed, using fallback]"
    
    async def start_workflow(self, request: str, workflow_type: str = "complex_ui_feature") -> str:
        """Start a new workflow based on user request"""
        # Validate input parameters
        if not request or not isinstance(request, str):
            raise ValueError("request must be a non-empty string")
        
        if not workflow_type or not isinstance(workflow_type, str):
            raise ValueError("workflow_type must be a non-empty string")
        
        try:
            # Initialize knowledge systems if not already done
            await self.initialize_knowledge_systems()
            
            # Get workflow requirements from knowledge registry
            workflow_requirements = await self.knowledge_registry.get_workflow_requirements(workflow_type)
            
            # Create initial context enriched with workflow knowledge
            context = {
                "user_request": request,
                "timestamp": datetime.now().isoformat(),
                "workflow_type": workflow_type,
                "workflow_requirements": workflow_requirements,
                "required_agents": workflow_requirements.get("required_agents", []),
                "required_tools": workflow_requirements.get("required_tools", [])
            }
            
            # Create workflow
            workflow_id = self.orchestration_pipeline.create_agent_workflow(workflow_type, context)
            
            # Validate workflow_id was created
            if not workflow_id:
                raise ValueError("Failed to create workflow ID")
            
            # Add workflow_id to context for future use
            context["workflow_id"] = workflow_id
            
            # Add to active workflows
            self.active_workflows[workflow_id] = {
                "id": workflow_id,
                "type": workflow_type,
                "context": context,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "current_agent": workflow_requirements.get("required_agents", ["Product_Analyst"])[0],
                "current_phase": "specification"
            }
            
            # Log workflow start
            self.log_tools.record_log(
                task_id=workflow_id,
                event="WORKFLOW_STARTED",
                data={
                    "workflow_id": workflow_id,
                    "type": workflow_type,
                    "request": request,
                    "workflow_requirements": workflow_requirements
                }
            )
            
            # Start with first agent in sequence
            await self._assign_initial_task(workflow_id, context)
            
            return workflow_id
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="WORKFLOW_START_ERROR",
                event="WORKFLOW_START_ERROR",
                data={
                    "error": str(e),
                    "request": request,
                    "workflow_type": workflow_type
                }
            )
            raise Exception(f"Failed to start workflow: {str(e)}")
    
    async def _assign_initial_task(self, workflow_id: str, context: Dict[str, Any]):
        """Assign the initial task in a workflow"""
        # Validate parameters
        if not workflow_id:
            raise ValueError("workflow_id cannot be empty")
        
        if not context:
            raise ValueError("context cannot be empty")
        
        # Get the first agent from workflow requirements
        required_agents = context.get("required_agents", ["Product_Analyst"])
        if not required_agents:
            required_agents = ["Product_Analyst"]
        first_agent = required_agents[0]
        
        # Get agent knowledge package
        agent_knowledge = await self.knowledge_registry.generate_agent_knowledge_package(first_agent)
        
        # Create specification task for first agent
        task_id = f"TASK-{workflow_id}-001"
        
        task_description = f"Create detailed specification for: {context['user_request']}"
        
        # Enrich context with agent knowledge
        enriched_context = {
            **context,
            "agent_knowledge": agent_knowledge,
            "available_tools": agent_knowledge.get("available_tools", []),
            "workflow_participation": agent_knowledge.get("workflow_participation", []),
            "best_practices": agent_knowledge.get("best_practices", [])
        }
        
        # Apply context optimization for the agent
        optimized_context = self._optimize_context_for_agent(enriched_context, first_agent)
        
        try:
            # Create agent prompt with optimized context
            agent_prompt = await self.agent_factory.create_agent_prompt(
                first_agent,
                task_description,
                optimized_context
            )
            
            # Store task
            task_data = {
                "id": task_id,
                "workflow_id": workflow_id,
                "agent": first_agent,
                "description": task_description,
                "prompt": agent_prompt,
                "status": "assigned",
                "created_at": datetime.now().isoformat()
            }
            
            # Store task using task_tools
            self.task_tools.create_new_task(task_description, task_description, context.get("workflow_id"))
            
            # Log task assignment
            self.log_tools.record_log(
                task_id=task_id,
                event="TASK_ASSIGNED",
                data={
                    "workflow_id": workflow_id,
                    "agent": first_agent,
                    "task_description": task_description,
                    "agent_knowledge_tools": len(agent_knowledge.get("available_tools", [])),
                    "agent_knowledge_workflows": len(agent_knowledge.get("workflow_participation", [])),
                    "agent_knowledge_best_practices": len(agent_knowledge.get("best_practices", []))
                }
            )
            
        except Exception as e:
            self.log_tools.record_log(
                task_id=task_id,
                event="TASK_ASSIGNMENT_ERROR",
                data={
                    "workflow_id": workflow_id,
                    "agent": first_agent,
                    "error": str(e)
                }
            )
            raise Exception(f"Failed to assign initial task: {str(e)}")
    
    async def process_agent_completion(self, task_id: str, agent_output: str, 
                                      session_id: Optional[str] = None, 
                                      is_checkpoint: bool = False) -> Dict[str, Any]:
        """Process completed agent work and route next steps"""
        try:
            # Extract handoff packet from agent output
            handoff_packet = self._extract_handoff_packet(agent_output)
            
            if not handoff_packet:
                raise ValueError("No valid handoff packet found in agent output")
            
            # Log handoff
            self.log_tools.record_log(
                task_id=task_id,
                event="HANDOFF_RECEIVED",
                data={
                    "agent": handoff_packet.agent_name,
                    "status": handoff_packet.status.value,
                    "suggestion": handoff_packet.next_step_suggestion.value,
                    "session_id": session_id
                }
            )
            
            # Store handoff in history (legacy)
            self.handoff_history.append(handoff_packet)
            
            # Add to handoff cache if session provided
            if session_id:
                add_handoff_packet(session_id, handoff_packet, is_checkpoint)
                
                # Update workflow status
                if session_id in self.active_workflows:
                    self.active_workflows[session_id]["current_agent"] = handoff_packet.agent_name
                    self.active_workflows[session_id]["last_update"] = datetime.now().isoformat()
                    
                    if handoff_packet.status == TaskStatus.SUCCESS:
                        self.active_workflows[session_id]["status"] = "progressing"
                    elif handoff_packet.status == TaskStatus.FAILURE:
                        self.active_workflows[session_id]["status"] = "failed"
            
            # Process artifacts
            await self._process_artifacts(handoff_packet)
            
            # Route next tasks
            routing_result = await self._route_next_tasks(handoff_packet)
            
            return routing_result
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="AGENT_COMPLETION_ERROR",
                event="AGENT_COMPLETION_ERROR",
                data={
                "task_id": task_id,
                "error": str(e),
                "session_id": session_id
            }
            )
            raise
    
    def _extract_handoff_packet(self, agent_output: str) -> Optional[HandoffPacket]:
        """Extract handoff packet from agent output"""
        if not agent_output or not agent_output.strip():
            self.log_tools.record_log(
                task_id="HANDOFF_EXTRACTION_ERROR",
                event="HANDOFF_EXTRACTION_ERROR",
                data={"error": "Agent output is empty"}
            )
            return None
            
        try:
            # Look for HANDOFF_PACKET: section in agent output
            import re
            
            # First try to find HANDOFF_PACKET: section
            handoff_pattern = r'HANDOFF_PACKET:\s*(\{.*?\})'
            matches = re.findall(handoff_pattern, agent_output, re.DOTALL)
            
            if matches:
                packet_json = matches[-1]  # Take the last match
                return HandoffPacket.from_json(packet_json)
            
            # Fallback: Look for JSON block in agent output
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, agent_output, re.DOTALL)
            
            if matches:
                packet_json = matches[-1]  # Take the last JSON block
                return HandoffPacket.from_json(packet_json)
            
            self.log_tools.record_log(
                task_id="HANDOFF_EXTRACTION_WARNING",
                event="HANDOFF_EXTRACTION_WARNING",
                data={"error": "No handoff packet found in agent output"}
            )
            return None
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="HANDOFF_EXTRACTION_ERROR",
                event="HANDOFF_EXTRACTION_ERROR",
                data={"error": str(e), "output_length": len(agent_output)}
            )
            return None
    
    async def _process_artifacts(self, handoff_packet: HandoffPacket):
        """Process artifacts produced by agent"""
        if not handoff_packet or not handoff_packet.artifacts_produced:
            self.log_tools.record_log(
                task_id="ARTIFACT_PROCESSING_WARNING",
                event="ARTIFACT_PROCESSING_WARNING",
                data={"message": "No artifacts to process"}
            )
            return
            
        for artifact_path in handoff_packet.artifacts_produced:
            try:
                if not artifact_path or not artifact_path.strip():
                    self.log_tools.record_log(
                        task_id="ARTIFACT_PROCESSING_WARNING",
                        event="ARTIFACT_PROCESSING_WARNING",
                        data={"message": "Empty artifact path"}
                    )
                    continue
                    
                # Verify artifact exists
                if Path(artifact_path).exists():
                    # Index artifact for semantic search
                    if self.config["semantic_indexing_enabled"]:
                        await self._index_artifact(artifact_path)
                    
                    self.log_tools.record_log(
                        task_id="ARTIFACT_PROCESSED",
                        event="ARTIFACT_PROCESSED",
                        data={
                            "artifact": artifact_path,
                            "task": handoff_packet.completed_task_id,
                            "agent": handoff_packet.agent_name
                        }
                    )
                else:
                    self.log_tools.record_log(
                        task_id="ARTIFACT_MISSING",
                        event="ARTIFACT_MISSING",
                        data={
                            "artifact": artifact_path,
                            "task": handoff_packet.completed_task_id,
                            "agent": handoff_packet.agent_name
                        }
                    )
                    
            except Exception as e:
                self.log_tools.record_log(
                    task_id="ARTIFACT_PROCESSING_ERROR",
                    event="ARTIFACT_PROCESSING_ERROR",
                    data={
                        "artifact": artifact_path,
                        "error": str(e),
                        "task": handoff_packet.completed_task_id
                    }
                )
    
    async def _index_artifact(self, artifact_path: str):
        """Index artifact for semantic search"""
        if not artifact_path or not artifact_path.strip():
            self.log_tools.record_log(
                task_id="INDEXING_ERROR",
                event="INDEXING_ERROR",
                data={"error": "Empty artifact path"}
            )
            return
            
        try:
            artifact_file = Path(artifact_path)
            
            if not artifact_file.exists():
                self.log_tools.record_log(
                    task_id="INDEXING_ERROR",
                    event="INDEXING_ERROR",
                    data={"error": f"Artifact file does not exist: {artifact_path}"}
                )
                return
                
            if not artifact_file.is_file():
                self.log_tools.record_log(
                    task_id="INDEXING_ERROR",
                    event="INDEXING_ERROR",
                    data={"error": f"Artifact path is not a file: {artifact_path}"}
                )
                return
                
            content = artifact_file.read_text(encoding='utf-8')
            
            if not content.strip():
                self.log_tools.record_log(
                    task_id="INDEXING_WARNING",
                    event="INDEXING_WARNING",
                    data={"message": f"Artifact file is empty: {artifact_path}"}
                )
                return
                
            self.indexing_tools.index_document(artifact_path)
            
            self.log_tools.record_log(
                task_id="INDEXING_SUCCESS",
                event="INDEXING_SUCCESS",
                data={
                    "artifact": artifact_path,
                    "content_length": len(content)
                }
            )
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="INDEXING_ERROR",
                event="INDEXING_ERROR",
                data={
                    "artifact": artifact_path,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def _route_next_tasks(self, handoff_packet: HandoffPacket) -> Dict[str, Any]:
        """Route next tasks based on handoff packet"""
        # Handle human approval cases
        if handoff_packet.next_step_suggestion == NextStepSuggestion.HUMAN_APPROVAL_NEEDED:
            return await self._handle_human_approval_gate(handoff_packet)
        
        # Use router to determine next tasks
        next_tasks = await self.router.route_next_task(handoff_packet)
        
        # Create and assign next tasks
        created_tasks = []
        for task_config in next_tasks:
            task_id = await self._create_next_task(handoff_packet, task_config)
            created_tasks.append(task_id)
        
        return {
            "status": "tasks_routed",
            "next_tasks": created_tasks,
            "routing_reason": handoff_packet.next_step_suggestion.value
        }
    
    async def _handle_human_approval_gate(self, handoff_packet: HandoffPacket) -> Dict[str, Any]:
        """Handle human approval gate"""
        approval_request = {
            "id": f"APPROVAL-{len(self.human_approval_queue) + 1:03d}",
            "task_id": handoff_packet.completed_task_id,
            "agent": handoff_packet.agent_name,
            "artifacts": handoff_packet.artifacts_produced,
            "notes": handoff_packet.notes,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        self.human_approval_queue.append(approval_request)
        
        # Create human approval gate document
        await self._create_approval_gate_document(approval_request)
        
        self.log_tools.record_log(
                task_id="HUMAN_APPROVAL_REQUESTED",
                event="HUMAN_APPROVAL_REQUESTED",
                data={
            "approval_id": approval_request["id"],
            "task_id": handoff_packet.completed_task_id
        }
            )
        
        return {
            "status": "human_approval_required",
            "approval_id": approval_request["id"],
            "artifacts_to_review": handoff_packet.artifacts_produced
        }
    
    async def _create_approval_gate_document(self, approval_request: Dict[str, Any]):
        """Create human approval gate document"""
        doc_path = f"workspace/documentation/approval_gate_{approval_request['id']}.md"
        
        content = f"""# Human Approval Gate: {approval_request['id']}

## Status: AWAITING APPROVAL

## Task Information
- **Task ID:** {approval_request['task_id']}
- **Agent:** {approval_request['agent']}
- **Created:** {approval_request['created_at']}

## Artifacts for Review
{chr(10).join(f"- {artifact}" for artifact in approval_request['artifacts'])}

## Notes
{approval_request['notes']}

## Decision Required
Please respond with one of the following:
- **"APPROVE"** - to proceed with next phase
- **"CHANGES: [specific feedback]"** - to request modifications
- **"REJECT: [reason]"** - to reject the current implementation

---
**Awaiting your decision to proceed...**
"""
        
        self.file_tools.write_file(doc_path, content)
    
    async def _create_next_task(self, handoff_packet: HandoffPacket, task_config: Dict[str, Any]) -> str:
        """Create and assign next task based on routing"""
        # Generate task ID
        base_task_id = handoff_packet.completed_task_id.split('-')[1] if '-' in handoff_packet.completed_task_id else "001"
        next_task_id = f"TASK-{base_task_id}-{len(self.handoff_history) + 1:03d}"
        
        # Create context for next agent
        context = {
            "previous_task": handoff_packet.completed_task_id,
            "previous_artifacts": handoff_packet.artifacts_produced,
            "previous_notes": handoff_packet.notes,
            "task_type": task_config["task_type"]
        }
        
        # Add specific context based on task type
        if "artifacts" in task_config:
            context["code_artifacts"] = task_config["artifacts"]
        if "context" in task_config:
            context["additional_context"] = task_config["context"]
        
        # Apply context optimization for the target agent
        optimized_context = self._optimize_context_for_agent(context, task_config["agent"])
        
        # Create agent prompt with optimized context
        agent_prompt = await self.agent_factory.create_agent_prompt(
            task_config["agent"],
            task_config["description"],
            optimized_context
        )
        
        # Initialize task data
        task_data = {
            "id": next_task_id,
            "agent": task_config["agent"],
            "description": task_config["description"],
            "prompt": agent_prompt,
            "priority": task_config.get("priority", "medium"),
            "status": "assigned",
            "created_at": datetime.now().isoformat(),
            "parent_task": handoff_packet.completed_task_id
        }
        
        # Execute LLM call with caching if enabled
        if self.caching_enabled:
            cached_response = await self.execute_llm_call_with_cache(
                task_config["agent"],
                agent_prompt,
                optimized_context
            )
            if cached_response:
                # Update task data with cached response
                task_data["cached_response"] = cached_response
                task_data["status"] = "cached_response_available"
        
        # Log context optimization metrics
        original_tokens = self._estimate_context_tokens(context)
        optimized_tokens = self._estimate_context_tokens(optimized_context)
        
        self.log_tools.record_log(
            task_id="CONTEXT_OPTIMIZATION_METRICS",
            event="CONTEXT_OPTIMIZED",
            data={
                "task_id": next_task_id,
                "agent": task_config["agent"],
                "original_tokens": original_tokens,
                "optimized_tokens": optimized_tokens,
                "token_reduction": original_tokens - optimized_tokens,
                "optimization_enabled": self.context_optimization_enabled
            }
        )
        
        # Store task using task_tools
        self.task_tools.create_new_task(task_config["description"], task_config["description"], handoff_packet.completed_task_id)
        
        self.log_tools.record_log(
                task_id="NEXT_TASK_CREATED",
                event="NEXT_TASK_CREATED",
                data={
            "task_id": next_task_id,
            "agent": task_config["agent"],
            "parent_task": handoff_packet.completed_task_id
        }
            )
        
        return next_task_id
    
    async def process_human_approval(self, approval_id: str, decision: str) -> Dict[str, Any]:
        """Process human approval decision"""
        if not approval_id or not approval_id.strip():
            raise ValueError("approval_id cannot be empty")
            
        if not decision or not decision.strip():
            raise ValueError("decision cannot be empty")
            
        # Find approval request
        approval_request = None
        for req in self.human_approval_queue:
            if req["id"] == approval_id:
                approval_request = req
                break
        
        if not approval_request:
            raise ValueError(f"Approval request not found: {approval_id}")
            
        if approval_request["status"] != "pending":
            raise ValueError(f"Approval request {approval_id} is not pending (status: {approval_request['status']})")
        
        try:
            # Process decision
            decision_upper = decision.upper().strip()
            
            if decision_upper == "APPROVE":
                return await self._handle_approval_approved(approval_request)
            elif decision_upper.startswith("CHANGES:"):
                return await self._handle_approval_changes(approval_request, decision)
            elif decision_upper.startswith("REJECT:"):
                return await self._handle_approval_rejected(approval_request, decision)
            else:
                raise ValueError(f"Invalid decision format: {decision}. Expected 'APPROVE', 'CHANGES: [feedback]', or 'REJECT: [reason]'")
                
        except Exception as e:
            self.log_tools.record_log(
                task_id="HUMAN_APPROVAL_ERROR",
                event="HUMAN_APPROVAL_ERROR",
                data={
                    "approval_id": approval_id,
                    "decision": decision,
                    "error": str(e)
                }
            )
            raise
    
    async def _handle_approval_approved(self, approval_request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle approved decision"""
        approval_request["status"] = "approved"
        approval_request["decided_at"] = datetime.now().isoformat()
        
        # Create handoff packet for approval
        approval_handoff = HandoffPacket(
            completed_task_id=approval_request["task_id"],
            agent_name="Human_Approver",
            status=TaskStatus.SUCCESS,
            artifacts_produced=approval_request["artifacts"],
            next_step_suggestion=NextStepSuggestion.MERGE_APPROVED,
            notes="Human approval granted - proceed with next phase",
            timestamp=datetime.now().isoformat()
        )
        
        # Route next tasks
        return await self._route_next_tasks(approval_handoff)
    
    async def _handle_approval_changes(self, approval_request: Dict[str, Any], decision: str) -> Dict[str, Any]:
        """Handle changes requested decision"""
        changes_requested = decision[8:].strip()  # Remove "CHANGES:" prefix
        
        approval_request["status"] = "changes_requested"
        approval_request["feedback"] = changes_requested
        approval_request["decided_at"] = datetime.now().isoformat()
        
        # Create handoff packet for changes
        changes_handoff = HandoffPacket(
            completed_task_id=approval_request["task_id"],
            agent_name="Human_Approver",
            status=TaskStatus.BLOCKED,
            artifacts_produced=approval_request["artifacts"],
            next_step_suggestion=NextStepSuggestion.IMPLEMENTATION_NEEDED,
            notes=f"Changes requested: {changes_requested}",
            timestamp=datetime.now().isoformat(),
            blocking_issues=[changes_requested]
        )
        
        # Route back to implementation
        return await self._route_next_tasks(changes_handoff)
    
    async def _handle_approval_rejected(self, approval_request: Dict[str, Any], decision: str) -> Dict[str, Any]:
        """Handle rejected decision"""
        rejection_reason = decision[7:].strip()  # Remove "REJECT:" prefix
        
        approval_request["status"] = "rejected"
        approval_request["rejection_reason"] = rejection_reason
        approval_request["decided_at"] = datetime.now().isoformat()
        
        self.log_tools.record_log(
                task_id="HUMAN_APPROVAL_REJECTED",
                event="HUMAN_APPROVAL_REJECTED",
                data={
            "approval_id": approval_request["id"],
            "reason": rejection_reason
        }
            )
        
        return {
            "status": "workflow_rejected",
            "reason": rejection_reason,
            "approval_id": approval_request["id"]
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        # Validate input
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow = self.active_workflows[workflow_id]
        
        # Get related handoffs
        related_handoffs = [
            h for h in self.handoff_history
            if h.completed_task_id.startswith(workflow_id)
        ]
        
        # Get pending approvals
        pending_approvals = [
            a for a in self.human_approval_queue
            if a["task_id"].startswith(workflow_id) and a["status"] == "pending"
        ]
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.get("status", "unknown"),
            "current_agent": workflow.get("current_agent", "unknown"),
            "current_phase": workflow.get("current_phase", "unknown"),
            "created_at": workflow.get("created_at", "unknown"),
            "total_handoffs": len(related_handoffs),
            "pending_approvals": len(pending_approvals),
            "last_activity": related_handoffs[-1].timestamp if related_handoffs else None,
            "workflow_type": workflow.get("type", "unknown")
        }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending human approvals"""
        return [a for a in self.human_approval_queue if a["status"] == "pending"]
    
    async def execute_task_with_recovery(self, task_id: str, agent_name: str, 
                                       task_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with automatic error handling and recovery"""
        
        # Create initial checkpoint
        checkpoint = self.checkpoint_manager.create_checkpoint(
            task_id=task_id,
            workflow_id=context.get("workflow_id", "unknown"),
            agent_name=agent_name,
            progress_percentage=0.0,
            state_data={"status": "starting"},
            intermediate_results={},
            dependencies_completed=context.get("dependencies_completed", []),
            context=context
        )
        
        max_attempts = 3
        attempt = 0
        error_info = None  # Initialize error_info
        
        while attempt < max_attempts:
            try:
                # Update checkpoint with current attempt
                self.checkpoint_manager.update_checkpoint(
                    checkpoint.checkpoint_id,
                    progress_percentage=25.0 + (attempt * 25.0),
                    state_data={"status": "executing", "attempt": attempt + 1}
                )
                
                # Execute the task
                result = await self._execute_agent_task(agent_name, task_prompt, context)
                
                # Update checkpoint with success
                self.checkpoint_manager.update_checkpoint(
                    checkpoint.checkpoint_id,
                    progress_percentage=100.0,
                    state_data={"status": "completed"},
                    intermediate_results=result
                )
                
                # Clean up checkpoint after successful completion
                self.checkpoint_manager.cleanup_completed_task(task_id)
                
                return result
                
            except Exception as e:
                attempt += 1
                
                # Classify the error
                error_info = self.error_classifier.classify_error(e, context)
                error_info.retry_count = attempt - 1
                
                # Log the error
                self.log_tools.record_log(
                    task_id=task_id,
                    event="TASK_ERROR",
                    data={
                        "error_type": error_info.error_type,
                        "error_message": error_info.error_message,
                        "category": error_info.category.value,
                        "attempt": attempt,
                        "agent": agent_name
                    }
                )
                
                # Add to error history
                self.error_history.append(error_info)
                
                # Check if we should retry
                should_retry, updated_error_info = self.retry_manager.should_retry(e, context)
                
                if not should_retry or attempt >= max_attempts:
                    # Final failure - apply recovery strategy
                    recovery_result = self.recovery_strategy.apply_recovery(error_info, context)
                    
                    # Update checkpoint with failure
                    self.checkpoint_manager.update_checkpoint(
                        checkpoint.checkpoint_id,
                        state_data={"status": "failed", "error": error_info.error_message},
                        last_error=error_info.error_message
                    )
                    
                    if recovery_result["action"] == "escalate":
                        # Escalate to human approval
                        await self._escalate_to_human(task_id, error_info, recovery_result)
                        
                        return {
                            "status": "escalated",
                            "error": error_info.to_dict(),
                            "recovery_action": recovery_result
                        }
                    
                    raise Exception(f"Task failed after {max_attempts} attempts: {error_info.error_message}")
                
                # Calculate delay and wait
                delay = self.retry_manager.calculate_delay(error_info)
                
                self.log_tools.record_log(
                    task_id=task_id,
                    event="TASK_RETRY",
                    data={
                        "attempt": attempt,
                        "delay": delay,
                        "error_category": error_info.category.value
                    }
                )
                
                await asyncio.sleep(delay)
                
                # Record failure for circuit breaker
                self.retry_manager.record_failure(error_info)
        
        # If we reach here, all attempts failed
        error_message = error_info.error_message if error_info else "Unknown error"
        raise Exception(f"Task failed after {max_attempts} attempts: Last error - {error_message}")
    
    async def _execute_agent_task(self, agent_name: str, task_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent task using real LLM calls"""
        try:
            # Execute the task using the real LLM interface with caching
            response = await self.execute_llm_call_with_cache(agent_name, task_prompt, context)
            
            # Process the response to extract structured data
            return {
                "status": "completed",
                "agent": agent_name,
                "result": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Handle task execution errors
            self.log_tools.record_log(
                task_id=f"AGENT_TASK_ERROR_{agent_name}",
                event="AGENT_TASK_ERROR",
                data={
                    "agent": agent_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return error result
            return {
                "status": "failed",
                "agent": agent_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _escalate_to_human(self, task_id: str, error_info: ErrorInfo, recovery_result: Dict[str, Any]):
        """Escalate failed task to human approval queue"""
        approval_item = {
            "task_id": task_id,
            "error_info": error_info.to_dict(),
            "recovery_suggestion": recovery_result,
            "timestamp": datetime.now().isoformat(),
            "status": "pending_human_review"
        }
        
        self.human_approval_queue.append(approval_item)
        
        self.log_tools.record_log(
            task_id=task_id,
            event="HUMAN_ESCALATION",
            data={
                "reason": "task_failure_recovery",
                "error_category": error_info.category.value,
                "error_severity": error_info.severity.value
            }
        )
    
    def get_checkpoint_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current checkpoint status for a task"""
        checkpoint = self.checkpoint_manager.get_latest_checkpoint(task_id)
        if checkpoint:
            return {
                "task_id": task_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "progress": checkpoint.progress_percentage,
                "status": checkpoint.state_data.get("status", "unknown"),
                "timestamp": checkpoint.timestamp,
                "retry_count": checkpoint.retry_count
            }
        return None
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        if not self.error_history:
            return {"total_errors": 0, "categories": {}, "severity_distribution": {}}
        
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "categories": category_counts,
            "severity_distribution": severity_counts,
            "recent_errors": [error.to_dict() for error in self.error_history[-5:]]
        }
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old checkpoints and error history"""
        if max_age_hours <= 0:
            raise ValueError("max_age_hours must be positive")
            
        try:
            # Clean up old checkpoints
            self.checkpoint_manager.cleanup_old_checkpoints(max_age_hours)
            
            # Clean up old error history
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            old_error_count = len(self.error_history)
            
            self.error_history = [
                error for error in self.error_history 
                if datetime.fromisoformat(error.timestamp) > cutoff_time
            ]
            
            # Clean up old summary cache
            old_cache_size = len(self.summary_cache)
            self.summary_cache.clear()
            
            # Clean up old workflows (keep active ones)
            old_workflows = {}
            for workflow_id, workflow in self.active_workflows.items():
                workflow_time = datetime.fromisoformat(workflow.get("created_at", datetime.now().isoformat()))
                if datetime.now() - workflow_time > timedelta(hours=max_age_hours):
                    if workflow.get("status") not in ["active", "pending"]:
                        old_workflows[workflow_id] = workflow
            
            # Remove old inactive workflows
            for workflow_id in old_workflows:
                del self.active_workflows[workflow_id]
            
            self.log_tools.record_log(
                task_id="CLEANUP_COMPLETED",
                event="CLEANUP_COMPLETED",
                data={
                    "errors_cleaned": old_error_count - len(self.error_history),
                    "cache_entries_cleaned": old_cache_size,
                    "workflows_cleaned": len(old_workflows),
                    "max_age_hours": max_age_hours
                }
            )
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="CLEANUP_ERROR",
                event="CLEANUP_ERROR",
                data={
                    "error": str(e),
                    "max_age_hours": max_age_hours
                }
            )
            raise
    
    def get_context_optimization_stats(self) -> Dict[str, Any]:
        """Get statistics about context optimization usage"""
        return {
            "optimization_enabled": self.context_optimization_enabled,
            "max_context_tokens": self.max_context_tokens,
            "cached_summaries": len(self.summary_cache),
            "total_handoffs": len(self.handoff_history),
            "active_workflows": len(self.active_workflows)
        }
    
    def get_cache_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        llm_stats = self.llm_cache.get_cache_stats()
        
        return {
            "caching_enabled": self.caching_enabled,
            "llm_cache": llm_stats,
            "context_optimization": self.get_context_optimization_stats(),
            "performance_summary": {
                "total_cost_saved": llm_stats.get("total_cost_saved", 0),
                "total_tokens_saved": llm_stats.get("total_tokens_saved", 0),
                "hit_rate": llm_stats.get("hit_rate", 0),
                "cache_efficiency": self._calculate_cache_efficiency()
            }
        }
    
    def _calculate_cache_efficiency(self) -> float:
        """Calculate overall cache efficiency score"""
        llm_stats = self.llm_cache.get_cache_stats()
        hit_rate = llm_stats.get("hit_rate", 0)
        
        # Cache efficiency score (0-100)
        # Based on hit rate, cost savings, and memory usage
        efficiency = hit_rate * 0.7  # 70% weight on hit rate
        
        if llm_stats.get("total_cost_saved", 0) > 0:
            efficiency += 20  # 20% bonus for cost savings
        
        if llm_stats.get("cache_size_mb", 0) < 50:  # Under 50MB
            efficiency += 10  # 10% bonus for efficient memory usage
        
        return min(100, efficiency)
        
        return min(100, efficiency)
    
    def generate_cache_report(self) -> str:
        """Generate a comprehensive cache performance report"""
        stats = self.get_cache_performance_stats()
        
        report = f"""
# Cache Performance Report
Generated: {datetime.now().isoformat()}

## LLM Cache Statistics
- **Hit Rate**: {stats['llm_cache']['hit_rate']:.1f}%
- **Total Requests**: {stats['llm_cache']['hits'] + stats['llm_cache']['misses']}
- **Cache Hits**: {stats['llm_cache']['hits']}
- **Cache Misses**: {stats['llm_cache']['misses']}
- **Cost Saved**: ${stats['llm_cache']['total_cost_saved']:.4f}
- **Tokens Saved**: {stats['llm_cache']['total_tokens_saved']:,}
- **Cache Size**: {stats['llm_cache']['cache_size_mb']:.1f} MB
- **Active Entries**: {stats['llm_cache']['entries_count']}

## Context Optimization
- **Optimization Enabled**: {stats['context_optimization']['optimization_enabled']}
- **Max Context Tokens**: {stats['context_optimization']['max_context_tokens']:,}
- **Cached Summaries**: {stats['context_optimization']['cached_summaries']}
- **Active Workflows**: {stats['context_optimization']['active_workflows']}

## Performance Summary
- **Total Cost Saved**: ${stats['performance_summary']['total_cost_saved']:.4f}
- **Total Tokens Saved**: {stats['performance_summary']['total_tokens_saved']:,}
- **Overall Hit Rate**: {stats['performance_summary']['hit_rate']:.1f}%
- **Cache Efficiency Score**: {stats['performance_summary']['cache_efficiency']:.1f}/100

## Agent Distribution
"""
        
        # Add agent distribution
        agent_dist = stats['llm_cache'].get('agent_distribution', {})
        for agent, count in agent_dist.items():
            report += f"- **{agent}**: {count} cached entries\n"
        
        return report
    
    def start_workflow_session(self, workflow_name: str, initial_agent: str) -> str:
        """Start a new workflow session with handoff caching"""
        session_id = create_workflow_session(workflow_name, initial_agent)
        
        # Track in active workflows
        self.active_workflows[session_id] = {
            "workflow_name": workflow_name,
            "current_agent": initial_agent,
            "started_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.log_tools.record_log(
            task_id=session_id,
            event="WORKFLOW_SESSION_STARTED",
            data={
                "workflow_name": workflow_name,
                "initial_agent": initial_agent,
                "session_id": session_id
            }
        )
        
        return session_id
    
    def resume_workflow_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Resume a paused workflow session"""
        from tools.handoff_cache import resume_workflow, get_workflow_history
        
        # Get the last checkpoint
        last_checkpoint = resume_workflow(session_id)
        
        if last_checkpoint:
            # Get the full workflow history
            history = get_workflow_history(session_id)
            
            # Update active workflows
            self.active_workflows[session_id] = {
                "workflow_name": f"resumed_{session_id}",
                "current_agent": last_checkpoint.agent_name,
                "resumed_at": datetime.now().isoformat(),
                "status": "resumed"
            }
            
            self.log_tools.record_log(
                task_id=session_id,
                event="WORKFLOW_SESSION_RESUMED",
                data={
                    "session_id": session_id,
                    "last_checkpoint": last_checkpoint.completed_task_id,
                    "history_length": len(history)
                }
            )
            
            return {
                "session_id": session_id,
                "last_checkpoint": last_checkpoint,
                "history": history
            }
        
        return None
    
    def pause_workflow_session(self, session_id: str) -> bool:
        """Pause a workflow session"""
        success = self.handoff_cache_manager.pause_workflow(session_id)
        
        if success and session_id in self.active_workflows:
            self.active_workflows[session_id]["status"] = "paused"
            self.active_workflows[session_id]["paused_at"] = datetime.now().isoformat()
            
            self.log_tools.record_log(
                task_id=session_id,
                event="WORKFLOW_SESSION_PAUSED",
                data={"session_id": session_id}
            )
        
        return success
    
    def get_handoff_cache_statistics(self) -> Dict[str, Any]:
        """Get handoff cache statistics"""
        return self.handoff_cache_manager.get_statistics()
    
    def get_resumable_workflows(self) -> List[str]:
        """Get list of resumable workflow session IDs"""
        return self.handoff_cache_manager.get_resumable_workflows()
    
    def get_workflow_sessions(self) -> Dict[str, Any]:
        """Get information about all workflow sessions"""
        active_sessions = self.handoff_cache_manager.get_active_workflows()
        resumable_sessions = self.handoff_cache_manager.get_resumable_workflows()
        
        return {
            "active_sessions": active_sessions,
            "resumable_sessions": resumable_sessions,
            "total_sessions": len(active_sessions) + len(resumable_sessions),
            "cache_statistics": self.get_handoff_cache_statistics()
        }
    
    async def initialize_knowledge_systems(self):
        """Initialize the knowledge integration system asynchronously"""
        if self.knowledge_registry is None:
            self.knowledge_registry = await get_knowledge_registry()
            
            # Update agent factory with knowledge registry
            self.agent_factory.knowledge_registry = self.knowledge_registry
            
            self.log_tools.record_log(
                task_id="ORCHESTRATOR_INIT",
                event="KNOWLEDGE_SYSTEM_INITIALIZED",
                data={
                    "timestamp": datetime.now().isoformat(),
                    "available_agents": len(self.knowledge_registry.agent_profiles),
                    "available_tools": len(self.knowledge_registry.capabilities)
                }
            )
    
    async def validate_agent_knowledge(self, agent_name: str) -> Dict[str, Any]:
        """Validate that an agent has access to all necessary tools and workflows"""
        await self.initialize_knowledge_systems()
        
        validation_results = await self.knowledge_registry.validate_agent_knowledge(agent_name)
        
        # Log validation results
        self.log_tools.record_log(
            task_id=f"VALIDATION_{agent_name}",
            event="AGENT_KNOWLEDGE_VALIDATION",
            data={
                "agent_name": agent_name,
                "tools_accessible": validation_results.get("tools_accessible", False),
                "workflows_understood": validation_results.get("workflows_understood", False),
                "validation_timestamp": validation_results.get("validation_timestamp", datetime.now()).isoformat() if validation_results.get("validation_timestamp") else datetime.now().isoformat(),
                "issues_count": len(validation_results.get("issues", []))
            }
        )
        
        return validation_results
    
    async def get_agent_knowledge_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get a summary of an agent's knowledge and capabilities"""
        await self.initialize_knowledge_systems()
        
        knowledge_package = await self.knowledge_registry.generate_agent_knowledge_package(agent_name)
        
        summary = {
            "agent_name": agent_name,
            "available_tools_count": len(knowledge_package.get("available_tools", [])),
            "workflow_participation_count": len(knowledge_package.get("workflow_participation", [])),
            "integration_capabilities_count": len(knowledge_package.get("integration_capabilities", [])),
            "best_practices_count": len(knowledge_package.get("best_practices", [])),
            "collaboration_partners": knowledge_package.get("collaboration_matrix", {}),
            "performance_metrics": knowledge_package.get("performance_metrics", {})
        }
        
        return summary
    
    async def validate_all_agents_knowledge(self) -> Dict[str, Any]:
        """Validate knowledge for all agents in the system"""
        await self.initialize_knowledge_systems()
        
        all_agents = self.agent_factory.list_available_agents()
        validation_results = {}
        
        for agent_name in all_agents:
            try:
                validation_result = await self.validate_agent_knowledge(agent_name)
                validation_results[agent_name] = validation_result
            except Exception as e:
                validation_results[agent_name] = {
                    "error": str(e),
                    "tools_accessible": False,
                    "workflows_understood": False,
                    "validation_failed": True
                }
        
        # Generate summary report
        summary = {
            "total_agents": len(all_agents),
            "validated_agents": len([r for r in validation_results.values() 
                                   if r.get("tools_accessible", False) and r.get("workflows_understood", False)]),
            "failed_validations": len([r for r in validation_results.values() 
                                     if not (r.get("tools_accessible", False) and r.get("workflows_understood", False))]),
            "validation_details": validation_results
        }
        
        self.log_tools.record_log(
            task_id="SYSTEM_VALIDATION",
            event="ALL_AGENTS_KNOWLEDGE_VALIDATION",
            data={
                "total_agents": summary["total_agents"],
                "validated_agents": summary["validated_agents"],
                "failed_validations": summary["failed_validations"]
            }
        )
        
        return summary
    
    async def get_agent_capabilities(self, agent_name: str) -> Dict[str, Any]:
        """Get capabilities for a specific agent"""
        await self.initialize_knowledge_systems()
        return await self.knowledge_registry.get_agent_capabilities(agent_name)
    
    async def _save_agent_artifacts(self, agent_response: str, workflow_id: str) -> List[str]:
        """Parse agent response and save any code artifacts to files"""
        debug_print(f"Saving artifacts for workflow {workflow_id}")
        saved_files = []
        
        try:
            # Use workspace organizer if available, otherwise fall back to old method
            if self.workspace_organizer:
                workspace_dir = self.workspace_organizer.get_workflow_folder(workflow_id)
            else:
                workspace_dir = Path("workspace") / workflow_id
                workspace_dir.mkdir(parents=True, exist_ok=True)
            
            verbose_print(f"Created workspace directory: {workspace_dir}")
            
            # Look for code blocks in the response
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', agent_response, re.DOTALL)
            debug_print(f"Found {len(code_blocks)} code blocks")
            
            for i, (language, code) in enumerate(code_blocks):
                if not code.strip():
                    continue
                    
                # Determine file extension
                if language.lower() == 'javascript':
                    ext = '.js'
                elif language.lower() == 'python':
                    ext = '.py'
                elif language.lower() == 'sql':
                    ext = '.sql'
                elif language.lower() == 'json':
                    ext = '.json'
                elif language.lower() == 'html':
                    ext = '.html'
                elif language.lower() == 'css':
                    ext = '.css'
                elif language.lower() == 'dockerfile':
                    ext = '.dockerfile'
                elif language.lower() == 'yaml' or language.lower() == 'yml':
                    ext = '.yml'
                else:
                    ext = '.txt'
                
                # Try to extract filename from code or use generic name
                filename = f"generated_code_{i+1}{ext}"
                
                # Look for filename hints in the response
                filename_patterns = [
                    r'###\s*([^\n]+\.(?:js|py|sql|json|html|css|dockerfile|yml|yaml|txt))',
                    r'File:\s*([^\n]+\.(?:js|py|sql|json|html|css|dockerfile|yml|yaml|txt))',
                    r'`([^`]+\.(?:js|py|sql|json|html|css|dockerfile|yml|yaml|txt))`',
                    r'(/[^/\n]+\.(?:js|py|sql|json|html|css|dockerfile|yml|yaml|txt))',
                ]
                
                for pattern in filename_patterns:
                    match = re.search(pattern, agent_response, re.IGNORECASE)
                    if match:
                        suggested_filename = match.group(1).strip()
                        if suggested_filename:
                            filename = Path(suggested_filename).name
                            break
                
                # Save the file
                file_path = workspace_dir / filename
                
                # Clean up the code (remove extra whitespace)
                cleaned_code = code.strip()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_code)
                
                saved_files.append(str(file_path))
                
                self.log_tools.record_log(
                    task_id=f"ARTIFACT_SAVED_{workflow_id}",
                    event="ARTIFACT_SAVED",
                    data={
                        "file_path": str(file_path),
                        "language": language,
                        "size": len(cleaned_code),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Look for documentation files in markdown format
            if '# ' in agent_response or '## ' in agent_response:
                # Save the entire response as documentation
                doc_path = workspace_dir / "documentation.md"
                with open(doc_path, 'w', encoding='utf-8') as f:
                    f.write(agent_response)
                saved_files.append(str(doc_path))
                
                self.log_tools.record_log(
                    task_id=f"DOCUMENTATION_SAVED_{workflow_id}",
                    event="DOCUMENTATION_SAVED",
                    data={
                        "file_path": str(doc_path),
                        "size": len(agent_response),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
        except Exception as e:
            self.log_tools.record_log(
                task_id=f"ARTIFACT_SAVE_ERROR_{workflow_id}",
                event="ARTIFACT_SAVE_ERROR",
                data={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return saved_files
