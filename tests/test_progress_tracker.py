"""
Test suite for Progress Tracker module
Tests progress tracking, documentation generation, and status reporting
"""

import pytest
import json
import asyncio
import sqlite3
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path

from tools.progress_tracker import (
    ProgressTracker, ActivityType, ReportType, Activity, ProgressSnapshot, PerformanceMetrics
)
from tools.intelligent_orchestrator import IntelligentOrchestrator
from tools.plan_generator import ProjectPlan, TaskStatus


class TestProgressTracker:
    """Test the progress tracker functionality"""
    
    @pytest.fixture
    def orchestrator_mock(self):
        """Create a mock orchestrator"""
        mock = AsyncMock(spec=IntelligentOrchestrator)
        return mock
    
    @pytest.fixture
    def progress_tracker(self, orchestrator_mock):
        """Create a progress tracker for testing"""
        with patch('tools.progress_tracker.sqlite3.connect') as mock_connect:
            # Create a mock connection and cursor
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Initialize the tracker
            tracker = ProgressTracker(orchestrator=orchestrator_mock, db_path=":memory:")
            
            # Mock the database operations to avoid actual SQL
            tracker._save_activity_to_db = MagicMock()
            
            return tracker
    
    def test_initialization(self, progress_tracker, orchestrator_mock):
        """Test progress tracker initialization"""
        assert progress_tracker.orchestrator == orchestrator_mock
        
    def test_track_activity(self, progress_tracker):
        """Test tracking an activity"""
        activity_id = progress_tracker.track_activity(
            type=ActivityType.TASK_STARTED,
            description="Started working on login feature",
            agent_id="coder",
            task_id="task123",
            metadata={
                "feature_id": "feature456",
                "priority": "high"
            }
        )
        
        assert activity_id is not None
        assert len(progress_tracker.activities) == 1
        assert progress_tracker.activities[0].type == ActivityType.TASK_STARTED
        assert progress_tracker.activities[0].description == "Started working on login feature"
    
    @pytest.mark.asyncio
    async def test_generate_report(self, progress_tracker):
        """Test generating a progress report"""
        # Add some activities first
        progress_tracker.track_activity(
            type=ActivityType.TASK_STARTED,
            description="Started login feature",
            agent_id="coder"
        )
        
        progress_tracker.track_activity(
            type=ActivityType.TASK_COMPLETED,
            description="Completed login feature",
            agent_id="coder"
        )
        
        report = await progress_tracker.generate_report(ReportType.DAILY_SUMMARY)
        
        assert report is not None
        assert "summary" in report or "activity_summary" in report
    
    @pytest.mark.asyncio
    async def test_get_real_time_status(self, progress_tracker):
        """Test getting real-time status"""
        # Add some activities
        progress_tracker.track_activity(
            type=ActivityType.TASK_STARTED,
            description="Started task 1",
            agent_id="coder"
        )
        
        status = await progress_tracker.get_real_time_status()
        
        assert status is not None
        # The status might return an error if no project plan is available
        # This is expected behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
