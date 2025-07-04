#!/usr/bin/env python3
"""
Tool Output Caching System
Provides intelligent caching for deterministic tool outputs with file change detection
"""

import json
import hashlib
import time
import os
import stat
import logging
from typing import Any, Dict, Optional, List, Tuple, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import pickle
import gzip
import subprocess
from functools import wraps

class ToolCacheStrategy(Enum):
    """Tool cache strategy enumeration"""
    FILE_BASED = "file_based"  # Cache based on file modification time
    CONTENT_HASH = "content_hash"  # Cache based on content hash
    GIT_AWARE = "git_aware"  # Cache aware of git state
    TIME_BASED = "time_based"  # Simple time-based caching
    NEVER_CACHE = "never_cache"  # Never cache (for non-deterministic tools)

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ToolCacheEntry:
    """Tool cache entry with file change detection"""
    key: str
    tool_name: str
    args: tuple
    kwargs: dict
    result: Any
    cache_strategy: ToolCacheStrategy
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    file_dependencies: List[str] = None
    file_hashes: Dict[str, str] = None
    git_commit_hash: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.file_dependencies is None:
            self.file_dependencies = []
        if self.file_hashes is None:
            self.file_hashes = {}
        if self.last_accessed == 0:
            self.last_accessed = self.created_at
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()

    def _calculate_size(self) -> int:
        """Calculate the size of the cached result in bytes"""
        try:
            return len(pickle.dumps(self.result))
        except (pickle.PickleError, TypeError, AttributeError) as e:
            logger.warning(f"Could not pickle result for size calculation: {e}")
            return len(str(self.result).encode())

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.created_at > self.ttl

    def is_valid(self) -> bool:
        """Check if cache entry is still valid (not expired and dependencies unchanged)"""
        if self.is_expired():
            return False
        
        # Check file dependencies
        if self.cache_strategy == ToolCacheStrategy.FILE_BASED:
            return self._check_file_dependencies()
        elif self.cache_strategy == ToolCacheStrategy.CONTENT_HASH:
            return self._check_content_hashes()
        elif self.cache_strategy == ToolCacheStrategy.GIT_AWARE:
            return self._check_git_state()
        
        return True

    def _check_file_dependencies(self) -> bool:
        """Check if file dependencies have changed"""
        for file_path in self.file_dependencies:
            if not os.path.exists(file_path):
                return False
            
            # Check modification time
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self.metadata.get(f"mtime_{file_path}", 0)
            
            if current_mtime != cached_mtime:
                return False
        
        return True

    def _check_content_hashes(self) -> bool:
        """Check if content hashes have changed"""
        for file_path, cached_hash in self.file_hashes.items():
            if not os.path.exists(file_path):
                return False
            
            try:
                with open(file_path, 'rb') as f:
                    current_hash = hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
                
                if current_hash != cached_hash:
                    return False
            except (OSError, IOError) as e:
                logger.warning(f"Could not read file {file_path} for hash comparison: {e}")
                return False
        
        return True

    def _check_git_state(self) -> bool:
        """Check if git state has changed"""
        if not self.git_commit_hash:
            return True
        
        try:
            # Use 'git' command which should be in PATH on Windows
            # Input validation: only allow specific git commands
            git_command = ['git', 'rev-parse', 'HEAD']
            result = subprocess.run(
                git_command,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=10,  # Add timeout
                check=False  # Don't raise on non-zero exit
            )
            
            current_hash = result.stdout.strip()
            return current_hash == self.git_commit_hash
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
            logger.warning(f"Git command failed in cache validation: {e}")
            return True  # If git fails, assume valid

    def update_access(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = time.time()

class ToolCacheManager:
    """Enhanced tool cache manager with file change detection"""
    
    def __init__(self, cache_dir: str = "cache/tools", max_memory_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # In-memory cache
        self.memory_cache: Dict[str, ToolCacheEntry] = {}
        self.cache_lock = threading.RLock()
        
        # Tool-specific cache configuration
        self.tool_cache_config = {
            # File operations - cache based on file modification time
            "read_file": {
                "strategy": ToolCacheStrategy.FILE_BASED,
                "ttl": 3600,  # 1 hour
                "max_entries": 1000
            },
            "list_dir": {
                "strategy": ToolCacheStrategy.FILE_BASED,
                "ttl": 1800,  # 30 minutes
                "max_entries": 500
            },
            "get_file_info": {
                "strategy": ToolCacheStrategy.FILE_BASED,
                "ttl": 3600,  # 1 hour
                "max_entries": 800
            },
            
            # Git operations - cache based on git state
            "git_status": {
                "strategy": ToolCacheStrategy.GIT_AWARE,
                "ttl": 300,  # 5 minutes
                "max_entries": 100
            },
            "git_log": {
                "strategy": ToolCacheStrategy.GIT_AWARE,
                "ttl": 1800,  # 30 minutes
                "max_entries": 200
            },
            "git_diff": {
                "strategy": ToolCacheStrategy.GIT_AWARE,
                "ttl": 600,  # 10 minutes
                "max_entries": 150
            },
            
            # Document processing - cache based on content hash
            "generate_summary": {
                "strategy": ToolCacheStrategy.CONTENT_HASH,
                "ttl": 7200,  # 2 hours
                "max_entries": 300
            },
            "extract_section": {
                "strategy": ToolCacheStrategy.CONTENT_HASH,
                "ttl": 3600,  # 1 hour
                "max_entries": 500
            },
            
            # Static analysis tools - content hash based
            "analyze_code": {
                "strategy": ToolCacheStrategy.CONTENT_HASH,
                "ttl": 5400,  # 1.5 hours
                "max_entries": 400
            },
            "check_syntax": {
                "strategy": ToolCacheStrategy.CONTENT_HASH,
                "ttl": 1800,  # 30 minutes
                "max_entries": 600
            },
            
            # Non-deterministic tools - never cache
            "execute_shell_command": {
                "strategy": ToolCacheStrategy.NEVER_CACHE,
                "ttl": 0,
                "max_entries": 0
            },
            "get_current_time": {
                "strategy": ToolCacheStrategy.NEVER_CACHE,
                "ttl": 0,
                "max_entries": 0
            },
            
            # Default configuration
            "default": {
                "strategy": ToolCacheStrategy.TIME_BASED,
                "ttl": 1800,  # 30 minutes
                "max_entries": 300
            }
        }
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "evictions": 0,
            "total_size_mb": 0.0,
            "entries_count": 0
        }
        
        # Start background cleanup
        self._start_cleanup_task()

    def _generate_cache_key(self, tool_name: str, *args, **kwargs) -> str:
        """Generate cache key for tool call"""
        key_data = {
            'tool': tool_name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()

    def _extract_file_dependencies(self, tool_name: str, *args, **kwargs) -> List[str]:
        """Extract file dependencies from tool arguments"""
        dependencies = []
        
        # Common patterns for file-based tools
        if tool_name in ["read_file", "get_file_info"]:
            if args:
                dependencies.append(str(args[0]))
        elif tool_name == "list_dir":
            if args:
                dependencies.append(str(args[0]))
        elif tool_name in ["generate_summary", "extract_section"]:
            if args:
                dependencies.append(str(args[0]))
        elif "file_path" in kwargs:
            dependencies.append(str(kwargs["file_path"]))
        elif "document_path" in kwargs:
            dependencies.append(str(kwargs["document_path"]))
        else:
            # Generic case: assume first argument is a file path if it exists
            if args and os.path.exists(str(args[0])):
                dependencies.append(str(args[0]))
        
        # Filter out non-existent files
        return [dep for dep in dependencies if os.path.exists(dep)]

    def _get_file_hashes(self, file_paths: List[str]) -> Dict[str, str]:
        """Get content hashes for files"""
        hashes = {}
        
        for file_path in file_paths:
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    hashes[file_path] = hashlib.md5(content, usedforsecurity=False).hexdigest()
            except (OSError, IOError) as e:
                logger.warning(f"Could not read file {file_path} for hashing: {e}")
                # Skip files that can't be read
        
        return hashes

    def _get_git_commit_hash(self) -> str:
        """Get current git commit hash"""
        try:
            # Use 'git' command which should be in PATH on Windows
            # Input validation: only allow specific git commands
            git_command = ['git', 'rev-parse', 'HEAD']
            result = subprocess.run(
                git_command,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=10,  # Add timeout
                check=False  # Don't raise on non-zero exit
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
            logger.warning(f"Git command failed: {e}")
            return ""

    def get_cached_result(self, tool_name: str, *args, **kwargs) -> Optional[Any]:
        """Get cached tool result if available and valid"""
        config = self.tool_cache_config.get(tool_name, self.tool_cache_config["default"])
        
        # Never cache certain tools
        if config["strategy"] == ToolCacheStrategy.NEVER_CACHE:
            self.stats["misses"] += 1
            return None
        
        with self.cache_lock:
            cache_key = self._generate_cache_key(tool_name, *args, **kwargs)
            
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                # Check if entry is still valid
                if entry.is_valid():
                    entry.update_access()
                    self.stats["hits"] += 1
                    return entry.result
                else:
                    # Remove invalid entry
                    del self.memory_cache[cache_key]
                    self.stats["invalidations"] += 1
            
            self.stats["misses"] += 1
            return None

    def cache_tool_result(self, tool_name: str, result: Any, *args, **kwargs) -> bool:
        """Cache tool result with appropriate strategy"""
        config = self.tool_cache_config.get(tool_name, self.tool_cache_config["default"])
        
        # Never cache certain tools
        if config["strategy"] == ToolCacheStrategy.NEVER_CACHE:
            return False
        
        with self.cache_lock:
            try:
                cache_key = self._generate_cache_key(tool_name, *args, **kwargs)
                
                # Extract file dependencies
                file_dependencies = self._extract_file_dependencies(tool_name, *args, **kwargs)
                
                # Get file hashes if needed
                file_hashes = {}
                if config["strategy"] == ToolCacheStrategy.CONTENT_HASH:
                    file_hashes = self._get_file_hashes(file_dependencies)
                
                # Get git commit hash if needed
                git_commit_hash = ""
                if config["strategy"] == ToolCacheStrategy.GIT_AWARE:
                    git_commit_hash = self._get_git_commit_hash()
                
                # Create metadata for file-based caching
                metadata = {}
                if config["strategy"] == ToolCacheStrategy.FILE_BASED:
                    for file_path in file_dependencies:
                        try:
                            metadata[f"mtime_{file_path}"] = os.path.getmtime(file_path)
                        except (OSError, IOError) as e:
                            logger.warning(f"Could not get mtime for {file_path}: {e}")
                            # Skip files that can't be accessed
                
                # Create cache entry
                entry = ToolCacheEntry(
                    key=cache_key,
                    tool_name=tool_name,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                    cache_strategy=config["strategy"],
                    created_at=time.time(),
                    ttl=config["ttl"],
                    file_dependencies=file_dependencies,
                    file_hashes=file_hashes,
                    git_commit_hash=git_commit_hash,
                    metadata=metadata
                )
                
                # Check memory limits
                if self._get_memory_usage() + entry.size_bytes > self.max_memory_bytes:
                    self._evict_old_entries()
                
                # Store in memory cache
                self.memory_cache[cache_key] = entry
                
                # Update statistics
                self.stats["entries_count"] = len(self.memory_cache)
                self.stats["total_size_mb"] = self._get_memory_usage() / (1024 * 1024)
                
                return True
                
            except Exception as e:
                print(f"Error caching tool result: {e}")
                return False

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        return sum(entry.size_bytes for entry in self.memory_cache.values())

    def _evict_old_entries(self):
        """Evict old entries using LRU strategy"""
        if not self.memory_cache:
            return
        
        # Sort by last accessed time (LRU)
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest 20% of entries
        remove_count = max(1, len(sorted_entries) // 5)
        
        for i in range(remove_count):
            cache_key, entry = sorted_entries[i]
            del self.memory_cache[cache_key]
            self.stats["evictions"] += 1

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        def cleanup():
            while True:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired_entries()
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_entries(self):
        """Clean up expired and invalid entries"""
        with self.cache_lock:
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if not entry.is_valid()
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
                self.stats["invalidations"] += 1
            
            # Update statistics
            self.stats["entries_count"] = len(self.memory_cache)
            self.stats["total_size_mb"] = self._get_memory_usage() / (1024 * 1024)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self.cache_lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": round(hit_rate, 2),
                "invalidations": self.stats["invalidations"],
                "evictions": self.stats["evictions"],
                "total_size_mb": round(self.stats["total_size_mb"], 2),
                "entries_count": self.stats["entries_count"],
                "memory_usage_mb": round(self._get_memory_usage() / (1024 * 1024), 2),
                "tool_distribution": self._get_tool_distribution(),
                "strategy_distribution": self._get_strategy_distribution()
            }

    def _get_tool_distribution(self) -> Dict[str, int]:
        """Get distribution of cached entries by tool"""
        distribution = {}
        for entry in self.memory_cache.values():
            tool = entry.tool_name
            distribution[tool] = distribution.get(tool, 0) + 1
        return distribution

    def _get_strategy_distribution(self) -> Dict[str, int]:
        """Get distribution of cached entries by strategy"""
        distribution = {}
        for entry in self.memory_cache.values():
            strategy = entry.cache_strategy.value
            distribution[strategy] = distribution.get(strategy, 0) + 1
        return distribution

    def clear_cache(self, tool_name: str = None):
        """Clear cache for specific tool or all"""
        with self.cache_lock:
            if tool_name:
                # Clear specific tool cache
                keys_to_remove = [
                    key for key, entry in self.memory_cache.items()
                    if entry.tool_name == tool_name
                ]
                for key in keys_to_remove:
                    del self.memory_cache[key]
            else:
                # Clear all cache
                self.memory_cache.clear()
            
            # Update statistics
            self.stats["entries_count"] = len(self.memory_cache)
            self.stats["total_size_mb"] = self._get_memory_usage() / (1024 * 1024)

    def invalidate_file_cache(self, file_path: str):
        """Invalidate cache entries that depend on a specific file"""
        with self.cache_lock:
            keys_to_remove = []
            
            for key, entry in self.memory_cache.items():
                if file_path in entry.file_dependencies:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.memory_cache[key]
                self.stats["invalidations"] += 1
            
            # Update statistics
            self.stats["entries_count"] = len(self.memory_cache)
            self.stats["total_size_mb"] = self._get_memory_usage() / (1024 * 1024)

# Decorator for caching tool functions
def cache_tool_output(tool_name: str = None):
    """Decorator to automatically cache tool outputs"""
    def decorator(func: Callable) -> Callable:
        actual_tool_name = tool_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get cached result
            cached_result = tool_cache.get_cached_result(actual_tool_name, *args, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            tool_cache.cache_tool_result(actual_tool_name, result, *args, **kwargs)
            
            return result
        
        return wrapper
    return decorator

# Global tool cache instance
tool_cache = ToolCacheManager()
