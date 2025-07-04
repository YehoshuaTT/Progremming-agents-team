#!/usr/bin/env python3
"""
Tests for Multi-Layered Context and Drill-Down System
Tests document summary generation and section extraction functionality
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from tools.document_summary_generator import DocumentSummaryGenerator, DocumentSection
from tools.section_extraction import (
    get_document_section, get_document_summary, list_document_sections,
    get_section_context
)

class TestDocumentSummaryGenerator(unittest.TestCase):
    """Test the document summary generation functionality"""
    
    def setUp(self):
        self.generator = DocumentSummaryGenerator()
        self.test_content = """# Test Document

This is a test document for summary generation.

## Section 1: Introduction

This section introduces the main concepts and provides background information.

### Subsection 1.1: Overview

Here we provide a detailed overview of the system architecture and design principles.

## Section 2: Implementation

This section covers the implementation details and code examples.

```python
def example_function():
    return "Hello, World!"
```

### Subsection 2.1: Testing

Testing approaches and methodologies.

## Section 3: Conclusion

Final thoughts and next steps for the project.
"""
        
        # Create temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = self.temp_file.name
    
    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.temp_path):
            os.unlink(self.temp_path)
        
        summary_path = Path(self.temp_path).with_suffix('.md.summary.json')
        if summary_path.exists():
            summary_path.unlink()
    
    def test_generate_summary(self):
        """Test basic summary generation"""
        summary = self.generator.generate_summary(self.temp_path)
        
        # Check structure
        self.assertIn('document_title', summary)
        self.assertIn('total_tokens', summary)
        self.assertIn('sections', summary)
        self.assertIn('total_sections', summary)
        
        # Check sections
        sections = summary['sections']
        self.assertGreater(len(sections), 0)
        
        # Check first section structure
        first_section = sections[0]
        self.assertIn('section_id', first_section)
        self.assertIn('title', first_section)
        self.assertIn('summary', first_section)
        self.assertIn('token_count', first_section)
        self.assertIn('start_line', first_section)
        self.assertIn('end_line', first_section)
    
    def test_section_identification(self):
        """Test that sections are correctly identified"""
        summary = self.generator.generate_summary(self.temp_path)
        sections = summary['sections']
        
        # Should have multiple sections
        self.assertGreaterEqual(len(sections), 4)
        
        # Check that we have the expected sections
        section_titles = [s['title'] for s in sections]
        self.assertIn('Test Document', section_titles)
        self.assertIn('Section 1: Introduction', section_titles)
        self.assertIn('Section 2: Implementation', section_titles)
        self.assertIn('Section 3: Conclusion', section_titles)
    
    def test_token_estimation(self):
        """Test token count estimation"""
        summary = self.generator.generate_summary(self.temp_path)
        
        total_tokens = summary['total_tokens']
        self.assertGreater(total_tokens, 0)
        
        # Sum of section tokens should equal total
        section_tokens = sum(s['token_count'] for s in summary['sections'])
        self.assertEqual(total_tokens, section_tokens)
    
    def test_save_and_load_summary(self):
        """Test saving and loading summaries"""
        # Generate and save summary
        summary = self.generator.generate_summary(self.temp_path)
        summary_path = self.generator.save_summary(self.temp_path, summary)
        
        # Check file was created
        self.assertTrue(os.path.exists(summary_path))
        
        # Load and compare
        loaded_summary = self.generator.load_summary(self.temp_path)
        self.assertEqual(summary['document_title'], loaded_summary['document_title'])
        self.assertEqual(len(summary['sections']), len(loaded_summary['sections']))
    
    def test_summary_currency_check(self):
        """Test checking if summary is current"""
        # Generate and save summary
        summary = self.generator.generate_summary(self.temp_path)
        self.generator.save_summary(self.temp_path, summary)
        
        # Should be current initially
        self.assertTrue(self.generator.is_summary_current(self.temp_path))
        
        # Modify file (simulate change)
        import time
        time.sleep(0.1)  # Ensure different timestamp
        with open(self.temp_path, 'a') as f:
            f.write("\n\n## New Section\n\nNew content")
        
        # Should no longer be current
        self.assertFalse(self.generator.is_summary_current(self.temp_path))

class TestSectionExtraction(unittest.TestCase):
    """Test section extraction functionality"""
    
    def setUp(self):
        self.test_content = """# Main Document

Introduction to the document.

## Section A: Overview

This is the overview section with important information about the system.

## Section B: Details

Detailed implementation information and code examples.

```python
def test_function():
    return True
```

## Section C: Conclusion

