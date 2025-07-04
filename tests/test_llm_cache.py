#!/usr/bin/env python3
"""
Tests for LLM Cache System
Tests intelligent caching of LLM responses with various strategies
"""

import unittest
import tempfile
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.llm_cache import LLMCacheManager, LLMCacheStrategy, LLMCacheEntry, llm_cache

class TestLLMCacheManager(unittest.TestCase):
    """Test LLM cache manager functionality"""
    
    def setUp(self):
        # Create temporary cache directory
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = LLMCacheManager(cache_dir=self.temp_dir, max_memory_mb=10)
    
    def tearDown(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_key_generation(self):
        """Test cache key generation for different strategies"""
        agent_name = "Product_Analyst"
        prompt = "Create a specification for user profile page"
        context = {"task_id": "TASK-001", "priority": "high"}
        
        # Test exact match strategy
        key1 = self.cache_manager._generate_cache_key(agent_name, prompt, context)
        key2 = self.cache_manager._generate_cache_key(agent_name, prompt, context)
        self.assertEqual(key1, key2)
        
        # Test different prompts generate different keys
        key3 = self.cache_manager._generate_cache_key(agent_name, "Different prompt", context)
        self.assertNotEqual(key1, key3)
        
        # Test different agents generate different keys
        key4 = self.cache_manager._generate_cache_key("Coder", prompt, context)
        self.assertNotEqual(key1, key4)
    
    def test_prompt_normalization(self):
        """Test prompt normalization for semantic matching"""
        prompt1 = "Create spec for TASK-123-456 at 2025-01-01T10:00:00"
        prompt2 = "Create spec for TASK-789-012 at 2025-01-02T15:30:00"
        
        normalized1 = self.cache_manager._normalize_prompt(prompt1)
        normalized2 = self.cache_manager._normalize_prompt(prompt2)
        
        # Should normalize to same pattern
        self.assertEqual(normalized1, normalized2)
        self.assertIn("[TASK-ID]", normalized1)
        self.assertIn("[TIMESTAMP]", normalized1)
    
    def test_cache_entry_creation(self):
        """Test LLM cache entry creation and properties"""
        entry = LLMCacheEntry(
            key="test_key",
            prompt="Test prompt",
            response="Test response",
            agent_name="Test_Agent",
            cache_strategy=LLMCacheStrategy.EXACT_MATCH,
            created_at=time.time(),
            ttl=3600
        )
        
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.agent_name, "Test_Agent")
        self.assertGreater(entry.size_bytes, 0)
        self.assertGreater(entry.prompt_tokens, 0)
        self.assertGreater(entry.response_tokens, 0)
        self.assertFalse(entry.is_expired())
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic"""
        entry = LLMCacheEntry(
            key="test_key",
            prompt="Test prompt",
            response="Test response",
            agent_name="Test_Agent",
            cache_strategy=LLMCacheStrategy.EXACT_MATCH,
            created_at=time.time() - 7200,  # 2 hours ago
            ttl=3600  # 1 hour TTL
        )
        
        self.assertTrue(entry.is_expired())
    
    def test_cache_store_and_retrieve(self):
        """Test basic cache store and retrieve functionality"""
        agent_name = "Product_Analyst"
        prompt = "Create a specification for user profile page"
        response = "# User Profile Page Specification\n\n## Overview\nThis page displays user information..."
        context = {"task_id": "TASK-001"}
        
        # Store in cache
        success = self.cache_manager.cache_llm_response(agent_name, prompt, response, context)
        self.assertTrue(success)
        
        # Retrieve from cache
        cached_response = self.cache_manager.get_llm_response(agent_name, prompt, context)
        self.assertEqual(cached_response, response)
        
        # Verify cache statistics
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["entries_count"], 1)
    
    def test_cache_miss(self):
        """Test cache miss scenarios"""
        agent_name = "Product_Analyst"
        prompt = "Create a specification for user profile page"
        context = {"task_id": "TASK-001"}
        
        # Try to retrieve non-existent entry
        cached_response = self.cache_manager.get_llm_response(agent_name, prompt, context)
        self.assertIsNone(cached_response)
        
        # Verify cache statistics
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 1)
    
    def test_cache_expiration_cleanup(self):
        """Test automatic cleanup of expired entries"""
        agent_name = "Test_Agent"
        prompt = "Test prompt"
        response = "Test response"
        
        # Create entry with short TTL
        with patch.object(self.cache_manager, 'agent_cache_config') as mock_config:
            mock_config.get.return_value = {
                "ttl": 1,  # 1 second TTL
                "strategy": LLMCacheStrategy.EXACT_MATCH,
                "max_entries": 100,
                "cost_per_1k_tokens": 0.002
            }
            
            # Store entry
            success = self.cache_manager.cache_llm_response(agent_name, prompt, response)
            self.assertTrue(success)
            
            # Verify entry exists
            cached_response = self.cache_manager.get_llm_response(agent_name, prompt)
            self.assertEqual(cached_response, response)
            
            # Wait for expiration
            time.sleep(2)
            
            # Try to retrieve expired entry
            cached_response = self.cache_manager.get_llm_response(agent_name, prompt)
            self.assertIsNone(cached_response)
    
    def test_cache_memory_limits(self):
        """Test cache memory limit enforcement"""
        # Create cache with very small memory limit
        small_cache = LLMCacheManager(cache_dir=self.temp_dir, max_memory_mb=1)
        
        # Fill cache with large responses
        for i in range(10):
            agent_name = f"Agent_{i}"
            prompt = f"Test prompt {i}"
            response = "Large response " * 1000  # Large response
            
            small_cache.cache_llm_response(agent_name, prompt, response)
        
        # Verify cache size is within limits
        stats = small_cache.get_cache_stats()
        self.assertLess(stats["cache_size_mb"], 2)  # Should be close to 1MB limit
    
    def test_agent_specific_configuration(self):
        """Test agent-specific cache configuration"""
        # Test Product_Analyst (long TTL)
        product_analyst_config = self.cache_manager.agent_cache_config["Product_Analyst"]
        self.assertEqual(product_analyst_config["ttl"], 7200)  # 2 hours
        self.assertEqual(product_analyst_config["strategy"], LLMCacheStrategy.CONTEXT_AWARE)
        
        # Test Coder (medium TTL)
        coder_config = self.cache_manager.agent_cache_config["Coder"]
        self.assertEqual(coder_config["ttl"], 3600)  # 1 hour
        self.assertEqual(coder_config["strategy"], LLMCacheStrategy.SEMANTIC_MATCH)
        
        # Test Code_Reviewer (short TTL)
        reviewer_config = self.cache_manager.agent_cache_config["Code_Reviewer"]
        self.assertEqual(reviewer_config["ttl"], 1800)  # 30 minutes
        self.assertEqual(reviewer_config["strategy"], LLMCacheStrategy.EXACT_MATCH)
    
    def test_cache_statistics_accuracy(self):
        """Test accuracy of cache statistics"""
        agent_name = "Test_Agent"
        
        # Perform cache operations
        for i in range(5):
            prompt = f"Test prompt {i}"
            response = f"Test response {i}"
            
            # Store response
            self.cache_manager.cache_llm_response(agent_name, prompt, response)
            
            # Retrieve twice (1 miss, 1 hit)
            self.cache_manager.get_llm_response(agent_name, f"Non-existent prompt {i}")  # Miss
            self.cache_manager.get_llm_response(agent_name, prompt)  # Hit
        
        # Verify statistics
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["hits"], 5)
        self.assertEqual(stats["misses"], 5)
        self.assertEqual(stats["hit_rate"], 50.0)
        self.assertEqual(stats["entries_count"], 5)
        self.assertGreater(stats["total_cost_saved"], 0)
        self.assertGreater(stats["total_tokens_saved"], 0)
    
    def test_cache_clear_functionality(self):
        """Test cache clearing functionality"""
        # Add entries for different agents
        agents = ["Agent_A", "Agent_B", "Agent_C"]
        
        for agent in agents:
            prompt = f"Test prompt for {agent}"
            response = f"Test response for {agent}"
            self.cache_manager.cache_llm_response(agent, prompt, response)
        
        # Verify all entries exist
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["entries_count"], 3)
        
        # Clear cache for specific agent
        self.cache_manager.clear_cache("Agent_A")
        
        # Verify only Agent_A's cache is cleared
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["entries_count"], 2)
        
        # Clear all cache
        self.cache_manager.clear_cache()
        
        # Verify all cache is cleared
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["entries_count"], 0)
    
    def test_agent_distribution_tracking(self):
        """Test agent distribution tracking in cache"""
        agents = ["Product_Analyst", "Coder", "Code_Reviewer"]
        
        # Add multiple entries for each agent
        for agent in agents:
            for i in range(3):
                prompt = f"Test prompt {i} for {agent}"
                response = f"Test response {i} for {agent}"
                self.cache_manager.cache_llm_response(agent, prompt, response)
        
        # Check agent distribution
        stats = self.cache_manager.get_cache_stats()
        distribution = stats["agent_distribution"]
        
        for agent in agents:
            self.assertEqual(distribution[agent], 3)

class TestLLMCacheIntegration(unittest.TestCase):
    """Test LLM cache integration with the system"""
    
    def setUp(self):
        # Use global cache instance
        self.cache = llm_cache
        self.cache.clear_cache()  # Start with clean cache
    
    def test_global_cache_instance(self):
        """Test that global cache instance works correctly"""
        agent_name = "Product_Analyst"
        prompt = "Create specification for user authentication"
        response = "# User Authentication Specification\n\n## Overview\n..."
        
        # Store in global cache
        success = self.cache.cache_llm_response(agent_name, prompt, response)
        self.assertTrue(success)
        
        # Retrieve from global cache
        cached_response = self.cache.get_llm_response(agent_name, prompt)
        self.assertEqual(cached_response, response)
    
    def test_concurrent_access(self):
        """Test concurrent access to cache"""
        import threading
        
        def cache_worker(agent_id):
            agent_name = f"Agent_{agent_id}"
            prompt = f"Test prompt for {agent_name}"
            response = f"Test response for {agent_name}"
            
            # Store and retrieve
            self.cache.cache_llm_response(agent_name, prompt, response)
            cached_response = self.cache.get_llm_response(agent_name, prompt)
            
            self.assertEqual(cached_response, response)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache has entries from all threads
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats["entries_count"], 10)

if __name__ == '__main__':
    unittest.main(verbosity=2)
