import os
import json
from datetime import datetime

LOGS_DIR = "c:\\Users\\a0526\\DEV\\Agents\\logs"
EXECUTION_LOG = os.path.join(LOGS_DIR, "execution.log")

def record_log(task_id: str, event: str, data: dict):
    """Records a structured log entry."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "event": event,
        "data": data
    }

    with open(EXECUTION_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"Recorded log for task {task_id}: {event}")
