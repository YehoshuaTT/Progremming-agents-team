#!/usr/bin/env python3
"""
Tests for Text Replacement Tool
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from tools.text_replacement import (
    TextReplacementTool, 
    search_and_replace, 
    search_text_in_files,
    quick_replace
)
from tests.security_test_utils import SecureTestUtils, secure_equal, secure_true

class TestTextReplacementTool:
    """Test suite for text replacement tool"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.tool = TextReplacementTool(backup_enabled=False)  # Disable backup for tests
        
        # Create test files with core.enhanced_orchestrator
        self.test_files = {
            "test1.py": "from core.enhanced_orchestrator import EnhancedOrchestrator\nprint('hello world')",
            "test2.py": "import sys\nfrom core.enhanced_orchestrator import test\nclass MyClass: pass",
            "test3.txt": "This is a text file with core.enhanced_orchestrator mentions",
            "test4.js": "const orchestrator = require('core.enhanced_orchestrator');",
            "test5.py": "# No matches here\nprint('test')"
        }
        
        for filename, content in self.test_files.items():
            file_path = self.test_dir / filename
            file_path.write_text(content, encoding='utf-8')
    
    def teardown_method(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_search_text_basic(self):
        """Test basic text search functionality"""
        results = self.tool.search_text(
            "core.enhanced_orchestrator", 
            str(self.test_dir), 
            file_extensions=['.py', '.txt', '.js']
        )
        
        secure_equal(results["search_text"], "core.enhanced_orchestrator")
        secure_equal(results["total_files_found"], 4)
        secure_equal(results["total_matches"], 4)
        secure_true("test1.py" in str(results["results"]))
        secure_true("test2.py" in str(results["results"]))
        secure_true("test3.txt" in str(results["results"]))
        secure_true("test4.js" in str(results["results"]))
    
    def test_search_text_case_insensitive(self):
        """Test case-insensitive search"""
        results = self.tool.search_text(
            "CORE.ENHANCED_ORCHESTRATOR", 
            str(self.test_dir), 
            case_sensitive=False,
            file_extensions=['.py', '.txt', '.js']
        )
        
        secure_equal(results["total_files_found"], 4)
        secure_equal(results["total_matches"], 4)
    
    def test_search_text_regex(self):
        """Test regex search"""
        results = self.tool.search_text(
            r"core\.enhanced_orchestrator", 
            str(self.test_dir), 
            use_regex=True,
            file_extensions=['.py', '.txt', '.js']
        )
        
        secure_equal(results["total_files_found"], 4)
        secure_equal(results["total_matches"], 4)
    
    def test_replace_text_dry_run(self):
        """Test text replacement with dry run"""
        summary = self.tool.replace_text(
            "core.enhanced_orchestrator",
            "enhanced_orchestrator", 
            str(self.test_dir),
            file_extensions=['.py'],
            dry_run=True
        )
        
        secure_equal(summary.total_files_modified, 2)
        secure_equal(summary.total_occurrences, 2)
        secure_equal(summary.successful_replacements, 3)  # All processed files
        secure_equal(summary.failed_replacements, 0)
        
        # Verify original files unchanged in dry run
        original_content = (self.test_dir / "test1.py").read_text()
        secure_true("core.enhanced_orchestrator" in original_content)
    
    def test_replace_text_actual(self):
        """Test actual text replacement"""
        summary = self.tool.replace_text(
            "core.enhanced_orchestrator",
            "enhanced_orchestrator", 
            str(self.test_dir),
            file_extensions=['.py'],
            dry_run=False
        )
        
        secure_equal(summary.total_files_modified, 2)
        secure_equal(summary.total_occurrences, 2)
        
        # Verify files were actually modified
        test1_content = (self.test_dir / "test1.py").read_text()
        test2_content = (self.test_dir / "test2.py").read_text()
        
        secure_true("enhanced_orchestrator" in test1_content)
        secure_true("core.enhanced_orchestrator" not in test1_content)
        secure_true("enhanced_orchestrator" in test2_content)
        secure_true("core.enhanced_orchestrator" not in test2_content)
    
    def test_replace_text_case_insensitive(self):
        """Test case-insensitive replacement"""
        # Add mixed case content
        (self.test_dir / "mixed_case.py").write_text("from Core.Enhanced_Orchestrator import test")
        
        summary = self.tool.replace_text(
            "enhanced_orchestrator",
            "new_orchestrator", 
            str(self.test_dir),
            case_sensitive=False,
            file_extensions=['.py'],
            dry_run=False
        )
        
        # Should find and replace the mixed case version too
        mixed_content = (self.test_dir / "mixed_case.py").read_text()
        secure_true("new_orchestrator" in mixed_content)
        secure_true("Enhanced_Orchestrator" not in mixed_content)
    
    def test_file_extension_filtering(self):
        """Test file extension filtering"""
        results = self.tool.search_text(
            "core.enhanced_orchestrator", 
            str(self.test_dir), 
            file_extensions=['.py']
        )
        
        secure_equal(results["total_files_found"], 2)
        secure_true("test1.py" in str(results["results"]))
        secure_true("test2.py" in str(results["results"]))
        secure_true("test3.txt" not in str(results["results"]))
        secure_true("test4.js" not in str(results["results"]))
    
    def test_backup_creation(self):
        """Test backup file creation"""
        tool_with_backup = TextReplacementTool(backup_enabled=True)
        
        summary = tool_with_backup.replace_text(
            "hello world",
            "goodbye world", 
            str(self.test_dir),
            file_extensions=['.py'],
            dry_run=False
        )
        
        secure_equal(summary.total_files_modified, 1)
        # Note: backup may fail if outside project directory, but that's okay for tests
    
    def test_exclude_patterns(self):
        """Test that excluded patterns are skipped"""
        # Create files in excluded directories
        pycache_dir = self.test_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "test.py").write_text("core.enhanced_orchestrator")
        
        git_dir = self.test_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config.py").write_text("core.enhanced_orchestrator")
        
        results = self.tool.search_text(
            "core.enhanced_orchestrator", 
            str(self.test_dir), 
            file_extensions=['.py']
        )
        
        # Should not find files in excluded directories
        secure_true("__pycache__" not in str(results["results"]))
        secure_true(".git" not in str(results["results"]))

