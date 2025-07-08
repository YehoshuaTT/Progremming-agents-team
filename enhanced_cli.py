"""
Enhanced Command-Line Interface for the Intelligent Multi-Agent System
Integrates with the new workflow system and intelligent orchestration capabilities
"""

import argparse
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from tools.workflow_integration import IntegratedWorkflowSystem
from tools.intelligent_orchestrator import WorkflowPhase, AgentRole
from tools.certainty_framework import DecisionType, create_decision

class EnhancedCLI:
    """Enhanced CLI with intelligent workflow capabilities"""
    
    def __init__(self):
        self.workflow_system = IntegratedWorkflowSystem()
        self.config_file = Path("cli_config.json")
        self.load_config()
    
    def load_config(self):
        """Load CLI configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'default_workspace': 'workspace',
                'auto_approve_high_certainty': True,
                'verbose': False,
                'output_format': 'json'
            }
            self.save_config()
    
    def save_config(self):
        """Save CLI configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    async def start_workflow(self, args) -> Dict[str, Any]:
        """Start a new intelligent workflow"""
        try:
            print(f"🚀 Starting new workflow: {args.prompt}")
            
            # Start workflow
            context = await self.workflow_system.start_workflow(
                user_prompt=args.prompt,
                workflow_id=args.workflow_id if hasattr(args, 'workflow_id') else None
            )
            
            if args.interactive:
                await self._run_interactive_workflow(context)
            else:
                await self._run_automated_workflow(context)
            
            return {
                'status': 'success',
                'workflow_id': context.workflow_id,
                'message': f"Workflow started successfully"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': f"Failed to start workflow: {e}"
            }
    
    async def _run_interactive_workflow(self, context):
        """Run workflow with user interaction"""
        print(f"\\n📋 Interactive workflow: {context.workflow_id}")
        print(f"📝 Description: {context.user_prompt}")
        
        # Define workflow phases
        phases = [
            WorkflowPhase.PLANNING,
            WorkflowPhase.REQUIREMENTS,
            WorkflowPhase.ARCHITECTURE,
            WorkflowPhase.DESIGN,
            WorkflowPhase.IMPLEMENTATION,
            WorkflowPhase.REVIEW,
            WorkflowPhase.TESTING,
            WorkflowPhase.DEPLOYMENT,
            WorkflowPhase.DOCUMENTATION
        ]
        
        for phase in phases:
            print(f"\\n🔄 Starting {phase.value.upper()} phase...")
            
            # Ask for user confirmation
            if not await self._get_user_confirmation(f"Proceed with {phase.value} phase?"):
                print(f"⏸️  Workflow paused at {phase.value} phase")
                break
            
            # Execute phase
            result = await self.workflow_system.execute_workflow_phase(
                context.workflow_id, phase
            )
            
            # Display results
            print(f"✅ {phase.value.upper()} phase completed")
            if self.config['verbose']:
                print(f"   📊 Result: {json.dumps(result, indent=2)}")
            
            # Check for approvals needed
            if result.get('requires_approval', False):
                approved = await self._handle_approval_request(result)
                if not approved:
                    print(f"❌ Workflow stopped due to approval rejection")
                    break
        
        # Complete workflow
        final_report = await self.workflow_system.complete_workflow(context.workflow_id)
        print(f"\\n🎉 Workflow completed successfully!")
        print(f"📊 Final report: {json.dumps(final_report, indent=2)}")
    
    async def _run_automated_workflow(self, context):
        """Run workflow automatically with minimal user interaction"""
        print(f"\\n🤖 Automated workflow: {context.workflow_id}")
        
        # Execute all phases automatically
        phases = [
            WorkflowPhase.PLANNING,
            WorkflowPhase.REQUIREMENTS,
            WorkflowPhase.ARCHITECTURE,
            WorkflowPhase.IMPLEMENTATION,
            WorkflowPhase.TESTING
        ]
        
        for phase in phases:
            print(f"🔄 Executing {phase.value}...")
            result = await self.workflow_system.execute_workflow_phase(
                context.workflow_id, phase
            )
            print(f"✅ {phase.value} completed")
        
        # Complete workflow
        final_report = await self.workflow_system.complete_workflow(context.workflow_id)
        print(f"🎉 Workflow completed! Files created: {final_report.get('files_created', 0)}")
    
    async def _get_user_confirmation(self, message: str) -> bool:
        """Get user confirmation"""
        while True:
            response = input(f"{message} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    async def _handle_approval_request(self, result: Dict[str, Any]) -> bool:
        """Handle approval request from workflow"""
        print(f"\\n🔍 Approval Required:")
        print(f"📋 Decision: {result.get('decision', 'Unknown')}")
        print(f"🎯 Reasoning: {result.get('reasoning', 'No reasoning provided')}")
        print(f"📊 Certainty: {result.get('certainty', 0)}%")
        
        return await self._get_user_confirmation("Approve this decision?")
    
    async def check_workflow_status(self, args) -> Dict[str, Any]:
        """Check the status of a workflow"""
        try:
            status = await self.workflow_system.get_workflow_status(args.workflow_id)
            
            if args.follow:
                await self._follow_workflow(args.workflow_id)
            else:
                print(f"📊 Workflow Status: {args.workflow_id}")
                print(json.dumps(status, indent=2))
            
            return {
                'status': 'success',
                'workflow_status': status
            }
            
        except ValueError as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': f"Workflow {args.workflow_id} not found"
            }
    
    async def _follow_workflow(self, workflow_id: str):
        """Follow workflow progress in real-time"""
        print(f"📺 Following workflow: {workflow_id}")
        print("Press Ctrl+C to stop following")
        
        try:
            while True:
                status = await self.workflow_system.get_workflow_status(workflow_id)
                print(f"\\r🔄 Phase: {status.get('current_phase', 'unknown')} | "
                      f"Decisions: {status.get('decisions_made', 0)} | "
                      f"Pending: {status.get('pending_approvals', 0)}", end="")
                
                await asyncio.sleep(2)
                
        except KeyboardInterrupt:
            print("\\n📺 Stopped following workflow")
    
    async def list_agents(self, args) -> Dict[str, Any]:
        """List all available agents"""
        agents = []
        
        for agent_name, agent_info in self.workflow_system.orchestrator.agent_registry.agents.items():
            agents.append({
                'name': agent_name,
                'role': agent_info.role.value,
                'specialties': agent_info.specialties,
                'available': agent_info.is_available,
                'workload': agent_info.workload,
                'max_workload': agent_info.max_workload
            })
        
        print(f"👥 Available Agents ({len(agents)}):")
        for agent in agents:
            status = "🟢" if agent['available'] else "🔴"
            print(f"  {status} {agent['name']} ({agent['role']})")
            if args.verbose:
                print(f"      Specialties: {', '.join(agent['specialties'])}")
                print(f"      Workload: {agent['workload']}/{agent['max_workload']}")
        
        return {
            'status': 'success',
            'agents': agents
        }
    
    async def list_workflows(self, args) -> Dict[str, Any]:
        """List all active workflows"""
        workflows = await self.workflow_system.get_active_workflows()
        
        print(f"📋 Active Workflows ({len(workflows)}):")
        for workflow in workflows:
            print(f"  🔄 {workflow['workflow_id']}")
            print(f"      Phase: {workflow['current_phase']}")
            print(f"      Prompt: {workflow['user_prompt'][:50]}...")
            print(f"      Decisions: {workflow['decisions_made']}")
            print(f"      Pending: {workflow['pending_approvals']}")
        
        return {
            'status': 'success',
            'workflows': workflows
        }
    
    async def handle_approval(self, args) -> Dict[str, Any]:
        """Handle approval requests"""
        try:
            decision = args.decision == 'approve'
            
            result = await self.workflow_system.process_user_approval(
                args.workflow_id,
                args.approval_id,
                decision
            )
            
            print(f"✅ Approval processed: {args.approval_id}")
            print(f"📋 Decision: {'Approved' if decision else 'Rejected'}")
            
            return {
                'status': 'success',
                'approval_result': result
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': f"Failed to process approval: {e}"
            }
    
    async def export_workflow(self, args) -> Dict[str, Any]:
        """Export workflow data"""
        try:
            output_file = args.output or f"{args.workflow_id}_export.json"
            
            await self.workflow_system.export_workflow_data(
                args.workflow_id,
                output_file
            )
            
            print(f"📤 Workflow exported to: {output_file}")
            
            return {
                'status': 'success',
                'exported_file': output_file
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': f"Failed to export workflow: {e}"
            }
    
    async def configure_system(self, args) -> Dict[str, Any]:
        """Configure system settings"""
        if args.set:
            key, value = args.set.split('=', 1)
            
            # Convert string values to appropriate types
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            
            self.config[key] = value
            self.save_config()
            
            print(f"⚙️  Configuration updated: {key} = {value}")
            
        elif args.get:
            if args.get in self.config:
                print(f"⚙️  {args.get} = {self.config[args.get]}")
            else:
                print(f"❌ Configuration key not found: {args.get}")
                
        else:
            print("⚙️  Current Configuration:")
            for key, value in self.config.items():
                print(f"  {key} = {value}")
        
        return {
            'status': 'success',
            'config': self.config
        }

