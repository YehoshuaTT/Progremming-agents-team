"""
Security Framework for Autonomous Multi-Agent System
Implements sandboxing, command filtering, and access controls
"""

import os
import re
import json
import time
import hashlib
import subprocess
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class SecurityLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityAction(Enum):
    """Security response actions"""
    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    QUARANTINE = "quarantine"
    ESCALATE = "escalate"

@dataclass
class SecurityEvent:
    """Security event record"""
    event_type: str
    severity: SecurityLevel
    agent_id: str
    details: Dict[str, Any]
    timestamp: str
    action_taken: SecurityAction
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'severity': self.severity.value,
            'agent_id': self.agent_id,
            'details': self.details,
            'timestamp': self.timestamp,
            'action_taken': self.action_taken.value
        }

class CommandWhitelist:
    """Command whitelist and blacklist management"""
    
    def __init__(self):
        self.allowed_commands = {
            "safe": {
                "echo", "cat", "head", "tail", "grep", "find", "ls", "pwd", 
                "whoami", "date", "wc", "sort", "uniq", "diff"
            },
            "file_ops": {
                "mkdir", "cp", "mv", "touch", "chmod"
            },
            "git": {
                "git add", "git commit", "git push", "git pull", "git status",
                "git log", "git diff", "git branch", "git checkout"
            },
            "development": {
                "python", "pip", "npm", "node", "pytest", "flake8"
            }
        }
        
        self.forbidden_commands = {
            # Dangerous system commands
            "rm -rf", "format", "del", "rd /s", "fdisk", "mkfs",
            # Network commands
            "wget", "curl", "nc", "netcat", "telnet", "ssh",
            # Privilege escalation
            "sudo", "su", "chmod +s", "setuid",
            # System modification
            "crontab", "systemctl", "service", "chkconfig",
            # Dangerous Python/Shell
            "eval", "exec", "import os", "__import__"
        }
        
        self.command_patterns = {
            "file_deletion": re.compile(r'rm\s+.*-rf|del\s+/[sq]|rd\s+.*\/s'),
            "network_access": re.compile(r'wget|curl|nc|netcat|telnet|ssh'),
            "privilege_escalation": re.compile(r'sudo|su\s|chmod\s+\+s'),
            "system_modification": re.compile(r'crontab|systemctl|service'),
            "code_injection": re.compile(r'eval\s*\(|exec\s*\(|__import__')
        }
    
    def is_command_allowed(self, command: str) -> tuple[bool, Optional[str]]:
        """Check if command is allowed and return reason if not"""
        command_lower = command.lower().strip()
        
        # Check dangerous patterns first
        for pattern_name, pattern in self.command_patterns.items():
            if pattern.search(command_lower):
                return False, f"Dangerous pattern detected: {pattern_name}"
        
        # Check if command starts with allowed command
        command_parts = command_lower.split()
        if not command_parts:
            return False, "Empty command"
        
        base_command = command_parts[0]
        
        # Check forbidden commands (exact match on base command)
        for forbidden in self.forbidden_commands:
            if base_command == forbidden or base_command.startswith(forbidden + " "):
                return False, f"Forbidden command detected: {forbidden}"
        
        # Check against whitelist
        for category, commands in self.allowed_commands.items():
            if base_command in commands or any(cmd.startswith(base_command) for cmd in commands):
                return True, None
        
        return False, f"Command not in whitelist: {base_command}"
    
    def add_allowed_command(self, command: str, category: str = "custom"):
        """Add a command to the whitelist"""
        if category not in self.allowed_commands:
            self.allowed_commands[category] = set()
        self.allowed_commands[category].add(command)
    
    def remove_allowed_command(self, command: str, category: str):
        """Remove a command from the whitelist"""
        if category in self.allowed_commands:
            self.allowed_commands[category].discard(command)

