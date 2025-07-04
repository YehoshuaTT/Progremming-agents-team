"""
Experience Database System for Agent Learning

This module implements a comprehensive experience database that tracks agent
actions, outcomes, and learning patterns. It provides analytics and pattern
recognition capabilities to improve future agent performance.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import aiosqlite
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans


class TaskType(Enum):
    """Task types for experience categorization"""
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PLANNING = "planning"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"


class OutcomeType(Enum):
    """Outcome types for experience classification"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ExperienceEntry:
    """Data class for experience entries"""
    id: str
    agent_id: str
    task_type: TaskType
    context: Dict[str, Any]
    actions_taken: List[str]
    outcome: OutcomeType
    success: bool
    duration: float  # in seconds
    challenges: List[str]
    lessons_learned: List[str]
    created_at: datetime
    project_id: str
    workflow_id: str
    quality_score: float = 0.0
    complexity_score: float = 0.0
    impact_score: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExperiencePattern:
    """Data class for recognized patterns"""
    id: str
    pattern_type: str
    description: str
    conditions: List[str]
    actions: List[str]
    success_rate: float
    frequency: int
    last_seen: datetime
    confidence: float
    tags: List[str]


class ExperienceDatabase:
    """
    Advanced experience database for agent learning and pattern recognition
    """
    
    def __init__(self, db_path: str = "cache/experience_database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.context_vectors = None
        self.experience_cache = {}
        
    async def initialize(self):
        """Initialize the database with required tables"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    context TEXT NOT NULL,
                    actions_taken TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    duration REAL NOT NULL,
                    challenges TEXT NOT NULL,
                    lessons_learned TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    project_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    quality_score REAL DEFAULT 0.0,
                    complexity_score REAL DEFAULT 0.0,
                    impact_score REAL DEFAULT 0.0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    success_rate REAL NOT NULL,
                    frequency INTEGER NOT NULL,
                    last_seen TIMESTAMP NOT NULL,
                    confidence REAL NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS experience_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experience_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (experience_id) REFERENCES experiences (id)
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON experiences(agent_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_task_type ON experiences(task_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_outcome ON experiences(outcome)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON experiences(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_success ON experiences(success)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_pattern_type ON patterns(pattern_type)")
            
            await db.commit()
            
        self.logger.info("Experience database initialized")
    
    async def log_experience(self, experience: ExperienceEntry) -> bool:
        """Log a new experience entry"""
        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("""
                    INSERT INTO experiences (
                        id, agent_id, task_type, context, actions_taken, outcome,
                        success, duration, challenges, lessons_learned, created_at,
                        project_id, workflow_id, quality_score, complexity_score,
                        impact_score, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    experience.id,
                    experience.agent_id,
                    experience.task_type.value,
                    json.dumps(experience.context),
                    json.dumps(experience.actions_taken),
                    experience.outcome.value,
                    experience.success,
                    experience.duration,
                    json.dumps(experience.challenges),
                    json.dumps(experience.lessons_learned),
                    experience.created_at.isoformat(),
                    experience.project_id,
                    experience.workflow_id,
                    experience.quality_score,
                    experience.complexity_score,
                    experience.impact_score,
                    json.dumps(experience.metadata)
                ))
                await db.commit()
                
            # Update cache
            self.experience_cache[experience.id] = experience
            
            # Trigger pattern recognition
            await self._update_patterns(experience)
            
            self.logger.info(f"Logged experience: {experience.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging experience: {e}")
            return False
    
    async def get_experience(self, experience_id: str) -> Optional[ExperienceEntry]:
        """Get a specific experience by ID"""
        # Check cache first
        if experience_id in self.experience_cache:
            return self.experience_cache[experience_id]
            
        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                cursor = await db.execute("""
                    SELECT * FROM experiences WHERE id = ?
                """, (experience_id,))
                row = await cursor.fetchone()
                
                if row:
                    experience = self._row_to_experience(row)
                    self.experience_cache[experience_id] = experience
                    return experience
                    
        except Exception as e:
            self.logger.error(f"Error retrieving experience: {e}")
            
        return None
    
    async def search_experiences(
        self,
        agent_id: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        outcome: Optional[OutcomeType] = None,
        success: Optional[bool] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ExperienceEntry]:
        """Search experiences with filters"""
        conditions = []
        params = []
        
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
            
        if task_type:
            conditions.append("task_type = ?")
            params.append(task_type.value)
            
        if outcome:
            conditions.append("outcome = ?")
            params.append(outcome.value)
            
        if success is not None:
            conditions.append("success = ?")
            params.append(success)
            
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                cursor = await db.execute(f"""
                    SELECT * FROM experiences 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, params + [limit, offset])
                
                rows = await cursor.fetchall()
                return [self._row_to_experience(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error searching experiences: {e}")
            return []
    
    async def get_similar_experiences(
        self,
        context: Dict[str, Any],
        task_type: Optional[TaskType] = None,
        limit: int = 10
    ) -> List[Tuple[ExperienceEntry, float]]:
        """Find similar experiences based on context similarity"""
        try:
            # Get all experiences of the same task type
            experiences = await self.search_experiences(
                task_type=task_type,
                limit=1000
            )
            
            if not experiences:
                return []
                
            # Prepare context vectors
            context_text = json.dumps(context)
            experience_texts = [json.dumps(exp.context) for exp in experiences]
            all_texts = [context_text] + experience_texts
            
            # Compute similarity
            vectors = self.vectorizer.fit_transform(all_texts)
            similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
            
            # Sort by similarity
            similar_indices = np.argsort(similarities)[::-1][:limit]
            
            return [
                (experiences[i], similarities[i])
                for i in similar_indices
                if similarities[i] > 0.1  # Minimum similarity threshold
            ]
            
        except Exception as e:
            self.logger.error(f"Error finding similar experiences: {e}")
            return []
    
    async def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for an agent"""
        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                # Basic stats
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_experiences,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                        AVG(duration) as avg_duration,
                        AVG(quality_score) as avg_quality,
                        AVG(complexity_score) as avg_complexity,
                        AVG(impact_score) as avg_impact
                    FROM experiences 
                    WHERE agent_id = ?
                """, (agent_id,))
                
                basic_stats = await cursor.fetchone()
                
                # Task type distribution
                cursor = await db.execute("""
                    SELECT task_type, COUNT(*) as count
                    FROM experiences 
                    WHERE agent_id = ?
                    GROUP BY task_type
                """, (agent_id,))
                
                task_distribution = dict(await cursor.fetchall())
                
                # Outcome distribution
                cursor = await db.execute("""
                    SELECT outcome, COUNT(*) as count
                    FROM experiences 
                    WHERE agent_id = ?
                    GROUP BY outcome
                """, (agent_id,))
                
                outcome_distribution = dict(await cursor.fetchall())
                
                # Recent performance trend
                cursor = await db.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as experiences,
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM experiences 
                    WHERE agent_id = ? AND created_at >= datetime('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """, (agent_id,))
                
                performance_trend = [
                    {"date": row[0], "experiences": row[1], "success_rate": row[2]}
                    for row in await cursor.fetchall()
                ]
                
                return {
                    "agent_id": agent_id,
                    "total_experiences": basic_stats[0] or 0,
                    "success_count": basic_stats[1] or 0,
                    "success_rate": (basic_stats[1] or 0) / max(basic_stats[0] or 1, 1),
                    "avg_duration": basic_stats[2] or 0,
                    "avg_quality_score": basic_stats[3] or 0,
                    "avg_complexity_score": basic_stats[4] or 0,
                    "avg_impact_score": basic_stats[5] or 0,
                    "task_distribution": task_distribution,
                    "outcome_distribution": outcome_distribution,
                    "performance_trend": performance_trend
                }
                
        except Exception as e:
            self.logger.error(f"Error getting agent statistics: {e}")
            return {}
    
    async def recognize_patterns(self, min_frequency: int = 5) -> List[ExperiencePattern]:
        """Recognize patterns in experiences using clustering and analysis"""
        try:
            # Get all experiences
            experiences = await self.search_experiences(limit=10000)
            
            if len(experiences) < min_frequency:
                return []
                
            # Group by task type and outcome
            groups = {}
            for exp in experiences:
                key = (exp.task_type.value, exp.outcome.value)
                if key not in groups:
                    groups[key] = []
                groups[key].append(exp)
            
            patterns = []
            
            for (task_type, outcome), group_experiences in groups.items():
                if len(group_experiences) < min_frequency:
                    continue
                    
                # Analyze common patterns
                common_actions = self._find_common_actions(group_experiences)
                common_challenges = self._find_common_challenges(group_experiences)
                
                if common_actions:
                    success_rate = sum(1 for exp in group_experiences if exp.success) / len(group_experiences)
                    
                    pattern = ExperiencePattern(
                        id=f"pattern_{task_type}_{outcome}_{len(patterns)}",
                        pattern_type=f"{task_type}_{outcome}",
                        description=f"Common pattern for {task_type} tasks with {outcome} outcome",
                        conditions=common_challenges,
                        actions=common_actions,
                        success_rate=success_rate,
                        frequency=len(group_experiences),
                        last_seen=max(exp.created_at for exp in group_experiences),
                        confidence=min(0.9, success_rate * (len(group_experiences) / 10)),
                        tags=[task_type, outcome]
                    )
                    patterns.append(pattern)
            
            # Store patterns
            await self._store_patterns(patterns)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error recognizing patterns: {e}")
            return []
    
    async def get_recommendations(
        self,
        context: Dict[str, Any],
        task_type: TaskType
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on similar experiences and patterns"""
        recommendations = []
        
        try:
            # Get similar experiences
            similar_experiences = await self.get_similar_experiences(
                context=context,
                task_type=task_type,
                limit=5
            )
            
            # Get relevant patterns
            patterns = await self.get_patterns_by_type(f"{task_type.value}_success")
            
            # Generate recommendations from similar experiences
            for exp, similarity in similar_experiences:
                if exp.success and similarity > 0.5:
                    recommendations.append({
                        "type": "experience",
                        "confidence": similarity,
                        "title": f"Similar successful {task_type.value} experience",
                        "description": f"Based on experience {exp.id}",
                        "actions": exp.actions_taken,
                        "lessons": exp.lessons_learned,
                        "source": exp.id
                    })
            
            # Generate recommendations from patterns
            for pattern in patterns:
                if pattern.success_rate > 0.7:
                    recommendations.append({
                        "type": "pattern",
                        "confidence": pattern.confidence,
                        "title": f"Proven pattern: {pattern.description}",
                        "description": f"Used successfully {pattern.frequency} times",
                        "actions": pattern.actions,
                        "conditions": pattern.conditions,
                        "source": pattern.id
                    })
            
            # Sort by confidence
            recommendations.sort(key=lambda x: x["confidence"], reverse=True)
            
            return recommendations[:10]
            
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def add_feedback(
        self,
        experience_id: str,
        feedback_type: str,
        rating: int,
        comment: Optional[str] = None
    ) -> bool:
        """Add feedback to an experience"""
        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("""
                    INSERT INTO experience_feedback (
                        experience_id, feedback_type, rating, comment
                    ) VALUES (?, ?, ?, ?)
                """, (experience_id, feedback_type, rating, comment))
                await db.commit()
                
            self.logger.info(f"Added feedback for experience: {experience_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding feedback: {e}")
            return False
    
    async def get_patterns_by_type(self, pattern_type: str) -> List[ExperiencePattern]:
        """Get patterns by type"""
        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                cursor = await db.execute("""
                    SELECT * FROM patterns WHERE pattern_type = ?
                    ORDER BY confidence DESC
                """, (pattern_type,))
                
                rows = await cursor.fetchall()
                return [self._row_to_pattern(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting patterns: {e}")
            return []
    
    def _row_to_experience(self, row) -> ExperienceEntry:
        """Convert database row to ExperienceEntry"""
        return ExperienceEntry(
            id=row[0],
            agent_id=row[1],
            task_type=TaskType(row[2]),
            context=json.loads(row[3]),
            actions_taken=json.loads(row[4]),
            outcome=OutcomeType(row[5]),
            success=bool(row[6]),
            duration=row[7],
            challenges=json.loads(row[8]),
            lessons_learned=json.loads(row[9]),
            created_at=datetime.fromisoformat(row[10]),
            project_id=row[11],
            workflow_id=row[12],
            quality_score=row[13],
            complexity_score=row[14],
            impact_score=row[15],
            metadata=json.loads(row[16])
        )
    
    def _row_to_pattern(self, row) -> ExperiencePattern:
        """Convert database row to ExperiencePattern"""
        return ExperiencePattern(
            id=row[0],
            pattern_type=row[1],
            description=row[2],
            conditions=json.loads(row[3]),
            actions=json.loads(row[4]),
            success_rate=row[5],
            frequency=row[6],
            last_seen=datetime.fromisoformat(row[7]),
            confidence=row[8],
            tags=json.loads(row[9])
        )
    
    def _find_common_actions(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find common actions across experiences"""
        action_counts = {}
        
        for exp in experiences:
            for action in exp.actions_taken:
                action_counts[action] = action_counts.get(action, 0) + 1
        
        # Return actions that appear in at least 30% of experiences
        min_count = max(1, len(experiences) * 0.3)
        return [
            action for action, count in action_counts.items()
            if count >= min_count
        ]
    
    def _find_common_challenges(self, experiences: List[ExperienceEntry]) -> List[str]:
        """Find common challenges across experiences"""
        challenge_counts = {}
        
        for exp in experiences:
            for challenge in exp.challenges:
                challenge_counts[challenge] = challenge_counts.get(challenge, 0) + 1
        
        # Return challenges that appear in at least 20% of experiences
        min_count = max(1, len(experiences) * 0.2)
        return [
            challenge for challenge, count in challenge_counts.items()
            if count >= min_count
        ]
    
    async def _update_patterns(self, experience: ExperienceEntry):
        """Update patterns based on new experience"""
        # This would be called after each experience is logged
        # For now, we'll just trigger periodic pattern recognition
        pass
    
    async def _store_patterns(self, patterns: List[ExperiencePattern]):
        """Store recognized patterns in the database"""
        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                for pattern in patterns:
                    await db.execute("""
                        INSERT OR REPLACE INTO patterns (
                            id, pattern_type, description, conditions, actions,
                            success_rate, frequency, last_seen, confidence, tags
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pattern.id,
                        pattern.pattern_type,
                        pattern.description,
                        json.dumps(pattern.conditions),
                        json.dumps(pattern.actions),
                        pattern.success_rate,
                        pattern.frequency,
                        pattern.last_seen.isoformat(),
                        pattern.confidence,
                        json.dumps(pattern.tags)
                    ))
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing patterns: {e}")


# Example usage and testing
async def main():
    """Example usage of the Experience Database"""
    db = ExperienceDatabase()
    await db.initialize()
    
    # Create a sample experience
    experience = ExperienceEntry(
        id="exp_001",
        agent_id="orchestrator",
        task_type=TaskType.CODE_GENERATION,
        context={"language": "python", "complexity": "medium"},
        actions_taken=["analyze_requirements", "generate_code", "test_code"],
        outcome=OutcomeType.SUCCESS,
        success=True,
        duration=45.5,
        challenges=["complex_logic", "edge_cases"],
        lessons_learned=["test_early", "break_down_complex_logic"],
        created_at=datetime.now(),
        project_id="proj_001",
        workflow_id="wf_001",
        quality_score=0.9,
        complexity_score=0.7,
        impact_score=0.8
    )
    
    # Log the experience
    await db.log_experience(experience)
    
    # Get statistics
    stats = await db.get_agent_statistics("orchestrator")
    print(f"Agent Statistics: {stats}")
    
    # Get recommendations
    recommendations = await db.get_recommendations(
        context={"language": "python", "complexity": "high"},
        task_type=TaskType.CODE_GENERATION
    )
    print(f"Recommendations: {recommendations}")


if __name__ == "__main__":
    asyncio.run(main())
