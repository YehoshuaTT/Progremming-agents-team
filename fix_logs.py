"""
Script to fix all log calls in enhanced_orchestrator.py
"""

import re

# Read the file
with open('c:/Users/a0526/DEV/Agents/enhanced_orchestrator.py', 'r') as f:
    content = f.read()

# Pattern to match old log calls
pattern = r'self\.log_tools\.record_log\("([^"]+)",\s*\{([^}]+)\}\)'

def replace_log_call(match):
    event = match.group(1)
    data_content = match.group(2)
    
    # Extract task_id from data if present, otherwise use event as task_id
    task_id_match = re.search(r'"task_id":\s*"([^"]+)"', data_content)
    if task_id_match:
        task_id = task_id_match.group(1)
        # Remove task_id from data
        data_content = re.sub(r'"task_id":\s*"[^"]+",?\s*', '', data_content)
    else:
        task_id = event
    
    # Clean up trailing commas
    data_content = re.sub(r',\s*$', '', data_content)
    
    return f'''self.log_tools.record_log(
                task_id="{task_id}",
                event="{event}",
                data={{{data_content}}}
            )'''

# Replace all matches
new_content = re.sub(pattern, replace_log_call, content, flags=re.DOTALL)

# Write back
with open('c:/Users/a0526/DEV/Agents/enhanced_orchestrator.py', 'w') as f:
    f.write(new_content)

print("Fixed all log calls in enhanced_orchestrator.py")
