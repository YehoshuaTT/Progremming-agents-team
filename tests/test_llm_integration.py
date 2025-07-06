"""
Test suite for the Enhanced Orchestrator LLM Integration
Tests all the new functionality we added for real LLM integration
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

# Import the modules we want to test
from enhanced_orchestrator import EnhancedOrchestrator
from llm_interface import LLMInterface, llm_interface


class TestLLMInterface:
    """Test the LLM interface functionality"""
    
    def test_llm_interface_initialization_with_gemini(self):
        """Test LLM interface initialization with Gemini API key"""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            interface = LLMInterface()
            assert interface.provider == "gemini"
            assert interface.gemini_api_key == "test_key"
    
    def test_llm_interface_initialization_with_openai(self):
        """Test LLM interface initialization with OpenAI API key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}, clear=True):
            interface = LLMInterface()
            assert interface.provider == "openai"
            assert interface.openai_api_key == "test_key"
    
    def test_llm_interface_initialization_no_keys(self):
        """Test LLM interface initialization without API keys"""
        with patch.dict(os.environ, {}, clear=True):
            interface = LLMInterface()
            assert interface.provider == "mock"
    
    def test_system_prompts_exist_for_all_agents(self):
        """Test that system prompts exist for all agent types"""
        interface = LLMInterface()
        
        agents = [
            "Product_Analyst", "Architect", "Coder", "Code_Reviewer",
            "QA_Guardian", "DevOps_Specialist", "Security_Specialist", "Technical_Writer"
        ]
        
        for agent in agents:
            prompt = interface._get_system_prompt(agent)
            assert prompt is not None
            assert len(prompt) > 50  # Should be a substantial prompt
            assert "JSON format" in prompt  # Should mention handoff packet
    
    @pytest.mark.asyncio
    async def test_mock_llm_response_product_analyst(self):
        """Test mock response for Product Analyst"""
        interface = LLMInterface()
        
        response = await interface._mock_llm_response(
            "Product_Analyst",
            "Create a JWT authentication system",
            {"workflow_id": "test-001"}
        )
        
        assert "Product Specification" in response
        assert "JWT" in response
        assert "HANDOFF_PACKET" in response
        assert "Product_Analyst" in response
    
    @pytest.mark.asyncio
    async def test_mock_llm_response_coder(self):
        """Test mock response for Coder"""
        interface = LLMInterface()
        
        response = await interface._mock_llm_response(
            "Coder",
            "Implement JWT authentication",
            {"workflow_id": "test-002"}
        )
        
        assert "Implementation Complete" in response
        assert "```javascript" in response or "```" in response
        assert "HANDOFF_PACKET" in response
        assert "Coder" in response


