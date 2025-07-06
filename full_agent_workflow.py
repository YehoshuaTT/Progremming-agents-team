#!/usr/bin/env python3
"""
Full Multi-Agent Workflow Demo
Shows how tasks flow between agents: Product_Analyst → Developer → QA_Engineer
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_orchestrator import EnhancedOrchestrator

async def full_agent_workflow():
    """Demonstrate full multi-agent workflow"""
    print("🔄 Full Multi-Agent Workflow Demo")
    print("=" * 60)
    print("🎯 Request: 'Create a user registration system'")
    print("📋 Flow: Product_Analyst → Developer → QA_Engineer")
    print("=" * 60)
    
    # Initialize the orchestrator
    orchestrator = EnhancedOrchestrator()
    
    # Phase 1: Product Analysis
    print("\n🔍 PHASE 1: PRODUCT ANALYSIS")
    print("-" * 40)
    
    analyst_prompt = """
    Create a detailed product specification for a user registration system.
    Include:
    - User requirements
    - Technical requirements
    - UI/UX specifications
    - Data models
    - API endpoints needed
    
    Format your response as a comprehensive specification document.
    """
    
    try:
        print("⏳ Product Analyst working...")
        analyst_response = await orchestrator.execute_llm_call_with_cache(
            "Product_Analyst", 
            analyst_prompt, 
            {"workflow_id": "full-workflow-001", "phase": "analysis"}
        )
        
        print(f"✅ Product Analyst completed ({len(analyst_response)} characters)")
        print(f"📋 Specification preview: {analyst_response[:200]}...")
        
        # Phase 2: Development
        print("\n💻 PHASE 2: DEVELOPMENT")
        print("-" * 40)
        
        developer_prompt = f"""
        Based on the following product specification, create the implementation:

        SPECIFICATION:
        {analyst_response[:1000]}...

        Create:
        1. Backend API (Python/Flask or FastAPI)
        2. Frontend form (HTML/CSS/JavaScript)
        3. Database schema (SQL)
        4. Validation logic

        Provide complete, working code for each component.
        """
        
        print("⏳ Developer working...")
        developer_response = await orchestrator.execute_llm_call_with_cache(
            "Developer", 
            developer_prompt, 
            {"workflow_id": "full-workflow-002", "phase": "development", "previous_output": analyst_response}
        )
        
        print(f"✅ Developer completed ({len(developer_response)} characters)")
        print(f"💻 Code preview: {developer_response[:200]}...")
        
        # Phase 3: Quality Assurance
        print("\n🧪 PHASE 3: QUALITY ASSURANCE")
        print("-" * 40)
        
        qa_prompt = f"""
        Review the following implementation and create comprehensive tests:

        ORIGINAL REQUIREMENTS:
        {analyst_response[:500]}...

        IMPLEMENTATION:
        {developer_response[:1000]}...

        Create:
        1. Unit tests for backend API
        2. Integration tests
        3. Frontend validation tests
        4. Test data and scenarios
        5. Bug report if any issues found

        Provide complete test suite and testing strategy.
        """
        
        print("⏳ QA Engineer working...")
        qa_response = await orchestrator.execute_llm_call_with_cache(
            "QA_Engineer", 
            qa_prompt, 
            {"workflow_id": "full-workflow-003", "phase": "testing", "requirements": analyst_response, "implementation": developer_response}
        )
        
        print(f"✅ QA Engineer completed ({len(qa_response)} characters)")
        print(f"🧪 Tests preview: {qa_response[:200]}...")
        
    except Exception as e:
        print(f"❌ Error in workflow: {e}")
        return
    
    # Summary
    print("\n📊 WORKFLOW SUMMARY")
    print("=" * 40)
    print(f"✅ Product Analyst: {len(analyst_response)} characters")
    print(f"✅ Developer: {len(developer_response)} characters") 
    print(f"✅ QA Engineer: {len(qa_response)} characters")
    
    # Check generated files
    print("\n📁 Generated Artifacts:")
    print("-" * 30)
    workspace_dir = Path("workspace")
    if workspace_dir.exists():
        for workflow_dir in sorted(workspace_dir.glob("full-workflow-*")):
            print(f"📂 {workflow_dir.name}/")
            for file_path in sorted(workflow_dir.glob("*")):
                if file_path.is_file():
                    print(f"  📄 {file_path.name}")
    
    # Show potential next steps
    print("\n🔄 POTENTIAL NEXT STEPS:")
    print("-" * 30)
    print("🔄 If bugs found → back to Developer")
    print("🔄 If requirements unclear → back to Product_Analyst") 
    print("🔄 If tests pass → ready for deployment")
    print("🔄 If new requirements → start new cycle")
    
    print("\n🎯 Multi-agent workflow completed!")

async def interactive_workflow():
    """Interactive workflow where user can see handoffs"""
    print("\n" + "=" * 60)
    print("🎮 INTERACTIVE MODE")
    print("=" * 60)
    print("You can now see how agents would hand off to each other!")
    
    # Simulate handoff packets
    print("\n📦 HANDOFF PACKET EXAMPLE:")
    print("-" * 30)
    
    handoff_example = {
        "from_agent": "Product_Analyst",
        "to_agent": "Developer", 
        "status": "SUCCESS",
        "artifacts_produced": ["requirements.md", "user_stories.md"],
        "next_step_suggestion": "IMPLEMENTATION_NEEDED",
        "notes": "Requirements are complete. Ready for development phase.",
        "blocking_issues": [],
        "estimated_effort": "medium"
    }
    
    for key, value in handoff_example.items():
        print(f"  {key}: {value}")
    
    print("\n🔄 WORKFLOW DECISION POINTS:")
    print("-" * 30)
    print("✅ If SUCCESS → continue to next agent")
    print("⚠️  If BLOCKED → request clarification")
    print("❌ If FAILURE → retry or escalate")
    print("👤 If HUMAN_APPROVAL_NEEDED → pause for review")

if __name__ == "__main__":
    async def main():
        await full_agent_workflow()
        await interactive_workflow()
    
    asyncio.run(main())
