"""
Enhanced Orchestrator with Intelligent Agent Integration
Implements the full autonomous multi-agent system as defined in master documents
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from tools.handoff_system import HandoffPacket, ConductorRouter, TaskStatus, NextStepSuggestion
from tools.agent_factory import AgentFactory, AgentOrchestrationPipeline
from tools.checkpoint_system import checkpoint_manager, TaskCheckpoint
from tools.error_handling import error_classifier, retry_manager, recovery_strategy, ErrorInfo
from tools import task_tools
from tools import log_tools
from tools import indexing_tools
from tools import file_tools
from tools import git_tools
from tools import execution_tools

class EnhancedOrchestrator:
    """Enhanced orchestrator with full agent integration and intelligent routing"""
    
    def __init__(self):
        # Initialize core tools (as modules, not classes)
        self.task_tools = task_tools
        self.log_tools = log_tools
        self.indexing_tools = indexing_tools
        self.file_tools = file_tools
        self.git_tools = git_tools
        self.execution_tools = execution_tools
        
        # Initialize intelligent systems
        self.router = ConductorRouter()
        self.agent_factory = AgentFactory()
        self.orchestration_pipeline = AgentOrchestrationPipeline(self.agent_factory)
        
        # Initialize error handling and recovery systems
        self.checkpoint_manager = checkpoint_manager
        self.error_classifier = error_classifier
        self.retry_manager = retry_manager
        self.recovery_strategy = recovery_strategy
        
        # State management
        self.active_workflows = {}
        self.agent_sessions = {}
        self.handoff_history = []
        self.human_approval_queue = []
        self.error_history = []  # Track error patterns
        
        # Configuration
        self.config = self._load_configuration()
        
        self.log_tools.record_log(
            task_id="ORCHESTRATOR_INIT",
            event="ORCHESTRATOR_INITIALIZED",
            data={
                "timestamp": datetime.now().isoformat(),
                "available_agents": self.agent_factory.list_available_agents()
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
            "git_auto_push": True
        }
    
    async def start_workflow(self, request: str, workflow_type: str = "complex_ui_feature") -> str:
        """Start a new workflow based on user request"""
        try:
            # Create initial context
            context = {
                "user_request": request,
                "timestamp": datetime.now().isoformat(),
                "workflow_type": workflow_type
            }
            
            # Create workflow
            workflow_id = self.orchestration_pipeline.create_agent_workflow(workflow_type, context)
            
            # Add to active workflows
            self.active_workflows[workflow_id] = {
                "id": workflow_id,
                "type": workflow_type,
                "context": context,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
            
            # Log workflow start
            self.log_tools.record_log(
                task_id=workflow_id,
                event="WORKFLOW_STARTED",
                data={
                    "workflow_id": workflow_id,
                    "type": workflow_type,
                    "request": request
                }
            )
            
            # Start with Product Analyst
            await self._assign_initial_task(workflow_id, context)
            
            return workflow_id
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="WORKFLOW_START_ERROR",
                event="WORKFLOW_START_ERROR",
                data={"error": str(e)}
            )
            raise
    
    async def _assign_initial_task(self, workflow_id: str, context: Dict[str, Any]):
        """Assign the initial task in a workflow"""
        # Create specification task for Product Analyst
        task_id = f"TASK-{workflow_id}-001"
        
        task_description = f"Create detailed specification for: {context['user_request']}"
        
        # Create agent prompt
        agent_prompt = self.agent_factory.create_agent_prompt(
            "Product_Analyst",
            task_description,
            context
        )
        
        # Store task
        task_data = {
            "id": task_id,
            "workflow_id": workflow_id,
            "agent": "Product_Analyst",
            "description": task_description,
            "prompt": agent_prompt,
            "status": "assigned",
            "created_at": datetime.now().isoformat()
        }
        
        self.task_tools.create_new_task(
            title=f"Task {task_id}",
            description=task_description,
            parent_task_id=workflow_id
        )
        
        self.log_tools.record_log(
            task_id=task_id,
            event="TASK_ASSIGNED",
            data={
                "workflow_id": workflow_id,
                "agent": "Product_Analyst"
            }
        )
    
    async def process_agent_completion(self, task_id: str, agent_output: str) -> Dict[str, Any]:
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
                    "suggestion": handoff_packet.next_step_suggestion.value
                }
            )
            
            # Store handoff in history
            self.handoff_history.append(handoff_packet)
            
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
                "error": str(e)
            }
            )
            raise
    
    def _extract_handoff_packet(self, agent_output: str) -> Optional[HandoffPacket]:
        """Extract handoff packet from agent output"""
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
            
            return None
            
        except Exception as e:
            self.log_tools.record_log(
                task_id="HANDOFF_EXTRACTION_ERROR",
                event="HANDOFF_EXTRACTION_ERROR",
                data={"error": str(e)}
            )
            return None
    
    async def _process_artifacts(self, handoff_packet: HandoffPacket):
        """Process artifacts produced by agent"""
        for artifact_path in handoff_packet.artifacts_produced:
            try:
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
                        "task": handoff_packet.completed_task_id
                    }
            )
                else:
                    self.log_tools.record_log(
                task_id="ARTIFACT_MISSING",
                event="ARTIFACT_MISSING",
                data={
                        "artifact": artifact_path,
                        "task": handoff_packet.completed_task_id
                    }
            )
                    
            except Exception as e:
                self.log_tools.record_log(
                task_id="ARTIFACT_PROCESSING_ERROR",
                event="ARTIFACT_PROCESSING_ERROR",
                data={
                    "artifact": artifact_path,
                    "error": str(e)
                }
            )
    
    async def _index_artifact(self, artifact_path: str):
        """Index artifact for semantic search"""
        try:
            content = Path(artifact_path).read_text()
            self.indexing_tools.index_document(artifact_path, content)
        except Exception as e:
            self.log_tools.record_log(
                task_id="INDEXING_ERROR",
                event="INDEXING_ERROR",
                data={
                "artifact": artifact_path,
                "error": str(e)
            }
            )
    
    async def _route_next_tasks(self, handoff_packet: HandoffPacket) -> Dict[str, Any]:
        """Route next tasks based on handoff packet"""
        # Handle human approval cases
        if handoff_packet.next_step_suggestion == NextStepSuggestion.HUMAN_APPROVAL_NEEDED:
            return await self._handle_human_approval_gate(handoff_packet)
        
        # Use router to determine next tasks
        next_tasks = self.router.route_next_task(handoff_packet)
        
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
        
        # Create agent prompt
        agent_prompt = self.agent_factory.create_agent_prompt(
            task_config["agent"],
            task_config["description"],
            context
        )
        
        # Store task
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
        
        self.task_tools.create_task(next_task_id, task_data)
        
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
        # Find approval request
        approval_request = None
        for req in self.human_approval_queue:
            if req["id"] == approval_id:
                approval_request = req
                break
        
        if not approval_request:
            raise ValueError(f"Approval request not found: {approval_id}")
        
        # Process decision
        if decision.upper() == "APPROVE":
            return await self._handle_approval_approved(approval_request)
        elif decision.upper().startswith("CHANGES:"):
            return await self._handle_approval_changes(approval_request, decision)
        elif decision.upper().startswith("REJECT:"):
            return await self._handle_approval_rejected(approval_request, decision)
        else:
            raise ValueError(f"Invalid decision format: {decision}")
    
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
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
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
            "current_phase": workflow.get("current_phase", 0),
            "total_handoffs": len(related_handoffs),
            "pending_approvals": len(pending_approvals),
            "last_activity": related_handoffs[-1].timestamp if related_handoffs else None
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
    
    async def _execute_agent_task(self, agent_name: str, task_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent task (placeholder for actual implementation)"""
        # This would be replaced with actual agent execution logic
        # For now, simulate some work
        await asyncio.sleep(0.1)
        
        # Simulate occasional failures for testing
        import random
        if random.random() < 0.1:  # 10% failure rate for testing
            raise Exception("Simulated task failure")
        
        return {
            "status": "completed",
            "agent": agent_name,
            "result": f"Task completed by {agent_name}",
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
        # Clean up old checkpoints
        self.checkpoint_manager.cleanup_old_checkpoints(max_age_hours)
        
        # Clean up old error history
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        self.error_history = [
            error for error in self.error_history
            if datetime.fromisoformat(error.timestamp) > cutoff_time
        ]
        
        self.log_tools.record_log(
            task_id="CLEANUP",
            event="OLD_DATA_CLEANUP",
            data={"max_age_hours": max_age_hours}
        )