class TestEnhancedOrchestratorLLMIntegration:
    """Test the Enhanced Orchestrator LLM integration"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator instance for testing"""
        return EnhancedOrchestrator()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory"""
        temp_dir = tempfile.mkdtemp()
        workspace_dir = Path(temp_dir) / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        yield workspace_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_execute_llm_call_direct_with_mock(self, orchestrator):
        """Test direct LLM call execution with mock responses"""
        response = await orchestrator._execute_llm_call_direct(
            "Product_Analyst",
            "Create a simple API",
            {"workflow_id": "test-003"}
        )
        
        assert response is not None
        assert len(response) > 50
        assert "Product_Analyst" in response or "Analysis" in response
    
    @pytest.mark.asyncio
    async def test_execute_llm_call_with_cache(self, orchestrator):
        """Test LLM call with caching enabled"""
        context = {"workflow_id": "test-004"}
        
        response = await orchestrator.execute_llm_call_with_cache(
            "Coder",
            "Create a simple function",
            context
        )
        
        assert response is not None
        assert len(response) > 50
    
    @pytest.mark.asyncio
    async def test_save_agent_artifacts_javascript(self, orchestrator, temp_workspace):
        """Test saving JavaScript artifacts from agent response"""
        response_with_code = '''# Implementation Complete

Here's the JavaScript code:

```javascript
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.json({ message: 'Hello World' });
});

module.exports = app;
```

This creates a simple Express server.
'''
        
        # Temporarily change workspace to our temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_workspace.parent)
        
        try:
            saved_files = await orchestrator._save_agent_artifacts(response_with_code, "test-005")
            
            assert len(saved_files) >= 1
            
            # Check if JavaScript file was created
            js_files = [f for f in saved_files if f.endswith('.js')]
            assert len(js_files) >= 1
            
            # Check file content
            js_file_path = Path(js_files[0])
            assert js_file_path.exists()
            
            content = js_file_path.read_text()
            assert "express" in content
            assert "Hello World" in content
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_save_agent_artifacts_multiple_files(self, orchestrator, temp_workspace):
        """Test saving multiple artifacts from agent response"""
        response_with_multiple_files = '''# Implementation Complete

Here's the backend code:

```javascript
const express = require('express');
const app = express();
app.listen(3000);
```

And the database schema:

```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255)
);
```

Configuration file:

```json
{
    "port": 3000,
    "database": "myapp"
}
```
'''
        
        original_cwd = os.getcwd()
        os.chdir(temp_workspace.parent)
        
        try:
            saved_files = await orchestrator._save_agent_artifacts(response_with_multiple_files, "test-006")
            
            # Debug: print what files were actually saved
            print(f"DEBUG: Saved files: {saved_files}")
            extensions = [Path(f).suffix for f in saved_files]
            print(f"DEBUG: Extensions found: {extensions}")
            
            assert len(saved_files) >= 3  # Should have JS, SQL, JSON files + documentation
            
            # Check for different file types
            assert '.js' in extensions
            assert '.sql' in extensions
            assert '.json' in extensions
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_workflow_creation_with_context(self, orchestrator):
        """Test workflow creation with proper context"""
        
        # Mock the knowledge registry to avoid initialization issues
        mock_registry = AsyncMock()
        mock_registry.get_workflow_requirements.return_value = {
            "required_agents": ["Product_Analyst", "Architect", "Coder"],
            "required_tools": ["llm_interface", "file_tools"]
        }
        mock_registry.generate_agent_knowledge_package.return_value = {
            "available_tools": ["create_file", "edit_file"],
            "workflow_participation": ["analysis", "implementation"],
            "best_practices": ["Use clear specifications", "Write clean code"]
        }
        
        orchestrator.knowledge_registry = mock_registry
        
        # Mock the orchestration pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.create_agent_workflow.return_value = "WORKFLOW-TEST-001"
        orchestrator.orchestration_pipeline = mock_pipeline
        
        # Mock agent factory
        mock_agent_factory = AsyncMock()
        mock_agent_factory.create_agent_prompt.return_value = "Test prompt for agent"
        orchestrator.agent_factory = mock_agent_factory
        
        workflow_id = await orchestrator.start_workflow(
            "Create a simple REST API",
            "complex_ui_feature"
        )
        
        assert workflow_id == "WORKFLOW-TEST-001"
        assert workflow_id in orchestrator.active_workflows
        
        workflow = orchestrator.active_workflows[workflow_id]
        assert workflow["status"] == "active"
        assert "workflow_id" in workflow["context"]


class TestErrorHandling:
    """Test error handling in LLM integration"""
    
    @pytest.mark.asyncio
    async def test_llm_call_with_invalid_agent(self):
        """Test LLM call with invalid agent name"""
        orchestrator = EnhancedOrchestrator()
        
        with pytest.raises(ValueError, match="agent_name must be a non-empty string"):
            await orchestrator._execute_llm_call_direct("", "test prompt")
        
        with pytest.raises(ValueError, match="agent_name must be a non-empty string"):
            await orchestrator._execute_llm_call_direct(None, "test prompt")
    
    @pytest.mark.asyncio
    async def test_llm_call_with_invalid_prompt(self):
        """Test LLM call with invalid prompt"""
        orchestrator = EnhancedOrchestrator()
        
        with pytest.raises(ValueError, match="prompt must be a non-empty string"):
            await orchestrator._execute_llm_call_direct("Product_Analyst", "")
        
        with pytest.raises(ValueError, match="prompt must be a non-empty string"):
            await orchestrator._execute_llm_call_direct("Product_Analyst", None)


class TestFileHandling:
    """Test file handling functionality"""
    
    def test_artifact_regex_matching(self):
        """Test that our regex correctly identifies code blocks"""
        import re
        
        test_response = '''# Test Response

Here's some JavaScript:

```javascript
console.log('Hello World');
```

And some Python:

```python
print("Hello World")
```

And some SQL:

```sql
SELECT * FROM users;
```
'''
        
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', test_response, re.DOTALL)
        
        assert len(code_blocks) == 3
        assert code_blocks[0][0] == 'javascript'
        assert 'console.log' in code_blocks[0][1]
        assert code_blocks[1][0] == 'python'
        assert 'print' in code_blocks[1][1]
        assert code_blocks[2][0] == 'sql'
        assert 'SELECT' in code_blocks[2][1]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
