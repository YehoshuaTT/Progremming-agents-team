import os
from typing import Dict, Any, Optional, Tuple
from tools.security_framework import security_manager
from tools.tool_cache import cache_tool_output, tool_cache

@cache_tool_output("read_file")
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

@cache_tool_output("list_dir")
def list_dir(path: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """List directory contents with security validation and caching."""
    
    # Security validation
    is_allowed, reason = security_manager.validate_file_access(path, agent_id, "read")
    
    if not is_allowed:
        return {
            "success": False,
            "contents": [],
            "error": f"Security violation: {reason}",
            "security_blocked": True
        }
    
    try:
        if not os.path.exists(path):
            return {
                "success": False,
                "contents": [],
                "error": f"Path does not exist: {path}",
                "security_blocked": False
            }
        
        if not os.path.isdir(path):
            return {
                "success": False,
                "contents": [],
                "error": f"Path is not a directory: {path}",
                "security_blocked": False
            }
        
        contents = os.listdir(path)
        return {
            "success": True,
            "contents": contents,
            "error": "",
            "security_blocked": False
        }
        
    except Exception as e:
        return {
            "success": False,
            "contents": [],
            "error": str(e),
            "security_blocked": False
        }

@cache_tool_output("get_file_info")
def get_file_info(path: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """Get file information with security validation and caching."""
    
    # Security validation
    is_allowed, reason = security_manager.validate_file_access(path, agent_id, "read")
    
    if not is_allowed:
        return {
            "success": False,
            "info": {},
            "error": f"Security violation: {reason}",
            "security_blocked": True
        }
    
    try:
        if not os.path.exists(path):
            return {
                "success": False,
                "info": {},
                "error": f"Path does not exist: {path}",
                "security_blocked": False
            }
        
        stat_info = os.stat(path)
        info = {
            "size": stat_info.st_size,
            "modified": stat_info.st_mtime,
            "created": stat_info.st_ctime,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "permissions": oct(stat_info.st_mode)[-3:]
        }
        
        return {
            "success": True,
            "info": info,
            "error": "",
            "security_blocked": False
        }
        
    except Exception as e:
        return {
            "success": False,
            "info": {},
            "error": str(e),
            "security_blocked": False
        }

def invalidate_file_cache(file_path: str):
    """Invalidate cache entries for a specific file"""
    tool_cache.invalidate_file_cache(file_path)
