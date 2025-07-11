import os
import json
from datetime import datetime

# Use project-relative path for tasks
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_DIR = os.path.join(PROJECT_ROOT, "tasks")

def create_new_task(title: str, description: str, parent_task_id: str | None = None):
    """Creates a new task directory and task.json file."""
    global TASKS_DIR
    
    task_id = f"TASK-{int(datetime.now().timestamp())}"
    task_dir = os.path.join(TASKS_DIR, task_id)
    
    try:
        os.makedirs(task_dir, exist_ok=True)
    except PermissionError:
        # Fallback to temp directory if project tasks not accessible
        import tempfile
        TASKS_DIR = os.path.join(tempfile.gettempdir(), "agent_tasks")
        task_dir = os.path.join(TASKS_DIR, task_id)
        os.makedirs(task_dir, exist_ok=True)

    task_data = {
        "id": task_id,
        "title": title,
        "description": description,
        "parent_task_id": parent_task_id,
        "status": "OPEN",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "files": []
    }

    with open(os.path.join(task_dir, "task.json"), "w") as f:
        json.dump(task_data, f, indent=4)

    print(f"Created new task with ID: {task_id}")
    return task_id

def update_task_status(task_id: str, status: str):
    """Updates the status of a task."""
    task_dir = os.path.join(TASKS_DIR, task_id)
    task_file = os.path.join(task_dir, "task.json")

    if not os.path.exists(task_file):
        print(f"Error: Task file for {task_id} not found.")
        return

    with open(task_file, "r+") as f:
        task_data = json.load(f)
        task_data["status"] = status
        task_data["updated_at"] = datetime.now().isoformat()
        f.seek(0)
        json.dump(task_data, f, indent=4)
        f.truncate()

    print(f"Updated status for task {task_id} to {status}")
