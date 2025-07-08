"""
Configuration file for pytest that sets up the Python path for testing.
"""

import sys
import os
import pytest
import glob
import shutil
import fnmatch

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
        "./workspace/temp*",
        "./workspace/RUN-*",          # Workspace organizer run directories
        "./workspace/WORKFLOW-*",     # Legacy workflow directories
        "**/test_workspace*",         # Test workspace directories
        "**/auth_test_*",            # Authentication test directories
    ]
    
    print("CLEANUP: Removing test workspace directories...")
    removed_count = 0
    
    for pattern in workspace_patterns:
        for workspace_dir in glob.glob(pattern, recursive=True):
            try:
                if os.path.exists(workspace_dir) and os.path.isdir(workspace_dir):
                    shutil.rmtree(workspace_dir, ignore_errors=True)
                    removed_count += 1
                    print(f"✓ Removed workspace: {workspace_dir}")
            except (OSError, PermissionError) as e:
                print(f"⚠ Could not remove workspace {workspace_dir}: {e}")
    
    if removed_count > 0:
        print(f"✅ Removed {removed_count} workspace directories")
    else:
        print("✅ No workspace directories to clean up")


@pytest.fixture(autouse=True)
def cleanup_after_test(request):
    """Automatically cleanup test data after each test"""
    # Reset tracking before test
    reset_cleanup_tracking()
    
    # Yield control to the test
    yield
    
    # Cleanup after test
    test_name = request.node.name
    print(f"\n🧹 Cleaning up after test: {test_name}")
    
    cleanup_test_data()
    cleanup_workspace_directories()
    
    print(f"✅ Cleanup complete for: {test_name}")


@pytest.fixture(scope="session", autouse=True)
def cleanup_session():
    """Comprehensive cleanup at the end of the entire test session"""
    yield
    
    print("\n" + "="*50)
    print("FINAL TEST CLEANUP: Removing all generated files...")
    print("="*50)
    
    # Final cleanup
    cleanup_test_data()
    cleanup_workspace_directories()
    
    # Additional comprehensive cleanup
    cleanup_patterns = [
        "./workspace/RUN-*",          # Workspace organizer sessions
        "./workspace/WORKFLOW-*",     # Legacy workflow directories  
        "./temp_dir_*",               # Temporary directories (not temp files with content)
        "./test_workspace_*",         # Test workspace directories
        "./tempfile_*",               # Actual temporary files
        "./cache/test*",              # Test cache files
        "./logs/test*",               # Test log files
        "./artifacts/test*",          # Test artifact files
        "./results/test*",            # Test result files
        "./**/__pycache__",           # Python cache directories
        "./**/*.pyc",                 # Python cache files
        "./sandbox/temp",             # Sandbox temp directories only
        "./sandbox/**/temp",          # Nested sandbox temp directories
        "./tests/sandbox/temp*",      # Tests sandbox temp files
    ]
    
    # Exclude important files that contain "temp" in their name
    excluded_files = [
        "temp_prompt_test.py",        # Prompt optimization analysis
        "template_*",                 # Template files
        "config_template.py",         # Configuration template
        "*_template.py",              # Any template files
        "*_template.*",               # Any template files with any extension
    ]
    
    files_removed = 0
    dirs_removed = 0
    
    for pattern in cleanup_patterns:
        for path in glob.glob(pattern, recursive=True):
            # Check if this file should be excluded
            filename = os.path.basename(path)
            should_exclude = False
            
            for excluded_pattern in excluded_files:
                if excluded_pattern.startswith('*') or excluded_pattern.endswith('*'):
                    # Handle wildcard patterns
                    if fnmatch.fnmatch(filename, excluded_pattern):
                        should_exclude = True
                        break
                else:
                    # Handle exact matches
                    if excluded_pattern in filename:
                        should_exclude = True
                        break
            
            if should_exclude:
                print(f"⚠ Skipping excluded file: {path}")
                continue
                
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    files_removed += 1
                    print(f"✓ Removed file: {path}")
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    dirs_removed += 1
                    print(f"✓ Removed directory: {path}")
            except (OSError, PermissionError) as e:
                print(f"⚠ Could not remove {path}: {e}")
    
    print(f"\n✅ CLEANUP COMPLETE: Removed {files_removed} files and {dirs_removed} directories")
    print("="*50)
