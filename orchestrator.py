import queue
from enum import Enum
from tools.task_tools import create_new_task

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

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
