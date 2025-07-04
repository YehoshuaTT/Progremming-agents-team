"""
Test suite for advanced error handling and recovery system
"""

import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from tools.checkpoint_system import TaskCheckpoint, CheckpointManager
from tools.error_handling import ErrorClassifier, RetryManager, RecoveryStrategy, ErrorCategory, ErrorSeverity
from core.enhanced_orchestrator import EnhancedOrchestrator


class TestCheckpointSystem:
    """Test the checkpoint system functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.checkpoint_manager = CheckpointManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_checkpoint(self):
        """Test checkpoint creation"""
        checkpoint = self.checkpoint_manager.create_checkpoint(
            task_id="test_task_001",
            workflow_id="test_workflow_001",
            agent_name="Test_Agent",
            progress_percentage=50.0,
            state_data={"status": "in_progress"},
            intermediate_results={"result": "partial"},
            dependencies_completed=["dep1"],
            context={"test": "context"}
        )
        
        assert checkpoint.task_id == "test_task_001"
        assert checkpoint.progress_percentage == 50.0
        assert checkpoint.state_data["status"] == "in_progress"
        assert len(checkpoint.checkpoint_id) == 12
    
    def test_checkpoint_persistence(self):
        """Test that checkpoints are saved and loaded correctly"""
        # Create checkpoint
        checkpoint = self.checkpoint_manager.create_checkpoint(
            task_id="test_task_002",
            workflow_id="test_workflow_002",
            agent_name="Test_Agent",
            progress_percentage=75.0,
            state_data={"status": "nearly_done"},
            intermediate_results={},
            dependencies_completed=[],
            context={}
        )
        
        # Create new manager to test loading
        new_manager = CheckpointManager(self.temp_dir)
        loaded_checkpoint = new_manager.get_checkpoint(checkpoint.checkpoint_id)
        
        assert loaded_checkpoint is not None
        assert loaded_checkpoint.task_id == "test_task_002"
        assert loaded_checkpoint.progress_percentage == 75.0
    
    def test_checkpoint_cleanup(self):
        """Test checkpoint cleanup functionality"""
        # Create checkpoint
        checkpoint = self.checkpoint_manager.create_checkpoint(
            task_id="test_task_003",
            workflow_id="test_workflow_003",
            agent_name="Test_Agent",
            progress_percentage=100.0,
            state_data={"status": "completed"},
            intermediate_results={},
            dependencies_completed=[],
            context={}
        )
        
        # Clean up completed task
        self.checkpoint_manager.cleanup_completed_task("test_task_003")
        
        # Verify checkpoint is removed
        assert self.checkpoint_manager.get_checkpoint(checkpoint.checkpoint_id) is None


class TestErrorHandling:
    """Test error classification and handling"""
    
    def setup_method(self):
        """Setup test environment"""
        self.classifier = ErrorClassifier()
        self.retry_manager = RetryManager()
        self.recovery_strategy = RecoveryStrategy()
    
    def test_error_classification_transient(self):
        """Test transient error classification"""
        error = Exception("Connection timeout occurred")
        error_info = self.classifier.classify_error(error)
        
        assert error_info.category == ErrorCategory.TRANSIENT
        assert error_info.max_retries == 3
        assert "retry" in error_info.suggested_fix.lower()
    
    def test_error_classification_recoverable(self):
        """Test recoverable error classification"""
        error = Exception("Invalid format in input data")
        error_info = self.classifier.classify_error(error)
        
        assert error_info.category == ErrorCategory.RECOVERABLE
        assert error_info.max_retries == 2
    
    def test_error_classification_fatal(self):
        """Test fatal error classification"""
        error = Exception("Authentication failed - invalid credentials")
        error_info = self.classifier.classify_error(error)
        
        assert error_info.category == ErrorCategory.FATAL
        assert error_info.max_retries == 0
    
    def test_retry_logic(self):
        """Test retry decision logic"""
        # Test transient error - should retry
        transient_error = Exception("Network timeout")
        should_retry, error_info = self.retry_manager.should_retry(transient_error)
        assert should_retry
        
        # Test fatal error - should not retry
        fatal_error = Exception("System crash detected")
        should_retry, error_info = self.retry_manager.should_retry(fatal_error)
        assert not should_retry
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        error = Exception("Rate limit exceeded")
        error_info = self.classifier.classify_error(error)
        
        # Test increasing delays
        delays = []
        for i in range(3):
            error_info.retry_count = i
            delay = self.retry_manager.calculate_delay(error_info)
            delays.append(delay)
        
        assert delays[0] < delays[1] < delays[2]
    
    def test_recovery_strategies(self):
        """Test different recovery strategies"""
        # Test transient error recovery
        transient_error = Exception("Connection timeout")
        error_info = self.classifier.classify_error(transient_error)
        recovery = self.recovery_strategy.apply_recovery(error_info, {})
        
        assert recovery["action"] == "retry"
        assert recovery["delay"] > 0
        
        # Test fatal error recovery
        fatal_error = Exception("Authentication failed")
        error_info = self.classifier.classify_error(fatal_error)
        recovery = self.recovery_strategy.apply_recovery(error_info, {})
        
        assert recovery["action"] == "escalate"


class TestEnhancedOrchestratorErrorHandling:
    """Test error handling integration in enhanced orchestrator"""
    
    def setup_method(self):
        """Setup test environment"""
        self.orchestrator = EnhancedOrchestrator()
    
    @pytest.mark.asyncio
    async def test_task_execution_with_recovery_success(self):
        """Test successful task execution with recovery system"""
        # Mock successful execution
        with patch.object(self.orchestrator, '_execute_agent_task') as mock_execute:
            mock_execute.return_value = {
                "status": "completed",
                "result": "Task completed successfully"
            }
            
            result = await self.orchestrator.execute_task_with_recovery(
                task_id="test_task_001",
                agent_name="Test_Agent",
                task_prompt="Test task",
                context={"workflow_id": "test_workflow"}
            )
            
            assert result["status"] == "completed"
            assert mock_execute.call_count == 1
    
    @pytest.mark.asyncio
    async def test_task_execution_with_retry(self):
        """Test task execution with retry on transient error"""
        # Mock failing then succeeding execution
        with patch.object(self.orchestrator, '_execute_agent_task') as mock_execute:
            mock_execute.side_effect = [
                Exception("Connection timeout"),  # First attempt fails
                {"status": "completed", "result": "Success after retry"}  # Second attempt succeeds
            ]
            
            result = await self.orchestrator.execute_task_with_recovery(
                task_id="test_task_002",
                agent_name="Test_Agent",
                task_prompt="Test task",
                context={"workflow_id": "test_workflow"}
            )
            
            assert result["status"] == "completed"
            assert mock_execute.call_count == 2  # Should have retried once
    
    @pytest.mark.asyncio
    async def test_task_execution_with_escalation(self):
        """Test task execution with escalation on fatal error"""
        # Mock fatal error
        with patch.object(self.orchestrator, '_execute_agent_task') as mock_execute:
            mock_execute.side_effect = Exception("Authentication failed")
            
            result = await self.orchestrator.execute_task_with_recovery(
                task_id="test_task_003",
                agent_name="Test_Agent",
                task_prompt="Test task",
                context={"workflow_id": "test_workflow"}
            )
            
            assert result["status"] == "escalated"
            assert len(self.orchestrator.human_approval_queue) == 1
    
    def test_checkpoint_status_retrieval(self):
        """Test checkpoint status retrieval"""
        # Create a checkpoint
        checkpoint = self.orchestrator.checkpoint_manager.create_checkpoint(
            task_id="test_task_004",
            workflow_id="test_workflow",
            agent_name="Test_Agent",
            progress_percentage=60.0,
            state_data={"status": "in_progress"},
            intermediate_results={},
            dependencies_completed=[],
            context={}
        )
        
        # Get status
        status = self.orchestrator.get_checkpoint_status("test_task_004")
        
        assert status is not None
        assert status["task_id"] == "test_task_004"
        assert status["progress"] == 60.0
        assert status["status"] == "in_progress"
    
    def test_error_statistics(self):
        """Test error statistics collection"""
        # Add some mock errors
        from tools.error_handling import ErrorInfo, ErrorCategory, ErrorSeverity
        
        error1 = ErrorInfo(
            error_type="ConnectionError",
            error_message="Connection timeout",
            category=ErrorCategory.TRANSIENT,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now().isoformat(),
            context={}
        )
        
        error2 = ErrorInfo(
            error_type="AuthenticationError",
            error_message="Invalid credentials",
            category=ErrorCategory.FATAL,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now().isoformat(),
            context={}
        )
        
        self.orchestrator.error_history = [error1, error2]
        
        stats = self.orchestrator.get_error_statistics()
        
        assert stats["total_errors"] == 2
        assert stats["categories"]["transient"] == 1
        assert stats["categories"]["fatal"] == 1
        assert stats["severity_distribution"]["medium"] == 1
        assert stats["severity_distribution"]["high"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
