#!/usr/bin/env python3
"""Debug command checking"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from tools.security_framework import CommandWhitelist

# Test command validation
whitelist = CommandWhitelist()

test_commands = [
    "echo 'Success'",
    "echo",
    "ls",
    "pwd",
    "dangerous_command"
]

print("Testing command validation:")
for cmd in test_commands:
    allowed, reason = whitelist.is_command_allowed(cmd)
    print(f"Command: '{cmd}' -> Allowed: {allowed}, Reason: {reason}")
    
    # Debug: show command parts
    parts = cmd.lower().split()
    if parts:
        base_cmd = parts[0]
        print(f"  Base command: '{base_cmd}'")
        
        # Check if in whitelist
        for category, commands in whitelist.allowed_commands.items():
            if base_cmd in commands:
                print(f"  Found in category '{category}': {base_cmd}")
                break
        else:
            print(f"  Not found in whitelist")
    print()
