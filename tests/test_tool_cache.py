#!/usr/bin/env python3
"""
Tests for Tool Output Caching System
Tests intelligent caching of tool outputs with file change detection
"""

import unittest
import tempfile
import time
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.tool_cache import ToolCacheManager, ToolCacheStrategy, ToolCacheEntry, cache_tool_output, tool_cache
from tools.file_tools import read_file, list_dir, get_file_info, invalidate_file_cache
from tools.git_tools import git_status, git_log, git_diff

class TestToolCacheManager(unittest.TestCase):
    """Test tool cache manager functionality"""
    
    def setUp(self):
        # Create temporary cache directory
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = ToolCacheManager(cache_dir=self.temp_dir, max_memory_mb=10)
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_key_generation(self):
        """Test cache key generation for tool calls"""
        tool_name = "read_file"
        args = ("test.txt",)
        kwargs = {"agent_id": "test_agent"}
        
        # Test consistent key generation
        key1 = self.cache_manager._generate_cache_key(tool_name, *args, **kwargs)
        key2 = self.cache_manager._generate_cache_key(tool_name, *args, **kwargs)
        self.assertEqual(key1, key2)
        
        # Test different args generate different keys
        key3 = self.cache_manager._generate_cache_key(tool_name, "different.txt", **kwargs)
        self.assertNotEqual(key1, key3)
    
    def test_file_dependency_extraction(self):
        """Test extraction of file dependencies from tool arguments"""
        # Test read_file tool
        deps = self.cache_manager._extract_file_dependencies("read_file", "test.txt")
        self.assertEqual(deps, [])  # File doesn't exist
        
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        deps = self.cache_manager._extract_file_dependencies("read_file", test_file)
        self.assertEqual(deps, [test_file])
        
        # Test with kwargs
        deps = self.cache_manager._extract_file_dependencies("some_tool", file_path=test_file)
        self.assertEqual(deps, [test_file])
    
    def test_cache_entry_creation(self):
        """Test tool cache entry creation and properties"""
        entry = ToolCacheEntry(
            key="test_key",
            tool_name="read_file",
            args=("test.txt",),
            kwargs={"agent_id": "test"},
            result={"success": True, "content": "test"},
            cache_strategy=ToolCacheStrategy.FILE_BASED,
            created_at=time.time(),
            ttl=3600
        )
        
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.tool_name, "read_file")
        self.assertGreater(entry.size_bytes, 0)
        self.assertFalse(entry.is_expired())
        self.assertTrue(entry.is_valid())
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic"""
        entry = ToolCacheEntry(
            key="test_key",
            tool_name="read_file",
            args=("test.txt",),
            kwargs={},
            result={"content": "test"},
            cache_strategy=ToolCacheStrategy.TIME_BASED,
            created_at=time.time() - 7200,  # 2 hours ago
            ttl=3600  # 1 hour TTL
        )
        
        self.assertTrue(entry.is_expired())
        self.assertFalse(entry.is_valid())
    
    def test_file_based_caching(self):
        """Test file-based cache validation"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("original content")
        
        # Cache result
        result = {"success": True, "content": "original content"}
        success = self.cache_manager.cache_tool_result("read_file", result, test_file)
        self.assertTrue(success)
        
        # Retrieve from cache
        cached_result = self.cache_manager.get_cached_result("read_file", test_file)
        self.assertEqual(cached_result, result)
        
        # Modify file
        time.sleep(0.1)  # Ensure different mtime
        with open(test_file, 'w') as f:
            f.write("modified content")
        
        # Cache should be invalid now
        cached_result = self.cache_manager.get_cached_result("read_file", test_file)
        self.assertIsNone(cached_result)
    
    def test_content_hash_caching(self):
        """Test content hash-based cache validation"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Configure tool for content hash strategy
        self.cache_manager.tool_cache_config["test_tool"] = {
            "strategy": ToolCacheStrategy.CONTENT_HASH,
            "ttl": 3600,
            "max_entries": 100
        }
        
        # Cache result
        result = {"summary": "Test file summary"}
        success = self.cache_manager.cache_tool_result("test_tool", result, test_file)
        self.assertTrue(success)
        
        # Retrieve from cache
        cached_result = self.cache_manager.get_cached_result("test_tool", test_file)
        self.assertEqual(cached_result, result)
        
        # Modify file content
        with open(test_file, 'w') as f:
            f.write("different content")
        
        # Cache should be invalid now
        cached_result = self.cache_manager.get_cached_result("test_tool", test_file)
        self.assertIsNone(cached_result)
    
    def test_git_aware_caching(self):
        """Test git-aware cache validation"""
        # Mock git commands
        with patch('subprocess.run') as mock_run:
            # First call returns initial commit hash
            mock_run.return_value.stdout = "abc123\n"
            
            # Cache result
            result = {"status": "clean"}
            success = self.cache_manager.cache_tool_result("git_status", result)
            self.assertTrue(success)
            
            # Retrieve from cache (same commit)
            cached_result = self.cache_manager.get_cached_result("git_status")
            self.assertEqual(cached_result, result)
            
            # Change commit hash
            mock_run.return_value.stdout = "def456\n"
            
            # Cache should be invalid now
            cached_result = self.cache_manager.get_cached_result("git_status")
            self.assertIsNone(cached_result)
    
    def test_never_cache_strategy(self):
        """Test that certain tools are never cached"""
        # Configure tool to never cache
        self.cache_manager.tool_cache_config["execute_shell_command"] = {
            "strategy": ToolCacheStrategy.NEVER_CACHE,
            "ttl": 0,
            "max_entries": 0
        }
        
        # Try to cache result
        result = {"output": "command output"}
        success = self.cache_manager.cache_tool_result("execute_shell_command", result, "echo test")
        self.assertFalse(success)
        
        # Try to retrieve from cache
        cached_result = self.cache_manager.get_cached_result("execute_shell_command", "echo test")
        self.assertIsNone(cached_result)
    
    def test_cache_statistics(self):
        """Test cache statistics accuracy"""
        # Perform cache operations
        for i in range(5):
            tool_name = f"test_tool_{i}"
            result = f"result_{i}"
            
            # Cache result
            self.cache_manager.cache_tool_result(tool_name, result, f"arg_{i}")
            
            # Try to retrieve (miss first time, hit second time)
            self.cache_manager.get_cached_result("nonexistent_tool", f"arg_{i}")  # Miss
            self.cache_manager.get_cached_result(tool_name, f"arg_{i}")  # Hit
        
        # Verify statistics
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["hits"], 5)
        self.assertEqual(stats["misses"], 5)
        self.assertEqual(stats["hit_rate"], 50.0)
        self.assertEqual(stats["entries_count"], 5)
    
    def test_cache_eviction(self):
        """Test cache eviction when memory limit is reached"""
        # Create cache with very small memory limit
        small_cache = ToolCacheManager(cache_dir=self.temp_dir, max_memory_mb=1)
        
        # Fill cache with large results
        for i in range(20):
            tool_name = f"test_tool_{i}"
            result = {"large_data": "x" * 10000}  # Large result
            
            small_cache.cache_tool_result(tool_name, result, f"arg_{i}")
        
        # Verify cache size is within limits
        stats = small_cache.get_cache_stats()
        self.assertLess(stats["memory_usage_mb"], 2)  # Should be close to 1MB limit
    
    def test_file_cache_invalidation(self):
        """Test invalidation of cache entries for specific files"""
        # Create test files
        file1 = os.path.join(self.temp_dir, "file1.txt")
        file2 = os.path.join(self.temp_dir, "file2.txt")
        
        with open(file1, 'w') as f:
            f.write("content1")
        with open(file2, 'w') as f:
            f.write("content2")
        
        # Cache results for both files
        self.cache_manager.cache_tool_result("read_file", {"content": "content1"}, file1)
        self.cache_manager.cache_tool_result("read_file", {"content": "content2"}, file2)
        
        # Verify both are cached
        self.assertEqual(self.cache_manager.get_cache_stats()["entries_count"], 2)
        
        # Invalidate cache for file1
        self.cache_manager.invalidate_file_cache(file1)
        
        # Verify only file1's cache is invalidated
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["entries_count"], 1)
        self.assertEqual(stats["invalidations"], 1)

class TestToolCacheDecorator(unittest.TestCase):
    """Test the cache decorator functionality"""
    
    def setUp(self):
        # Clear global cache
        tool_cache.clear_cache()
        
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write("test content")
        self.temp_file.close()
        self.temp_path = self.temp_file.name
    
    def tearDown(self):
        # Clean up
        if os.path.exists(self.temp_path):
            os.unlink(self.temp_path)
    
    def test_cache_decorator(self):
        """Test that the cache decorator works correctly"""
        
        @cache_tool_output("test_function")
        def test_function(arg1, arg2=None):
            return f"result_{arg1}_{arg2}"
        
        # First call should execute function
        result1 = test_function("test", arg2="value")
        self.assertEqual(result1, "result_test_value")
        
        # Second call should return cached result
        result2 = test_function("test", arg2="value")
        self.assertEqual(result2, result1)
        
        # Verify cache hit
        stats = tool_cache.get_cache_stats()
        self.assertGreater(stats["hits"], 0)

class TestFileToolsCaching(unittest.TestCase):
    """Test caching integration with file tools"""
    
    def setUp(self):
        # Clear global cache
        tool_cache.clear_cache()
        
        # Create temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write("test file content\nline 2\nline 3")
        self.temp_file.close()
        self.temp_path = self.temp_file.name
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
    
    def tearDown(self):
        # Clean up
        if os.path.exists(self.temp_path):
            os.unlink(self.temp_path)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_read_file_caching(self):
        """Test that read_file results are cached"""
        # First call
        result1 = read_file(self.temp_path, "test_agent")
        # Check if security blocked or successful
        if result1.get("security_blocked", False):
            self.skipTest("Security framework blocked file access")
        
        self.assertTrue(result1["success"])
        
        # Second call should hit cache
        result2 = read_file(self.temp_path, "test_agent")
        self.assertEqual(result1, result2)
        
        # Verify cache hit
        stats = tool_cache.get_cache_stats()
        self.assertGreater(stats["hits"], 0)
    
    def test_list_dir_caching(self):
        """Test that list_dir results are cached"""
        # First call
        result1 = list_dir(self.temp_dir, "test_agent")
        # Check if security blocked or successful
        if result1.get("security_blocked", False):
            self.skipTest("Security framework blocked directory access")
        
        self.assertTrue(result1["success"])
        
        # Second call should hit cache
        result2 = list_dir(self.temp_dir, "test_agent")
        self.assertEqual(result1, result2)
        
        # Verify cache hit
        stats = tool_cache.get_cache_stats()
        self.assertGreater(stats["hits"], 0)
    
    def test_get_file_info_caching(self):
        """Test that get_file_info results are cached"""
        # First call
        result1 = get_file_info(self.temp_path, "test_agent")
        # Check if security blocked or successful
        if result1.get("security_blocked", False):
            self.skipTest("Security framework blocked file access")
        
        self.assertTrue(result1["success"])
        
        # Second call should hit cache
        result2 = get_file_info(self.temp_path, "test_agent")
        self.assertEqual(result1, result2)
        
        # Verify cache hit
        stats = tool_cache.get_cache_stats()
        self.assertGreater(stats["hits"], 0)
    
    def test_file_cache_invalidation_integration(self):
        """Test file cache invalidation integration"""
        # Cache file info
        result1 = get_file_info(self.temp_path, "test_agent")
        # Check if security blocked or successful
        if result1.get("security_blocked", False):
            self.skipTest("Security framework blocked file access")
        
        self.assertTrue(result1["success"])
        
        # Invalidate cache
        invalidate_file_cache(self.temp_path)
        
        # Next call should miss cache
        initial_misses = tool_cache.get_cache_stats()["misses"]
        result2 = get_file_info(self.temp_path, "test_agent")
        final_misses = tool_cache.get_cache_stats()["misses"]
        
        self.assertEqual(final_misses, initial_misses + 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
