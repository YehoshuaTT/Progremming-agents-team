#!/usr/bin/env python3
"""
Document Summary Generator for Multi-Layered Context System
Generates structured summaries of documents to optimize token usage
"""

import json
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import tiktoken

class DocumentSection:
    """Represents a section within a document"""
    
    def __init__(self, section_id: str, title: str, content: str, 
                 start_line: int, end_line: int, level: int = 1):
        self.section_id = section_id
        self.title = title
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.level = level
        self.subsections: List[DocumentSection] = []
        self.token_count = self._estimate_tokens()
        self.summary = self._generate_summary()
    
    def _estimate_tokens(self) -> int:
        """Estimate token count for this section"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(self.content))
        except:
            # Fallback estimation: ~4 characters per token
            return len(self.content) // 4
    
    def _generate_summary(self) -> str:
        """Generate a brief summary of the section content"""
        if not self.content.strip():
            return "Empty section"
        
        # Simple heuristic-based summary (much more concise)
        lines = self.content.strip().split('\n')
        
        # Remove empty lines and headers
        content_lines = [line for line in lines if line.strip() and not line.startswith('#')]
        
        if not content_lines:
            return "Header-only section"
        
        # Take first non-empty line as summary base
        first_line = content_lines[0].strip()
        
        # Keep summary very short
        if len(first_line) > 50:
            return first_line[:47] + "..."
        
        return first_line
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary for JSON serialization"""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "summary": self.summary,
            "token_count": self.token_count,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "level": self.level
        }

