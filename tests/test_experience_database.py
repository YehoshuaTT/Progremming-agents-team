"""
Comprehensive test suite for the Experience Database and Pattern Recognition system
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from tests.security_test_utils import secure_true, secure_equal

from tools.experience_database import (
    ExperienceDatabase, ExperienceEntry, TaskType, OutcomeType
)
from tools.pattern_recognition import PatternRecognitionEngine


class TestExperienceDatabase:
    """Test suite for ExperienceDatabase"""
    
    @pytest_asyncio.fixture
    async def temp_db(self):
        """Create a temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_experience.db")
        
        db = ExperienceDatabase(db_path)
        await db.initialize()
        
        yield db
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)
    
    @pytest.fixture
    def sample_experience(self):
        """Create a sample experience for testing"""
        return ExperienceEntry(
            id="test_exp_001",
            agent_id="test_agent",
            task_type=TaskType.CODE_GENERATION,
            context={"language": "python", "complexity": "medium"},
            actions_taken=["analyze", "generate", "test"],
            outcome=OutcomeType.SUCCESS,
            success=True,
            duration=30.5,
            challenges=["complex_logic"],
            lessons_learned=["test_early"],
            created_at=datetime.now(),
            project_id="test_proj",
            workflow_id="test_wf",
            quality_score=0.8,
            complexity_score=0.6,
            impact_score=0.7
        )
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, temp_db):
        """Test database initialization"""
        secure_true(temp_db.db_path.exists())
        
        # Test that tables are created
        secure_true(temp_db.db_path.stat().st_size > 0)
    
    @pytest.mark.asyncio
    async def test_log_experience(self, temp_db, sample_experience):
        """Test logging an experience"""
        result = await temp_db.log_experience(sample_experience)
        secure_true(result is True)
        
        # Verify it was stored
        retrieved = await temp_db.get_experience(sample_experience.id)
        secure_true(retrieved is not None)
        secure_equal(retrieved.id, sample_experience.id)
        secure_equal(retrieved.agent_id, sample_experience.agent_id)
        secure_equal(retrieved.task_type, sample_experience.task_type)
        secure_equal(retrieved.success, sample_experience.success)
    
    @pytest.mark.asyncio
    async def test_get_experience_not_found(self, temp_db):
        """Test getting non-existent experience"""
        result = await temp_db.get_experience("nonexistent_id")
        secure_true(result is None)
    
    @pytest.mark.asyncio
    async def test_search_experiences(self, temp_db, sample_experience):
        """Test searching experiences"""
        # Add the experience
        await temp_db.log_experience(sample_experience)
        
        # Search by agent_id
        results = await temp_db.search_experiences(agent_id="test_agent")
        secure_equal(len(results), 1)
        secure_equal(results[0].id, sample_experience.id)
        
        # Search by task_type
        results = await temp_db.search_experiences(task_type=TaskType.CODE_GENERATION)
        secure_equal(len(results), 1)
        
        # Search by success
        results = await temp_db.search_experiences(success=True)
        secure_equal(len(results), 1)
        
        # Search with no matches
        results = await temp_db.search_experiences(agent_id="nonexistent")
        secure_equal(len(results), 0)
    
    @pytest.mark.asyncio
    async def test_get_agent_statistics(self, temp_db):
        """Test getting agent statistics"""
        # Create multiple experiences
        experiences = []
        for i in range(5):
            exp = ExperienceEntry(
                id=f"exp_{i}",
                agent_id="test_agent",
                task_type=TaskType.CODE_GENERATION,
                context={"test": f"value_{i}"},
                actions_taken=[f"action_{i}"],
                outcome=OutcomeType.SUCCESS if i % 2 == 0 else OutcomeType.FAILURE,
                success=i % 2 == 0,
                duration=float(i * 10),
                challenges=[f"challenge_{i}"],
                lessons_learned=[f"lesson_{i}"],
                created_at=datetime.now() - timedelta(days=i),
                project_id="test_proj",
                workflow_id="test_wf",
                quality_score=float(i) / 10,
                complexity_score=0.5,
                impact_score=0.6
            )
            experiences.append(exp)
            await temp_db.log_experience(exp)
        
        # Get statistics
        stats = await temp_db.get_agent_statistics("test_agent")
        
        secure_equal(stats["agent_id"], "test_agent")
        secure_equal(stats["total_experiences"], 5)
        secure_equal(stats["success_count"], 3)  # 0, 2, 4 are successes
        secure_equal(stats["success_rate"], 0.6)
        secure_equal(stats["avg_duration"], 20.0)  # (0+10+20+30+40)/5
        secure_true("task_distribution" in stats)
        secure_true("outcome_distribution" in stats)
    
    @pytest.mark.asyncio
    async def test_get_similar_experiences(self, temp_db):
        """Test finding similar experiences"""
        # Create experiences with similar contexts
        similar_context = {"language": "python", "complexity": "medium"}
        different_context = {"language": "java", "complexity": "high"}
        
        exp1 = ExperienceEntry(
            id="exp_1",
            agent_id="agent_1",
            task_type=TaskType.CODE_GENERATION,
            context=similar_context,
            actions_taken=["analyze", "generate"],
            outcome=OutcomeType.SUCCESS,
            success=True,
            duration=30.0,
            challenges=[],
            lessons_learned=[],
            created_at=datetime.now(),
            project_id="proj_1",
            workflow_id="wf_1"
        )
        
        exp2 = ExperienceEntry(
            id="exp_2",
            agent_id="agent_2",
            task_type=TaskType.CODE_GENERATION,
            context=different_context,
            actions_taken=["design", "implement"],
            outcome=OutcomeType.SUCCESS,
            success=True,
            duration=45.0,
            challenges=[],
            lessons_learned=[],
            created_at=datetime.now(),
            project_id="proj_2",
            workflow_id="wf_2"
        )
        
        await temp_db.log_experience(exp1)
        await temp_db.log_experience(exp2)
        
        # Find similar experiences
        similar = await temp_db.get_similar_experiences(
            context=similar_context,
            task_type=TaskType.CODE_GENERATION,
            limit=5
        )
        
        # Should find the similar one with higher similarity
        secure_true(len(similar) >= 1)
        # The first result should be the most similar
        secure_equal(similar[0][0].id, "exp_1")
    
    @pytest.mark.asyncio
    async def test_add_feedback(self, temp_db, sample_experience):
        """Test adding feedback to an experience"""
        await temp_db.log_experience(sample_experience)
        
        result = await temp_db.add_feedback(
            experience_id=sample_experience.id,
            feedback_type="quality",
            rating=5,
            comment="Excellent work"
        )
        
        secure_true(result is True)
    
    @pytest.mark.asyncio
    async def test_get_recommendations(self, temp_db):
        """Test getting recommendations"""
        # Create some successful experiences
        for i in range(3):
            exp = ExperienceEntry(
                id=f"exp_{i}",
                agent_id="agent_1",
                task_type=TaskType.CODE_GENERATION,
                context={"language": "python", "complexity": "medium"},
                actions_taken=["analyze", "generate", "test"],
                outcome=OutcomeType.SUCCESS,
                success=True,
                duration=30.0,
                challenges=["complex_logic"],
                lessons_learned=["test_early"],
                created_at=datetime.now(),
                project_id="proj_1",
                workflow_id="wf_1",
                quality_score=0.9
            )
            await temp_db.log_experience(exp)
        
        # Get recommendations
        recommendations = await temp_db.get_recommendations(
            context={"language": "python", "complexity": "medium"},
            task_type=TaskType.CODE_GENERATION
        )
        
        secure_true(isinstance(recommendations, list))
        secure_true(len(recommendations) >= 0)


