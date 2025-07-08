#!/usr/bin/env python3
"""
Test suite for Gemini API integration
Tests actual API calls and functionality
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm_interface import LLMInterface

class TestGeminiAPIIntegration:
    """Test suite for Gemini API integration"""
    
    @pytest.fixture
    def llm_interface(self):
        """Create LLM interface for testing"""
        return LLMInterface()
    
    def test_environment_setup(self, llm_interface):
        """Test that environment variables are loaded correctly"""
        # If we have a real API key, test it; otherwise skip
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping environment setup test")
        
        # Should have loaded from .env file or environment
        assert llm_interface.gemini_api_key is not None
        assert llm_interface.gemini_api_key != "your_gemini_api_key_here"
        assert llm_interface.provider == "gemini"
    
    def test_api_key_validation(self, llm_interface):
        """Test API key validation"""
        # If we have a real API key, test it; otherwise skip
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping API key validation test")
        
        # Should have a valid-looking API key
        assert llm_interface.gemini_api_key.startswith("AIza")
        assert len(llm_interface.gemini_api_key) > 20
    
    @pytest.mark.asyncio
    async def test_simple_gemini_call(self, llm_interface):
        """Test basic Gemini API call"""
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping live API test")
        
        # Simple test prompt
        prompt = "Hello, please respond with just 'Hello back!'"
        
        try:
            response = await llm_interface.call_llm("test_agent", prompt)
            
            # Verify we got a response
            assert response is not None
            assert len(response) > 0
            assert isinstance(response, str)
            
            # Log the response for debugging
            print(f"Gemini response: {response}")
            
        except Exception as e:
            pytest.fail(f"Gemini API call failed: {e}")
    
    @pytest.mark.asyncio
    async def test_code_generation(self, llm_interface):
        """Test code generation with Gemini"""
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping live API test")
        
        prompt = """Create a simple Python function that adds two numbers.
        Please format your response as a code block."""
        
        try:
            response = await llm_interface.call_llm("Developer", prompt)
            
            # Verify we got a response
            assert response is not None
            assert len(response) > 0
            
            # Check if response contains code-like content
            assert "def " in response or "function" in response
            
            print(f"Code generation response: {response}")
            
        except Exception as e:
            pytest.fail(f"Code generation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_context_handling(self, llm_interface):
        """Test context handling in API calls"""
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping live API test")
        
        prompt = "Create a simple HTML page based on the context provided."
        context = {
            "user_request": "Create a login page",
            "requirements": ["username field", "password field", "login button"],
            "style": "modern and clean"
        }
        
        try:
            response = await llm_interface.call_llm("Frontend_Developer", prompt, context)
            
            # Verify we got a response
            assert response is not None
            assert len(response) > 0
            
            # Check if response contains HTML-like content
            assert "html" in response.lower() or "<" in response
            
            print(f"Context handling response: {response}")
            
        except Exception as e:
            pytest.fail(f"Context handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, llm_interface):
        """Test error handling with invalid requests"""
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping live API test")
        
        # Test with very long prompt (should handle gracefully)
        long_prompt = "Please respond to this: " + "x" * 50000
        
        try:
            response = await llm_interface.call_llm("test_agent", long_prompt)
            
            # Should either succeed or fail gracefully
            assert response is not None
            
        except Exception as e:
            # Should be a handled exception, not a crash
            assert "token" in str(e).lower() or "length" in str(e).lower()
            print(f"Expected error handled: {e}")
    
    @pytest.mark.asyncio
    async def test_multiple_agents(self, llm_interface):
        """Test calls with different agent types"""
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping live API test")
        
        agents_and_prompts = [
            ("Product_Analyst", "Analyze the requirements for a todo app"),
            ("Developer", "Create a Python function to add numbers"),
            ("QA_Engineer", "Write test cases for a login function")
        ]
        
        for agent, prompt in agents_and_prompts:
            try:
                response = await llm_interface.call_llm(agent, prompt)
                
                assert response is not None
                assert len(response) > 0
                
                print(f"{agent} response: {response[:100]}...")
                
            except Exception as e:
                pytest.fail(f"{agent} call failed: {e}")
    
    def test_fallback_mechanism(self):
        """Test fallback to mock when no API key"""
        # Create interface without API key in testing environment
        with patch.dict(os.environ, {'PYTEST_CURRENT_TEST': 'test'}, clear=False):
            with patch.dict(os.environ, {'GEMINI_API_KEY': '', 'OPENAI_API_KEY': ''}, clear=False):
                # In testing mode, should create a mock provider instead of raising error
                interface = LLMInterface()
                assert interface.provider == "mock"
    
    @pytest.mark.asyncio
    async def test_response_parsing(self, llm_interface):
        """Test that responses are properly parsed"""
        if llm_interface.provider == "mock":
            pytest.skip("No API key available, skipping live API test")
        
        prompt = "Please respond with a JSON object containing a greeting message."
        
        try:
            response = await llm_interface.call_llm("test_agent", prompt)
            
            # Should be a string response
            assert isinstance(response, str)
            assert len(response) > 0
            
            # Should contain some structured content
            assert "{" in response or "greeting" in response.lower()
            
            print(f"Response parsing test: {response}")
            
        except Exception as e:
            pytest.fail(f"Response parsing failed: {e}")

class TestGeminiAPIConfiguration:
    """Test configuration and setup"""
    
    def test_environment_variables(self):
        """Test that environment variables are configured correctly"""
        # In CI/testing environments, we may not have a .env file, and that's fine
        env_file = Path(".env")
        
        if env_file.exists():
            # Check that it contains Gemini key
            env_content = env_file.read_text()
            assert "GEMINI_API_KEY" in env_content
            # Note: We don't check for "AIza" as the value might be a placeholder
        else:
            # In CI environments, we expect no .env file and that's acceptable
            print("INFO: No .env file found - using environment variables or mock provider")
    
    def test_llm_interface_initialization(self):
        """Test LLM interface initializes correctly"""
        interface = LLMInterface()
        
        # Should have loaded configuration
        assert hasattr(interface, 'gemini_api_key')
        assert hasattr(interface, 'provider')
        assert hasattr(interface, 'max_tokens')
        assert hasattr(interface, 'temperature')
    
    def test_provider_selection(self):
        """Test provider selection logic"""
        interface = LLMInterface()
        
        # Should select Gemini if key is available, otherwise fall back
        assert interface.provider in ["gemini", "openai", "mock"]
        
        # If using mock provider, it means no API key was available
        if interface.provider == "mock":
            print("INFO: Using mock provider - no API key available")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])
