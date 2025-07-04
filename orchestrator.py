import queue
from enum import Enum
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from tools.task_tools import create_new_task, TaskTools
from tools.log_tools import LogTools
from tools.indexing_tools import IndexingTools
from tools.file_tools import FileTools
from tools.git_tools import GitTools
from tools.execution_tools import ExecutionTools
from tools.handoff_system import HandoffPacket, ConductorRouter, TaskStatus, NextStepSuggestion

class ProjectState(Enum):
    PLANNING = "PLANNING"
    AWAITING_HUMAN_APPROVAL = "AWAITING_HUMAN_APPROVAL"
    DEVELOPING = "DEVELOPING"
    DEPLOYING = "DEPLOYING"
    DONE = "DONE"

class Orchestrator:
    def __init__(self):
        self.state = ProjectState.PLANNING
        self.task_queue = queue.Queue()
        self.router = ConductorRouter()
        self.active_handoff_packets = []
        print("Orchestrator initialized.")

    def run(self):
        print("Orchestrator run loop started.")
        while not self.task_queue.empty() or self.state != ProjectState.DONE:
            if self.state == ProjectState.PLANNING:
                print("Current State: PLANNING")
                # Create a task for the Product Analyst to create a specification.
                spec_task_id = create_new_task(
                    title="Create Specification for CSV Export",
                    description="Write a detailed specification for a feature that allows exporting a user list to a CSV file."
                )
                initial_task = {"agent": "Product Analyst", "task_id": spec_task_id, "details": "Create a specification for CSV export."}
                self.task_queue.put(initial_task)
                print(f"Task added to queue: {initial_task}")
                self.state = ProjectState.AWAITING_HUMAN_APPROVAL
                print("State changed to: AWAITING_HUMAN_APPROVAL")

            elif self.state == ProjectState.AWAITING_HUMAN_APPROVAL:
                print("Current State: AWAITING_HUMAN_APPROVAL")
                # Here, the orchestrator would present the plan to the human user for approval.
                # This simulates the human approval gate.
                print("Presenting plan to user for approval...")
                # In a real implementation, this would involve a tool call to get user input.
                user_input = input("Do you approve the plan? (yes/no): ")
                if user_input.lower() == "yes":
                    self.state = ProjectState.DEVELOPING
                    print("Plan approved by user. State changed to: DEVELOPING")
                else:
                    print("Plan rejected by user. Returning to PLANNING state.")
                    self.state = ProjectState.PLANNING

            elif self.state == ProjectState.DEVELOPING:
                print("Current State: DEVELOPING")
                if not self.task_queue.empty():
                    task = self.task_queue.get()
                    print(f"Processing task: {task}")
                    # Agent and Crew factory would be called here to execute the task.
                    print(f"Delegating task to {task['agent']}...")
                    # Simulate task completion
                    print(f"Task {task['task_id']} completed by {task['agent']}.")

                    # Simple Linear Workflow: Product Analyst -> Coder
                    if task['agent'] == "Product Analyst":
                        # Create a task for the Coder to implement the feature.
                        code_task_id = create_new_task(
                            title="Implement CSV Export Feature",
                            description="Write the code to export the user list to a CSV file based on the specification.",
                            parent_task_id=task['task_id']
                        )
                        coder_task = {"agent": "Coder", "task_id": code_task_id, "details": "Implement the CSV export feature."}
                        self.task_queue.put(coder_task)
                        print(f"Task added to queue: {coder_task}")

                else:
                    print("Development tasks finished.")
                    self.state = ProjectState.DONE # Or DEPLOYING if applicable
                    print("State changed to: DONE")

            elif self.state == ProjectState.DONE:
                print("Current State: DONE")
                print("All tasks completed. Shutting down.")
                break

    def process_handoff_packet(self, handoff_packet: HandoffPacket):
        """Process a handoff packet and route next tasks"""
        try:
            # Log the handoff packet
            self.log_tools.record_log(
                f"HANDOFF_PACKET_RECEIVED",
                {
                    "task_id": handoff_packet.completed_task_id,
                    "agent": handoff_packet.agent_name,
                    "status": handoff_packet.status.value,
                    "suggestion": handoff_packet.next_step_suggestion.value
                }
            )
            
            # Route next tasks
            next_tasks = self.router.route_next_task(handoff_packet)
            
            # Create and assign next tasks
            for task_config in next_tasks:
                task_id = self.create_and_assign_task(
                    title=task_config["title"],
                    description=task_config["description"],
                    agent_type=task_config["agent"],
                    priority=task_config.get("priority", "medium"),
                    context=task_config.get("context"),
                    artifacts=task_config.get("artifacts", [])
                )
                
                self.log_tools.record_log(
                    f"TASK_ROUTED",
                    {
                        "from_task": handoff_packet.completed_task_id,
                        "to_task": task_id,
                        "agent": task_config["agent"],
                        "routing_reason": handoff_packet.next_step_suggestion.value
                    }
                )
            
            # Store handoff packet for reference
            self.active_handoff_packets.append(handoff_packet)
            
            return next_tasks
            
        except Exception as e:
            self.log_tools.record_log(
                "HANDOFF_ROUTING_ERROR",
                {"error": str(e), "packet": handoff_packet.to_json()}
            )
            raise
    
    def create_handoff_packet(self, task_id: str, agent_name: str, status: TaskStatus, 
                            artifacts: List[str], suggestion: NextStepSuggestion, 
                            notes: str, dependencies_satisfied: List[str] = None,
                            blocking_issues: List[str] = None) -> HandoffPacket:
        """Create a standardized handoff packet"""
        return HandoffPacket(
            completed_task_id=task_id,
            agent_name=agent_name,
            status=status,
            artifacts_produced=artifacts,
            next_step_suggestion=suggestion,
            notes=notes,
            timestamp=datetime.now().isoformat(),
            dependencies_satisfied=dependencies_satisfied or [],
            blocking_issues=blocking_issues or []
        )
