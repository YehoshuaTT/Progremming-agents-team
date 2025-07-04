import subprocess
from typing import Dict, Any, Optional, Tuple
from tools.security_framework import security_manager, SecurityLevel, SecurityAction

def execute_shell_command(command: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """Runs a shell (terminal) command with security validation."""
    
    # Security validation
    is_allowed, reason = security_manager.validate_command_execution(command, agent_id)
    
    if not is_allowed:
        return {
            "success": False,
            "output": "",
            "error": f"Security violation: {reason}",
            "security_blocked": True
        }
    
    try:
        # Execute in sandbox context
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30,  # 30 second timeout
            cwd=str(security_manager.filesystem_sandbox.get_agent_sandbox_path(agent_id))
        )
        
        # Log successful execution
        security_manager.security_logger.log_security_event(
            event_type="command_executed",
            severity=SecurityLevel.LOW,
            agent_id=agent_id,
            details={"command": command, "return_code": result.returncode},
            action_taken=SecurityAction.ALLOW
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "security_blocked": False
            }
        
        return {
            "success": True,
            "output": result.stdout,
            "error": "",
            "return_code": 0,
            "security_blocked": False
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Command execution timeout (30 seconds)",
            "security_blocked": False
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"Execution error: {str(e)}",
            "security_blocked": False
        }

# Legacy function for backward compatibility
def execute_shell_command_legacy(command: str):
    """Legacy function - use execute_shell_command with agent_id instead"""
    result = execute_shell_command(command, "legacy")
    if result["success"]:
        return result["output"]
    else:
        print(f"Error executing command: {command}")
        print(result["error"])
        return result["error"]