class FileSystemSandbox:
    """File system access control and sandboxing"""
    
    def __init__(self, base_sandbox_path: str = "sandbox"):
        self.base_sandbox_path = Path(base_sandbox_path).resolve()
        self.base_sandbox_path.mkdir(exist_ok=True)
        
        # Create standard sandbox structure
        self._create_sandbox_structure()
        
        # Allowed paths for different operations
        self.shared_paths = {
            self.base_sandbox_path / "shared",
            self.base_sandbox_path / "templates",
            self.base_sandbox_path / "dependencies"
        }
    
    def _create_sandbox_structure(self):
        """Create standard sandbox directory structure"""
        directories = [
            "agents",
            "shared",
            "templates", 
            "dependencies",
            "logs",
            "temp"
        ]
        
        for directory in directories:
            (self.base_sandbox_path / directory).mkdir(exist_ok=True)
    
    def get_agent_sandbox_path(self, agent_id: str) -> Path:
        """Get or create agent-specific sandbox path"""
        agent_path = self.base_sandbox_path / "agents" / agent_id
        agent_path.mkdir(parents=True, exist_ok=True)
        
        # Create agent subdirectories
        for subdir in ["workspace", "temp", "output", "logs"]:
            (agent_path / subdir).mkdir(exist_ok=True)
        
        return agent_path
    
    def validate_path(self, path: str, agent_id: str) -> tuple[bool, Optional[Path]]:
        """Validate if path is allowed for agent access"""
        try:
            # Get agent sandbox
            agent_sandbox = self.get_agent_sandbox_path(agent_id)
            
            # If path is relative, resolve it relative to agent sandbox
            if not os.path.isabs(path):
                resolved_path = (agent_sandbox / path).resolve()
            else:
                resolved_path = Path(path).resolve()
            
            # Check if path is within agent sandbox or shared areas
            allowed_paths = [agent_sandbox] + list(self.shared_paths)
            
            for allowed_path in allowed_paths:
                try:
                    resolved_path.relative_to(allowed_path)
                    return True, resolved_path
                except ValueError:
                    continue
            
            return False, None
            
        except (OSError, ValueError) as e:
            return False, None
    
    def safe_read_file(self, path: str, agent_id: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Safely read file with sandbox validation"""
        is_valid, resolved_path = self.validate_path(path, agent_id)
        
        if not is_valid:
            return False, None, f"Path access denied: {path}"
        
        try:
            if not resolved_path.exists():
                return False, None, f"File not found: {path}"
            
            if not resolved_path.is_file():
                return False, None, f"Path is not a file: {path}"
            
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return True, content, None
            
        except Exception as e:
            return False, None, f"Error reading file: {str(e)}"
    
    def safe_write_file(self, path: str, content: str, agent_id: str) -> tuple[bool, Optional[str]]:
        """Safely write file with sandbox validation"""
        is_valid, resolved_path = self.validate_path(path, agent_id)
        
        if not is_valid:
            return False, f"Path access denied: {path}"
        
        try:
            # Create parent directories if needed
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, None
            
        except Exception as e:
            return False, f"Error writing file: {str(e)}"

class NetworkSecurityManager:
    """Network access control and monitoring"""
    
    def __init__(self):
        self.allowed_domains = {
            "api.anthropic.com",
            "api.openai.com",
            "github.com", 
            "api.github.com",
            "stackoverflow.com",
            "docs.python.org",
            "pypi.org",
            "npmjs.com"
        }
        
        self.rate_limits = {
            "api_calls_per_hour": 100,
            "downloads_per_hour": 10,
            "requests_per_hour": 100
        }
        
        self.agent_usage: Dict[str, Dict[str, List[float]]] = {}
    
    def is_domain_allowed(self, url: str) -> tuple[bool, Optional[str]]:
        """Check if domain is allowed for access"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            
            if domain in self.allowed_domains:
                return True, None
            
            return False, f"Domain not allowed: {domain}"
            
        except Exception as e:
            return False, f"Invalid URL: {str(e)}"
    
    def check_rate_limit(self, agent_id: str, request_type: str = "requests") -> tuple[bool, Optional[str]]:
        """Check if agent has exceeded rate limits"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Initialize agent usage if not exists
        if agent_id not in self.agent_usage:
            self.agent_usage[agent_id] = {
                "api_calls": [],
                "downloads": [],
                "requests": []
            }
        
        # Clean old entries
        self.agent_usage[agent_id][request_type] = [
            timestamp for timestamp in self.agent_usage[agent_id][request_type]
            if timestamp > hour_ago
        ]
        
        # Check current usage
        current_usage = len(self.agent_usage[agent_id][request_type])
        limit_key = f"{request_type}_per_hour"
        
        if limit_key in self.rate_limits:
            if current_usage >= self.rate_limits[limit_key]:
                return False, f"Rate limit exceeded for {request_type}: {current_usage}/{self.rate_limits[limit_key]}"
        
        # Record this request
        self.agent_usage[agent_id][request_type].append(current_time)
        
        return True, None

class SecurityLogger:
    """Security event logging and monitoring"""
    
    def __init__(self, log_file: str = "security.log"):
        self.log_file = Path(log_file)
        self.events: List[SecurityEvent] = []
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_security_event(self, event_type: str, severity: SecurityLevel, 
                          agent_id: str, details: Dict[str, Any], 
                          action_taken: SecurityAction):
        """Log a security event"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            agent_id=agent_id,
            details=details,
            timestamp=datetime.now().isoformat(),
            action_taken=action_taken
        )
        
        self.events.append(event)
        
        # Write to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
        
        # Print critical events to console
        if severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            print(f"SECURITY ALERT [{severity.value.upper()}]: {event_type} - Agent: {agent_id}")
    
    def get_recent_events(self, hours: int = 24) -> List[SecurityEvent]:
        """Get security events from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            event for event in self.events
            if datetime.fromisoformat(event.timestamp) > cutoff_time
        ]
    
    def get_agent_events(self, agent_id: str, hours: int = 24) -> List[SecurityEvent]:
        """Get security events for specific agent"""
        recent_events = self.get_recent_events(hours)
        return [event for event in recent_events if event.agent_id == agent_id]

class SecurityManager:
    """Main security manager coordinating all security components"""
    
    def __init__(self, sandbox_path: str = "sandbox"):
        self.command_whitelist = CommandWhitelist()
        self.filesystem_sandbox = FileSystemSandbox(sandbox_path)
        self.network_security = NetworkSecurityManager()
        self.security_logger = SecurityLogger()
        
        # Security configuration
        self.strict_mode = True
        self.auto_quarantine = True
        
    def validate_command_execution(self, command: str, agent_id: str) -> tuple[bool, Optional[str]]:
        """Validate if command execution is allowed"""
        is_allowed, reason = self.command_whitelist.is_command_allowed(command)
        
        if not is_allowed:
            self.security_logger.log_security_event(
                event_type="command_blocked",
                severity=SecurityLevel.HIGH,
                agent_id=agent_id,
                details={"command": command, "reason": reason},
                action_taken=SecurityAction.DENY
            )
            
        return is_allowed, reason
    
    def validate_file_access(self, file_path: str, agent_id: str, operation: str) -> tuple[bool, Optional[str]]:
        """Validate file system access"""
        is_valid, resolved_path = self.filesystem_sandbox.validate_path(file_path, agent_id)
        
        if not is_valid:
            self.security_logger.log_security_event(
                event_type="file_access_denied",
                severity=SecurityLevel.MEDIUM,
                agent_id=agent_id,
                details={"path": file_path, "operation": operation},
                action_taken=SecurityAction.DENY
            )
            
            return False, f"File access denied: {file_path}"
        
        return True, None
    
    def validate_network_request(self, url: str, agent_id: str) -> tuple[bool, Optional[str]]:
        """Validate network request"""
        # Check domain
        is_domain_allowed, domain_reason = self.network_security.is_domain_allowed(url)
        if not is_domain_allowed:
            self.security_logger.log_security_event(
                event_type="domain_blocked",
                severity=SecurityLevel.MEDIUM,
                agent_id=agent_id,
                details={"url": url, "reason": domain_reason},
                action_taken=SecurityAction.DENY
            )
            return False, domain_reason
        
        # Check rate limits
        is_rate_ok, rate_reason = self.network_security.check_rate_limit(agent_id)
        if not is_rate_ok:
            self.security_logger.log_security_event(
                event_type="rate_limit_exceeded",
                severity=SecurityLevel.MEDIUM,
                agent_id=agent_id,
                details={"url": url, "reason": rate_reason},
                action_taken=SecurityAction.DENY
            )
            return False, rate_reason
        
        return True, None
    
    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate security report"""
        recent_events = self.security_logger.get_recent_events(hours)
        
        # Count events by type and severity
        event_counts = {}
        severity_counts = {}
        
        for event in recent_events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
            severity_counts[event.severity.value] = severity_counts.get(event.severity.value, 0) + 1
        
        return {
            "report_period_hours": hours,
            "total_events": len(recent_events),
            "events_by_type": event_counts,
            "events_by_severity": severity_counts,
            "critical_events": [
                event.to_dict() for event in recent_events
                if event.severity == SecurityLevel.CRITICAL
            ],
            "generated_at": datetime.now().isoformat()
        }

# Global security manager instance
security_manager = SecurityManager()
