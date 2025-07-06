#!/usr/bin/env python3
"""
Enhanced Agent Decision System Configuration
==========================================

This module provides configuration for agent decision thresholds,
confidence levels, and workflow optimization settings.
"""

# Decision confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'VERY_HIGH': 0.9,
    'HIGH': 0.8,
    'MEDIUM': 0.6,
    'LOW': 0.4,
    'MINIMUM': 0.2
}

# Quality score thresholds for different actions
QUALITY_THRESHOLDS = {
    'COMPLETE': 0.85,
    'NEXT_AGENT': 0.60,
    'HUMAN_REVIEW': 0.30,
    'RETRY': 0.40
}

# Agent routing preferences based on project type
ROUTING_PREFERENCES = {
    'simple_script': {
        'skip_agents': ['Architect', 'DevOps_Specialist', 'Security_Specialist'],
        'essential_agents': ['Coder', 'QA_Guardian'],
        'max_iterations': 5
    },
    'web_application': {
        'skip_agents': [],
        'essential_agents': ['UX_UI_Designer', 'Coder', 'Security_Specialist', 'QA_Guardian'],
        'max_iterations': 12
    },
    'security_critical': {
        'skip_agents': [],
        'essential_agents': ['Security_Specialist', 'Code_Reviewer', 'QA_Guardian'],
        'max_iterations': 15
    },
    'enterprise_system': {
        'skip_agents': [],
        'essential_agents': ['Architect', 'Security_Specialist', 'DevOps_Specialist', 'QA_Guardian'],
        'max_iterations': 20
    }
}

# Context optimization settings
CONTEXT_OPTIMIZATION = {
    'max_context_length': 10000,  # Maximum characters in context
    'max_decisions_history': 3,    # Keep last N decisions
    'max_artifacts_history': 5,    # Keep last N artifacts
    'compress_responses': True,    # Compress long responses
    'max_response_length': 1000    # Maximum response length to keep
}

# Agent execution patterns
EXECUTION_PATTERNS = {
    'Product_Analyst': {
        'max_executions': 1,  # Usually only needed once
        'required_first': True,
        'skip_after_iteration': 3
    },
    'UX_UI_Designer': {
        'max_executions': 2,
        'required_first': False,
        'skip_after_iteration': 5
    },
    'Architect': {
        'max_executions': 2,
        'required_first': False,
        'skip_after_iteration': 6
    },
    'Coder': {
        'max_executions': 3,  # May need multiple coding iterations
        'required_first': False,
        'skip_after_iteration': None
    },
    'Code_Reviewer': {
        'max_executions': 2,
        'required_first': False,
        'skip_after_iteration': None
    },
    'Security_Specialist': {
        'max_executions': 1,
        'required_first': False,
        'skip_after_iteration': 8
    },
    'QA_Guardian': {
        'max_executions': 1,  # Final validation
        'required_first': False,
        'skip_after_iteration': None
    },
    'DevOps_Specialist': {
        'max_executions': 1,
        'required_first': False,
        'skip_after_iteration': 10
    },
    'Technical_Writer': {
        'max_executions': 1,
        'required_first': False,
        'skip_after_iteration': 12
    },
    'Debugger': {
        'max_executions': 2,
        'required_first': False,
        'skip_after_iteration': None
    },
    'Git_Agent': {
        'max_executions': 1,
        'required_first': False,
        'skip_after_iteration': 15
    },
    'Ask_Agent': {
        'max_executions': 1,
        'required_first': False,
        'skip_after_iteration': 2
    }
}

# Token usage optimization
TOKEN_OPTIMIZATION = {
    'max_prompt_tokens': 8000,
    'max_response_tokens': 4000,
    'context_compression_ratio': 0.7,
    'prioritize_recent_context': True
}