class DocumentSummaryGenerator:
    """Generates structured summaries of documents"""
    
    def __init__(self):
        self.supported_formats = {'.md', '.txt', '.py', '.js', '.html', '.css', '.json'}
    
    def generate_summary(self, document_path: str) -> Dict[str, Any]:
        """Generate a structured summary of a document"""
        path = Path(document_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported document format: {path.suffix}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate document-level summary
        sections = self._identify_sections(content)
        total_tokens = sum(section.token_count for section in sections)
        
        # Generate overall summary
        overall_summary = self._generate_overall_summary(content, sections)
        
        # Create summary structure (optimized for minimal tokens)
        summary = {
            "document_title": self._extract_title(content, path.name),
            "total_tokens": total_tokens,
            "sections": [section.to_dict() for section in sections],
            "total_sections": len(sections)
        }
        
        return summary
    
    def _identify_sections(self, content: str) -> List[DocumentSection]:
        """Identify sections within the document"""
        sections = []
        lines = content.split('\n')
        
        # Pattern for markdown headers
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        
        # Find all headers first
        headers = []
        for i, line in enumerate(lines):
            header_match = header_pattern.match(line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                headers.append({
                    'line': i,
                    'level': level,
                    'title': title
                })
        
        # Create sections based on headers
        section_counter = 1
        for i, header in enumerate(headers):
            section_id = f"SEC-{section_counter:03d}"
            start_line = header['line']
            
            # Find end line (start of next section at same or higher level)
            end_line = len(lines) - 1  # Default to end of document
            
            for j in range(i + 1, len(headers)):
                next_header = headers[j]
                # End section when we hit a header at same or higher level
                # (lower level number means higher hierarchy)
                if next_header['level'] <= header['level']:
                    end_line = next_header['line'] - 1
                    break
            
            # Create section with all content up to next same-level header
            section_content = '\n'.join(lines[start_line:end_line + 1])
            
            section = DocumentSection(
                section_id=section_id,
                title=header['title'],
                content=section_content,
                start_line=start_line,
                end_line=end_line,
                level=header['level']
            )
            
            sections.append(section)
            section_counter += 1
        
        # If no sections found, create one section for entire document
        if not sections:
            sections.append(DocumentSection(
                section_id="SEC-001",
                title="Document Content",
                content=content,
                start_line=0,
                end_line=len(lines) - 1,
                level=1
            ))
        
        return sections
    
    def _create_section(self, section_info: Dict, lines: List[str]) -> DocumentSection:
        """Create a DocumentSection object from section information"""
        start_line = section_info['start_line']
        end_line = section_info['end_line']
        content = '\n'.join(lines[start_line:end_line + 1])
        
        return DocumentSection(
            section_id=section_info['section_id'],
            title=section_info['title'],
            content=content,
            start_line=start_line,
            end_line=end_line,
            level=section_info['level']
        )
    
    def _extract_title(self, content: str, filename: str) -> str:
        """Extract document title from content or filename"""
        lines = content.split('\n')
        
        # Look for first level 1 header
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith('# '):
                return line[2:].strip()
        
        # Look for title in first few lines
        for line in lines[:5]:
            if line.strip() and not line.startswith('#'):
                # If line looks like a title (short, no periods)
                if len(line.strip()) < 100 and '.' not in line.strip():
                    return line.strip()
        
        # Fallback to filename
        return Path(filename).stem.replace('_', ' ').title()
    
    def _generate_overall_summary(self, content: str, sections: List[DocumentSection]) -> str:
        """Generate an overall summary of the document"""
        if not sections:
            return "Empty document"
        
        # Analyze document structure
        total_sections = len(sections)
        has_code = any('```' in section.content for section in sections)
        has_lists = any(re.search(r'^\s*[-*+]\s', section.content, re.MULTILINE) for section in sections)
        has_tables = any('|' in section.content for section in sections)
        
        # Build summary
        summary_parts = []
        
        # Document structure
        summary_parts.append(f"Document with {total_sections} main sections")
        
        # Content types
        content_types = []
        if has_code:
            content_types.append("code examples")
        if has_lists:
            content_types.append("structured lists")
        if has_tables:
            content_types.append("tables")
        
        if content_types:
            summary_parts.append(f"containing {', '.join(content_types)}")
        
        # Section titles overview
        if len(sections) <= 5:
            titles = [section.title for section in sections]
            summary_parts.append(f"covering: {', '.join(titles)}")
        
        return ". ".join(summary_parts) + "."
    
    def save_summary(self, document_path: str, summary: Dict[str, Any]) -> str:
        """Save summary to a .summary.json file"""
        path = Path(document_path)
        summary_path = path.with_suffix(path.suffix + '.summary.json')
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return str(summary_path)
    
    def load_summary(self, document_path: str) -> Optional[Dict[str, Any]]:
        """Load existing summary if available"""
        path = Path(document_path)
        summary_path = path.with_suffix(path.suffix + '.summary.json')
        
        if summary_path.exists():
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def is_summary_current(self, document_path: str) -> bool:
        """Check if existing summary is current (document not modified)"""
        path = Path(document_path)
        summary_path = path.with_suffix(path.suffix + '.summary.json')
        
        if not summary_path.exists():
            return False
        
        try:
            doc_mtime = path.stat().st_mtime
            summary_mtime = summary_path.stat().st_mtime
            return summary_mtime >= doc_mtime
        except:
            return False

# Example usage and testing
if __name__ == "__main__":
    generator = DocumentSummaryGenerator()
    
    # Test with a sample document
    test_doc = """# Sample Document

This is a sample document for testing.

## Section 1: Introduction

This section introduces the concepts.

### Subsection 1.1: Overview

Here's an overview of the topics.

## Section 2: Implementation

This section covers implementation details.

```python
def example_function():
    return "Hello, World!"
```

## Section 3: Conclusion

Final thoughts and conclusions.
"""
    
    # Save test document
    test_path = Path("test_document.md")
    with open(test_path, 'w') as f:
        f.write(test_doc)
    
    try:
        # Generate summary
        summary = generator.generate_summary(str(test_path))
        print("Generated Summary:")
        print(json.dumps(summary, indent=2))
        
        # Save summary
        summary_path = generator.save_summary(str(test_path), summary)
        print(f"\nSummary saved to: {summary_path}")
        
    finally:
        # Clean up
        if test_path.exists():
            test_path.unlink()
        summary_path = Path("test_document.md.summary.json")
        if summary_path.exists():
            summary_path.unlink()
