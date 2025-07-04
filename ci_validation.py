#!/usr/bin/env python3
"""
CI Validation Script for Autonomous Multi-Agent System

This script validates that all components can be imported and basic functionality works.
It's designed to be run in CI environments to catch import and dependency issues early.
"""

import sys
import importlib
from pathlib import Path

def test_import(module_name, description):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {description}: {module_name} - Unexpected error: {e}")
        return False

def validate_environment():
    """Validate the CI environment"""
    print("🔍 Validating CI Environment for Autonomous Multi-Agent System")
    print("=" * 60)
    
    # Check Python version
    print(f"Python Version: {sys.version}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {Path.cwd()}")
    print()
    
    # Test core dependencies
    dependencies = [
        ("pytest", "Testing Framework"),
        ("pytest_asyncio", "Async Testing Support"),
        ("networkx", "Graph Analysis"),
        ("sklearn", "Machine Learning"),
        ("numpy", "Numerical Computing"),
        ("pandas", "Data Analysis"),
        ("aiofiles", "Async File Operations"),
        ("aiosqlite", "Async SQLite"),
    ]
    
    failed_imports = []
    
    print("📦 Testing Core Dependencies:")
    for module, desc in dependencies:
        if not test_import(module, desc):
            failed_imports.append(module)
    
    print()
    
    # Test project modules
    project_modules = [
        ("tools.knowledge_graph", "Knowledge Graph System"),
        ("tools.experience_database", "Experience Database"),
        ("tools.pattern_recognition", "Pattern Recognition"),
        ("core.enhanced_orchestrator", "Enhanced Orchestrator"),
    ]
    
    print("🔧 Testing Project Modules:")
    for module, desc in project_modules:
        if not test_import(module, desc):
            failed_imports.append(module)
    
    print()
    
    # Check critical files
    critical_files = [
        "requirements.txt",
        "config/requirements.txt",
        "tools/knowledge_graph.py",
        "tools/experience_database.py",
        "core/enhanced_orchestrator.py",
        "tests/test_knowledge_graph.py",
        "tests/test_experience_database.py",
    ]
    
    print("📁 Checking Critical Files:")
    missing_files = []
    for file_path in critical_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            missing_files.append(file_path)
    
    print()
    print("📊 Validation Summary:")
    print(f"Failed Imports: {len(failed_imports)}")
    print(f"Missing Files: {len(missing_files)}")
    
    if failed_imports:
        print(f"❌ Failed imports: {', '.join(failed_imports)}")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
    
    # Return success status
    success = len(failed_imports) == 0 and len(missing_files) == 0
    
    if success:
        print("🎉 All validation checks passed!")
        return 0
    else:
        print("💥 Validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(validate_environment())