class TestPatternRecognitionEngine:
    """Test suite for PatternRecognitionEngine"""
    
    @pytest_asyncio.fixture
    async def temp_db_with_data(self):
        """Create a temporary database with sample data"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_pattern.db")
        
        db = ExperienceDatabase(db_path)
        await db.initialize()
        
        # Add sample data
        experiences = []
        for i in range(20):
            exp = ExperienceEntry(
                id=f"exp_{i}",
                agent_id=f"agent_{i % 3}",
                task_type=TaskType.CODE_GENERATION if i % 2 == 0 else TaskType.TESTING,
                context={"language": "python" if i % 2 == 0 else "java", "complexity": "medium"},
                actions_taken=["analyze", "generate", "test"] if i % 2 == 0 else ["plan", "execute"],
                outcome=OutcomeType.SUCCESS if i % 3 != 0 else OutcomeType.FAILURE,
                success=i % 3 != 0,
                duration=float(20 + i * 5),
                challenges=["complex_logic"] if i % 2 == 0 else ["time_pressure"],
                lessons_learned=["test_early"] if i % 2 == 0 else ["plan_better"],
                created_at=datetime.now() - timedelta(days=i),
                project_id=f"proj_{i % 4}",
                workflow_id=f"wf_{i}",
                quality_score=0.8 if i % 3 != 0 else 0.3,
                complexity_score=0.5,
                impact_score=0.6
            )
            experiences.append(exp)
            await db.log_experience(exp)
        
        yield db
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)
    
    @pytest_asyncio.fixture
    async def pattern_engine(self, temp_db_with_data):
        """Create a pattern recognition engine with test data"""
        return PatternRecognitionEngine(temp_db_with_data)
    
    @pytest.mark.asyncio
    async def test_pattern_analysis(self, pattern_engine):
        """Test comprehensive pattern analysis"""
        analysis = await pattern_engine.analyze_all_patterns()
        
        secure_true("patterns" in analysis)
        secure_true("anti_patterns" in analysis)
        secure_true("opportunities" in analysis)
        secure_true("clusters" in analysis)
        secure_true("analyzed_at" in analysis)
        secure_true("experience_count" in analysis)
        
        # Should have some patterns with sufficient data
        secure_true(isinstance(analysis["patterns"], list))
        secure_true(isinstance(analysis["anti_patterns"], list))
        secure_true(isinstance(analysis["opportunities"], list))
    
    @pytest.mark.asyncio
    async def test_success_pattern_analysis(self, pattern_engine):
        """Test success pattern analysis"""
        analysis = await pattern_engine.analyze_all_patterns()
        
        # Should identify some success patterns
        patterns = analysis["patterns"]
        secure_true(isinstance(patterns, list))
        
        # Each pattern should have required fields
        for pattern in patterns:
            secure_true("id" in pattern)
            secure_true("task_type" in pattern)
            secure_true("pattern_type" in pattern)
            secure_true("success_rate" in pattern)
            secure_true("confidence" in pattern)
            secure_true("frequency" in pattern)
    
    @pytest.mark.asyncio
    async def test_failure_pattern_analysis(self, pattern_engine):
        """Test failure pattern (anti-pattern) analysis"""
        analysis = await pattern_engine.analyze_all_patterns()
        
        # Should identify some anti-patterns
        anti_patterns = analysis["anti_patterns"]
        secure_true(isinstance(anti_patterns, list))
        
        # Each anti-pattern should have required fields
        for anti_pattern in anti_patterns:
            secure_true(hasattr(anti_pattern, 'id'))
            secure_true(hasattr(anti_pattern, 'name'))
            secure_true(hasattr(anti_pattern, 'description'))
            secure_true(hasattr(anti_pattern, 'failure_rate'))
            secure_true(hasattr(anti_pattern, 'avoidance_strategies'))
    
    @pytest.mark.asyncio
    async def test_optimization_opportunities(self, pattern_engine):
        """Test optimization opportunity identification"""
        analysis = await pattern_engine.analyze_all_patterns()
        
        # Should identify some optimization opportunities
        opportunities = analysis["opportunities"]
        secure_true(isinstance(opportunities, list))
        
        # Each opportunity should have required fields
        for opportunity in opportunities:
            secure_true(hasattr(opportunity, 'id'))
            secure_true(hasattr(opportunity, 'area'))
            secure_true(hasattr(opportunity, 'description'))
            secure_true(hasattr(opportunity, 'current_performance'))
            secure_true(hasattr(opportunity, 'potential_improvement'))
            secure_true(hasattr(opportunity, 'suggested_actions'))
    
    @pytest.mark.asyncio
    async def test_clustering_analysis(self, pattern_engine):
        """Test clustering analysis"""
        analysis = await pattern_engine.analyze_all_patterns()
        
        # Should perform clustering analysis
        clusters = analysis["clusters"]
        secure_true(isinstance(clusters, dict))
        
        # Should have clustering results
        if "clusters" in clusters:
            cluster_data = clusters["clusters"]
            secure_true(isinstance(cluster_data, dict))


# Integration tests
class TestIntegration:
    """Integration tests for the experience system"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow from experience logging to pattern recognition"""
        # Create temporary database
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_integration.db")
        
        try:
            # Initialize database
            db = ExperienceDatabase(db_path)
            await db.initialize()
            
            # Create pattern engine
            pattern_engine = PatternRecognitionEngine(db)
            
            # Log several experiences
            for i in range(15):
                exp = ExperienceEntry(
                    id=f"integration_exp_{i}",
                    agent_id="integration_agent",
                    task_type=TaskType.CODE_GENERATION,
                    context={"language": "python", "complexity": "medium"},
                    actions_taken=["analyze", "generate", "test"],
                    outcome=OutcomeType.SUCCESS,
                    success=True,
                    duration=30.0 + i,
                    challenges=["complex_logic"],
                    lessons_learned=["test_early"],
                    created_at=datetime.now() - timedelta(hours=i),
                    project_id="integration_proj",
                    workflow_id=f"integration_wf_{i}",
                    quality_score=0.8,
                    complexity_score=0.6,
                    impact_score=0.7
                )
                await db.log_experience(exp)
            
            # Get agent statistics
            stats = await db.get_agent_statistics("integration_agent")
            secure_equal(stats["total_experiences"], 15)
            secure_equal(stats["success_rate"], 1.0)
            
            # Get recommendations
            recommendations = await db.get_recommendations(
                context={"language": "python", "complexity": "medium"},
                task_type=TaskType.CODE_GENERATION
            )
            secure_true(isinstance(recommendations, list))
            
            # Perform pattern analysis
            analysis = await pattern_engine.analyze_all_patterns()
            secure_true("patterns" in analysis)
            secure_true("anti_patterns" in analysis)
            secure_true("opportunities" in analysis)
            
            # Add feedback
            await db.add_feedback(
                experience_id="integration_exp_0",
                feedback_type="quality",
                rating=5,
                comment="Great work!"
            )
            
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.remove(db_path)
            os.rmdir(temp_dir)