def create_parser():
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        description="Enhanced CLI for the Intelligent Multi-Agent Software Development System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")
    
    # Start workflow command
    start_parser = subparsers.add_parser(
        "start", 
        help="Start a new intelligent workflow"
    )
    start_parser.add_argument(
        "prompt", 
        type=str, 
        help="Natural language description of the task"
    )
    start_parser.add_argument(
        "--workflow-id", 
        type=str, 
        help="Custom workflow ID"
    )
    start_parser.add_argument(
        "--interactive", 
        action="store_true", 
        help="Run in interactive mode with user confirmations"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status", 
        help="Check workflow status"
    )
    status_parser.add_argument(
        "workflow_id", 
        type=str, 
        help="Workflow ID to check"
    )
    status_parser.add_argument(
        "--follow", 
        action="store_true", 
        help="Follow workflow progress in real-time"
    )
    
    # List agents command
    agents_parser = subparsers.add_parser(
        "agents", 
        help="List all available agents"
    )
    agents_parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Show detailed agent information"
    )
    
    # List workflows command
    workflows_parser = subparsers.add_parser(
        "workflows", 
        help="List all active workflows"
    )
    
    # Approval command
    approval_parser = subparsers.add_parser(
        "approve", 
        help="Handle approval requests"
    )
    approval_parser.add_argument(
        "workflow_id", 
        type=str, 
        help="Workflow ID"
    )
    approval_parser.add_argument(
        "approval_id", 
        type=str, 
        help="Approval request ID"
    )
    approval_parser.add_argument(
        "--decision", 
        type=str, 
        choices=["approve", "reject"], 
        default="approve",
        help="Approval decision"
    )
    
    # Export command
    export_parser = subparsers.add_parser(
        "export", 
        help="Export workflow data"
    )
    export_parser.add_argument(
        "workflow_id", 
        type=str, 
        help="Workflow ID to export"
    )
    export_parser.add_argument(
        "--output", 
        type=str, 
        help="Output file path"
    )
    
    # Configuration command
    config_parser = subparsers.add_parser(
        "config", 
        help="Configure system settings"
    )
    config_parser.add_argument(
        "--set", 
        type=str, 
        help="Set configuration value (key=value)"
    )
    config_parser.add_argument(
        "--get", 
        type=str, 
        help="Get configuration value"
    )
    
    return parser

async def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    cli = EnhancedCLI()
    
    # Command routing
    command_handlers = {
        'start': cli.start_workflow,
        'status': cli.check_workflow_status,
        'agents': cli.list_agents,
        'workflows': cli.list_workflows,
        'approve': cli.handle_approval,
        'export': cli.export_workflow,
        'config': cli.configure_system
    }
    
    if args.command in command_handlers:
        try:
            result = await command_handlers[args.command](args)
            
            if result['status'] == 'error':
                print(f"❌ Error: {result['message']}")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\\n⏹️  Operation cancelled by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