Summary and conclusions.
"""
        
        # Create temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = self.temp_file.name
        
        # Generate summary
        generator = DocumentSummaryGenerator()
        summary = generator.generate_summary(self.temp_path)
        generator.save_summary(self.temp_path, summary)
    
    def tearDown(self):
        # Clean up
        if os.path.exists(self.temp_path):
            os.unlink(self.temp_path)
        
        summary_path = Path(self.temp_path).with_suffix('.md.summary.json')
        if summary_path.exists():
            summary_path.unlink()
    
    def test_get_document_summary(self):
        """Test getting document summary"""
        result = get_document_summary(self.temp_path, "test_agent")
        
        self.assertTrue(result['success'])
        self.assertIn('summary', result)
        self.assertIn('usage_instructions', result)
        
        summary = result['summary']
        self.assertIn('sections', summary)
        self.assertGreater(len(summary['sections']), 0)
    
    def test_get_document_section(self):
        """Test extracting specific section"""
        # First get summary to find section IDs
        summary_result = get_document_summary(self.temp_path, "test_agent")
        self.assertTrue(summary_result['success'])
        
        sections = summary_result['summary']['sections']
        first_section_id = sections[0]['section_id']
        
        # Extract the section
        result = get_document_section(self.temp_path, first_section_id, "test_agent")
        
        self.assertTrue(result['success'])
        self.assertIn('content', result)
        self.assertIn('section_info', result)
        self.assertGreater(len(result['content']), 0)
    
    def test_get_nonexistent_section(self):
        """Test error handling for nonexistent section"""
        result = get_document_section(self.temp_path, "INVALID-SECTION", "test_agent")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('available_sections', result)
    
    def test_list_document_sections(self):
        """Test listing all sections"""
        result = list_document_sections(self.temp_path, "test_agent")
        
        self.assertTrue(result['success'])
        self.assertIn('sections', result)
        self.assertIn('total_sections', result)
        self.assertGreater(result['total_sections'], 0)
        
        # Check section structure
        first_section = result['sections'][0]
        self.assertIn('section_id', first_section)
        self.assertIn('title', first_section)
        self.assertIn('summary', first_section)
    
    def test_get_section_context(self):
        """Test getting section with context"""
        # Get a middle section for context testing
        summary_result = get_document_summary(self.temp_path, "test_agent")
        sections = summary_result['summary']['sections']
        
        if len(sections) >= 2:
            middle_section_id = sections[1]['section_id']
            
            result = get_section_context(self.temp_path, middle_section_id, True, "test_agent")
            
            self.assertTrue(result['success'])
            self.assertIn('main_section', result)
            
            # Should have neighboring sections if available
            if len(sections) > 2:
                self.assertIn('neighboring_sections', result)

class TestIntegrationWorkflow(unittest.TestCase):
    """Test the complete workflow integration"""
    
    def test_complete_workflow(self):
        """Test the complete context optimization workflow"""
        # Create a realistic document
        document_content = """# User Authentication System Specification

This document specifies the requirements for a user authentication system.

## 1. Overview

The system provides secure user authentication with JWT tokens.

## 2. Authentication Requirements

### 2.1 User Registration

Users must register with email and password.

### 2.2 User Login

Users authenticate with email/password credentials.

## 3. API Endpoints

### 3.1 POST /auth/register

Register a new user account.

### 3.2 POST /auth/login

Authenticate user and return JWT token.

### 3.3 GET /auth/profile

Get user profile information (requires authentication).

## 4. Security Requirements

### 4.1 Password Security

Passwords must be hashed using bcrypt.

### 4.2 Token Security

JWT tokens must expire after 24 hours.

## 5. Implementation Notes

The system should be implemented using Node.js and Express.
"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_file.write(document_content)
        temp_file.close()
        temp_path = temp_file.name
        
        try:
            # Step 1: Agent requests document summary
            summary_result = get_document_summary(temp_path, "coder_agent")
            self.assertTrue(summary_result['success'])
            
            summary = summary_result['summary']
            self.assertGreater(len(summary['sections']), 5)
            
            # Step 2: Agent analyzes summary and identifies needed section
            # Looking for API endpoints section
            api_section = None
            for section in summary['sections']:
                if 'API' in section['title'] or 'Endpoints' in section['title']:
                    api_section = section
                    break
            
            self.assertIsNotNone(api_section, "Should find API section")
            
            # Step 3: Agent requests specific section
            section_result = get_document_section(temp_path, api_section['section_id'], "coder_agent")
            self.assertTrue(section_result['success'])
            
            content = section_result['content']
            self.assertIn('POST /auth/register', content)
            self.assertIn('POST /auth/login', content)
            self.assertIn('GET /auth/profile', content)
            
            # Step 4: Verify token savings
            # Original document would be ~500+ tokens
            # Section should be much smaller
            section_tokens = section_result['section_info']['token_count_estimate']
            total_tokens = summary['total_tokens']
            
            # Section should be significantly smaller than total
            self.assertLess(section_tokens, total_tokens * 0.5)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            summary_path = Path(temp_path).with_suffix('.md.summary.json')
            if summary_path.exists():
                summary_path.unlink()

if __name__ == '__main__':
    unittest.main(verbosity=2)
