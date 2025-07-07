#!/usr/bin/env python3
"""
Cleanup Utility for Agent Workflow System
Manages workspace folders and provides cleanup functionality
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import argparse

class WorkspaceCleanup:
    def __init__(self, workspace_root: str = "workspace"):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(exist_ok=True)
        
    def cleanup_old_runs(self, days_to_keep: int = 7):
        """Remove workspace folders older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        print(f"CLEANUP: Removing workspace folders older than {days_to_keep} days...")
        
        for folder in self.workspace_root.iterdir():
            if folder.is_dir():
                try:
                    # Check if it's a run folder (contains timestamp)
                    if self._is_run_folder(folder):
                        folder_time = self._get_folder_timestamp(folder)
                        if folder_time and folder_time < cutoff_date:
                            print(f"CLEANUP: Removing old folder: {folder.name}")
                            shutil.rmtree(folder)
                            removed_count += 1
                except Exception as e:
                    print(f"CLEANUP: Error removing folder {folder.name}: {e}")
        
        print(f"CLEANUP: Removed {removed_count} old workspace folders")
        return removed_count
    
    def cleanup_empty_folders(self):
        """Remove empty folders from workspace"""
        removed_count = 0
        
        print("CLEANUP: Removing empty folders...")
        
        for folder in self.workspace_root.iterdir():
            if folder.is_dir():
                try:
                    # Check if folder is empty or contains only empty subfolders
                    if self._is_empty_recursive(folder):
                        print(f"CLEANUP: Removing empty folder: {folder.name}")
                        shutil.rmtree(folder)
                        removed_count += 1
                except Exception as e:
                    print(f"CLEANUP: Error removing empty folder {folder.name}: {e}")
        
        print(f"CLEANUP: Removed {removed_count} empty folders")
        return removed_count
    
    def cleanup_cache_files(self):
        """Clean up corrupted or old cache files"""
        cache_dirs = ["cache/llm", "cache/tools", "cache/handoff"]
        removed_count = 0
        
        print("CLEANUP: Cleaning cache files...")
        
        for cache_dir in cache_dirs:
            cache_path = Path(cache_dir)
            if cache_path.exists():
                for cache_file in cache_path.glob("*.cache"):
                    try:
                        # Try to validate cache file
                        if not self._is_valid_cache_file(cache_file):
                            print(f"CLEANUP: Removing corrupted cache file: {cache_file.name}")
                            cache_file.unlink()
                            removed_count += 1
                    except Exception as e:
                        print(f"CLEANUP: Error checking cache file {cache_file.name}: {e}")
                        # Remove corrupted file
                        try:
                            cache_file.unlink()
                            removed_count += 1
                        except:
                            pass
        
        print(f"CLEANUP: Removed {removed_count} cache files")
        return removed_count
    
    def get_workspace_stats(self):
        """Get statistics about workspace usage"""
        stats = {
            "total_folders": 0,
            "total_files": 0,
            "total_size_mb": 0,
            "run_folders": 0,
            "oldest_run": None,
            "newest_run": None
        }
        
        if not self.workspace_root.exists():
            return stats
        
        for item in self.workspace_root.rglob("*"):
            if item.is_file():
                stats["total_files"] += 1
                stats["total_size_mb"] += item.stat().st_size / (1024 * 1024)
            elif item.is_dir():
                stats["total_folders"] += 1
                
                # Check if it's a run folder
                if self._is_run_folder(item):
                    stats["run_folders"] += 1
                    folder_time = self._get_folder_timestamp(item)
                    if folder_time:
                        if not stats["oldest_run"] or folder_time < stats["oldest_run"]:
                            stats["oldest_run"] = folder_time
                        if not stats["newest_run"] or folder_time > stats["newest_run"]:
                            stats["newest_run"] = folder_time
        
        return stats
    
    def full_cleanup(self, days_to_keep: int = 7, keep_recent: int = 5):
        """Perform a full cleanup of workspace"""
        print("CLEANUP: Starting full workspace cleanup...")
        
        # Get stats before cleanup
        before_stats = self.get_workspace_stats()
        
        # Keep most recent runs regardless of age
        self._preserve_recent_runs(keep_recent)
        
        # Clean up old runs
        self.cleanup_old_runs(days_to_keep)
        
        # Clean up empty folders
        self.cleanup_empty_folders()
        
        # Clean up cache files
        self.cleanup_cache_files()
        
        # Get stats after cleanup
        after_stats = self.get_workspace_stats()
        
        print("CLEANUP: Cleanup completed!")
        print(f"CLEANUP: Folders: {before_stats['total_folders']} -> {after_stats['total_folders']}")
        print(f"CLEANUP: Files: {before_stats['total_files']} -> {after_stats['total_files']}")
        print(f"CLEANUP: Size: {before_stats['total_size_mb']:.2f}MB -> {after_stats['total_size_mb']:.2f}MB")
        
        return after_stats
    
    def _is_run_folder(self, folder: Path) -> bool:
        """Check if folder is a workflow run folder"""
        folder_name = folder.name
        # Check for patterns like "agent-driven-1751895257" or "WORKFLOW-001"
        return (folder_name.startswith("agent-driven-") or 
                folder_name.startswith("WORKFLOW-") or
                folder_name.startswith("workflow-"))
    
    def _get_folder_timestamp(self, folder: Path) -> Optional[datetime]:
        """Extract timestamp from folder name or creation time"""
        folder_name = folder.name
        
        # Try to extract timestamp from folder name
        if "agent-driven-" in folder_name:
            try:
                timestamp_str = folder_name.split("agent-driven-")[1].split("-")[0]
                if timestamp_str.isdigit():
                    return datetime.fromtimestamp(int(timestamp_str))
            except:
                pass
        
        # Fall back to folder creation time
        try:
            return datetime.fromtimestamp(folder.stat().st_ctime)
        except:
            return None
    
    def _is_empty_recursive(self, folder: Path) -> bool:
        """Check if folder is empty recursively"""
        try:
            for item in folder.rglob("*"):
                if item.is_file():
                    return False
            return True
        except:
            return False
    
    def _is_valid_cache_file(self, cache_file: Path) -> bool:
        """Check if cache file is valid"""
        try:
            # Try to read the file
            with open(cache_file, 'rb') as f:
                data = f.read(100)  # Read first 100 bytes
                if len(data) == 0:
                    return False
                # Basic validation - should not be empty
                return True
        except:
            return False
    
    def _preserve_recent_runs(self, keep_recent: int):
        """Mark recent runs to be preserved"""
        run_folders = []
        
        for folder in self.workspace_root.iterdir():
            if folder.is_dir() and self._is_run_folder(folder):
                folder_time = self._get_folder_timestamp(folder)
                if folder_time:
                    run_folders.append((folder, folder_time))
        
        # Sort by timestamp (newest first)
        run_folders.sort(key=lambda x: x[1], reverse=True)
        
        # Mark recent ones for preservation
        for i, (folder, _) in enumerate(run_folders[:keep_recent]):
            marker_file = folder / ".preserve"
            try:
                marker_file.touch()
                print(f"CLEANUP: Preserving recent run: {folder.name}")
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Cleanup Agent Workflow System")
    parser.add_argument("--days", type=int, default=7, help="Days to keep old runs")
    parser.add_argument("--keep-recent", type=int, default=5, help="Number of recent runs to always keep")
    parser.add_argument("--stats-only", action="store_true", help="Only show statistics")
    parser.add_argument("--cache-only", action="store_true", help="Only clean cache files")
    
    args = parser.parse_args()
    
    cleanup = WorkspaceCleanup()
    
    if args.stats_only:
        stats = cleanup.get_workspace_stats()
        print("WORKSPACE STATISTICS:")
        print(f"  Total folders: {stats['total_folders']}")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total size: {stats['total_size_mb']:.2f}MB")
        print(f"  Run folders: {stats['run_folders']}")
        if stats['oldest_run']:
            print(f"  Oldest run: {stats['oldest_run'].strftime('%Y-%m-%d %H:%M:%S')}")
        if stats['newest_run']:
            print(f"  Newest run: {stats['newest_run'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    elif args.cache_only:
        cleanup.cleanup_cache_files()
    
    else:
        cleanup.full_cleanup(args.days, args.keep_recent)

if __name__ == "__main__":
    main()
