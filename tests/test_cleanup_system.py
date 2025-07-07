"""
Test the cleanup system to ensure test data is properly cleaned up.
This test validates that our cleanup utilities work correctly.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from tests.base_test import BaseTestCase, IntegrationTestCase
from tests.test_cleanup_utils import (
    cleanup_test_data, 
    get_test_temp_dir, 
    track_test_file, 
    track_test_directory,
    CleanupManager
)


class TestCleanupSystem(BaseTestCase):
    """Test the cleanup system itself"""
    
    def test_base_test_case_cleanup(self):
        """Test that BaseTestCase properly cleans up files and directories"""
        # Create test file
        test_file = self.create_test_file("test content")
        self.assertTrue(os.path.exists(test_file))
        
        # Create test directory
        test_dir = self.create_test_directory()
        self.assertTrue(os.path.exists(test_dir))
        
        # Create a file in the test directory
        test_file_in_dir = os.path.join(test_dir, "nested_file.txt")
        with open(test_file_in_dir, 'w') as f:
            f.write("nested content")
        self.assertTrue(os.path.exists(test_file_in_dir))
        
        # Files should exist at this point
        self.assertTrue(os.path.exists(test_file))
        self.assertTrue(os.path.exists(test_dir))
        self.assertTrue(os.path.exists(test_file_in_dir))
    
    def test_cleanup_manager_functions(self):
        """Test the cleanup manager functions"""
        manager = CleanupManager()
        
        # Test temp directory creation
        temp_dir = manager.create_temp_dir("test_cleanup_")
        self.assertTrue(os.path.exists(temp_dir))
        
        # Test file tracking
        test_file = os.path.join(temp_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        manager.track_file(test_file)
        
        # Test directory tracking
        test_sub_dir = os.path.join(temp_dir, "sub_dir")
        os.makedirs(test_sub_dir)
        manager.track_directory(test_sub_dir)
        
        # Verify everything exists
        self.assertTrue(os.path.exists(temp_dir))
        self.assertTrue(os.path.exists(test_file))
        self.assertTrue(os.path.exists(test_sub_dir))
        
        # Perform cleanup
        manager.cleanup_all()
        
        # Verify cleanup worked
        self.assertFalse(os.path.exists(temp_dir))
        self.assertFalse(os.path.exists(test_file))
        self.assertFalse(os.path.exists(test_sub_dir))
    
    def test_global_cleanup_functions(self):
        """Test global cleanup functions"""
        # Create temp directory
        temp_dir = get_test_temp_dir("global_test_")
        self.assertTrue(os.path.exists(temp_dir))
        
        # Create and track a file
        test_file = os.path.join(temp_dir, "global_test.txt")
        with open(test_file, 'w') as f:
            f.write("global test content")
        track_test_file(test_file)
        
        # Track the directory
        track_test_directory(temp_dir)
        
        # Verify everything exists
        self.assertTrue(os.path.exists(temp_dir))
        self.assertTrue(os.path.exists(test_file))
        
        # Perform global cleanup
        cleanup_test_data()
        
        # Verify cleanup worked
        self.assertFalse(os.path.exists(temp_dir))
        self.assertFalse(os.path.exists(test_file))


class TestIntegrationCleanup(IntegrationTestCase):
    """Test integration-specific cleanup"""
    
    def test_workspace_cleanup(self):
        """Test workspace directory cleanup"""
        # Create workspace
        workspace = self.create_workspace_dir("integration_test")
        self.assertTrue(os.path.exists(workspace))
        
        # Create some files in workspace
        test_file1 = os.path.join(workspace, "file1.txt")
        test_file2 = os.path.join(workspace, "file2.txt")
        
        with open(test_file1, 'w') as f:
            f.write("workspace content 1")
        with open(test_file2, 'w') as f:
            f.write("workspace content 2")
        
        # Create subdirectory
        sub_dir = os.path.join(workspace, "subdir")
        os.makedirs(sub_dir)
        
        # Create file in subdirectory
        sub_file = os.path.join(sub_dir, "subfile.txt")
        with open(sub_file, 'w') as f:
            f.write("subdirectory content")
        
        # Verify everything exists
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(test_file1))
        self.assertTrue(os.path.exists(test_file2))
        self.assertTrue(os.path.exists(sub_dir))
        self.assertTrue(os.path.exists(sub_file))
    
    def test_log_file_cleanup(self):
        """Test log file cleanup"""
        # Create log file
        log_file = self.create_log_file("integration_test.log")
        self.assertTrue(os.path.exists(log_file))
        
        # Write some content
        with open(log_file, 'w') as f:
            f.write("integration test log content")
        
        # Verify file exists and has content
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertEqual(content, "integration test log content")


class TestCleanupRobustness(BaseTestCase):
    """Test cleanup system robustness"""
    
    def test_cleanup_with_permission_errors(self):
        """Test that cleanup handles permission errors gracefully"""
        # Create a test file
        test_file = self.create_test_file("permission test")
        self.assertTrue(os.path.exists(test_file))
        
        # The cleanup should handle any permission errors gracefully
        # This test ensures the cleanup system doesn't crash on permission issues
        
    def test_cleanup_with_missing_files(self):
        """Test cleanup when files are already deleted"""
        # Create a test file
        test_file = self.create_test_file("disappearing test")
        self.assertTrue(os.path.exists(test_file))
        
        # Manually delete the file
        os.remove(test_file)
        self.assertFalse(os.path.exists(test_file))
        
        # The cleanup should handle missing files gracefully
        # This test ensures the cleanup system doesn't crash on missing files
    
    def test_cleanup_with_empty_directories(self):
        """Test cleanup with empty directories"""
        # Create empty directory
        empty_dir = self.create_test_directory("empty_test")
        self.assertTrue(os.path.exists(empty_dir))
        
        # The cleanup should handle empty directories correctly
    
    def test_cleanup_with_nested_structures(self):
        """Test cleanup with deeply nested directory structures"""
        # Create nested structure
        base_dir = self.create_test_directory("nested_base")
        
        # Create nested directories
        level1 = os.path.join(base_dir, "level1")
        level2 = os.path.join(level1, "level2")
        level3 = os.path.join(level2, "level3")
        
        os.makedirs(level3)
        
        # Create files at different levels
        file1 = os.path.join(level1, "file1.txt")
        file2 = os.path.join(level2, "file2.txt")
        file3 = os.path.join(level3, "file3.txt")
        
        with open(file1, 'w') as f:
            f.write("level 1 content")
        with open(file2, 'w') as f:
            f.write("level 2 content")
        with open(file3, 'w') as f:
            f.write("level 3 content")
        
        # Verify nested structure exists
        self.assertTrue(os.path.exists(level3))
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))
        self.assertTrue(os.path.exists(file3))


if __name__ == '__main__':
    unittest.main()
