"""
Base test class with comprehensive cleanup capabilities.
All test classes should inherit from this for proper cleanup.
"""

import unittest
import tempfile
import os
import shutil
from typing import List, Optional
from tests.test_cleanup_utils import (
    get_test_temp_dir, 
    track_test_file, 
    track_test_directory,
    cleanup_test_data
)


class BaseTestCase(unittest.TestCase):
    """Enhanced base test case with automatic cleanup"""
    
    def setUp(self):
        """Set up test environment with cleanup tracking"""
        super().setUp()
        self.test_files: List[str] = []
        self.test_dirs: List[str] = []
        self.temp_dirs: List[str] = []
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up tracked files
        for file_path in self.test_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except (OSError, PermissionError):
                    pass
        
        # Clean up tracked directories
        for dir_path in self.test_dirs:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path, ignore_errors=True)
                except (OSError, PermissionError):
                    pass
        
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except (OSError, PermissionError):
                    pass
        
        super().tearDown()
    
    def create_temp_dir(self, prefix: str = "test_") -> str:
        """Create a temporary directory for testing"""
        temp_dir = get_test_temp_dir(prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def add_test_file(self, file_path: str) -> None:
        """Add a file to be cleaned up after the test"""
        self.test_files.append(file_path)
        track_test_file(file_path)
    
    def add_test_directory(self, dir_path: str) -> None:
        """Add a directory to be cleaned up after the test"""
        self.test_dirs.append(dir_path)
        track_test_directory(dir_path)
    
    def create_test_file(self, content: str = "", suffix: str = ".txt") -> str:
        """Create a temporary test file"""
        fd, file_path = tempfile.mkstemp(suffix=suffix, prefix="test_")
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        self.add_test_file(file_path)
        return file_path
    
    def create_test_directory(self, prefix: str = "test_dir_") -> str:
        """Create a temporary test directory"""
        temp_dir = self.create_temp_dir(prefix)
        self.add_test_directory(temp_dir)
        return temp_dir


class AsyncBaseTestCase(BaseTestCase):
    """Base test case for async tests with cleanup"""
    
    async def asyncSetUp(self):
        """Async setup with cleanup tracking"""
        super().setUp()
    
    async def asyncTearDown(self):
        """Async teardown with cleanup"""
        super().tearDown()


class IntegrationTestCase(BaseTestCase):
    """Base test case for integration tests with comprehensive cleanup"""
    
    def setUp(self):
        """Set up integration test environment"""
        super().setUp()
        # Additional setup for integration tests
        self.workspace_dirs: List[str] = []
        self.log_files: List[str] = []
    
    def tearDown(self):
        """Clean up integration test environment"""
        # Clean up workspace directories
        for workspace_dir in self.workspace_dirs:
            if os.path.exists(workspace_dir):
                try:
                    shutil.rmtree(workspace_dir, ignore_errors=True)
                except (OSError, PermissionError):
                    pass
        
        # Clean up log files
        for log_file in self.log_files:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except (OSError, PermissionError):
                    pass
        
        super().tearDown()
    
    def create_workspace_dir(self, name: str = "test_workspace") -> str:
        """Create a workspace directory for integration testing"""
        workspace_dir = self.create_temp_dir(f"{name}_")
        self.workspace_dirs.append(workspace_dir)
        return workspace_dir
    
    def create_log_file(self, name: str = "test.log") -> str:
        """Create a log file for integration testing"""
        log_file = self.create_test_file(suffix=f"_{name}")
        self.log_files.append(log_file)
        return log_file
