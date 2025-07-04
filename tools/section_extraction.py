#!/usr/bin/env python3
"""
Document Section Extraction Tool
Extracts specific sections from documents based on section IDs from summaries
"""

import json
import re
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import with proper path handling
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.document_summary_generator import DocumentSummaryGenerator
from tools.tool_cache import cache_tool_output

@cache_tool_output("extract_section")
def get_document_section(document_path: str, section_id: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """
    Extract a specific section from a document using its section ID.
    This is the main tool that agents will use for drill-down context.
    
    Args:
        document_path: Path to the original document
        section_id: Section identifier from the document summary
        agent_id: ID of the requesting agent (for logging)
    
    Returns:
        Dict containing success status, section content, and metadata
    """
    try:
        path = Path(document_path)
        
        # Validate document exists
        if not path.exists():
            return {
                "success": False,
                "content": "",
                "error": f"Document not found: {document_path}",
                "section_id": section_id,
                "agent_id": agent_id
            }
        
        # Load or generate document summary
        generator = DocumentSummaryGenerator()
        summary = generator.load_summary(document_path)
        
        if not summary or not generator.is_summary_current(document_path):
            # Generate new summary if needed
            summary = generator.generate_summary(document_path)
            generator.save_summary(document_path, summary)
        
        # Find the requested section
        section_info = _find_section_by_id(summary, section_id)
        if not section_info:
            return {
                "success": False,
                "content": "",
                "error": f"Section '{section_id}' not found in document",
                "section_id": section_id,
                "agent_id": agent_id,
                "available_sections": [s["section_id"] for s in summary.get("sections", [])]
            }
        
        # Extract section content from original document
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_line = section_info["start_line"]
        end_line = section_info["end_line"]
        
        # Extract the actual section content
        section_content = ''.join(lines[start_line:end_line + 1])
        
        # Log successful extraction (if security framework available)
        try:
            from tools.security_framework import security_manager, SecurityLevel, SecurityAction
            security_manager.security_logger.log_security_event(
                event_type="section_extracted",
                severity=SecurityLevel.LOW,
                agent_id=agent_id,
                details={
                    "document": document_path,
                    "section_id": section_id,
                    "content_length": len(section_content),
                    "token_estimate": section_info.get("token_count_estimate", 0)
                },
                action_taken=SecurityAction.ALLOW
            )
        except ImportError:
            # Security framework not available in standalone mode
            pass
        
        return {
            "success": True,
            "content": section_content.strip(),
            "section_info": {
                "section_id": section_id,
                "title": section_info.get("title", ""),
                "summary": section_info.get("summary", ""),
                "token_count_estimate": section_info.get("token_count_estimate", 0),
                "level": section_info.get("level", 1)
            },
            "document_path": document_path,
            "agent_id": agent_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "error": f"Error extracting section: {str(e)}",
            "section_id": section_id,
            "agent_id": agent_id
        }

def get_document_summary(document_path: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """
    Get the summary of a document. This is what agents will receive as initial context.
    
    Args:
        document_path: Path to the document
        agent_id: ID of the requesting agent
    
    Returns:
        Dict containing the document summary or error information
    """
    try:
        path = Path(document_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": f"Document not found: {document_path}",
                "agent_id": agent_id
            }
        
        generator = DocumentSummaryGenerator()
        
        # Load or generate summary
        summary = generator.load_summary(document_path)
        if not summary or not generator.is_summary_current(document_path):
            summary = generator.generate_summary(document_path)
            generator.save_summary(document_path, summary)
        
        # Log summary access (if security framework available)
        try:
            from tools.security_framework import security_manager, SecurityLevel, SecurityAction
            security_manager.security_logger.log_security_event(
                event_type="summary_accessed",
                severity=SecurityLevel.LOW,
                agent_id=agent_id,
                details={
                    "document": document_path,
                    "section_count": len(summary.get("sections", [])),
                    "total_tokens": summary.get("total_token_estimate", 0)
                },
                action_taken=SecurityAction.ALLOW
            )
        except ImportError:
            # Security framework not available in standalone mode
            pass
        
        return {
            "success": True,
            "summary": summary,
            "agent_id": agent_id,
            "usage_instructions": {
                "description": "This is a structured summary of the document. Use get_document_section(document_path, section_id) to retrieve full content of specific sections.",
                "available_sections": [
                    {
                        "id": section["section_id"],
                        "title": section["title"],
                        "summary": section["summary"]
                    }
                    for section in summary.get("sections", [])
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting document summary: {str(e)}",
            "agent_id": agent_id
        }

def list_document_sections(document_path: str, agent_id: str = "unknown") -> Dict[str, Any]:
    """
    List all available sections in a document.
    
    Args:
        document_path: Path to the document
        agent_id: ID of the requesting agent
    
    Returns:
        Dict containing list of sections with their metadata
    """
    try:
        summary_result = get_document_summary(document_path, agent_id)
        
        if not summary_result["success"]:
            return summary_result
        
        summary = summary_result["summary"]
        sections = []
        
        def extract_sections(section_list, level=0):
            for section in section_list:
                sections.append({
                    "section_id": section["section_id"],
                    "title": section["title"],
                    "summary": section["summary"],
                    "token_count_estimate": section.get("token_count_estimate", 0),
                    "level": section.get("level", 1),
                    "indent": "  " * level + section["title"]
                })
                
                # Recursively add subsections
                if "subsections" in section:
                    extract_sections(section["subsections"], level + 1)
        
        extract_sections(summary.get("sections", []))
        
        return {
            "success": True,
            "sections": sections,
            "total_sections": len(sections),
            "document_title": summary.get("document_title", ""),
            "total_token_estimate": summary.get("total_token_estimate", 0),
            "agent_id": agent_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing sections: {str(e)}",
            "agent_id": agent_id
        }

def _find_section_by_id(summary: Dict[str, Any], section_id: str) -> Optional[Dict[str, Any]]:
    """Find a section by its ID in the summary structure"""
    
    def search_sections(sections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for section in sections:
            if section.get("section_id") == section_id:
                return section
            
            # Search in subsections
            if "subsections" in section:
                result = search_sections(section["subsections"])
                if result:
                    return result
        
        return None
    
    return search_sections(summary.get("sections", []))

def get_section_context(document_path: str, section_id: str, include_neighbors: bool = True, agent_id: str = "unknown") -> Dict[str, Any]:
    """
    Get section content with optional neighboring sections for better context.
    
    Args:
        document_path: Path to the document
        section_id: Target section ID
        include_neighbors: Whether to include previous/next sections
        agent_id: ID of the requesting agent
    
    Returns:
        Dict containing section content with optional context
    """
    try:
        # Get the target section
        main_result = get_document_section(document_path, section_id, agent_id)
        
        if not main_result["success"]:
            return main_result
        
        result = {
            "success": True,
            "main_section": main_result,
            "agent_id": agent_id
        }
        
        if include_neighbors:
            # Get document summary to find neighboring sections
            summary_result = get_document_summary(document_path, agent_id)
            if summary_result["success"]:
                summary = summary_result["summary"]
                sections = summary.get("sections", [])
                
                # Find current section index
                current_idx = None
                for i, section in enumerate(sections):
                    if section["section_id"] == section_id:
                        current_idx = i
                        break
                
                if current_idx is not None:
                    neighbors = {}
                    
                    # Previous section
                    if current_idx > 0:
                        prev_section = sections[current_idx - 1]
                        prev_result = get_document_section(document_path, prev_section["section_id"], agent_id)
                        if prev_result["success"]:
                            neighbors["previous"] = prev_result
                    
                    # Next section
                    if current_idx < len(sections) - 1:
                        next_section = sections[current_idx + 1]
                        next_result = get_document_section(document_path, next_section["section_id"], agent_id)
                        if next_result["success"]:
                            neighbors["next"] = next_result
                    
                    if neighbors:
                        result["neighboring_sections"] = neighbors
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting section context: {str(e)}",
            "section_id": section_id,
            "agent_id": agent_id
        }

# Example usage and testing
if __name__ == "__main__":
    # Test the section extraction functionality
    test_doc = """# Test Document

This is a test document for section extraction.

## Section A: Introduction

This section introduces the main concepts and provides an overview of the topics covered.

### Section A.1: Overview

Here we provide a detailed overview of the system architecture.

## Section B: Implementation

This section covers the implementation details.

```python
def example_function():
    return "Hello, World!"
```

### Section B.1: Code Examples

More code examples and explanations.

## Section C: Conclusion

Final thoughts and conclusions about the implementation.
"""
    
    # Save test document
    test_path = Path("test_extraction.md")
    with open(test_path, 'w') as f:
        f.write(test_doc)
    
    try:
        print("Testing Document Section Extraction")
        print("=" * 50)
        
        # Test getting document summary
        print("\n1. Getting document summary:")
        summary_result = get_document_summary(str(test_path))
        if summary_result["success"]:
            summary = summary_result["summary"]
            print(f"Document: {summary['document_title']}")
            print(f"Sections: {len(summary['sections'])}")
            for section in summary['sections']:
                print(f"  - {section['section_id']}: {section['title']}")
        
        # Test section extraction
        print("\n2. Extracting specific section:")
        section_result = get_document_section(str(test_path), "SEC-002")
        if section_result["success"]:
            print(f"Section: {section_result['section_info']['title']}")
            print(f"Content length: {len(section_result['content'])} characters")
            print("Content preview:")
            print(section_result['content'][:200] + "...")
        
        # Test listing sections
        print("\n3. Listing all sections:")
        list_result = list_document_sections(str(test_path))
        if list_result["success"]:
            for section in list_result["sections"]:
                print(f"  {section['indent']} ({section['section_id']})")
        
    finally:
        # Clean up
        if test_path.exists():
            test_path.unlink()
        summary_path = Path("test_extraction.md.summary.json")
        if summary_path.exists():
            summary_path.unlink()
