#!/usr/bin/env python3
"""Debug section extraction"""

import tempfile
import os
from pathlib import Path
from tools.document_summary_generator import DocumentSummaryGenerator
from tools.section_extraction import get_document_summary, get_document_section

# Create test document
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
    print("Document content analysis:")
    print("=" * 50)
    
    # Generate summary
    generator = DocumentSummaryGenerator()
    summary = generator.generate_summary(temp_path)
    
    print(f"Total sections: {len(summary['sections'])}")
    print("\nSections:")
    for section in summary['sections']:
        print(f"  {section['section_id']}: {section['title']} (lines {section['start_line']}-{section['end_line']})")
    
    # Find API section
    api_section = None
    for section in summary['sections']:
        if 'API' in section['title'] or 'Endpoints' in section['title']:
            api_section = section
            break
    
    if api_section:
        print(f"\nFound API section: {api_section['section_id']} - {api_section['title']}")
        
        # Extract content
        result = get_document_section(temp_path, api_section['section_id'], "debug")
        if result['success']:
            content = result['content']
            print(f"\nExtracted content ({len(content)} chars):")
            print("=" * 30)
            print(content)
            print("=" * 30)
        else:
            print(f"Error: {result['error']}")
    else:
        print("No API section found!")

finally:
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    
    summary_path = Path(temp_path).with_suffix('.md.summary.json')
    if summary_path.exists():
        summary_path.unlink()
