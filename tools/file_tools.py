import os
from typing import Dict, Any, Optional, Tuple
from tools.security_framework import security_manager

def read_file(path: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """Reads the content of a specific file with security validation."""
    
    # Security validation
    is_allowed, reason = security_manager.validate_file_access(path, agent_id, "read")
    
    if not is_allowed:
        return {
            "success": False,
            "content": "",
            "error": f"Security violation: {reason}",
            "security_blocked": True
        }
    
    # Safe file reading
    success, content, error = security_manager.filesystem_sandbox.safe_read_file(path, agent_id)
    
    return {
        "success": success,
        "content": content or "",
        "error": error or "",
        "security_blocked": False
    }

def write_file(path: str, content: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """Writes content to a specific file with security validation."""
    
    # Security validation
    is_allowed, reason = security_manager.validate_file_access(path, agent_id, "write")
    
    if not is_allowed:
        return {
            "success": False,
            "error": f"Security violation: {reason}",
            "security_blocked": True
        }
    
    # Safe file writing
    success, error = security_manager.filesystem_sandbox.safe_write_file(path, content, agent_id)
    
    return {
        "success": success,
        "error": error or "",
        "security_blocked": False
    }

# Legacy functions for backward compatibility
def read_file_legacy(path: str):
    """Legacy function - use read_file with agent_id instead"""
    result = read_file(path, "legacy")
    if result["success"]:
        return result["content"]
    else:
        raise Exception(result["error"])

def write_file_legacy(path: str, content: str):
    """Legacy function - use write_file with agent_id instead"""
    result = write_file(path, content, "legacy")
    if not result["success"]:
        raise Exception(result["error"])
