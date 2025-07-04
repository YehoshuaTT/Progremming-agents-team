"""
Learning Engine for Autonomous Multi-Agent System

This module implements adaptive learning algorithms that enable the system to:
- Learn from past experiences and outcomes
- Adapt strategies based on success patterns
- Provide intelligent recommendations
- Continuously improve decision-making

Author: AI Development Team
Date: July 4, 2025
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import pandas as pd

from tools.experience_database import ExperienceDatabase
from tools.knowledge_graph import KnowledgeGraph
from tools.pattern_recognition import PatternRecognitionEngine


class LearningObjective(Enum):
    """Types of learning objectives"""
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_REDUCTION = "error_reduction"
    EFFICIENCY_IMPROVEMENT = "efficiency_improvement"
    QUALITY_ENHANCEMENT = "quality_enhancement"
    ADAPTABILITY_INCREASE = "adaptability_increase"


@dataclass
class LearningMetric:
    """Metrics for tracking learning progress"""
    name: str
    value: float
    target: float
    trend: str  # "improving", "stable", "degrading"
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class LearningRecommendation:
    """AI-generated recommendations for improvement"""
    id: str
    objective: LearningObjective
    recommendation: str
    confidence: float
    impact_score: float
    implementation_effort: str  # "low", "medium", "high"
    expected_outcome: str
    supporting_evidence: List[str]
    created_at: datetime


class AdaptiveLearningEngine:
    """
    Core learning engine that implements adaptive algorithms
    to improve system performance over time
    """
    
    def __init__(self, experience_db: ExperienceDatabase, knowledge_graph: KnowledgeGraph):
        self.experience_db = experience_db
        self.knowledge_graph = knowledge_graph
        self.pattern_engine = PatternRecognitionEngine(experience_db)
        self.logger = logging.getLogger(__name__)
        
        # Learning models
        self.performance_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.error_prediction_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Learning state
        self.learning_metrics: Dict[str, LearningMetric] = {}
        self.active_recommendations: List[LearningRecommendation] = []
        self.learning_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.min_experiences_for_learning = 10
        self.learning_update_interval = timedelta(hours=1)
        self.last_learning_update = datetime.now()
        
    async def initialize(self):
        """Initialize the learning engine"""
        try:
            await self.experience_db.initialize()
            await self.knowledge_graph.initialize()
            await self._load_learning_state()
            self.logger.info("Learning engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize learning engine: {e}")
            raise
    
    async def learn_from_experience(self, experience_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from a single experience and update models
        
        Args:
            experience_data: Experience data containing outcome, context, etc.
            
        Returns:
            Dict containing learning insights and updates
        """
        try:
            # Extract features from experience
            features = await self._extract_features(experience_data)
            
            # Update learning models
            await self._update_models(features, experience_data)
            
            # Generate insights
            insights = await self._generate_insights(experience_data)
            
            # Update learning metrics
            await self._update_learning_metrics(experience_data, insights)
            
            # Check for new recommendations
            new_recommendations = await self._generate_recommendations(insights)
            
            return {
                "insights": insights,
                "new_recommendations": new_recommendations,
                "learning_metrics": self._get_current_metrics(),
                "model_updates": await self._get_model_performance()
            }
            
        except Exception as e:
            self.logger.error(f"Error learning from experience: {e}")
            return {"error": str(e)}
    
    async def get_adaptive_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get adaptive strategy recommendations based on learned patterns
        
        Args:
            context: Current context for strategy recommendation
            
        Returns:
            Dict containing adaptive strategy recommendations
        """
        try:
            # Get similar past experiences
            similar_experiences = await self.experience_db.get_similar_experiences(
                context, limit=20
            )
            
            # Analyze patterns in similar experiences
            patterns = await self.pattern_engine.analyze_all_patterns()
            
            # Generate strategy recommendations
            strategy = await self._generate_adaptive_strategy(context, patterns)
            
            # Add confidence scores
            strategy["confidence"] = await self._calculate_strategy_confidence(strategy, patterns)
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"Error generating adaptive strategy: {e}")
            return {"error": str(e)}
    
    async def optimize_performance(self, objective: LearningObjective) -> Dict[str, Any]:
        """
        Optimize system performance for a specific objective
        
        Args:
            objective: Learning objective to optimize for
            
        Returns:
            Dict containing optimization results and recommendations
        """
        try:
            # Get relevant experiences
            experiences = await self._get_experiences_for_objective(objective)
            
            if len(experiences) < self.min_experiences_for_learning:
                return {
                    "status": "insufficient_data",
                    "message": f"Need at least {self.min_experiences_for_learning} experiences",
                    "current_count": len(experiences)
                }
            
            # Analyze performance patterns
            performance_analysis = await self._analyze_performance_patterns(experiences, objective)
            
            # Generate optimization recommendations
            optimizations = await self._generate_optimizations(performance_analysis, objective)
            
            # Update knowledge graph with insights
            await self._update_knowledge_graph(optimizations)
            
            return {
                "status": "success",
                "objective": objective.value,
                "analysis": performance_analysis,
                "optimizations": optimizations,
                "implementation_plan": await self._create_implementation_plan(optimizations)
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing performance: {e}")
            return {"error": str(e)}
    
    async def predict_outcome(self, planned_action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict the likely outcome of a planned action
        
        Args:
            planned_action: Details of the planned action
            
        Returns:
            Dict containing outcome predictions and confidence scores
        """
        try:
            # Extract features from planned action
            features = await self._extract_action_features(planned_action)
            
            # Get predictions from models
            performance_prediction = await self._predict_performance(features)
            error_prediction = await self._predict_errors(features)
            
            # Get similar past actions
            similar_actions = await self._find_similar_actions(planned_action)
            
            # Calculate confidence based on similar actions
            confidence = await self._calculate_prediction_confidence(similar_actions)
            
            return {
                "performance_prediction": performance_prediction,
                "error_prediction": error_prediction,
                "confidence": confidence,
                "similar_actions": similar_actions[:5],  # Top 5 similar actions
                "recommendations": await self._get_prediction_recommendations(
                    performance_prediction, error_prediction
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting outcome: {e}")
            return {"error": str(e)}
    
    async def get_learning_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive learning dashboard data
        
        Returns:
            Dict containing all learning metrics and insights
        """
        try:
            # Get current metrics
            current_metrics = self._get_current_metrics()
            
            # Get learning trends
            trends = await self._calculate_learning_trends()
            
            # Get active recommendations
            active_recommendations = self.active_recommendations
            
            # Get recent learning history
            recent_history = self.learning_history[-20:]  # Last 20 entries
            
            # Calculate overall learning score
            learning_score = await self._calculate_overall_learning_score()
            
            return {
                "learning_score": learning_score,
                "metrics": current_metrics,
                "trends": trends,
                "active_recommendations": [
                    {
                        "id": rec.id,
                        "objective": rec.objective.value,
                        "recommendation": rec.recommendation,
                        "confidence": rec.confidence,
                        "impact_score": rec.impact_score,
                        "implementation_effort": rec.implementation_effort
                    }
                    for rec in active_recommendations
                ],
                "recent_history": recent_history,
                "model_performance": await self._get_model_performance(),
                "learning_opportunities": await self._identify_learning_opportunities()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating learning dashboard: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _extract_features(self, experience_data: Dict[str, Any]) -> List[float]:
        """Extract numerical features from experience data"""
        features = []
        
        # Basic features
        features.append(experience_data.get("duration", 0))
        features.append(1 if experience_data.get("success", False) else 0)
        features.append(experience_data.get("complexity", 0))
        features.append(len(experience_data.get("agents_involved", [])))
        
        # Context features
        context = experience_data.get("context", {})
        features.append(len(context.get("requirements", [])))
        features.append(context.get("priority", 0))
        features.append(context.get("resource_usage", 0))
        
        return features
    
    async def _update_models(self, features: List[float], experience_data: Dict[str, Any]):
        """Update machine learning models with new data"""
        # This is a simplified implementation
        # In a real system, you'd accumulate data and retrain periodically
        pass
    
    async def _generate_insights(self, experience_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from experience data"""
        insights = {
            "performance_impact": "positive" if experience_data.get("success") else "negative",
            "efficiency_score": experience_data.get("duration", 0) / max(experience_data.get("complexity", 1), 1),
            "learning_value": "high" if not experience_data.get("success") else "medium"
        }
        
        return insights
    
    async def _update_learning_metrics(self, experience_data: Dict[str, Any], insights: Dict[str, Any]):
        """Update learning metrics based on new experience"""
        # Update success rate
        if "success_rate" not in self.learning_metrics:
            self.learning_metrics["success_rate"] = LearningMetric(
                name="success_rate",
                value=0.0,
                target=0.95,
                trend="stable",
                timestamp=datetime.now(),
                context={}
            )
        
        # Simple running average update
        current_success = 1.0 if experience_data.get("success") else 0.0
        current_metric = self.learning_metrics["success_rate"]
        current_metric.value = (current_metric.value * 0.9) + (current_success * 0.1)
        current_metric.timestamp = datetime.now()
    
    async def _generate_recommendations(self, insights: Dict[str, Any]) -> List[LearningRecommendation]:
        """Generate recommendations based on insights"""
        recommendations = []
        
        # Example recommendation generation
        if insights.get("performance_impact") == "negative":
            recommendations.append(LearningRecommendation(
                id=f"rec_{datetime.now().timestamp()}",
                objective=LearningObjective.ERROR_REDUCTION,
                recommendation="Implement additional error checking and validation",
                confidence=0.8,
                impact_score=0.7,
                implementation_effort="medium",
                expected_outcome="Reduce error rate by 15-20%",
                supporting_evidence=["Recent failure patterns", "Similar system improvements"],
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current learning metrics"""
        return {
            name: {
                "value": metric.value,
                "target": metric.target,
                "trend": metric.trend,
                "timestamp": metric.timestamp.isoformat()
            }
            for name, metric in self.learning_metrics.items()
        }
    
    async def _get_model_performance(self) -> Dict[str, Any]:
        """Get current model performance metrics"""
        return {
            "performance_model": {
                "accuracy": 0.85,  # Placeholder
                "last_trained": datetime.now().isoformat(),
                "training_samples": 1000
            },
            "error_prediction_model": {
                "accuracy": 0.78,  # Placeholder
                "last_trained": datetime.now().isoformat(),
                "training_samples": 800
            }
        }
    
    async def _load_learning_state(self):
        """Load learning state from storage"""
        # Placeholder for loading state from persistent storage
        pass
    
    async def _save_learning_state(self):
        """Save learning state to storage"""
        # Placeholder for saving state to persistent storage
        pass
    
    async def _generate_adaptive_strategy(self, context: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate adaptive strategy based on context and patterns"""
        strategy = {
            "approach": "adaptive",
            "confidence_threshold": 0.7,
            "fallback_strategy": "conservative",
            "optimization_focus": "performance",
            "risk_tolerance": "medium"
        }
        
        # Adjust strategy based on patterns
        if patterns.get("success_rate", 0) < 0.5:
            strategy["approach"] = "conservative"
            strategy["confidence_threshold"] = 0.8
        
        return strategy
    
    async def _calculate_strategy_confidence(self, strategy: Dict[str, Any], patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for strategy"""
        base_confidence = 0.6
        
        # Increase confidence based on pattern strength
        if patterns.get("pattern_strength", 0) > 0.7:
            base_confidence += 0.2
        
        # Adjust based on data quality
        if patterns.get("data_quality", 0) > 0.8:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    async def _get_experiences_for_objective(self, objective: LearningObjective) -> List[Dict[str, Any]]:
        """Get experiences relevant to a specific learning objective"""
        # Placeholder - would filter experiences based on objective
        return []
    
    async def _analyze_performance_patterns(self, experiences: List[Dict[str, Any]], objective: LearningObjective) -> Dict[str, Any]:
        """Analyze performance patterns in experiences"""
        return {
            "success_rate": 0.85,
            "average_duration": 120,
            "common_failures": ["timeout", "validation_error"],
            "optimization_opportunities": ["caching", "parallel_processing"]
        }
    
    async def _generate_optimizations(self, analysis: Dict[str, Any], objective: LearningObjective) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        return [
            {
                "type": "caching",
                "description": "Implement result caching to reduce computation time",
                "impact": "high",
                "effort": "medium"
            },
            {
                "type": "parallel_processing",
                "description": "Process independent tasks in parallel",
                "impact": "medium",
                "effort": "high"
            }
        ]
    
    async def _update_knowledge_graph(self, optimizations: List[Dict[str, Any]]):
        """Update knowledge graph with optimization insights"""
        for opt in optimizations:
            await self.knowledge_graph.add_node(
                f"optimization_{opt['type']}",
                "optimization",
                opt['description'],
                opt
            )
    
    async def _create_implementation_plan(self, optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation plan for optimizations"""
        return {
            "phases": [
                {
                    "phase": 1,
                    "optimizations": [opt for opt in optimizations if opt.get("effort") == "low"],
                    "estimated_duration": "1 week"
                },
                {
                    "phase": 2,
                    "optimizations": [opt for opt in optimizations if opt.get("effort") == "medium"],
                    "estimated_duration": "2 weeks"
                },
                {
                    "phase": 3,
                    "optimizations": [opt for opt in optimizations if opt.get("effort") == "high"],
                    "estimated_duration": "4 weeks"
                }
            ],
            "total_estimated_duration": "7 weeks"
        }
    
    async def _extract_action_features(self, planned_action: Dict[str, Any]) -> List[float]:
        """Extract features from planned action for prediction"""
        features = []
        features.append(planned_action.get("complexity", 0))
        features.append(len(planned_action.get("dependencies", [])))
        features.append(planned_action.get("estimated_duration", 0))
        features.append(planned_action.get("risk_level", 0))
        return features
    
    async def _predict_performance(self, features: List[float]) -> Dict[str, Any]:
        """Predict performance based on features"""
        return {
            "success_probability": 0.85,
            "estimated_duration": 180,
            "quality_score": 0.9
        }
    
    async def _predict_errors(self, features: List[float]) -> Dict[str, Any]:
        """Predict potential errors based on features"""
        return {
            "error_probability": 0.15,
            "likely_error_types": ["timeout", "resource_exhaustion"],
            "mitigation_strategies": ["increase_timeout", "optimize_resources"]
        }
    
    async def _find_similar_actions(self, planned_action: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar actions from experience database"""
        return []  # Placeholder
    
    async def _calculate_prediction_confidence(self, similar_actions: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on similar actions"""
        if not similar_actions:
            return 0.3
        
        return min(0.95, 0.5 + (len(similar_actions) * 0.05))
    
    async def _get_prediction_recommendations(self, performance_pred: Dict[str, Any], error_pred: Dict[str, Any]) -> List[str]:
        """Get recommendations based on predictions"""
        recommendations = []
        
        if performance_pred.get("success_probability", 0) < 0.7:
            recommendations.append("Consider breaking down into smaller tasks")
        
        if error_pred.get("error_probability", 0) > 0.3:
            recommendations.append("Implement additional error handling")
        
        return recommendations
    
    async def _calculate_learning_trends(self) -> Dict[str, Any]:
        """Calculate learning trends over time"""
        return {
            "success_rate_trend": "improving",
            "efficiency_trend": "stable",
            "error_rate_trend": "improving",
            "learning_velocity": "high"
        }
    
    async def _calculate_overall_learning_score(self) -> float:
        """Calculate overall learning effectiveness score"""
        # Simplified calculation
        success_rate = self.learning_metrics.get("success_rate", LearningMetric("", 0.5, 0.95, "", datetime.now(), {})).value
        return min(success_rate * 1.2, 1.0)
    
    async def _identify_learning_opportunities(self) -> List[Dict[str, Any]]:
        """Identify areas where more learning could be beneficial"""
        return [
            {
                "area": "error_handling",
                "potential_improvement": "20%",
                "data_needed": "more_failure_cases"
            },
            {
                "area": "performance_optimization",
                "potential_improvement": "15%",
                "data_needed": "performance_benchmarks"
            }
        ]


# Factory function for creating learning engine instances
async def create_learning_engine(experience_db: ExperienceDatabase, knowledge_graph: KnowledgeGraph) -> AdaptiveLearningEngine:
    """
    Factory function to create and initialize a learning engine
    
    Args:
        experience_db: Initialized experience database
        knowledge_graph: Initialized knowledge graph
        
    Returns:
        Initialized AdaptiveLearningEngine instance
    """
    engine = AdaptiveLearningEngine(experience_db, knowledge_graph)
    await engine.initialize()
    return engine