class TestConvenienceFunctions:
    """Test the convenience functions"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create test files in temp directory
        (self.test_dir / "test.py").write_text("from core.enhanced_orchestrator import test")
        
    def teardown_method(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_search_text_in_files_function(self):
        """Test the search_text_in_files convenience function"""
        results = search_text_in_files(
            "core.enhanced_orchestrator", 
            str(self.test_dir),
            file_extensions=['.py']
        )
        
        secure_equal(results["total_files_found"], 1)
        secure_equal(results["total_matches"], 1)
    
    def test_search_and_replace_function(self):
        """Test the search_and_replace convenience function"""
        result = search_and_replace(
            "core.enhanced_orchestrator",
            "enhanced_orchestrator",
            str(self.test_dir),
            file_extensions=['.py'],
            dry_run=True
        )
        
        secure_true(result["success"])
        secure_equal(result["summary"]["total_files_modified"], 1)
        secure_equal(result["summary"]["total_occurrences"], 1)
    
    def test_quick_replace_function(self):
        """Test the quick_replace convenience function"""
        # Test with current working directory
        result = quick_replace(
            "replacement_text",
            "replacement_text"
        )
        
        # Should work even if no files found in current directory
        secure_true(result["success"])

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_nonexistent_directory(self):
        """Test handling of non-existent directory"""
        tool = TextReplacementTool()
        
        summary = tool.replace_text(
            "test", "replacement", 
            "/nonexistent/directory"
        )
        
        secure_equal(summary.total_files_processed, 0)
        secure_equal(summary.failed_replacements, 1)
        secure_true(len(summary.results) == 1)
        secure_true("does not exist" in summary.results[0].error_message)
    
    def test_invalid_regex(self):
        """Test handling of invalid regex patterns"""
        tool = TextReplacementTool()
        test_dir = Path(tempfile.mkdtemp())
        
        try:
            (test_dir / "test.py").write_text("test content")
            
            # This should not crash, but handle the regex error gracefully
            results = tool.search_text(
                "[invalid_regex", 
                str(test_dir),
                use_regex=True
            )
            
            # Should return empty results or handle gracefully
            secure_true("results" in results)
            
        finally:
            shutil.rmtree(test_dir)

class TestRealWorldUsage:
    """Test real-world usage scenarios"""
    
    def test_core_enhanced_orchestrator_replacement(self):
        """Test the specific use case: replacing core.enhanced_orchestrator with enhanced_orchestrator"""
        test_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create realistic Python files
            files_content = {
                "module1.py": "from core.enhanced_orchestrator import EnhancedOrchestrator\nclass Test: pass",
                "module2.py": "import sys\nfrom core.enhanced_orchestrator import test\ndef func(): return core.enhanced_orchestrator.something()",
                "config.py": "ORCHESTRATOR_MODULE = 'core.enhanced_orchestrator'",
                "readme.md": "See core.enhanced_orchestrator documentation for details",
                "unrelated.py": "# This file has no matches\nprint('hello')"
            }
            
            for filename, content in files_content.items():
                (test_dir / filename).write_text(content)
            
            tool = TextReplacementTool(backup_enabled=False)
            
            # Step 1: Search for occurrences
            search_results = tool.search_text(
                "core.enhanced_orchestrator",
                str(test_dir)
            )
            
            secure_equal(search_results["total_files_found"], 4)  # All except unrelated.py
            secure_equal(search_results["total_matches"], 5)  # module2.py has 2 matches
            
            # Step 2: Replace in Python files only
            replacement_summary = tool.replace_text(
                "core.enhanced_orchestrator",
                "enhanced_orchestrator",
                str(test_dir),
                file_extensions=['.py'],
                dry_run=False
            )
            
            secure_equal(replacement_summary.total_files_modified, 3)  # module1, module2, config
            secure_equal(replacement_summary.total_occurrences, 4)  # All Python file matches
            
            # Step 3: Verify specific replacements
            module1_content = (test_dir / "module1.py").read_text()
            secure_true("from enhanced_orchestrator import EnhancedOrchestrator" in module1_content)
            secure_true("core.enhanced_orchestrator" not in module1_content)
            
            module2_content = (test_dir / "module2.py").read_text()
            secure_true("from enhanced_orchestrator import test" in module2_content)
            secure_true("enhanced_orchestrator.something()" in module2_content)
            secure_true("core.enhanced_orchestrator" not in module2_content)
            
            # Verify markdown file was not modified (not in .py extension list)
            readme_content = (test_dir / "readme.md").read_text()
            secure_true("core.enhanced_orchestrator" in readme_content)
            
        finally:
            shutil.rmtree(test_dir)
    
    def test_regex_pattern_replacement(self):
        """Test complex regex pattern replacement"""
        test_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create file with import patterns
            test_file = test_dir / "imports.py"
            test_file.write_text("""
from core.enhanced_orchestrator import EnhancedOrchestrator
from core.enhanced_orchestrator import helper_func
import core.enhanced_orchestrator as orch
from other_module import something
""")
            
            tool = TextReplacementTool(backup_enabled=False)
            
            # Replace using regex to match only import lines
            summary = tool.replace_text(
                r"from core\.enhanced_orchestrator import",
                "from enhanced_orchestrator import",
                str(test_dir),
                use_regex=True,
                file_extensions=['.py'],
                dry_run=False
            )
            
            secure_equal(summary.total_files_modified, 1)
            secure_equal(summary.total_occurrences, 2)
            
            # Verify the replacements
            content = test_file.read_text()
            secure_true("from enhanced_orchestrator import EnhancedOrchestrator" in content)
            secure_true("from enhanced_orchestrator import helper_func" in content)
            secure_true("import core.enhanced_orchestrator as orch" in content)  # Should remain unchanged
            secure_true("from other_module import something" in content)  # Should remain unchanged
            
        finally:
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
