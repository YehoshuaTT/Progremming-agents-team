#!/usr/bin/env python3
"""
Text Replacement Tool

This tool provides functionality to search and replace text across multiple files
with support for different file types, regex patterns, and backup creation.
"""

import os
import re
import shutil
import logging
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import json
from tools.security_framework import security_manager, SecurityLevel, SecurityAction
from tools.tool_cache import cache_tool_output

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ReplacementResult:
    """Result of a text replacement operation"""
    file_path: str
    old_text: str
    new_text: str
    occurrences: int
    success: bool
    error_message: Optional[str] = None
    backup_path: Optional[str] = None

@dataclass
class ReplacementSummary:
    """Summary of all replacement operations"""
    total_files_processed: int
    total_files_modified: int
    total_occurrences: int
    successful_replacements: int
    failed_replacements: int
    results: List[ReplacementResult]
    backup_directory: Optional[str] = None

class TextReplacementTool:
    """Advanced text replacement tool with safety features"""
    
    def __init__(self, backup_enabled: bool = True):
        """Initialize the text replacement tool"""
        self.backup_enabled = backup_enabled
        self.backup_base_dir = Path("backups/text_replacements")
        self.supported_extensions = {
            '.py', '.txt', '.md', '.yml', '.yaml', '.json', 
            '.js', '.ts', '.html', '.css', '.xml', '.cfg', '.ini'
        }
        self.exclude_patterns = {
            '*.pyc', '*.pyo', '*.pyd', '__pycache__',
            '.git', '.venv', 'node_modules', '.pytest_cache',
            '*.egg-info', 'dist', 'build'
        }
        
    def _create_backup_directory(self) -> Path:
        """Create a backup directory with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base_dir / f"replacement_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Check if a file should be processed based on extension and patterns"""
        # Check if file has supported extension
        if file_path.suffix.lower() not in self.supported_extensions:
            return False
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in str(file_path):
                return False
        
        # Simple security check - avoid system files and sensitive directories
        path_str = str(file_path).lower()
        dangerous_paths = ['/etc/', '/sys/', '/proc/', 'c:\\windows\\', 'c:\\system']
        for dangerous in dangerous_paths:
            if dangerous in path_str:
                return False
        
        return True
    
    def _create_backup(self, file_path: Path, backup_dir: Path) -> Optional[Path]:
        """Create backup of a file before modification"""
        if not self.backup_enabled:
            return None
        
        try:
            # Create relative path structure in backup directory
            relative_path = file_path.relative_to(Path.cwd())
            backup_path = backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to backup location
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _search_in_file(self, file_path: Path, search_text: str, 
                       use_regex: bool = False, case_sensitive: bool = True) -> List[Tuple[int, str]]:
        """Search for text in a file and return matches with line numbers"""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if use_regex:
                        flags = 0 if case_sensitive else re.IGNORECASE
                        if re.search(search_text, line, flags):
                            matches.append((line_num, line.strip()))
                    else:
                        search_in_line = search_text if case_sensitive else search_text.lower()
                        line_to_search = line if case_sensitive else line.lower()
                        if search_in_line in line_to_search:
                            matches.append((line_num, line.strip()))
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
        
        return matches
    
    def _replace_in_file(self, file_path: Path, old_text: str, new_text: str,
                        use_regex: bool = False, case_sensitive: bool = True,
                        backup_dir: Optional[Path] = None) -> ReplacementResult:
        """Replace text in a single file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Count occurrences before replacement
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                matches = re.findall(old_text, content, flags)
                occurrences = len(matches)
            else:
                search_text = old_text if case_sensitive else old_text.lower()
                content_to_search = content if case_sensitive else content.lower()
                occurrences = content_to_search.count(search_text)
            
            if occurrences == 0:
                return ReplacementResult(
                    file_path=str(file_path),
                    old_text=old_text,
                    new_text=new_text,
                    occurrences=0,
                    success=True
                )
            
            # Create backup if enabled
            backup_path = None
            if backup_dir:
                backup_path = self._create_backup(file_path, backup_dir)
            
            # Perform replacement
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                new_content = re.sub(old_text, new_text, content, flags=flags)
            else:
                if case_sensitive:
                    new_content = content.replace(old_text, new_text)
                else:
                    # Case-insensitive replacement
                    def replace_func(match):
                        return new_text
                    pattern = re.escape(old_text)
                    new_content = re.sub(pattern, replace_func, content, flags=re.IGNORECASE)
            
            # Write modified content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"Replaced {occurrences} occurrences in {file_path}")
            
            return ReplacementResult(
                file_path=str(file_path),
                old_text=old_text,
                new_text=new_text,
                occurrences=occurrences,
                success=True,
                backup_path=str(backup_path) if backup_path else None
            )
            
        except Exception as e:
            logger.error(f"Error replacing text in {file_path}: {e}")
            return ReplacementResult(
                file_path=str(file_path),
                old_text=old_text,
                new_text=new_text,
                occurrences=0,
                success=False,
                error_message=str(e)
            )
    
    def search_text(self, search_text: str, directory: str = ".", 
                   use_regex: bool = False, case_sensitive: bool = True,
                   file_extensions: Optional[List[str]] = None) -> Dict:
        """Search for text across multiple files"""
        search_results = {}
        total_matches = 0
        
        search_dir = Path(directory)
        if not search_dir.exists():
            return {"error": f"Directory {directory} does not exist"}
        
        # Update supported extensions if provided
        if file_extensions:
            extensions_to_search = set(ext.lower() for ext in file_extensions)
        else:
            extensions_to_search = self.supported_extensions
        
        # Walk through directory
        for root, dirs, files in os.walk(search_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.exclude_patterns)]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file should be processed
                if file_path.suffix.lower() not in extensions_to_search:
                    continue
                
                if not self._should_process_file(file_path):
                    continue
                
                # Search in file
                matches = self._search_in_file(file_path, search_text, use_regex, case_sensitive)
                if matches:
                    search_results[str(file_path)] = matches
                    total_matches += len(matches)
        
        return {
            "search_text": search_text,
            "total_files_found": len(search_results),
            "total_matches": total_matches,
            "results": search_results,
            "search_parameters": {
                "use_regex": use_regex,
                "case_sensitive": case_sensitive,
                "directory": directory,
                "file_extensions": list(extensions_to_search)
            }
        }
    
    def replace_text(self, old_text: str, new_text: str, directory: str = ".",
                    use_regex: bool = False, case_sensitive: bool = True,
                    file_extensions: Optional[List[str]] = None,
                    dry_run: bool = False) -> ReplacementSummary:
        """Replace text across multiple files"""
        results = []
        backup_dir = None
        
        if not dry_run and self.backup_enabled:
            backup_dir = self._create_backup_directory()
        
        search_dir = Path(directory)
        if not search_dir.exists():
            return ReplacementSummary(
                total_files_processed=0,
                total_files_modified=0,
                total_occurrences=0,
                successful_replacements=0,
                failed_replacements=1,
                results=[ReplacementResult(
                    file_path=directory,
                    old_text=old_text,
                    new_text=new_text,
                    occurrences=0,
                    success=False,
                    error_message=f"Directory {directory} does not exist"
                )]
            )
        
        # Update supported extensions if provided
        if file_extensions:
            extensions_to_search = set(ext.lower() for ext in file_extensions)
        else:
            extensions_to_search = self.supported_extensions
        
        # Walk through directory
        for root, dirs, files in os.walk(search_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.exclude_patterns)]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file should be processed
                if file_path.suffix.lower() not in extensions_to_search:
                    continue
                
                if not self._should_process_file(file_path):
                    continue
                
                # Perform replacement (or dry run)
                if dry_run:
                    # Just search for occurrences
                    matches = self._search_in_file(file_path, old_text, use_regex, case_sensitive)
                    occurrences = len(matches)
                    result = ReplacementResult(
                        file_path=str(file_path),
                        old_text=old_text,
                        new_text=new_text,
                        occurrences=occurrences,
                        success=True
                    )
                else:
                    # Actual replacement
                    result = self._replace_in_file(file_path, old_text, new_text, 
                                                 use_regex, case_sensitive, backup_dir)
                
                results.append(result)
        
        # Calculate summary
        total_files_processed = len(results)
        total_files_modified = sum(1 for r in results if r.success and r.occurrences > 0)
        total_occurrences = sum(r.occurrences for r in results)
        successful_replacements = sum(1 for r in results if r.success)
        failed_replacements = sum(1 for r in results if not r.success)
        
        return ReplacementSummary(
            total_files_processed=total_files_processed,
            total_files_modified=total_files_modified,
            total_occurrences=total_occurrences,
            successful_replacements=successful_replacements,
            failed_replacements=failed_replacements,
            results=results,
            backup_directory=str(backup_dir) if backup_dir else None
        )
    
    def restore_from_backup(self, backup_directory: str) -> Dict:
        """Restore files from backup directory"""
        backup_dir = Path(backup_directory)
        if not backup_dir.exists():
            return {"error": f"Backup directory {backup_directory} does not exist"}
        
        restored_files = []
        failed_files = []
        
        # Walk through backup directory
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                backup_file = Path(root) / file
                
                # Calculate original file path
                relative_path = backup_file.relative_to(backup_dir)
                original_file = Path.cwd() / relative_path
                
                try:
                    # Ensure target directory exists
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy backup file to original location
                    shutil.copy2(backup_file, original_file)
                    restored_files.append(str(original_file))
                    
                except Exception as e:
                    failed_files.append({
                        "file": str(original_file),
                        "error": str(e)
                    })
        
        return {
            "restored_files": len(restored_files),
            "failed_files": len(failed_files),
            "restored_file_list": restored_files,
            "failed_file_list": failed_files
        }

# Global instance
text_replacement_tool = TextReplacementTool()

# Convenience functions for tool pool
def search_and_replace(old_text: str, new_text: str, directory: str = ".",
                      use_regex: bool = False, case_sensitive: bool = True,
                      file_extensions: Optional[List[str]] = None,
                      dry_run: bool = False) -> Dict:
    """Search and replace text across multiple files"""
    try:
        # Perform replacement
        summary = text_replacement_tool.replace_text(
            old_text, new_text, directory, use_regex, case_sensitive,
            file_extensions, dry_run
        )
        
        return {
            "summary": asdict(summary),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in search_and_replace: {e}")
        return {"error": str(e), "success": False}

def search_text_in_files(search_text: str, directory: str = ".",
                        use_regex: bool = False, case_sensitive: bool = True,
                        file_extensions: Optional[List[str]] = None) -> Dict:
    """Search for text across multiple files"""
    try:
        # Perform search
        results = text_replacement_tool.search_text(
            search_text, directory, use_regex, case_sensitive, file_extensions
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in search_text_in_files: {e}")
        return {"error": str(e)}

def quick_replace(old_text: str, new_text: str) -> Dict:
    """Quick replacement in current directory Python files"""
    return search_and_replace(
        old_text, new_text, 
        directory=".",
        file_extensions=['.py'],
        case_sensitive=True
    )

if __name__ == "__main__":
    # Example usage
    tool = TextReplacementTool()
    
    # Search for text
    search_results = tool.search_text("enhanced_orchestrator", ".", file_extensions=['.py'])
    print("Search Results:")
    print(json.dumps(search_results, indent=2))
    
    # Replace text (dry run first)
    replacement_summary = tool.replace_text(
        "enhanced_orchestrator", 
        "enhanced_orchestrator", 
        ".", 
        file_extensions=['.py'],
        dry_run=True
    )
    print("\nDry Run Results:")
    print(f"Files that would be modified: {replacement_summary.total_files_modified}")
    print(f"Total occurrences: {replacement_summary.total_occurrences}")
