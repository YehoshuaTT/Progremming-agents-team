"""
Pattern Recognition System for Experience Analysis

This module provides advanced pattern recognition capabilities for analyzing
agent experiences and identifying successful patterns, anti-patterns, and
optimization opportunities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from .experience_database import ExperienceDatabase, ExperienceEntry, TaskType, OutcomeType


@dataclass
class PatternMatch:
    """Represents a pattern match result"""
    pattern_id: str
    confidence: float
    relevance: float
    context_similarity: float
    action_similarity: float
    metadata: Dict[str, Any]


@dataclass
class AntiPattern:
    """Represents an anti-pattern (failure pattern)"""
    id: str
    name: str
    description: str
    conditions: List[str]
    failure_actions: List[str]
    failure_rate: float
    frequency: int
    impact_score: float
    avoidance_strategies: List[str]
    tags: List[str]


@dataclass
class OptimizationOpportunity:
    """Represents an optimization opportunity"""
    id: str
    area: str
    description: str
    current_performance: float
    potential_improvement: float
    suggested_actions: List[str]
    confidence: float
    effort_estimate: str
    impact_estimate: str


class PatternRecognitionEngine:
    """
    Advanced pattern recognition engine for experience analysis
    """
    
    def __init__(self, experience_db: ExperienceDatabase):
        self.experience_db = experience_db
        self.logger = logging.getLogger(__name__)
        
        # ML components
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        self.scaler = StandardScaler()
        self.clusterer = None
        
        # Pattern storage
        self.recognized_patterns = {}
        self.anti_patterns = {}
        self.optimization_opportunities = {}
        
        # Analysis cache
        self.analysis_cache = {}
        self.last_analysis_time = None
        
    async def analyze_all_patterns(self) -> Dict[str, Any]:
        """Perform comprehensive pattern analysis"""
        try:
            self.logger.info("Starting comprehensive pattern analysis")
            
            # Get all experiences
            experiences = await self.experience_db.search_experiences(limit=10000)
            
            if len(experiences) < 10:
                self.logger.warning("Insufficient experiences for pattern analysis")
                return {"patterns": [], "anti_patterns": [], "opportunities": []}
            
            # Analyze success patterns
            success_patterns = await self._analyze_success_patterns(experiences)
            
            # Analyze failure patterns (anti-patterns)
            anti_patterns = await self._analyze_failure_patterns(experiences)
            
            # Identify optimization opportunities
            opportunities = await self._identify_optimization_opportunities(experiences)
            
            # Perform clustering analysis
            clusters = await self._perform_clustering_analysis(experiences)
            
            # Update cache
            self.analysis_cache = {
                "patterns": success_patterns,
                "anti_patterns": anti_patterns,
                "opportunities": opportunities,
                "clusters": clusters,
                "analyzed_at": datetime.now(),
                "experience_count": len(experiences)
            }
            
            self.last_analysis_time = datetime.now()
            
            self.logger.info(f"Pattern analysis complete: {len(success_patterns)} patterns, "
                           f"{len(anti_patterns)} anti-patterns, {len(opportunities)} opportunities")
            
            return self.analysis_cache
            
        except Exception as e:
            self.logger.error(f"Error in pattern analysis: {e}")
            return {"patterns": [], "anti_patterns": [], "opportunities": []}
    
    async def _analyze_success_patterns(self, experiences: List[ExperienceEntry]) -> List[Dict[str, Any]]:
        """Analyze successful experiences to identify patterns"""
        success_patterns = []
        
        # Group successful experiences by task type
        successful_by_task = defaultdict(list)
        for exp in experiences:
            if exp.success and exp.quality_score > 0.6:
                successful_by_task[exp.task_type].append(exp)
        
        for task_type, task_experiences in successful_by_task.items():
            if len(task_experiences) < 5:
                continue
                
            # Analyze action sequences
            action_patterns = self._find_action_patterns(task_experiences)
            
            # Analyze context patterns
            context_patterns = self._find_context_patterns(task_experiences)
            
            # Analyze timing patterns
            timing_patterns = self._find_timing_patterns(task_experiences)
            
            # Create comprehensive patterns
            for pattern_type, pattern_data in [
                ("action_sequence", action_patterns),
                ("context_conditions", context_patterns),
                ("timing_optimization", timing_patterns)
            ]:
                if pattern_data:
                    success_patterns.append({
                        "id": f"{task_type.value}_{pattern_type}_{len(success_patterns)}",
                        "task_type": task_type.value,
                        "pattern_type": pattern_type,
                        "description": f"Successful {pattern_type} pattern for {task_type.value}",
                        "pattern_data": pattern_data,
                        "success_rate": self._calculate_success_rate(task_experiences),
                        "frequency": len(task_experiences),
                        "confidence": self._calculate_pattern_confidence(pattern_data, task_experiences),
                        "last_seen": max(exp.created_at for exp in task_experiences),
                        "avg_quality": np.mean([exp.quality_score for exp in task_experiences]),
                        "avg_duration": np.mean([exp.duration for exp in task_experiences])
                    })
        
        return success_patterns
    
    async def _analyze_failure_patterns(self, experiences: List[ExperienceEntry]) -> List[AntiPattern]:
        """Analyze failed experiences to identify anti-patterns"""
        anti_patterns = []
        
        # Group failed experiences
        failed_by_task = defaultdict(list)
        for exp in experiences:
            if not exp.success or exp.quality_score < 0.4:
                failed_by_task[exp.task_type].append(exp)
        
        for task_type, task_experiences in failed_by_task.items():
            if len(task_experiences) < 3:
                continue
                
            # Common failure actions
            failure_actions = self._find_common_failure_actions(task_experiences)
            
            # Common failure conditions
            failure_conditions = self._find_common_failure_conditions(task_experiences)
            
            # Common challenges
            common_challenges = self._find_common_challenges(task_experiences)
            
            if failure_actions or failure_conditions:
                failure_rate = len(task_experiences) / len([
                    exp for exp in experiences 
                    if exp.task_type == task_type
                ])
                
                anti_pattern = AntiPattern(
                    id=f"anti_{task_type.value}_{len(anti_patterns)}",
                    name=f"Common {task_type.value} Failure Pattern",
                    description=f"Frequent failure pattern in {task_type.value} tasks",
                    conditions=failure_conditions,
                    failure_actions=failure_actions,
                    failure_rate=failure_rate,
                    frequency=len(task_experiences),
                    impact_score=self._calculate_impact_score(task_experiences),
                    avoidance_strategies=self._generate_avoidance_strategies(
                        failure_actions, common_challenges
                    ),
                    tags=[task_type.value, "failure", "anti-pattern"]
                )
                
                anti_patterns.append(anti_pattern)
        
        return anti_patterns
    
    async def _identify_optimization_opportunities(
        self, 
        experiences: List[ExperienceEntry]
    ) -> List[OptimizationOpportunity]:
        """Identify optimization opportunities based on experience analysis"""
        opportunities = []
        
        # Analyze performance by task type
        performance_by_task = defaultdict(list)
        for exp in experiences:
            performance_by_task[exp.task_type].append({
                "duration": exp.duration,
                "quality": exp.quality_score,
                "success": exp.success,
                "complexity": exp.complexity_score
            })
        
        for task_type, performances in performance_by_task.items():
            if len(performances) < 10:
                continue
                
            # Duration optimization
            durations = [p["duration"] for p in performances]
            if len(durations) > 5:
                avg_duration = np.mean(durations)
                min_duration = np.min(durations)
                
                if avg_duration > min_duration * 1.5:  # 50% improvement potential
                    opportunities.append(OptimizationOpportunity(
                        id=f"duration_opt_{task_type.value}",
                        area="duration",
                        description=f"Duration optimization for {task_type.value} tasks",
                        current_performance=avg_duration,
                        potential_improvement=(avg_duration - min_duration) / avg_duration,
                        suggested_actions=self._generate_duration_optimizations(
                            task_type, performances
                        ),
                        confidence=0.7,
                        effort_estimate="medium",
                        impact_estimate="high"
                    ))
            
            # Quality optimization
            qualities = [p["quality"] for p in performances if p["quality"] > 0]
            if len(qualities) > 5:
                avg_quality = np.mean(qualities)
                max_quality = np.max(qualities)
                
                if max_quality > avg_quality + 0.2:  # 20% improvement potential
                    opportunities.append(OptimizationOpportunity(
                        id=f"quality_opt_{task_type.value}",
                        area="quality",
                        description=f"Quality optimization for {task_type.value} tasks",
                        current_performance=avg_quality,
                        potential_improvement=(max_quality - avg_quality) / avg_quality,
                        suggested_actions=self._generate_quality_optimizations(
                            task_type, performances
                        ),
                        confidence=0.8,
                        effort_estimate="low",
                        impact_estimate="medium"
                    ))
            
            # Success rate optimization
            success_rate = np.mean([p["success"] for p in performances])
            if success_rate < 0.9:  # Less than 90% success rate
                opportunities.append(OptimizationOpportunity(
                    id=f"success_opt_{task_type.value}",
                    area="success_rate",
                    description=f"Success rate optimization for {task_type.value} tasks",
                    current_performance=success_rate,
                    potential_improvement=(0.95 - success_rate) / success_rate,
                    suggested_actions=self._generate_success_optimizations(
                        task_type, performances
                    ),
                    confidence=0.9,
                    effort_estimate="high",
                    impact_estimate="very_high"
                ))
        
        return opportunities
    
    async def _perform_clustering_analysis(self, experiences: List[ExperienceEntry]) -> Dict[str, Any]:
        """Perform clustering analysis to identify experience groups"""
        try:
            if len(experiences) < 20:
                return {"clusters": [], "analysis": "Insufficient data for clustering"}
            
            # Prepare feature matrix
            features = []
            for exp in experiences:
                feature_vector = [
                    exp.duration,
                    exp.quality_score,
                    exp.complexity_score,
                    exp.impact_score,
                    1.0 if exp.success else 0.0,
                    len(exp.actions_taken),
                    len(exp.challenges),
                    len(exp.lessons_learned)
                ]
                features.append(feature_vector)
            
            features = np.array(features)
            features_scaled = self.scaler.fit_transform(features)
            
            # Perform DBSCAN clustering
            dbscan = DBSCAN(eps=0.5, min_samples=5)
            cluster_labels = dbscan.fit_predict(features_scaled)
            
            # Analyze clusters
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(experiences[i])
            
            cluster_analysis = {}
            for label, cluster_experiences in clusters.items():
                if label == -1:  # Noise cluster
                    continue
                    
                cluster_analysis[f"cluster_{label}"] = {
                    "size": len(cluster_experiences),
                    "avg_duration": np.mean([exp.duration for exp in cluster_experiences]),
                    "avg_quality": np.mean([exp.quality_score for exp in cluster_experiences]),
                    "success_rate": np.mean([exp.success for exp in cluster_experiences]),
                    "common_task_types": self._get_common_task_types(cluster_experiences),
                    "common_patterns": self._extract_cluster_patterns(cluster_experiences)
                }
            
            return {
                "clusters": cluster_analysis,
                "total_clusters": len([l for l in set(cluster_labels) if l != -1]),
                "noise_points": len([l for l in cluster_labels if l == -1]),
                "analysis": "Clustering analysis complete"
            }
            
        except Exception as e:
            self.logger.error(f"Error in clustering analysis: {e}")
            return {"clusters": [], "analysis": f"Error: {e}"}
    
    def _find_action_patterns(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find common action patterns in successful experiences"""
        action_sequences = []
        for exp in experiences:
            if len(exp.actions_taken) >= 2:
                # Create action bigrams and trigrams
                actions = exp.actions_taken
                for i in range(len(actions) - 1):
                    action_sequences.append(f"{actions[i]} -> {actions[i+1]}")
                if len(actions) >= 3:
                    for i in range(len(actions) - 2):
                        action_sequences.append(f"{actions[i]} -> {actions[i+1]} -> {actions[i+2]}")
        
        # Count frequencies
        sequence_counts = Counter(action_sequences)
        
        # Return sequences that appear in at least 30% of experiences
        min_count = max(1, len(experiences) * 0.3)
        return [seq for seq, count in sequence_counts.items() if count >= min_count]
    
    def _find_context_patterns(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find common context patterns in successful experiences"""
        context_patterns = []
        
        # Extract common context keys and values
        common_contexts = defaultdict(Counter)
        for exp in experiences:
            for key, value in exp.context.items():
                common_contexts[key][str(value)] += 1
        
        # Find patterns that appear in at least 40% of experiences
        min_count = max(1, len(experiences) * 0.4)
        for key, value_counts in common_contexts.items():
            for value, count in value_counts.items():
                if count >= min_count:
                    context_patterns.append(f"{key}={value}")
        
        return context_patterns
    
    def _find_timing_patterns(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find timing patterns in successful experiences"""
        durations = [exp.duration for exp in experiences]
        
        if not durations:
            return []
            
        avg_duration = np.mean(durations)
        std_duration = np.std(durations)
        
        patterns = []
        
        # Fast completion pattern
        fast_threshold = avg_duration - std_duration
        fast_count = len([d for d in durations if d < fast_threshold])
        if fast_count >= len(experiences) * 0.2:
            patterns.append(f"fast_completion_under_{fast_threshold:.1f}s")
        
        # Optimal duration range
        optimal_min = avg_duration - 0.5 * std_duration
        optimal_max = avg_duration + 0.5 * std_duration
        optimal_count = len([d for d in durations if optimal_min <= d <= optimal_max])
        if optimal_count >= len(experiences) * 0.4:
            patterns.append(f"optimal_duration_{optimal_min:.1f}s_to_{optimal_max:.1f}s")
        
        return patterns
    
    def _find_common_failure_actions(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find common actions that lead to failure"""
        action_counts = Counter()
        
        for exp in experiences:
            for action in exp.actions_taken:
                action_counts[action] += 1
        
        # Return actions that appear in at least 25% of failed experiences
        min_count = max(1, len(experiences) * 0.25)
        return [action for action, count in action_counts.items() if count >= min_count]
    
    def _find_common_failure_conditions(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find common conditions that lead to failure"""
        condition_counts = Counter()
        
        for exp in experiences:
            for key, value in exp.context.items():
                condition_counts[f"{key}={value}"] += 1
        
        # Return conditions that appear in at least 30% of failed experiences
        min_count = max(1, len(experiences) * 0.3)
        return [condition for condition, count in condition_counts.items() if count >= min_count]
    
    def _find_common_challenges(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find common challenges in experiences"""
        challenge_counts = Counter()
        
        for exp in experiences:
            for challenge in exp.challenges:
                challenge_counts[challenge] += 1
        
        # Return challenges that appear in at least 20% of experiences
        min_count = max(1, len(experiences) * 0.2)
        return [challenge for challenge, count in challenge_counts.items() if count >= min_count]
    
    def _calculate_success_rate(self, experiences: List[ExperienceEntry]) -> float:
        """Calculate success rate for a group of experiences"""
        if not experiences:
            return 0.0
        return sum(1 for exp in experiences if exp.success) / len(experiences)
    
    def _calculate_pattern_confidence(self, pattern_data: List[str], experiences: List[ExperienceEntry]) -> float:
        """Calculate confidence score for a pattern"""
        if not pattern_data or not experiences:
            return 0.0
        
        # Base confidence on frequency and success rate
        frequency_score = min(1.0, len(experiences) / 50)  # More experiences = higher confidence
        success_score = self._calculate_success_rate(experiences)
        pattern_strength = min(1.0, len(pattern_data) / 5)  # More patterns = higher confidence
        
        return (frequency_score + success_score + pattern_strength) / 3
    
    def _calculate_impact_score(self, experiences: List[ExperienceEntry]) -> float:
        """Calculate impact score for anti-patterns"""
        if not experiences:
            return 0.0
        
        # Consider duration, complexity, and failure frequency
        avg_duration = np.mean([exp.duration for exp in experiences])
        avg_complexity = np.mean([exp.complexity_score for exp in experiences])
        failure_frequency = len(experiences)
        
        # Normalize and combine
        duration_impact = min(1.0, avg_duration / 100)  # Normalize to 100s
        complexity_impact = avg_complexity
        frequency_impact = min(1.0, failure_frequency / 20)  # Normalize to 20 failures
        
        return (duration_impact + complexity_impact + frequency_impact) / 3
    
    def _generate_avoidance_strategies(self, failure_actions: List[str], challenges: List[str]) -> List[str]:
        """Generate avoidance strategies for anti-patterns"""
        strategies = []
        
        # Generic strategies based on common failure patterns
        if any("rush" in action.lower() for action in failure_actions):
            strategies.append("Take time to plan before executing")
        
        if any("skip" in action.lower() for action in failure_actions):
            strategies.append("Follow complete process steps")
        
        if any("complex" in challenge.lower() for challenge in challenges):
            strategies.append("Break down complex tasks into smaller steps")
        
        if any("test" in challenge.lower() for challenge in challenges):
            strategies.append("Implement thorough testing procedures")
        
        # Add generic best practices
        strategies.extend([
            "Validate inputs before processing",
            "Use incremental development approach",
            "Implement proper error handling",
            "Document assumptions and decisions"
        ])
        
        return strategies[:5]  # Return top 5 strategies
    
    def _generate_duration_optimizations(self, task_type: TaskType, performances: List[Dict]) -> List[str]:
        """Generate duration optimization suggestions"""
        optimizations = [
            "Implement parallel processing where possible",
            "Cache frequently used computations",
            "Optimize database queries and data access",
            "Use more efficient algorithms",
            "Reduce unnecessary validation steps"
        ]
        
        # Task-specific optimizations
        if task_type == TaskType.CODE_GENERATION:
            optimizations.extend([
                "Use code templates and snippets",
                "Implement automated code generation",
                "Optimize compilation and build processes"
            ])
        elif task_type == TaskType.TESTING:
            optimizations.extend([
                "Implement test parallelization",
                "Use smart test selection",
                "Optimize test data setup"
            ])
        
        return optimizations[:5]
    
    def _generate_quality_optimizations(self, task_type: TaskType, performances: List[Dict]) -> List[str]:
        """Generate quality optimization suggestions"""
        optimizations = [
            "Implement comprehensive code review process",
            "Add automated quality checks",
            "Improve validation and verification steps",
            "Enhance documentation and comments",
            "Use proven design patterns"
        ]
        
        return optimizations[:5]
    
    def _generate_success_optimizations(self, task_type: TaskType, performances: List[Dict]) -> List[str]:
        """Generate success rate optimization suggestions"""
        optimizations = [
            "Implement robust error handling",
            "Add comprehensive input validation",
            "Use defensive programming techniques",
            "Implement proper logging and monitoring",
            "Add automated rollback mechanisms"
        ]
        
        return optimizations[:5]
    
    def _get_common_task_types(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Get common task types in a cluster"""
        task_counts = Counter(exp.task_type.value for exp in experiences)
        return [task for task, count in task_counts.most_common(3)]
    
    def _extract_cluster_patterns(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Extract patterns from a cluster of experiences"""
        patterns = []
        
        # Common success patterns
        if np.mean([exp.success for exp in experiences]) > 0.8:
            patterns.append("high_success_rate")
        
        # Duration patterns
        durations = [exp.duration for exp in experiences]
        if np.std(durations) < np.mean(durations) * 0.2:
            patterns.append("consistent_duration")
        
        # Quality patterns
        qualities = [exp.quality_score for exp in experiences if exp.quality_score > 0]
        if qualities and np.mean(qualities) > 0.8:
            patterns.append("high_quality")
        
        return patterns


# Example usage
async def main():
    """Example usage of the Pattern Recognition Engine"""
    from .experience_database import ExperienceDatabase
    
    # Initialize
    experience_db = ExperienceDatabase()
    await experience_db.initialize()
    
    pattern_engine = PatternRecognitionEngine(experience_db)
    
    # Analyze patterns
    analysis = await pattern_engine.analyze_all_patterns()
    
    print("Pattern Analysis Results:")
    print(f"Success Patterns: {len(analysis['patterns'])}")
    print(f"Anti-Patterns: {len(analysis['anti_patterns'])}")
    print(f"Optimization Opportunities: {len(analysis['opportunities'])}")


if __name__ == "__main__":
    asyncio.run(main())
