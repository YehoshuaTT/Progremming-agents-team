import os
import json
from datetime import datetime

# Use project-relative path for logs
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
EXECUTION_LOG = os.path.join(LOGS_DIR, "execution.log")

def record_log(task_id: str, event: str, data: dict):
    """Records a structured log entry."""
    global LOGS_DIR, EXECUTION_LOG
    
    # Ensure logs directory exists
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
    except PermissionError:
        # Fallback to temp directory if project logs not accessible
        import tempfile
        LOGS_DIR = os.path.join(tempfile.gettempdir(), "agent_logs")
        EXECUTION_LOG = os.path.join(LOGS_DIR, "execution.log")
        os.makedirs(LOGS_DIR, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "event": event,
        "data": data
    }

    with open(EXECUTION_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"Recorded log for task {task_id}: {event}")
