"""
Configuration file for pytest that sets up the Python path for testing.
"""

import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)

# Also add the key directories
sys.path.insert(0, os.path.join(parent_dir, 'core'))
sys.path.insert(0, os.path.join(parent_dir, 'tools'))
sys.path.insert(0, os.path.join(parent_dir, 'development'))
sys.path.insert(0, os.path.join(parent_dir, 'project_management'))
