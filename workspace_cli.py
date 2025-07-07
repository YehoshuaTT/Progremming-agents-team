#!/usr/bin/env python3
"""
CLI for Workspace Cleanup
"""
import argparse
import sys
from cleanup_utility import WorkspaceCleanup
from workspace_organizer import WorkspaceOrganizer

def main():
    parser = argparse.ArgumentParser(description="Manage Agent Workflow Workspace")
    parser.add_argument("--cleanup", action="store_true", help="Run full cleanup")
    parser.add_argument("--stats", action="store_true", help="Show workspace statistics")
    parser.add_argument("--days", type=int, default=7, help="Days to keep old runs")
    parser.add_argument("--keep-recent", type=int, default=5, help="Number of recent runs to keep")
    parser.add_argument("--cache-only", action="store_true", help="Only clean cache files")
    parser.add_argument("--sessions", action="store_true", help="List existing sessions")
    
    args = parser.parse_args()
    
    if args.sessions:
        print("SESSIONS: Listing existing workspace sessions...")
        sessions = WorkspaceOrganizer.get_existing_sessions()
        for session in sessions:
            print(f"  - {session['session_id']}: {session.get('status', 'unknown')} (Created: {session.get('created_at', 'unknown')})")
        print(f"SESSIONS: Found {len(sessions)} sessions")
    
    elif args.stats:
        print("STATISTICS: Gathering workspace statistics...")
        cleanup = WorkspaceCleanup()
        stats = cleanup.get_workspace_stats()
        print(f"  Total folders: {stats['total_folders']}")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total size: {stats['total_size_mb']:.2f}MB")
        print(f"  Run folders: {stats['run_folders']}")
        if stats['oldest_run']:
            print(f"  Oldest run: {stats['oldest_run'].strftime('%Y-%m-%d %H:%M:%S')}")
        if stats['newest_run']:
            print(f"  Newest run: {stats['newest_run'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    elif args.cache_only:
        print("CACHE: Cleaning cache files only...")
        cleanup = WorkspaceCleanup()
        cleanup.cleanup_cache_files()
    
    elif args.cleanup:
        print("CLEANUP: Running full workspace cleanup...")
        cleanup = WorkspaceCleanup()
        cleanup.full_cleanup(args.days, args.keep_recent)
    
    else:
        print("WORKSPACE: Use --help for available options")
        print("WORKSPACE: Common commands:")
        print("  python workspace_cli.py --stats       # Show statistics")
        print("  python workspace_cli.py --sessions    # List sessions")
        print("  python workspace_cli.py --cleanup     # Full cleanup")
        print("  python workspace_cli.py --cache-only  # Clean cache only")

if __name__ == "__main__":
    main()
