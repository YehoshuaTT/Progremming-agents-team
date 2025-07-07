"""
Test utilities for comprehensive cleanup of test data.
This module provides centralized cleanup functions for all test types.
"""

import os
import shutil
import tempfile
import glob
from pathlib import Path
from typing import List, Optional
from tools.log_tools import LOGS_DIR
from tools.task_tools import TASKS_DIR


class CleanupManager:
    """Centralized test cleanup manager"""
    
    def __init__(self):
        self.temp_dirs: List[str] = []
        self.test_files: List[str] = []
        self.test_dirs: List[str] = []
        self.project_root = Path(__file__).parent.parent
        
    def create_temp_dir(self, prefix: str = "test_") -> str:
        """Create a temporary directory and track it for cleanup"""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def track_file(self, file_path: str) -> None:
        """Track a file for cleanup"""
        self.test_files.append(file_path)
    
    def track_directory(self, dir_path: str) -> None:
        """Track a directory for cleanup"""
        self.test_dirs.append(dir_path)
    
    def cleanup_logs(self) -> None:
        """Clean up all log files created during testing"""
        if os.path.exists(LOGS_DIR):
            for file in glob.glob(os.path.join(LOGS_DIR, "*.log")):
                try:
                    os.remove(file)
                except (OSError, PermissionError):
                    pass
    
    def cleanup_tasks(self) -> None:
        """Clean up all task directories created during testing"""
        if os.path.exists(TASKS_DIR):
            for task_dir in glob.glob(os.path.join(TASKS_DIR, "TASK-*")):
                try:
                    shutil.rmtree(task_dir, ignore_errors=True)
                except (OSError, PermissionError):
                    pass
    
    def cleanup_cache(self) -> None:
        """Clean up cache directories"""
        cache_dirs = [
            os.path.join(self.project_root, "cache"),
            os.path.join(self.project_root, "workspace", "cache"),
            os.path.join(self.project_root, ".cache"),
        ]
        
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                        else:
                            os.remove(item_path)
                    except (OSError, PermissionError):
                        pass
    
    def cleanup_workspace(self) -> None:
        """Clean up workspace test artifacts"""
        workspace_dirs = [
            os.path.join(self.project_root, "workspace", "temp*"),
            os.path.join(self.project_root, "workspace", "test_*"),
            os.path.join(self.project_root, "workspace", "agent-driven-*"),
        ]
        
        for pattern in workspace_dirs:
            for path in glob.glob(pattern):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
                except (OSError, PermissionError):
                    pass
    
    def cleanup_tracked_files(self) -> None:
        """Clean up tracked files"""
        for file_path in self.test_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except (OSError, PermissionError):
                pass
    
    def cleanup_tracked_directories(self) -> None:
        """Clean up tracked directories"""
        for dir_path in self.test_dirs:
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)
            except (OSError, PermissionError):
                pass
    
    def cleanup_temp_directories(self) -> None:
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except (OSError, PermissionError):
                pass
    
    def cleanup_all(self) -> None:
        """Perform comprehensive cleanup"""
        self.cleanup_logs()
        self.cleanup_tasks()
        self.cleanup_cache()
        self.cleanup_workspace()
        self.cleanup_tracked_files()
        self.cleanup_tracked_directories()
        self.cleanup_temp_directories()
    
    def reset(self) -> None:
        """Reset tracking lists"""
        self.temp_dirs.clear()
        self.test_files.clear()
        self.test_dirs.clear()


# Global cleanup manager instance
cleanup_manager = CleanupManager()


def cleanup_test_data():
    """Global cleanup function for all test data"""
    cleanup_manager.cleanup_all()


def reset_cleanup_tracking():
    """Reset the cleanup tracking"""
    cleanup_manager.reset()


def get_test_temp_dir(prefix: str = "test_") -> str:
    """Get a temporary directory for testing"""
    return cleanup_manager.create_temp_dir(prefix)


def track_test_file(file_path: str) -> None:
    """Track a file for cleanup"""
    cleanup_manager.track_file(file_path)


def track_test_directory(dir_path: str) -> None:
    """Track a directory for cleanup"""
    cleanup_manager.track_directory(dir_path)
