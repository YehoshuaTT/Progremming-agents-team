#!/usr/bin/env python3
"""
Test Context System Integration with Enhanced Orchestrator
Verifies that the context optimization system is properly integrated into the orchestrator
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enhanced_orchestrator import EnhancedOrchestrator
from tools.handoff_system import HandoffPacket, TaskStatus, NextStepSuggestion

class TestContextIntegration(unittest.TestCase):
    """Test context system integration with orchestrator"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = EnhancedOrchestrator()
        
        # Mock some dependencies to avoid file system operations
        self.orchestrator.task_tools = Mock()
        self.orchestrator.log_tools = Mock()
        self.orchestrator.file_tools = Mock()
        
        # Create test document
        self.test_doc_path = os.path.join(self.temp_dir, "test_doc.md")
        with open(self.test_doc_path, "w") as f:
            f.write("""# Test Document

## Section 1
This is the first section with some content.

## Section 2
This is the second section with more content.

### Subsection 2.1
This is a subsection.
""")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_context_optimization_initialization(self):
        """Test that context optimization is properly initialized"""
        self.assertTrue(self.orchestrator.context_optimization_enabled)
        self.assertIsNotNone(self.orchestrator.document_summary_generator)
        self.assertEqual(self.orchestrator.max_context_tokens, 16000)
        self.assertIsInstance(self.orchestrator.summary_cache, dict)
    
    def test_context_optimization_for_agent(self):
        """Test context optimization for specific agent"""
        # Create test context
        context = {
            "user_request": "Test request",
            "previous_artifacts": [self.test_doc_path],
            "previous_notes": "Test notes"
        }
        
        # Mock the summary generator to avoid actual file operations
        mock_summary = {
            "document_title": "Test Document",
            "total_sections": 2,
            "sections": [
                {
                    "section_id": "section_1",
                    "title": "Section 1",
                    "summary": "First section summary",
                    "token_count": 50
                }
            ]
        }
        
        with patch.object(self.orchestrator.document_summary_generator, 'generate_summary') as mock_gen:
            mock_gen.return_value = mock_summary
            
            # Test optimization
            optimized_context = self.orchestrator._optimize_context_for_agent(context, "Test_Agent")
            
            # Verify optimization
            self.assertIn("context_tools", optimized_context)
            self.assertIn("artifact_summaries", optimized_context)
            self.assertTrue(optimized_context["context_tools"]["summary_available"])
            self.assertTrue(optimized_context["context_tools"]["drill_down_available"])
    
    def test_token_estimation(self):
        """Test token estimation functionality"""
        test_context = {
            "user_request": "Test request",
            "data": "Some test data"
        }
        
        token_count = self.orchestrator._estimate_context_tokens(test_context)
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)
    
    async def test_section_extraction_integration(self):
        """Test section extraction integration"""
        # Mock the get_document_section function
        mock_result = {
            "success": True,
            "content": "Test section content",
            "section_id": "test_section",
            "agent_id": "test_agent"
        }
        
        with patch('enhanced_orchestrator.get_document_section', return_value=mock_result):
            result = await self.orchestrator.get_section_for_agent(
                self.test_doc_path, 
                "test_section", 
                "test_agent"
            )
            
            self.assertTrue(result["success"])
            self.assertEqual(result["content"], "Test section content")
    
    def test_context_optimization_stats(self):
        """Test context optimization statistics"""
        stats = self.orchestrator.get_context_optimization_stats()
        
        self.assertIn("optimization_enabled", stats)
        self.assertIn("max_context_tokens", stats)
        self.assertIn("cached_summaries", stats)
        self.assertIn("total_handoffs", stats)
        self.assertIn("active_workflows", stats)
        
        self.assertTrue(stats["optimization_enabled"])
        self.assertEqual(stats["max_context_tokens"], 16000)
    
    async def test_agent_context_request_handling(self):
        """Test agent context request handling"""
        # Mock the section extraction
        mock_result = {
            "success": True,
            "content": "Test content",
            "section_id": "test_section",
            "agent_id": "test_agent"
        }
        
        with patch.object(self.orchestrator, 'get_section_for_agent', return_value=mock_result):
            result = await self.orchestrator.handle_agent_context_request(
                "test_agent", 
                self.test_doc_path, 
                "test_section"
            )
            
            self.assertTrue(result["success"])
            self.assertEqual(result["content"], "Test content")
    
    def test_summary_caching(self):
        """Test summary caching functionality"""
        # Create test context with artifacts
        context = {
            "previous_artifacts": [self.test_doc_path]
        }
        
        mock_summary = {
            "document_title": "Test Document",
            "total_sections": 2
        }
        
        with patch.object(self.orchestrator.document_summary_generator, 'generate_summary') as mock_gen:
            mock_gen.return_value = mock_summary
            
            # First call should generate summary
            summaries1 = self.orchestrator._get_artifact_summaries([self.test_doc_path], "Agent1")
            self.assertEqual(len(summaries1), 1)
            
            # Second call should use cache
            summaries2 = self.orchestrator._get_artifact_summaries([self.test_doc_path], "Agent1")
            self.assertEqual(len(summaries2), 1)
            
            # Check that cache was used (summary generator called only once)
            self.assertEqual(mock_gen.call_count, 1)
    
    def test_context_optimization_logging(self):
        """Test that context optimization generates proper logs"""
        # Create test context
        context = {
            "previous_artifacts": [self.test_doc_path]
        }
        
        mock_summary = {
            "document_title": "Test Document"
        }
        
        with patch.object(self.orchestrator.document_summary_generator, 'generate_summary') as mock_gen:
            mock_gen.return_value = mock_summary
            
            # Call optimization
            self.orchestrator._optimize_context_for_agent(context, "Test_Agent")
            
            # Verify logging was called
            self.orchestrator.log_tools.record_log.assert_called()
            
            # Check for specific log entries
            call_args_list = self.orchestrator.log_tools.record_log.call_args_list
            log_events = [call[1]['event'] for call in call_args_list]
            
            # Should have summary generation log
            self.assertIn("SUMMARY_GENERATED", log_events)

if __name__ == '__main__':
    unittest.main()
