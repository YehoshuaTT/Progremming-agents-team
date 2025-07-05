"""
Command-Line Interface for the Autonomous Multi-Agent Software Development System
"""
import argparse
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_orchestrator import EnhancedOrchestrator

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CLI for interacting with the Autonomous Multi-Agent System."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command to start a new workflow
    start_parser = subparsers.add_parser("start", help="Start a new development workflow.")
    start_parser.add_argument(
        "prompt", type=str, help="A natural language description of the task to be done."
    )

    # Command to check workflow status
    status_parser = subparsers.add_parser("status", help="Check the status of a workflow.")
    status_parser.add_argument(
        "workflow_id", type=str, help="The ID of the workflow to check."
    )
    status_parser.add_argument(
        "-f", "--follow", action="store_true", help="Follow the workflow progress in real-time."
    )

    # Command to list available agents
    subparsers.add_parser("list-agents", help="List all available specialized agents.")

    # Command to manage human approvals
    approval_parser = subparsers.add_parser("approve", help="Manage tasks awaiting human approval.")
    approval_parser.add_argument(
        "approval_id", type=str, help="The ID of the approval request."
    )
    approval_parser.add_argument(
        "--decision", type=str, choices=["approve", "reject"], default="approve",
        help="The decision for the approval request."
    )

    args = parser.parse_args()
    orchestrator = EnhancedOrchestrator()

    if args.command == "start":
        workflow_id = await orchestrator.start_workflow(args.prompt)
        print(f"Successfully started new workflow.")
        print(f"  - Prompt: '{args.prompt}'")
        print(f"  - Workflow ID: {workflow_id}")
        print(f"\nTo follow the progress, run: python cli.py status {workflow_id} --follow")

    elif args.command == "status":
        if args.follow:
            last_status_str = ""
            print(f"Following workflow '{args.workflow_id}'. Press Ctrl+C to stop.")
            try:
                while True:
                    status = await orchestrator.get_workflow_status(args.workflow_id)
                    if not status:
                        print(f"Workflow with ID '{args.workflow_id}' not found.")
                        break
                    
                    current_status_str = json.dumps(status, sort_keys=True)
                    if current_status_str != last_status_str:
                        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Workflow status updated:")
                        for key, value in status.items():
                            print(f"  - {key.replace('_', ' ').title()}: {value}")
                        last_status_str = current_status_str

                    if status.get("status") in ["COMPLETED", "FAILED", "TERMINATED"]:
                        print("\nWorkflow has finished.")
                        break
                    
                    await asyncio.sleep(5)
            except KeyboardInterrupt:
                print("\nStopped following workflow.")
        else:
            status = await orchestrator.get_workflow_status(args.workflow_id)
            if status:
                print(f"Status for workflow '{args.workflow_id}':")
                for key, value in status.items():
                    print(f"  - {key.replace('_', ' ').title()}: {value}")
            else:
                print(f"Workflow with ID '{args.workflow_id}' not found.")

    elif args.command == "list-agents":
        agents = orchestrator.agent_factory.list_available_agents()
        print("Available Agents:")
        # The list_available_agents() method returns a list of agent names.
        if isinstance(agents, list):
            # To get details, we would need to call another method,
            # but for now, we'll just list the names as the method implies.
            for agent_name in agents:
                print(f"  - {agent_name}")
        elif isinstance(agents, dict):
             for agent_name, agent_details in agents.items():
                print(f"  - {agent_name}: {agent_details.get('description', 'No description available')}")
        else:
            print("Could not retrieve agent list in the expected format.")

    elif args.command == "approve":
        success = await orchestrator.process_human_approval(args.approval_id, args.decision)
        if success:
            print(f"Successfully processed approval '{args.approval_id}' with decision '{args.decision}'.")
        else:
            print(f"Could not process approval '{args.approval_id}'. Please check the ID.")

if __name__ == "__main__":
    asyncio.run(main())
