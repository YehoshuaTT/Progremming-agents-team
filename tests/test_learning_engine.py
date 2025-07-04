"""
Test suite for the Learning Engine module

Tests adaptive learning algorithms, performance optimization,
outcome prediction, and learning metrics tracking.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from tools.learning_engine import (
    AdaptiveLearningEngine, 
    LearningObjective, 
    LearningMetric, 
    LearningRecommendation,
    create_learning_engine
)
from tools.experience_database import ExperienceDatabase
from tools.knowledge_graph import KnowledgeGraph


class TestAdaptiveLearningEngine:
    """Test cases for the AdaptiveLearningEngine class"""
    
    @pytest_asyncio.fixture
    async def mock_experience_db(self):
        """Create a mock experience database"""
        db = Mock(spec=ExperienceDatabase)
        db.initialize = AsyncMock()
        db.get_similar_experiences = AsyncMock(return_value=[])
        db.log_experience = AsyncMock()
        return db
    
    @pytest_asyncio.fixture
    async def mock_knowledge_graph(self):
        """Create a mock knowledge graph"""
        kg = Mock(spec=KnowledgeGraph)
        kg.initialize = AsyncMock()
        kg.add_node = AsyncMock()
        kg.query_nodes = AsyncMock(return_value=[])
        return kg
    
    @pytest_asyncio.fixture
    async def learning_engine(self, mock_experience_db, mock_knowledge_graph):
        """Create a learning engine instance for testing"""
        engine = AdaptiveLearningEngine(mock_experience_db, mock_knowledge_graph)
        await engine.initialize()
        return engine
    
    @pytest.mark.asyncio
    async def test_learning_engine_initialization(self, mock_experience_db, mock_knowledge_graph):
        """Test learning engine initialization"""
        engine = AdaptiveLearningEngine(mock_experience_db, mock_knowledge_graph)
        await engine.initialize()
        
        assert engine.experience_db == mock_experience_db
        assert engine.knowledge_graph == mock_knowledge_graph
        assert engine.min_experiences_for_learning == 10
        assert isinstance(engine.learning_metrics, dict)
        assert isinstance(engine.active_recommendations, list)
        
        # Verify initialization calls
        mock_experience_db.initialize.assert_called_once()
        mock_knowledge_graph.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_learn_from_experience_success(self, learning_engine):
        """Test learning from successful experience"""
        experience_data = {
            "id": "exp_001",
            "success": True,
            "duration": 120,
            "complexity": 5,
            "agents_involved": ["agent1", "agent2"],
            "context": {
                "requirements": ["req1", "req2"],
                "priority": 3,
                "resource_usage": 0.7
            },
            "outcome": "Task completed successfully",
            "timestamp": datetime.now()
        }
        
        result = await learning_engine.learn_from_experience(experience_data)
        
        assert "insights" in result
        assert "new_recommendations" in result
        assert "learning_metrics" in result
        assert "model_updates" in result
        assert result["insights"]["performance_impact"] == "positive"
        assert isinstance(result["new_recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_learn_from_experience_failure(self, learning_engine):
        """Test learning from failed experience"""
        experience_data = {
            "id": "exp_002",
            "success": False,
            "duration": 300,
            "complexity": 8,
            "agents_involved": ["agent1", "agent2", "agent3"],
            "context": {
                "requirements": ["req1", "req2", "req3"],
                "priority": 5,
                "resource_usage": 0.9
            },
            "outcome": "Task failed due to timeout",
            "error": "TimeoutError",
            "timestamp": datetime.now()
        }
        
        result = await learning_engine.learn_from_experience(experience_data)
        
        assert result["insights"]["performance_impact"] == "negative"
        assert result["insights"]["learning_value"] == "high"
        assert len(result["new_recommendations"]) > 0
        
        # Check that error reduction recommendation was generated
        recommendations = result["new_recommendations"]
        error_reduction_recs = [r for r in recommendations if r.objective == LearningObjective.ERROR_REDUCTION]
        assert len(error_reduction_recs) > 0
    
    @pytest.mark.asyncio
    async def test_get_adaptive_strategy(self, learning_engine):
        """Test adaptive strategy generation"""
        context = {
            "task_type": "code_generation",
            "complexity": 6,
            "deadline": "2025-07-05",
            "resources": ["agent1", "agent2"],
            "requirements": ["python", "async", "testing"]
        }
        
        # Mock similar experiences
        similar_experiences = [
            {"success": True, "duration": 100, "approach": "modular"},
            {"success": False, "duration": 200, "approach": "monolithic"},
            {"success": True, "duration": 120, "approach": "modular"}
        ]
        learning_engine.experience_db.get_similar_experiences.return_value = similar_experiences
        
        # Mock pattern analysis
        with patch.object(learning_engine.pattern_engine, 'analyze_all_patterns') as mock_analyze:
            mock_analyze.return_value = {
                "success_rate": 0.67,
                "pattern_strength": 0.8,
                "data_quality": 0.9
            }
            
            strategy = await learning_engine.get_adaptive_strategy(context)
            
            assert "approach" in strategy
            assert "confidence_threshold" in strategy
            assert "confidence" in strategy
            assert strategy["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_optimize_performance_insufficient_data(self, learning_engine):
        """Test performance optimization with insufficient data"""
        objective = LearningObjective.PERFORMANCE_OPTIMIZATION
        
        # Mock insufficient experiences
        with patch.object(learning_engine, '_get_experiences_for_objective') as mock_get_exp:
            mock_get_exp.return_value = []  # No experiences
            
            result = await learning_engine.optimize_performance(objective)
            
            assert result["status"] == "insufficient_data"
            assert result["current_count"] == 0
            assert "Need at least" in result["message"]
    
    @pytest.mark.asyncio
    async def test_optimize_performance_success(self, learning_engine):
        """Test successful performance optimization"""
        objective = LearningObjective.PERFORMANCE_OPTIMIZATION
        
        # Mock sufficient experiences
        experiences = [{"id": f"exp_{i}", "success": True, "duration": 100 + i*10} for i in range(15)]
        
        with patch.object(learning_engine, '_get_experiences_for_objective') as mock_get_exp:
            mock_get_exp.return_value = experiences
            
            result = await learning_engine.optimize_performance(objective)
            
            assert result["status"] == "success"
            assert result["objective"] == objective.value
            assert "analysis" in result
            assert "optimizations" in result
            assert "implementation_plan" in result
    
    @pytest.mark.asyncio
    async def test_predict_outcome_high_confidence(self, learning_engine):
        """Test outcome prediction with high confidence"""
        planned_action = {
            "type": "code_generation",
            "complexity": 5,
            "dependencies": ["lib1", "lib2"],
            "estimated_duration": 120,
            "risk_level": 2
        }
        
        # Mock similar actions
        similar_actions = [
            {"success": True, "duration": 115},
            {"success": True, "duration": 125},
            {"success": False, "duration": 180}
        ]
        
        with patch.object(learning_engine, '_find_similar_actions') as mock_find:
            mock_find.return_value = similar_actions
            
            result = await learning_engine.predict_outcome(planned_action)
            
            assert "performance_prediction" in result
            assert "error_prediction" in result
            assert "confidence" in result
            assert "similar_actions" in result
            assert "recommendations" in result
            assert result["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_predict_outcome_low_confidence(self, learning_engine):
        """Test outcome prediction with low confidence"""
        planned_action = {
            "type": "new_task_type",
            "complexity": 10,
            "dependencies": [],
            "estimated_duration": 60,
            "risk_level": 1
        }
        
        # Mock no similar actions
        with patch.object(learning_engine, '_find_similar_actions') as mock_find:
            mock_find.return_value = []  # No similar actions
            
            result = await learning_engine.predict_outcome(planned_action)
            
            assert result["confidence"] == 0.3  # Low confidence due to no similar actions
            assert len(result["similar_actions"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_learning_dashboard(self, learning_engine):
        """Test learning dashboard generation"""
        # Set up some test data
        learning_engine.learning_metrics["success_rate"] = LearningMetric(
            name="success_rate",
            value=0.85,
            target=0.95,
            trend="improving",
            timestamp=datetime.now(),
            context={}
        )
        
        learning_engine.active_recommendations = [
            LearningRecommendation(
                id="rec_001",
                objective=LearningObjective.PERFORMANCE_OPTIMIZATION,
                recommendation="Implement caching",
                confidence=0.8,
                impact_score=0.7,
                implementation_effort="medium",
                expected_outcome="20% performance improvement",
                supporting_evidence=["Pattern analysis", "Similar systems"],
                created_at=datetime.now()
            )
        ]
        
        dashboard = await learning_engine.get_learning_dashboard()
        
        assert "learning_score" in dashboard
        assert "metrics" in dashboard
        assert "trends" in dashboard
        assert "active_recommendations" in dashboard
        assert "recent_history" in dashboard
        assert "model_performance" in dashboard
        assert "learning_opportunities" in dashboard
        
        # Check metrics structure
        assert "success_rate" in dashboard["metrics"]
        assert dashboard["metrics"]["success_rate"]["value"] == 0.85
        assert dashboard["metrics"]["success_rate"]["trend"] == "improving"
        
        # Check recommendations
        assert len(dashboard["active_recommendations"]) == 1
        assert dashboard["active_recommendations"][0]["id"] == "rec_001"
        assert dashboard["active_recommendations"][0]["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_learning_metrics_update(self, learning_engine):
        """Test learning metrics update functionality"""
        # Test with successful experience
        experience_data = {"success": True, "duration": 100}
        insights = {"performance_impact": "positive"}
        
        await learning_engine._update_learning_metrics(experience_data, insights)
        
        assert "success_rate" in learning_engine.learning_metrics
        metric = learning_engine.learning_metrics["success_rate"]
        assert metric.value > 0  # Should have updated from 0
        assert metric.target == 0.95
        assert metric.name == "success_rate"
        
        # Test with failed experience
        experience_data = {"success": False, "duration": 200}
        insights = {"performance_impact": "negative"}
        
        old_value = learning_engine.learning_metrics["success_rate"].value
        await learning_engine._update_learning_metrics(experience_data, insights)
        
        new_value = learning_engine.learning_metrics["success_rate"].value
        assert new_value < old_value  # Should have decreased due to failure
    
    @pytest.mark.asyncio
    async def test_feature_extraction(self, learning_engine):
        """Test feature extraction from experience data"""
        experience_data = {
            "duration": 120,
            "success": True,
            "complexity": 7,
            "agents_involved": ["agent1", "agent2", "agent3"],
            "context": {
                "requirements": ["req1", "req2"],
                "priority": 5,
                "resource_usage": 0.8
            }
        }
        
        features = await learning_engine._extract_features(experience_data)
        
        assert len(features) == 7
        assert features[0] == 120  # duration
        assert features[1] == 1    # success (converted to 1)
        assert features[2] == 7    # complexity
        assert features[3] == 3    # number of agents
        assert features[4] == 2    # number of requirements
        assert features[5] == 5    # priority
        assert features[6] == 0.8  # resource usage
    
    @pytest.mark.asyncio
    async def test_recommendation_generation(self, learning_engine):
        """Test recommendation generation based on insights"""
        # Test with negative performance impact
        insights = {"performance_impact": "negative", "learning_value": "high"}
        
        recommendations = await learning_engine._generate_recommendations(insights)
        
        assert len(recommendations) > 0
        error_reduction_recs = [r for r in recommendations if r.objective == LearningObjective.ERROR_REDUCTION]
        assert len(error_reduction_recs) > 0
        
        rec = error_reduction_recs[0]
        assert rec.confidence > 0
        assert rec.impact_score > 0
        assert rec.implementation_effort in ["low", "medium", "high"]
        assert isinstance(rec.supporting_evidence, list)
        assert rec.created_at is not None
    
    @pytest.mark.asyncio
    async def test_strategy_confidence_calculation(self, learning_engine):
        """Test strategy confidence calculation"""
        strategy = {"approach": "adaptive", "confidence_threshold": 0.7}
        
        # Test with high pattern strength
        patterns = {"pattern_strength": 0.8, "data_quality": 0.9}
        confidence = await learning_engine._calculate_strategy_confidence(strategy, patterns)
        assert confidence > 0.8
        
        # Test with low pattern strength
        patterns = {"pattern_strength": 0.3, "data_quality": 0.5}
        confidence = await learning_engine._calculate_strategy_confidence(strategy, patterns)
        assert confidence < 0.8
    
    @pytest.mark.asyncio
    async def test_action_feature_extraction(self, learning_engine):
        """Test feature extraction from planned actions"""
        planned_action = {
            "complexity": 6,
            "dependencies": ["dep1", "dep2", "dep3"],
            "estimated_duration": 180,
            "risk_level": 4
        }
        
        features = await learning_engine._extract_action_features(planned_action)
        
        assert len(features) == 4
        assert features[0] == 6    # complexity
        assert features[1] == 3    # number of dependencies
        assert features[2] == 180  # estimated duration
        assert features[3] == 4    # risk level
    
    @pytest.mark.asyncio
    async def test_learning_score_calculation(self, learning_engine):
        """Test overall learning score calculation"""
        # Set up test metric
        learning_engine.learning_metrics["success_rate"] = LearningMetric(
            name="success_rate",
            value=0.8,
            target=0.95,
            trend="improving",
            timestamp=datetime.now(),
            context={}
        )
        
        score = await learning_engine._calculate_overall_learning_score()
        
        assert 0 <= score <= 1
        assert score == min(0.8 * 1.2, 1.0)  # Should be 0.96 but capped at 1.0


class TestLearningEngineFactory:
    """Test cases for the learning engine factory function"""
    
    @pytest.mark.asyncio
    async def test_create_learning_engine(self):
        """Test learning engine factory function"""
        mock_experience_db = Mock(spec=ExperienceDatabase)
        mock_experience_db.initialize = AsyncMock()
        
        mock_knowledge_graph = Mock(spec=KnowledgeGraph)
        mock_knowledge_graph.initialize = AsyncMock()
        
        engine = await create_learning_engine(mock_experience_db, mock_knowledge_graph)
        
        assert isinstance(engine, AdaptiveLearningEngine)
        assert engine.experience_db == mock_experience_db
        assert engine.knowledge_graph == mock_knowledge_graph
        
        # Verify initialization was called
        mock_experience_db.initialize.assert_called_once()
        mock_knowledge_graph.initialize.assert_called_once()


class TestLearningDataStructures:
    """Test cases for learning data structures"""
    
    def test_learning_metric_creation(self):
        """Test LearningMetric dataclass creation"""
        metric = LearningMetric(
            name="test_metric",
            value=0.85,
            target=0.95,
            trend="improving",
            timestamp=datetime.now(),
            context={"test": "data"}
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 0.85
        assert metric.target == 0.95
        assert metric.trend == "improving"
        assert isinstance(metric.timestamp, datetime)
        assert metric.context == {"test": "data"}
    
    def test_learning_recommendation_creation(self):
        """Test LearningRecommendation dataclass creation"""
        recommendation = LearningRecommendation(
            id="rec_001",
            objective=LearningObjective.PERFORMANCE_OPTIMIZATION,
            recommendation="Implement caching",
            confidence=0.8,
            impact_score=0.7,
            implementation_effort="medium",
            expected_outcome="20% improvement",
            supporting_evidence=["data1", "data2"],
            created_at=datetime.now()
        )
        
        assert recommendation.id == "rec_001"
        assert recommendation.objective == LearningObjective.PERFORMANCE_OPTIMIZATION
        assert recommendation.recommendation == "Implement caching"
        assert recommendation.confidence == 0.8
        assert recommendation.impact_score == 0.7
        assert recommendation.implementation_effort == "medium"
        assert recommendation.expected_outcome == "20% improvement"
        assert recommendation.supporting_evidence == ["data1", "data2"]
        assert isinstance(recommendation.created_at, datetime)
    
    def test_learning_objective_enum(self):
        """Test LearningObjective enum values"""
        assert LearningObjective.PERFORMANCE_OPTIMIZATION.value == "performance_optimization"
        assert LearningObjective.ERROR_REDUCTION.value == "error_reduction"
        assert LearningObjective.EFFICIENCY_IMPROVEMENT.value == "efficiency_improvement"
        assert LearningObjective.QUALITY_ENHANCEMENT.value == "quality_enhancement"
        assert LearningObjective.ADAPTABILITY_INCREASE.value == "adaptability_increase"


class TestLearningEngineIntegration:
    """Integration tests for the learning engine"""
    
    @pytest.mark.asyncio
    async def test_full_learning_cycle(self):
        """Test complete learning cycle from experience to recommendation"""
        mock_experience_db = Mock(spec=ExperienceDatabase)
        mock_experience_db.initialize = AsyncMock()
        mock_experience_db.get_similar_experiences = AsyncMock(return_value=[])
        
        mock_knowledge_graph = Mock(spec=KnowledgeGraph)
        mock_knowledge_graph.initialize = AsyncMock()
        mock_knowledge_graph.add_node = AsyncMock()
        
        engine = await create_learning_engine(mock_experience_db, mock_knowledge_graph)
        
        # Simulate learning from multiple experiences
        experiences = [
            {"success": True, "duration": 100, "complexity": 3},
            {"success": False, "duration": 200, "complexity": 8},
            {"success": True, "duration": 120, "complexity": 4},
            {"success": True, "duration": 80, "complexity": 2}
        ]
        
        for exp in experiences:
            result = await engine.learn_from_experience(exp)
            assert "insights" in result
            assert "learning_metrics" in result
        
        # Check that metrics were updated
        assert "success_rate" in engine.learning_metrics
        
        # Test dashboard generation
        dashboard = await engine.get_learning_dashboard()
        assert dashboard["learning_score"] > 0
        assert len(dashboard["metrics"]) > 0
    
    @pytest.mark.asyncio
    async def test_learning_with_real_pattern_recognition(self):
        """Test learning engine with actual pattern recognition"""
        from tools.pattern_recognition import PatternRecognitionEngine
        
        mock_experience_db = Mock(spec=ExperienceDatabase)
        mock_experience_db.initialize = AsyncMock()
        mock_experience_db.get_similar_experiences = AsyncMock(return_value=[
            {"success": True, "approach": "modular", "duration": 100},
            {"success": True, "approach": "modular", "duration": 120},
            {"success": False, "approach": "monolithic", "duration": 300}
        ])
        
        mock_knowledge_graph = Mock(spec=KnowledgeGraph)
        mock_knowledge_graph.initialize = AsyncMock()
        
        engine = AdaptiveLearningEngine(mock_experience_db, mock_knowledge_graph)
        engine.pattern_engine = PatternRecognitionEngine(mock_experience_db)
        await engine.initialize()
        
        context = {"task_type": "development", "complexity": 5}
        strategy = await engine.get_adaptive_strategy(context)
        
        assert "approach" in strategy
        assert "confidence" in strategy
        assert strategy["confidence"] > 0
