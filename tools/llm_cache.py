#!/usr/bin/env python3
"""
Enhanced LLM Call Caching System
Provides intelligent caching for LLM API responses with context-aware strategies
"""

import json
import hashlib
import time
import os
import re
from typing import Any, Dict, Optional, List, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import pickle
import gzip
import tiktoken

class LLMCacheStrategy(Enum):
    """LLM cache strategy enumeration"""
    EXACT_MATCH = "exact_match"  # Exact prompt match
    SEMANTIC_MATCH = "semantic_match"  # Similar prompts
    CONTEXT_AWARE = "context_aware"  # Context-sensitive caching
    AGENT_SPECIFIC = "agent_specific"  # Agent-specific caching

@dataclass
class LLMCacheEntry:
    """LLM cache entry with enhanced metadata"""
    key: str
    prompt: str
    response: str
    agent_name: str
    cache_strategy: LLMCacheStrategy
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    prompt_tokens: int = 0
    response_tokens: int = 0
    cost_saved: float = 0.0
    context_hash: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_accessed == 0:
            self.last_accessed = self.created_at
        if self.size_bytes == 0:
            self.size_bytes = len(self.prompt.encode()) + len(self.response.encode())
        if self.prompt_tokens == 0:
            self.prompt_tokens = self._estimate_tokens(self.prompt)
        if self.response_tokens == 0:
            self.response_tokens = self._estimate_tokens(self.response)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except:
            return len(text) // 4  # Fallback estimation

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.created_at > self.ttl

    def update_access(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = time.time()

class LLMCacheManager:
    """Enhanced LLM cache manager with intelligent caching strategies"""
    
    def __init__(self, cache_dir: str = "cache/llm", max_memory_mb: int = 200):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # In-memory cache
        self.memory_cache: Dict[str, LLMCacheEntry] = {}
        self.cache_lock = threading.RLock()
        
        # Cache configuration per agent type
        self.agent_cache_config = {
            "Product_Analyst": {
                "ttl": 7200,  # 2 hours (specs don't change often)
                "strategy": LLMCacheStrategy.CONTEXT_AWARE,
                "max_entries": 500,
                "cost_per_1k_tokens": 0.002
            },
            "Coder": {
                "ttl": 3600,  # 1 hour (code changes frequently)
                "strategy": LLMCacheStrategy.SEMANTIC_MATCH,
                "max_entries": 1000,
                "cost_per_1k_tokens": 0.002
            },
            "Code_Reviewer": {
                "ttl": 1800,  # 30 minutes (reviews are context-specific)
                "strategy": LLMCacheStrategy.EXACT_MATCH,
                "max_entries": 300,
                "cost_per_1k_tokens": 0.002
            },
            "Tester": {
                "ttl": 5400,  # 1.5 hours (test scenarios are stable)
                "strategy": LLMCacheStrategy.CONTEXT_AWARE,
                "max_entries": 400,
                "cost_per_1k_tokens": 0.002
            },
            "Security_Specialist": {
                "ttl": 10800,  # 3 hours (security patterns are stable)
                "strategy": LLMCacheStrategy.SEMANTIC_MATCH,
                "max_entries": 200,
                "cost_per_1k_tokens": 0.002
            },
            "default": {
                "ttl": 3600,  # 1 hour
                "strategy": LLMCacheStrategy.EXACT_MATCH,
                "max_entries": 500,
                "cost_per_1k_tokens": 0.002
            }
        }
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_cost_saved": 0.0,
            "total_tokens_saved": 0,
            "cache_size_mb": 0.0,
            "entries_count": 0
        }
        
        # Load persistent cache
        self._load_persistent_cache()
        
        # Start background cleanup
        self._start_cleanup_task()

    def _generate_cache_key(self, agent_name: str, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate cache key based on agent and prompt"""
        config = self.agent_cache_config.get(agent_name, self.agent_cache_config["default"])
        strategy = config["strategy"]
        
        if strategy == LLMCacheStrategy.EXACT_MATCH:
            # Exact prompt match
            key_data = f"{agent_name}:{prompt}"
        elif strategy == LLMCacheStrategy.SEMANTIC_MATCH:
            # Normalize prompt for semantic matching
            normalized_prompt = self._normalize_prompt(prompt)
            key_data = f"{agent_name}:semantic:{normalized_prompt}"
        elif strategy == LLMCacheStrategy.CONTEXT_AWARE:
            # Include context in key
            context_str = json.dumps(context or {}, sort_keys=True)
            context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
            key_data = f"{agent_name}:context:{context_hash}:{prompt}"
        elif strategy == LLMCacheStrategy.AGENT_SPECIFIC:
            # Agent-specific caching
            key_data = f"{agent_name}:specific:{prompt}"
        else:
            key_data = f"{agent_name}:{prompt}"
        
        return hashlib.md5(key_data.encode()).hexdigest()

    def _normalize_prompt(self, prompt: str) -> str:
        """Normalize prompt for semantic matching"""
        # Remove timestamps, IDs, and other variable content
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '[TIMESTAMP]', prompt)
        normalized = re.sub(r'TASK-\d+-\d+', '[TASK-ID]', normalized)
        normalized = re.sub(r'ID:\s*\w+', 'ID: [ID]', normalized)
        normalized = re.sub(r'uuid:\s*[\w-]+', 'uuid: [UUID]', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def get_llm_response(self, agent_name: str, prompt: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Get cached LLM response if available"""
        with self.cache_lock:
            cache_key = self._generate_cache_key(agent_name, prompt, context)
            
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                # Check if expired
                if entry.is_expired():
                    del self.memory_cache[cache_key]
                    self.stats["misses"] += 1
                    return None
                
                # Update access statistics
                entry.update_access()
                self.stats["hits"] += 1
                
                # Calculate cost saved
                config = self.agent_cache_config.get(agent_name, self.agent_cache_config["default"])
                cost_saved = (entry.prompt_tokens + entry.response_tokens) / 1000 * config["cost_per_1k_tokens"]
                self.stats["total_cost_saved"] += cost_saved
                self.stats["total_tokens_saved"] += entry.prompt_tokens + entry.response_tokens
                
                return entry.response
            
            self.stats["misses"] += 1
            return None

    def cache_llm_response(self, agent_name: str, prompt: str, response: str, context: Dict[str, Any] = None) -> bool:
        """Cache LLM response"""
        with self.cache_lock:
            try:
                cache_key = self._generate_cache_key(agent_name, prompt, context)
                config = self.agent_cache_config.get(agent_name, self.agent_cache_config["default"])
                
                # Create context hash for context-aware caching
                context_hash = ""
                if context:
                    context_str = json.dumps(context, sort_keys=True)
                    context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
                
                # Create cache entry
                entry = LLMCacheEntry(
                    key=cache_key,
                    prompt=prompt,
                    response=response,
                    agent_name=agent_name,
                    cache_strategy=config["strategy"],
                    created_at=time.time(),
                    ttl=config["ttl"],
                    context_hash=context_hash,
                    metadata={"context": context}
                )
                
                # Check memory limits
                if self._get_memory_usage() + entry.size_bytes > self.max_memory_bytes:
                    self._evict_old_entries()
                
                # Store in memory cache
                self.memory_cache[cache_key] = entry
                
                # Update statistics
                self.stats["entries_count"] = len(self.memory_cache)
                self.stats["cache_size_mb"] = self._get_memory_usage() / (1024 * 1024)
                
                # Persist if needed
                if agent_name in ["Product_Analyst", "Architect", "Security_Specialist"]:
                    self._persist_entry(entry)
                
                return True
                
            except Exception as e:
                print(f"Error caching LLM response: {e}")
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

    def _persist_entry(self, entry: LLMCacheEntry):
        """Persist cache entry to disk"""
        try:
            filename = f"{entry.key}.cache"
            filepath = self.cache_dir / filename
            
            with gzip.open(filepath, 'wb') as f:
                pickle.dump(entry, f)
                
        except Exception as e:
            print(f"Error persisting cache entry: {e}")

    def _load_persistent_cache(self):
        """Load persistent cache from disk"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with gzip.open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                        
                        # Check if expired
                        if not entry.is_expired():
                            self.memory_cache[entry.key] = entry
                        else:
                            cache_file.unlink()  # Remove expired file
                            
                except Exception as e:
                    print(f"Error loading cache file {cache_file}: {e}")
                    cache_file.unlink()  # Remove corrupted file
                    
        except Exception as e:
            print(f"Error loading persistent cache: {e}")

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        def cleanup():
            while True:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired_entries()
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_entries(self):
        """Clean up expired entries"""
        with self.cache_lock:
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Update statistics
            self.stats["entries_count"] = len(self.memory_cache)
            self.stats["cache_size_mb"] = self._get_memory_usage() / (1024 * 1024)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self.cache_lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": round(hit_rate, 2),
                "total_cost_saved": round(self.stats["total_cost_saved"], 4),
                "total_tokens_saved": self.stats["total_tokens_saved"],
                "cache_size_mb": round(self.stats["cache_size_mb"], 2),
                "entries_count": self.stats["entries_count"],
                "memory_usage_mb": round(self._get_memory_usage() / (1024 * 1024), 2),
                "agent_distribution": self._get_agent_distribution()
            }

    def _get_agent_distribution(self) -> Dict[str, int]:
        """Get distribution of cached entries by agent"""
        distribution = {}
        for entry in self.memory_cache.values():
            agent = entry.agent_name
            distribution[agent] = distribution.get(agent, 0) + 1
        return distribution

    def clear_cache(self, agent_name: str = None):
        """Clear cache for specific agent or all"""
        with self.cache_lock:
            if agent_name:
                # Clear specific agent cache
                keys_to_remove = [
                    key for key, entry in self.memory_cache.items()
                    if entry.agent_name == agent_name
                ]
                for key in keys_to_remove:
                    del self.memory_cache[key]
            else:
                # Clear all cache
                self.memory_cache.clear()
            
            # Update statistics
            self.stats["entries_count"] = len(self.memory_cache)
            self.stats["cache_size_mb"] = self._get_memory_usage() / (1024 * 1024)

    def warm_cache(self, agent_name: str, common_prompts: List[str]):
        """Pre-warm cache with common prompts (for testing)"""
        print(f"Cache warming not implemented for LLM calls (requires actual API calls)")

# Global LLM cache instance
llm_cache = LLMCacheManager()
