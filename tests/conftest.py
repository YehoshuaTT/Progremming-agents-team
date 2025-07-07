"""
Configuration file for pytest that sets up the Python path for testing.
"""

import sys
import os
import pytest
import glob
import shutil

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)

# Also add the key directories
sys.path.insert(0, os.path.join(parent_dir, 'core'))
sys.path.insert(0, os.path.join(parent_dir, 'tools'))
sys.path.insert(0, os.path.join(parent_dir, 'development'))
sys.path.insert(0, os.path.join(parent_dir, 'project_management'))

# Import cleanup utilities
from tests.test_cleanup_utils import cleanup_test_data, reset_cleanup_tracking


def cleanup_workspace_directories():
    """Clean up workspace directories created by tests"""
    workspace_patterns = [
        "./workspace/agent-driven-*",
        "./workspace/test-*",
        "./workspace/temp*"
    ]
    
    for pattern in workspace_patterns:
        for workspace_dir in glob.glob(pattern):
            try:
                if os.path.exists(workspace_dir):
                    shutil.rmtree(workspace_dir, ignore_errors=True)
            except (OSError, PermissionError):
                pass


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically cleanup test data after each test"""
    # Reset tracking before test
    reset_cleanup_tracking()
    
    # Yield control to the test
    yield
    
    # Cleanup after test
    cleanup_test_data()
    cleanup_workspace_directories()


@pytest.fixture(scope="session", autouse=True)
def cleanup_session():
    """Cleanup at the end of the entire test session"""
    yield
    # Final cleanup
    cleanup_test_data()
    cleanup_workspace_directories()