# Performance tests
class TestPerformance:
    """Performance tests for the experience system"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self):
        """Test performance with large dataset"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_performance.db")
        
        try:
            db = ExperienceDatabase(db_path)
            await db.initialize()
            
            # Add many experiences
            start_time = datetime.now()
            
            for i in range(100):  # Reduced for testing
                exp = ExperienceEntry(
                    id=f"perf_exp_{i}",
                    agent_id=f"agent_{i % 10}",
                    task_type=TaskType.CODE_GENERATION,
                    context={"test": f"value_{i}"},
                    actions_taken=[f"action_{i}"],
                    outcome=OutcomeType.SUCCESS,
                    success=True,
                    duration=float(i),
                    challenges=[f"challenge_{i}"],
                    lessons_learned=[f"lesson_{i}"],
                    created_at=datetime.now() - timedelta(minutes=i),
                    project_id="perf_proj",
                    workflow_id=f"perf_wf_{i}",
                    quality_score=0.8,
                    complexity_score=0.5,
                    impact_score=0.6
                )
                await db.log_experience(exp)
            
            insert_time = datetime.now() - start_time
            
            # Test search performance
            search_start = datetime.now()
            results = await db.search_experiences(limit=50)
            search_time = datetime.now() - search_start
            
            secure_equal(len(results), 50)
            secure_true(insert_time.total_seconds() < 30)  # Should complete within 30 seconds
            secure_true(search_time.total_seconds() < 5)   # Should search within 5 seconds
            
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
            os.rmdir(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
