#!/usr/bin/env python3
"""
Caching System for Autonomous Agent Framework
Provides intelligent caching for LLM responses, tool outputs, and handoff packets
"""

import json
import hashlib
import time
import os
from typing import Any, Dict, Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import pickle
import gzip

class CacheType(Enum):
    """Cache type enumeration"""
    LLM_RESPONSE = "llm_response"
    TOOL_OUTPUT = "tool_output"
    HANDOFF_PACKET = "handoff_packet"
    CONTEXT = "context"

@dataclass
class CacheEntry:
    """Cache entry data structure"""
    key: str
    value: Any
    cache_type: CacheType
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_accessed == 0:
            self.last_accessed = self.created_at
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()

    def _calculate_size(self) -> int:
        """Calculate the size of the cached value in bytes"""
        try:
            return len(pickle.dumps(self.value))
        except:
            return len(str(self.value).encode('utf-8'))

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() > (self.created_at + self.ttl)

    def is_stale(self, stale_threshold: int = 300) -> bool:
        """Check if cache entry is stale (not accessed recently)"""
        return time.time() > (self.last_accessed + stale_threshold)

    def access(self):
        """Record cache access"""
        self.access_count += 1
        self.last_accessed = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'key': self.key,
            'value': self.value,
            'cache_type': self.cache_type.value,
            'created_at': self.created_at,
            'ttl': self.ttl,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed,
            'size_bytes': self.size_bytes,
            'metadata': self.metadata
        }

