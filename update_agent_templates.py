#!/usr/bin/env python3
"""
Add Handoff Packet requirements to all agent templates
"""

import os
from pathlib import Path

# Agent configurations with their specific handoff requirements
AGENT_CONFIGS = {
    "Code_Reviewer": {
        "role": "Code quality review and best practices enforcement",
        "artifacts": ["code_review_report.md", "quality_assessment.md"],
        "next_steps": ["MERGE_APPROVED", "IMPLEMENTATION_NEEDED", "SECURITY_SCAN_NEEDED", "HUMAN_APPROVAL_NEEDED"]
    },
    "Coder": {
        "role": "Implementation and coding tasks",
        "artifacts": ["src/", "*.py", "*.js", "*.ts"],
        "next_steps": ["CODE_REVIEW", "TESTING_NEEDED", "DOCUMENTATION_NEEDED"]
    },
    "Tester": {
        "role": "Test creation and quality assurance",
        "artifacts": ["tests/", "test_*.py", "test_report.md"],
        "next_steps": ["IMPLEMENTATION_NEEDED", "CODE_REVIEW", "MERGE_APPROVED"]
    },
    "UX_UI_Designer": {
        "role": "User experience and interface design",
        "artifacts": ["design_plan.md", "ui_mockups.md", "user_flows.md"],
        "next_steps": ["IMPLEMENTATION_NEEDED", "HUMAN_APPROVAL_NEEDED", "CODE_REVIEW"]
    },
    "Security_Specialist": {
        "role": "Security analysis and vulnerability assessment",
        "artifacts": ["security_report.md", "vulnerability_scan.md"],
        "next_steps": ["MERGE_APPROVED", "IMPLEMENTATION_NEEDED", "HUMAN_APPROVAL_NEEDED"]
    },
    "QA_Guardian": {
        "role": "Quality gate enforcement and final validation",
        "artifacts": ["qa_validation_report.md", "quality_checklist.md"],
        "next_steps": ["MERGE_APPROVED", "DEPLOY_TO_STAGING", "HUMAN_APPROVAL_NEEDED"]
    },
    "DevOps_Specialist": {
        "role": "Deployment and infrastructure management",
        "artifacts": ["deployment_scripts/", "docker-compose.yml", "deployment_report.md"],
        "next_steps": ["DEPLOY_TO_PRODUCTION", "TESTING_NEEDED", "DOCUMENTATION_NEEDED"]
    },
    "Technical_Writer": {
        "role": "Documentation creation and maintenance",
        "artifacts": ["README.md", "API_docs.md", "user_guide.md"],
        "next_steps": ["CODE_REVIEW", "HUMAN_APPROVAL_NEEDED", "MERGE_APPROVED"]
    },
    "Debugger": {
        "role": "Issue diagnosis and troubleshooting",
        "artifacts": ["debug_report.md", "issue_analysis.md"],
        "next_steps": ["IMPLEMENTATION_NEEDED", "TESTING_NEEDED", "CODE_REVIEW"]
    },
    "Git_Agent": {
        "role": "Version control and branch management",
        "artifacts": ["git_operations.log", "merge_report.md"],
        "next_steps": ["CODE_REVIEW", "TESTING_NEEDED", "DEPLOY_TO_STAGING"]
    }
}

def add_handoff_packet_to_agent(agent_name, config):
    """Add handoff packet requirements to an agent's markdown file"""
    
    file_path = Path(f"documentation/Agents/{agent_name}.md")
    
    if not file_path.exists():
        print(f"Warning: {file_path} does not exist")
        return
    
    # Read existing content
    content = file_path.read_text()
    
    # Check if handoff packet already exists
    if "HANDOFF PACKET REQUIREMENTS" in content:
        print(f"Handoff packet already exists in {agent_name}.md")
        return
    
    # Create handoff packet section
    handoff_section = f"""

## HANDOFF PACKET REQUIREMENTS

**CRITICAL:** At the end of every task, you MUST produce a structured Handoff Packet in JSON format:

```json
{{
  "completed_task_id": "TASK-XXX or SUB-XXX.X",
  "agent_name": "{agent_name}",
  "status": "SUCCESS|FAILURE|PENDING|BLOCKED",
  "artifacts_produced": {config["artifacts"]},
  "next_step_suggestion": "{"|".join(config["next_steps"])}",
  "notes": "Detailed explanation of work completed and key findings",
  "timestamp": "2025-07-04T10:00:00Z",
  "dependencies_satisfied": ["DEP-001", "DEP-002"],
  "blocking_issues": ["Issue description if any"]
}}
```

### Next Step Suggestions for {agent_name}:
"""
    
    # Add specific next step explanations
    next_step_explanations = {
        "CODE_REVIEW": "Code has been written and needs review",
        "IMPLEMENTATION_NEEDED": "Specifications/tests are ready, need implementation",
        "TESTING_NEEDED": "Code is ready for testing",
        "MERGE_APPROVED": "Ready for merge after all checks pass",
        "DEPLOY_TO_STAGING": "Ready for staging deployment",
        "DEPLOY_TO_PRODUCTION": "Ready for production deployment",
        "HUMAN_APPROVAL_NEEDED": "Requires human decision or approval",
        "DOCUMENTATION_NEEDED": "Implementation complete, needs documentation",
        "SECURITY_SCAN_NEEDED": "Needs security review and vulnerability scan",
        "DEBUG_NEEDED": "Issues found, requires debugging"
    }
    
    for step in config["next_steps"]:
        explanation = next_step_explanations.get(step, "Standard workflow step")
        handoff_section += f"- **{step}**: {explanation}\n"
    
    handoff_section += """
### Handoff Process:
1. Complete your assigned task and create all required artifacts
2. Validate all deliverables against acceptance criteria
3. Provide the Handoff Packet as your final output
4. Include specific next-step recommendations based on project context

**The Handoff Packet enables intelligent workflow orchestration - without it, the system cannot route your work to the next appropriate agent.**
"""
    
    # Append to file
    updated_content = content + handoff_section
    file_path.write_text(updated_content)
    print(f"Added handoff packet to {agent_name}.md")

def main():
    """Main function to update all agent templates"""
    print("Adding Handoff Packet requirements to all agent templates...")
    
    for agent_name, config in AGENT_CONFIGS.items():
        add_handoff_packet_to_agent(agent_name, config)
    
    print("Handoff packet requirements added to all agent templates!")

if __name__ == "__main__":
    main()
