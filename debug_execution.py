#!/usr/bin/env python3
"""Debug execution tools"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from execution_tools import execute_shell_command

# Test execution
result = execute_shell_command("echo 'Success'", agent_id="test_agent")
print(f"Result: {result}")
print(f"Success: {result.get('success', 'No success key')}")
print(f"Output: {result.get('output', 'No output key')}")
print(f"Error: {result.get('error', 'No error key')}")
print(f"Sandbox: {result.get('sandbox_restricted', 'No sandbox key')}")
