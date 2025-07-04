"""
Core module for the enhanced orchestrator system.
"""

# The enhanced orchestrator has been moved to the root directory
# Import from the root enhanced_orchestrator module
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from root
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_orchestrator import EnhancedOrchestrator

__all__ = ['EnhancedOrchestrator']
