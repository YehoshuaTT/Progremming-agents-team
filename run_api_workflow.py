#!/usr/bin/env python3
"""
Custom workflow runner for API creation task
This script runs the workflow in a single session so we can observe the complete process
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_orchestrator import EnhancedOrchestrator

async def run_api_creation_workflow():
    """Run the JWT authentication workflow and observe the complete process"""
    print("� Starting JWT Authentication Workflow")
    print("=" * 60)
    
    # Initialize the orchestrator
    orchestrator = EnhancedOrchestrator()
    
    # Start the workflow
    print("📝 Starting workflow: 'Create a JWT authentication system with login and registration'")
    workflow_id = await orchestrator.start_workflow("Create a JWT authentication system with login and registration")
    print(f"✅ Workflow started with ID: {workflow_id}")
    print()
    
    # Monitor the workflow progress
    print("👀 Monitoring workflow progress...")
    print("-" * 40)
    
    last_status = None
    max_iterations = 50  # Prevent infinite loop
    iteration = 0
    
    while iteration < max_iterations:
        try:
            # Get current status
            status = orchestrator.get_workflow_status(workflow_id)
            
            if status != last_status:
                print(f"🔄 Workflow Update #{iteration + 1}:")
                for key, value in status.items():
                    print(f"   {key.replace('_', ' ').title()}: {value}")
                print()
                last_status = status
            
            # Check if workflow is complete
            if status.get("status") in ["COMPLETED", "FAILED", "TERMINATED"]:
                print(f"🏁 Workflow finished with status: {status.get('status')}")
                break
                
            # Check for approvals needed
            approval_queue = orchestrator.human_approval_queue
            if approval_queue:
                print(f"⏳ {len(approval_queue)} approval(s) pending:")
                for approval in approval_queue:
                    print(f"   - {approval.get('description', 'Unknown approval')}")
                    print(f"     Risk Level: {approval.get('risk_level', 'Unknown')}")
                print()
            
            # Wait before next check
            await asyncio.sleep(3)
            iteration += 1
            
        except Exception as e:
            print(f"❌ Error checking workflow status: {e}")
            break
    
    # Final status report
    print("\n" + "=" * 60)
    print("📊 FINAL WORKFLOW REPORT")
    print("=" * 60)
    
    try:
        final_status = orchestrator.get_workflow_status(workflow_id)
        print("Final Status:")
        for key, value in final_status.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    except Exception as e:
        print(f"Could not get final status: {e}")
    
    # Show any artifacts created
    print("\n📁 Checking for created artifacts...")
    # List any files created in common output directories
    workspace_dirs = ["workspace", "output", "artifacts", "generated"]
    for dir_name in workspace_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            files = list(dir_path.glob("**/*"))
            if files:
                print(f"  📂 {dir_name}/:")
                for file_path in files[:10]:  # Show first 10 files
                    print(f"    - {file_path}")
                if len(files) > 10:
                    print(f"    ... and {len(files) - 10} more files")
    
    print("\n🎯 Workflow monitoring complete!")

if __name__ == "__main__":
    asyncio.run(run_api_creation_workflow())
