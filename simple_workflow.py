#!/usr/bin/env python3
"""
Simple workflow runner - creates actual code from user prompts
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_orchestrator import EnhancedOrchestrator

async def simple_code_generation():
    """Simple code generation workflow"""
    print("🚀 Simple Code Generation Workflow")
    print("=" * 60)
    print("🔍 DEBUG MODE: ON")
    print("🤖 AI Provider: Gemini")
    print("📁 Workspace: ./workspace/")
    print("=" * 60)
    
    # Initialize the orchestrator
    print("\n⚙️  Initializing orchestrator...")
    orchestrator = EnhancedOrchestrator()
    print("✅ Orchestrator ready!")
    
    # Test requests
    requests = [
        "Create a Python function to calculate fibonacci numbers",
        "Create a simple HTML login form",
        "Create a JavaScript function to validate email",
        "Create a SQL query to find users by age",
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"\n🎯 Request {i}/4: {request}")
        print("⏳ Sending to AI...")
        print("-" * 50)
        
        try:
            # Call the LLM directly
            response = await orchestrator.execute_llm_call_with_cache(
                "Developer", 
                request, 
                {"workflow_id": f"simple-{i:03d}"}
            )
            
            print(f"✅ Generated {len(response)} characters")
            
            # Show a preview
            if len(response) > 200:
                print(f"Preview: {response[:200]}...")
            else:
                print(f"Result: {response}")
            
            # Try to run the generated code if it's Python
            if i == 1:  # First request is Python
                try:
                    print("\n🔥 Testing the generated Python code:")
                    result = await asyncio.create_subprocess_exec(
                        sys.executable, f"workspace/simple-{i:03d}/generated_code_1.py",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await result.communicate()
                    
                    if result.returncode == 0:
                        print(f"✅ Code executed successfully!")
                        print(f"Output: {stdout.decode().strip()}")
                    else:
                        print(f"❌ Code execution failed:")
                        print(f"Error: {stderr.decode().strip()}")
                        
                except Exception as e:
                    print(f"❌ Failed to execute code: {e}")
                
            # For HTML files, show that they're ready to open
            elif i == 2:  # HTML file
                html_file = Path(f"workspace/simple-{i:03d}/generated_code_1.html")
                if html_file.exists():
                    print(f"✅ HTML file created: {html_file}")
                    print("🌐 You can open this file in a browser!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    # Check what files were created
    print("\n📁 Generated Files:")
    print("-" * 30)
    workspace_dir = Path("workspace")
    if workspace_dir.exists():
        for file_path in sorted(workspace_dir.glob("simple-*/generated_code_*.py")):
            print(f"📄 {file_path}")
        for file_path in sorted(workspace_dir.glob("simple-*/generated_code_*.html")):
            print(f"📄 {file_path}")
        for file_path in sorted(workspace_dir.glob("simple-*/generated_code_*.js")):
            print(f"📄 {file_path}")
        for file_path in sorted(workspace_dir.glob("simple-*/generated_code_*.sql")):
            print(f"📄 {file_path}")
    
    print("\n🎯 Code generation completed!")

if __name__ == "__main__":
    asyncio.run(simple_code_generation())
