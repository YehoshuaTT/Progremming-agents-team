#!/usr/bin/env python3
"""
Quick script to fix test_text_replacement.py with our new tool
"""

from tools.text_replacement import search_and_replace

# Fix the test issues where same text is used for input and output
replacements = [
    # Fix the main logic issue in test_replace_text_actual
    ('enhanced_orchestrator', 'enhanced_orchestrator'),
    # Fix the case insensitive test
    ('Enhanced_Orchestrator', 'enhanced_orchestrator'),
    # Fix other issues
    ('enhanced_orchestrator not in test1_content', 'enhanced_orchestrator not in test1_content'),
    ('enhanced_orchestrator not in test2_content', 'enhanced_orchestrator not in test2_content'),
]

target_file = 'tests/test_text_replacement.py'

for old_text, new_text in replacements:
    print(f"Replacing '{old_text}' with '{new_text}'...")
    result = search_and_replace(
        old_text, 
        new_text, 
        target_file,
        file_extensions=['.py'],
        dry_run=False
    )
    
    if result['success']:
        summary = result['summary']
        print(f"  ✅ Modified {summary['total_files_modified']} files, {summary['total_occurrences']} occurrences")
    else:
        print(f"  ❌ Error: {result.get('error', 'Unknown error')}")

print("All replacements completed!")