class CacheStats:
    """Cache statistics tracking"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
        self.errors = 0
        self.total_size = 0
        self.start_time = time.time()
        self.lock = threading.Lock()

    def record_hit(self):
        with self.lock:
            self.hits += 1

    def record_miss(self):
        with self.lock:
            self.misses += 1

    def record_set(self, size_bytes: int):
        with self.lock:
            self.sets += 1
            self.total_size += size_bytes

    def record_delete(self, size_bytes: int):
        with self.lock:
            self.deletes += 1
            self.total_size -= size_bytes

    def record_eviction(self, size_bytes: int):
        with self.lock:
            self.evictions += 1
            self.total_size -= size_bytes

    def record_error(self):
        with self.lock:
            self.errors += 1

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            uptime = time.time() - self.start_time
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': round(hit_rate, 2),
                'sets': self.sets,
                'deletes': self.deletes,
                'evictions': self.evictions,
                'errors': self.errors,
                'total_size_bytes': self.total_size,
                'total_size_mb': round(self.total_size / 1024 / 1024, 2),
                'uptime_seconds': round(uptime, 2),
                'requests_per_second': round(total_requests / uptime, 2) if uptime > 0 else 0
            }

class CacheManager:
    """Main cache management class"""
    
    def __init__(self, cache_dir: str = "cache", max_memory_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # In-memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.RLock()
        
        # Cache configuration
        self.cache_config = {
            CacheType.LLM_RESPONSE: {
                "ttl": 3600,  # 1 hour
                "max_entries": 1000,
                "compression": True,
                "persistent": True
            },
            CacheType.TOOL_OUTPUT: {
                "ttl": 86400,  # 24 hours
                "max_entries": 5000,
                "compression": False,
                "persistent": True
            },
            CacheType.HANDOFF_PACKET: {
                "ttl": 1800,  # 30 minutes
                "max_entries": 2000,
                "compression": True,
                "persistent": False
            },
            CacheType.CONTEXT: {
                "ttl": 7200,  # 2 hours
                "max_entries": 1000,
                "compression": True,
                "persistent": True
            }
        }
        
        # Statistics
        self.stats = CacheStats()
        
        # Load persistent cache
        self._load_persistent_cache()
        
        # Start background cleanup task
        self._start_cleanup_task()

    def _generate_cache_key(self, cache_type: CacheType, *args, **kwargs) -> str:
        """Generate a cache key based on input parameters"""
        key_data = {
            'type': cache_type.value,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _load_persistent_cache(self):
        """Load cache from persistent storage"""
        try:
            for cache_type in CacheType:
                if not self.cache_config[cache_type]["persistent"]:
                    continue
                    
                cache_file = self.cache_dir / f"{cache_type.value}.cache"
                if cache_file.exists():
                    with open(cache_file, 'rb') as f:
                        entries = pickle.load(f)
                        for entry_dict in entries:
                            entry = CacheEntry(**entry_dict)
                            if not entry.is_expired():
                                self.memory_cache[entry.key] = entry
                                self.stats.total_size += entry.size_bytes
        except Exception as e:
            print(f"Warning: Could not load persistent cache: {e}")

    def _save_persistent_cache(self):
        """Save cache to persistent storage"""
        try:
            cache_by_type = {}
            for entry in self.memory_cache.values():
                if self.cache_config[entry.cache_type]["persistent"]:
                    if entry.cache_type not in cache_by_type:
                        cache_by_type[entry.cache_type] = []
                    cache_by_type[entry.cache_type].append(entry.to_dict())
            
            for cache_type, entries in cache_by_type.items():
                cache_file = self.cache_dir / f"{cache_type.value}.cache"
                with open(cache_file, 'wb') as f:
                    pickle.dump(entries, f)
        except Exception as e:
            print(f"Warning: Could not save persistent cache: {e}")

    def _cleanup_expired_entries(self):
        """Remove expired entries from cache"""
        with self.cache_lock:
            expired_keys = []
            for key, entry in self.memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                entry = self.memory_cache.pop(key)
                self.stats.record_eviction(entry.size_bytes)

    def _evict_least_recently_used(self, target_size: int):
        """Evict least recently used entries to free memory"""
        with self.cache_lock:
            if len(self.memory_cache) == 0:
                return
            
            # Sort by last accessed time
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            bytes_freed = 0
            for key, entry in sorted_entries:
                if bytes_freed >= target_size:
                    break
                
                del self.memory_cache[key]
                bytes_freed += entry.size_bytes
                self.stats.record_eviction(entry.size_bytes)

    def _ensure_memory_limit(self):
        """Ensure cache doesn't exceed memory limit"""
        with self.cache_lock:
            if self.stats.total_size > self.max_memory_bytes:
                target_reduction = self.stats.total_size - self.max_memory_bytes
                self._evict_least_recently_used(target_reduction)

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        def cleanup_worker():
            while True:
                time.sleep(300)  # Run every 5 minutes
                try:
                    self._cleanup_expired_entries()
                    self._ensure_memory_limit()
                    self._save_persistent_cache()
                except Exception as e:
                    print(f"Cache cleanup error: {e}")
                    self.stats.record_error()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if entry.is_expired():
                    del self.memory_cache[key]
                    self.stats.record_eviction(entry.size_bytes)
                    self.stats.record_miss()
                    return None
                
                entry.access()
                self.stats.record_hit()
                return entry.value
            
            self.stats.record_miss()
            return None

    def set(self, key: str, value: Any, cache_type: CacheType, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            with self.cache_lock:
                if ttl is None:
                    ttl = self.cache_config[cache_type]["ttl"]
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    cache_type=cache_type,
                    created_at=time.time(),
                    ttl=ttl
                )
                
                # Check if we need to evict old entry
                if key in self.memory_cache:
                    old_entry = self.memory_cache[key]
                    self.stats.record_delete(old_entry.size_bytes)
                
                # Add new entry
                self.memory_cache[key] = entry
                self.stats.record_set(entry.size_bytes)
                
                # Ensure memory limit
                self._ensure_memory_limit()
                
                return True
                
        except Exception as e:
            print(f"Cache set error: {e}")
            self.stats.record_error()
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache.pop(key)
                self.stats.record_delete(entry.size_bytes)
                return True
            return False

    def clear(self, cache_type: CacheType = None) -> int:
        """Clear cache entries"""
        with self.cache_lock:
            if cache_type is None:
                # Clear all
                count = len(self.memory_cache)
                self.memory_cache.clear()
                self.stats.total_size = 0
                return count
            else:
                # Clear specific type
                keys_to_remove = []
                for key, entry in self.memory_cache.items():
                    if entry.cache_type == cache_type:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    entry = self.memory_cache.pop(key)
                    self.stats.record_delete(entry.size_bytes)
                
                return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.cache_lock:
            stats = self.stats.get_stats()
            stats['entries'] = len(self.memory_cache)
            stats['memory_limit_mb'] = self.max_memory_bytes / 1024 / 1024
            
            # Add per-type statistics
            type_stats = {}
            for cache_type in CacheType:
                type_entries = [e for e in self.memory_cache.values() if e.cache_type == cache_type]
                type_stats[cache_type.value] = {
                    'entries': len(type_entries),
                    'size_bytes': sum(e.size_bytes for e in type_entries),
                    'avg_access_count': sum(e.access_count for e in type_entries) / len(type_entries) if type_entries else 0
                }
            
            stats['by_type'] = type_stats
            return stats

    def cache_llm_response(self, model: str, prompt: str, context: str, response: str, ttl: int = None) -> str:
        """Cache LLM response with generated key"""
        key = self._generate_cache_key(CacheType.LLM_RESPONSE, model, prompt, context)
        self.set(key, response, CacheType.LLM_RESPONSE, ttl)
        return key

    def get_llm_response(self, model: str, prompt: str, context: str) -> Optional[str]:
        """Get cached LLM response"""
        key = self._generate_cache_key(CacheType.LLM_RESPONSE, model, prompt, context)
        return self.get(key)

    def cache_tool_output(self, tool_name: str, params: Dict[str, Any], output: Any, ttl: int = None) -> str:
        """Cache tool output with generated key"""
        key = self._generate_cache_key(CacheType.TOOL_OUTPUT, tool_name, params)
        self.set(key, output, CacheType.TOOL_OUTPUT, ttl)
        return key

    def get_tool_output(self, tool_name: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached tool output"""
        key = self._generate_cache_key(CacheType.TOOL_OUTPUT, tool_name, params)
        return self.get(key)

    def cache_handoff_packet(self, source_agent: str, target_agent: str, packet: Dict[str, Any], ttl: int = None) -> str:
        """Cache handoff packet with generated key"""
        key = self._generate_cache_key(CacheType.HANDOFF_PACKET, source_agent, target_agent, packet)
        self.set(key, packet, CacheType.HANDOFF_PACKET, ttl)
        return key

    def get_handoff_packet(self, source_agent: str, target_agent: str, packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached handoff packet"""
        key = self._generate_cache_key(CacheType.HANDOFF_PACKET, source_agent, target_agent, packet)
        return self.get(key)

# Global cache manager instance
cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    return cache_manager
