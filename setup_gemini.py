"""
Setup and Test Script for Gemini API Integration
This script helps set up and test the Gemini API integration
"""

import os
import asyncio
from pathlib import Path

def setup_gemini_api():
    """Setup Gemini API key"""
    print("🔧 Setting up Gemini API Integration")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Environment variables loaded from .env")
        except ImportError:
            print("⚠️  python-dotenv not installed, reading .env manually")
            # Read .env manually
            env_content = env_file.read_text()
            for line in env_content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    # Check if API key exists
    current_key = os.getenv('GEMINI_API_KEY')
    if current_key and current_key != "your_gemini_api_key_here":
        print(f"✅ Gemini API key found: {current_key[:10]}...")
        return current_key
    
    print("❌ No valid Gemini API key found")
    print("To use Gemini API, you need to:")
    print("1. Get your API key from: https://aistudio.google.com/app/apikey")
    print("2. Update the .env file with your API key")
    print("\nExample .env file:")
    print("GEMINI_API_KEY=AIzaSyDDT1MfDaWxT-kHPh0EPPS1FRBbRQCKnlE")
    
    # Ask user for API key
    api_key = input("\nEnter your Gemini API key (or press Enter to use mock responses): ").strip()
    
    if api_key:
        os.environ['GEMINI_API_KEY'] = api_key
        print(f"✅ API key set: {api_key[:10]}...")
        return api_key
    else:
        print("⚠️  No API key provided - will use mock responses")
        return None

async def test_gemini_integration():
    """Test Gemini API integration"""
    print("\n🧪 Testing Gemini Integration")
    print("=" * 50)
    
    try:
        from llm_interface import LLMInterface
        
        # Create interface
        interface = LLMInterface()
        print(f"Provider: {interface.provider}")
        
        if interface.provider == "gemini":
            print("✅ Gemini API detected")
        elif interface.provider == "mock":
            print("⚠️  Using mock responses (no API key)")
        else:
            print(f"ℹ️  Using {interface.provider} API")
        
        # Test with Product Analyst
        print("\n📋 Testing Product Analyst...")
        response = await interface.call_llm(
            "Product_Analyst",
            "Create a specification for a simple todo app with user authentication",
            {"workflow_id": "gemini-test-001"}
        )
        
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:200]}...")
        
        # Test with Coder
        print("\n💻 Testing Coder...")
        response = await interface.call_llm(
            "Coder",
            "Implement a simple todo item class in Python with CRUD operations",
            {"workflow_id": "gemini-test-002"}
        )
        
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:200]}...")
        
        # Test if code blocks are present
        if "```" in response:
            print("✅ Code blocks detected in response")
        else:
            print("⚠️  No code blocks detected")
        
        print("\n✅ Integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_full_workflow():
    """Test a complete workflow with file saving"""
    print("\n🔄 Testing Full Workflow")
    print("=" * 50)
    
    try:
        from enhanced_orchestrator import EnhancedOrchestrator
        
        orchestrator = EnhancedOrchestrator()
        
        # Test single agent with file saving
        print("Testing Coder agent with file saving...")
        response = await orchestrator.execute_llm_call_with_cache(
            "Coder",
            "Create a simple Python class for a Todo item with add, complete, and delete methods",
            {"workflow_id": "full-test-001"}
        )
        
        print(f"Response length: {len(response)} characters")
        
        # Check if files were created
        workspace_dir = Path("workspace") / "full-test-001"
        if workspace_dir.exists():
            files = list(workspace_dir.iterdir())
            print(f"✅ Files created: {[f.name for f in files]}")
            
            # Show content of first Python file
            py_files = [f for f in files if f.suffix == '.py']
            if py_files:
                print(f"\n📄 Content of {py_files[0].name}:")
                print("-" * 30)
                content = py_files[0].read_text()
                print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print("⚠️  No files created")
        
        print("\n✅ Full workflow test completed!")
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()

def run_tests():
    """Run all tests"""
    print("🔄 Running Test Suite")
    print("=" * 50)
    
    try:
        import pytest
        
        # Run our test file
        exit_code = pytest.main([
            "test_llm_integration.py", 
            "-v", 
            "--tb=short"
        ])
        
        if exit_code == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")
            
    except ImportError:
        print("⚠️  pytest not installed, skipping test suite")
    except Exception as e:
        print(f"❌ Test suite failed: {e}")

async def main():
    """Main setup and test function"""
    print("🚀 Gemini API Integration Setup & Test")
    print("=" * 60)
    
    # Setup API
    setup_gemini_api()
    
    # Test integration
    await test_gemini_integration()
    
    # Test full workflow
    await test_full_workflow()
    
    # Run test suite
    run_tests()
    
    print("\n🎉 Setup and testing completed!")
    print("\nNext steps:")
    print("1. If using Gemini API, make sure your API key is set")
    print("2. Run: python run_api_workflow.py")
    print("3. Check the workspace/ directory for generated files")

if __name__ == "__main__":
    asyncio.run(main())
