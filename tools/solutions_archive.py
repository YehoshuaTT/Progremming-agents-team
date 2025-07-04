"""
Solutions Archive System
Advanced memory system for storing and retrieving successful solutions
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import asyncio
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SolutionType(Enum):
    """Types of solutions that can be archived"""
    CODE_IMPLEMENTATION = "code_implementation"
    ARCHITECTURE_DESIGN = "architecture_design"
    BUG_FIX = "bug_fix"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_ENHANCEMENT = "security_enhancement"
    INTEGRATION_PATTERN = "integration_pattern"
    DEPLOYMENT_STRATEGY = "deployment_strategy"
    TESTING_APPROACH = "testing_approach"

class SolutionQuality(Enum):
    """Quality levels for solutions"""
    EXCELLENT = 5
    GOOD = 4
    AVERAGE = 3
    BELOW_AVERAGE = 2
    POOR = 1

@dataclass
class SolutionEntry:
    """Represents a solution stored in the archive"""
    id: str
    title: str
    description: str
    problem_type: str
    solution_type: SolutionType
    solution_steps: List[str]
    code_artifacts: List[Dict[str, str]]  # [{"filename": "...", "content": "..."}]
    success_metrics: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    agent_id: str
    project_context: Dict[str, Any]
    quality_score: float
    usage_count: int
    feedback_score: float
    problem_hash: str
    solution_hash: str
    dependencies: List[str]
    related_solutions: List[str]

class SolutionsArchive:
    """Advanced solutions archive with semantic search and quality scoring"""
    
    def __init__(self, db_path: str = "cache/solutions_archive.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize the solutions database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS solutions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    problem_type TEXT NOT NULL,
                    solution_type TEXT NOT NULL,
                    solution_steps TEXT NOT NULL,
                    code_artifacts TEXT NOT NULL,
                    success_metrics TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    project_context TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    feedback_score REAL DEFAULT 0.0,
                    problem_hash TEXT NOT NULL,
                    solution_hash TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    related_solutions TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_problem_type ON solutions(problem_type)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_solution_type ON solutions(solution_type)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_tags ON solutions(tags)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_quality_score ON solutions(quality_score)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_problem_hash ON solutions(problem_hash)
            ''')
            
            conn.commit()
            logger.info("Solutions archive database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            conn.close()
    
    def _calculate_problem_hash(self, problem_description: str, problem_type: str) -> str:
        """Calculate a hash for the problem to detect similar issues"""
        content = f"{problem_type.lower()}:{problem_description.lower()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _calculate_solution_hash(self, solution_steps: List[str], code_artifacts: List[Dict[str, str]]) -> str:
        """Calculate a hash for the solution to detect duplicates"""
        content = json.dumps(solution_steps, sort_keys=True)
        if code_artifacts:
            content += json.dumps(code_artifacts, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _calculate_quality_score(self, success_metrics: Dict[str, Any]) -> float:
        """Calculate quality score based on success metrics"""
        try:
            score = 0.0
            total_weight = 0.0
            
            # Performance metrics (weight: 0.3)
            if 'performance_improvement' in success_metrics:
                score += float(success_metrics['performance_improvement']) * 0.3
                total_weight += 0.3
            
            # Code quality metrics (weight: 0.25)
            if 'code_quality_score' in success_metrics:
                score += float(success_metrics['code_quality_score']) * 0.25
                total_weight += 0.25
            
            # Test coverage (weight: 0.2)
            if 'test_coverage' in success_metrics:
                score += float(success_metrics['test_coverage']) * 0.2
                total_weight += 0.2
            
            # User satisfaction (weight: 0.15)
            if 'user_satisfaction' in success_metrics:
                score += float(success_metrics['user_satisfaction']) * 0.15
                total_weight += 0.15
            
            # Deployment success (weight: 0.1)
            if 'deployment_success' in success_metrics:
                score += float(success_metrics['deployment_success']) * 0.1
                total_weight += 0.1
            
            # Default score if no metrics available
            if total_weight == 0:
                return 3.0
            
            return min(5.0, max(1.0, score / total_weight * 5.0))
            
        except Exception as e:
            logger.warning(f"Failed to calculate quality score: {e}")
            return 3.0
    
    async def archive_solution(self, 
                             title: str,
                             description: str,
                             problem_type: str,
                             solution_type: SolutionType,
                             solution_steps: List[str],
                             code_artifacts: List[Dict[str, str]],
                             success_metrics: Dict[str, Any],
                             tags: List[str],
                             agent_id: str,
                             project_context: Dict[str, Any],
                             dependencies: List[str] = None,
                             related_solutions: List[str] = None) -> str:
        """Archive a successful solution"""
        try:
            # Generate unique ID
            solution_id = f"SOL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(title.encode()).hexdigest()[:8]}"
            
            # Calculate hashes
            problem_hash = self._calculate_problem_hash(description, problem_type)
            solution_hash = self._calculate_solution_hash(solution_steps, code_artifacts)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(success_metrics)
            
            # Create solution entry
            solution = SolutionEntry(
                id=solution_id,
                title=title,
                description=description,
                problem_type=problem_type,
                solution_type=solution_type,
                solution_steps=solution_steps,
                code_artifacts=code_artifacts,
                success_metrics=success_metrics,
                tags=tags,
                created_at=datetime.now(),
                agent_id=agent_id,
                project_context=project_context,
                quality_score=quality_score,
                usage_count=0,
                feedback_score=0.0,
                problem_hash=problem_hash,
                solution_hash=solution_hash,
                dependencies=dependencies or [],
                related_solutions=related_solutions or []
            )
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute('''
                    INSERT INTO solutions VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                ''', (
                    solution.id,
                    solution.title,
                    solution.description,
                    solution.problem_type,
                    solution.solution_type.value,
                    json.dumps(solution.solution_steps),
                    json.dumps(solution.code_artifacts),
                    json.dumps(solution.success_metrics),
                    json.dumps(solution.tags),
                    solution.created_at.isoformat(),
                    solution.agent_id,
                    json.dumps(solution.project_context),
                    solution.quality_score,
                    solution.usage_count,
                    solution.feedback_score,
                    solution.problem_hash,
                    solution.solution_hash,
                    json.dumps(solution.dependencies),
                    json.dumps(solution.related_solutions)
                ))
                
                conn.commit()
                logger.info(f"Archived solution: {solution_id}")
                
                # Update related solutions
                if related_solutions:
                    await self._update_related_solutions(solution_id, related_solutions)
                
                return solution_id
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to archive solution: {e}")
                raise
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to archive solution: {e}")
            raise
    
    async def search_solutions(self, 
                             query: str = None,
                             problem_type: str = None,
                             solution_type: SolutionType = None,
                             tags: List[str] = None,
                             min_quality: float = None,
                             limit: int = 10) -> List[SolutionEntry]:
        """Search for solutions in the archive"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Build query
            where_clauses = []
            params = []
            
            if query:
                where_clauses.append("(title LIKE ? OR description LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            
            if problem_type:
                where_clauses.append("problem_type = ?")
                params.append(problem_type)
            
            if solution_type:
                where_clauses.append("solution_type = ?")
                params.append(solution_type.value)
            
            if tags:
                for tag in tags:
                    where_clauses.append("tags LIKE ?")
                    params.append(f"%{tag}%")
            
            if min_quality:
                where_clauses.append("quality_score >= ?")
                params.append(min_quality)
            
            # Construct SQL
            sql = "SELECT * FROM solutions"
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            sql += " ORDER BY quality_score DESC, usage_count DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convert to SolutionEntry objects
            solutions = []
            for row in rows:
                solution = SolutionEntry(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    problem_type=row[3],
                    solution_type=SolutionType(row[4]),
                    solution_steps=json.loads(row[5]),
                    code_artifacts=json.loads(row[6]),
                    success_metrics=json.loads(row[7]),
                    tags=json.loads(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    agent_id=row[10],
                    project_context=json.loads(row[11]),
                    quality_score=row[12],
                    usage_count=row[13],
                    feedback_score=row[14],
                    problem_hash=row[15],
                    solution_hash=row[16],
                    dependencies=json.loads(row[17]),
                    related_solutions=json.loads(row[18])
                )
                solutions.append(solution)
            
            conn.close()
            logger.info(f"Found {len(solutions)} solutions for query: {query}")
            return solutions
            
        except Exception as e:
            logger.error(f"Failed to search solutions: {e}")
            return []
    
    async def get_solution_by_id(self, solution_id: str) -> Optional[SolutionEntry]:
        """Get a specific solution by ID"""
        solutions = await self.search_solutions(limit=1)
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.execute("SELECT * FROM solutions WHERE id = ?", (solution_id,))
            row = cursor.fetchone()
            
            if row:
                await self._increment_usage_count(solution_id)
                
                return SolutionEntry(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    problem_type=row[3],
                    solution_type=SolutionType(row[4]),
                    solution_steps=json.loads(row[5]),
                    code_artifacts=json.loads(row[6]),
                    success_metrics=json.loads(row[7]),
                    tags=json.loads(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    agent_id=row[10],
                    project_context=json.loads(row[11]),
                    quality_score=row[12],
                    usage_count=row[13],
                    feedback_score=row[14],
                    problem_hash=row[15],
                    solution_hash=row[16],
                    dependencies=json.loads(row[17]),
                    related_solutions=json.loads(row[18])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get solution by ID: {e}")
            return None
        finally:
            conn.close()
    
    async def find_similar_solutions(self, problem_description: str, problem_type: str, limit: int = 5) -> List[SolutionEntry]:
        """Find solutions to similar problems"""
        problem_hash = self._calculate_problem_hash(problem_description, problem_type)
        
        # First try exact hash match
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT * FROM solutions WHERE problem_hash = ? ORDER BY quality_score DESC LIMIT ?",
                (problem_hash, limit)
            )
            rows = cursor.fetchall()
            
            solutions = []
            for row in rows:
                solution = SolutionEntry(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    problem_type=row[3],
                    solution_type=SolutionType(row[4]),
                    solution_steps=json.loads(row[5]),
                    code_artifacts=json.loads(row[6]),
                    success_metrics=json.loads(row[7]),
                    tags=json.loads(row[8]),
                    created_at=datetime.fromisoformat(row[9]),
                    agent_id=row[10],
                    project_context=json.loads(row[11]),
                    quality_score=row[12],
                    usage_count=row[13],
                    feedback_score=row[14],
                    problem_hash=row[15],
                    solution_hash=row[16],
                    dependencies=json.loads(row[17]),
                    related_solutions=json.loads(row[18])
                )
                solutions.append(solution)
            
            # If no exact matches, try semantic search
            if not solutions:
                solutions = await self.search_solutions(
                    query=problem_description,
                    problem_type=problem_type,
                    limit=limit
                )
            
            return solutions
            
        except Exception as e:
            logger.error(f"Failed to find similar solutions: {e}")
            return []
        finally:
            conn.close()
    
    async def _increment_usage_count(self, solution_id: str):
        """Increment usage count for a solution"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE solutions SET usage_count = usage_count + 1 WHERE id = ?",
                (solution_id,)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to increment usage count: {e}")
        finally:
            conn.close()
    
    async def _update_related_solutions(self, solution_id: str, related_ids: List[str]):
        """Update related solutions bidirectionally"""
        conn = sqlite3.connect(self.db_path)
        try:
            for related_id in related_ids:
                # Get current related solutions
                cursor = conn.execute(
                    "SELECT related_solutions FROM solutions WHERE id = ?",
                    (related_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    current_related = json.loads(row[0])
                    if solution_id not in current_related:
                        current_related.append(solution_id)
                        
                        conn.execute(
                            "UPDATE solutions SET related_solutions = ? WHERE id = ?",
                            (json.dumps(current_related), related_id)
                        )
            
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to update related solutions: {e}")
        finally:
            conn.close()
    
    async def add_feedback(self, solution_id: str, feedback_score: float, feedback_text: str = None):
        """Add feedback for a solution"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Update feedback score (weighted average)
            cursor = conn.execute(
                "SELECT feedback_score, usage_count FROM solutions WHERE id = ?",
                (solution_id,)
            )
            row = cursor.fetchone()
            
            if row:
                current_score = row[0]
                usage_count = row[1]
                
                # Calculate weighted average
                if usage_count > 0:
                    new_score = (current_score * usage_count + feedback_score) / (usage_count + 1)
                else:
                    new_score = feedback_score
                
                conn.execute(
                    "UPDATE solutions SET feedback_score = ? WHERE id = ?",
                    (new_score, solution_id)
                )
                
                conn.commit()
                logger.info(f"Added feedback for solution {solution_id}: {feedback_score}")
                
        except Exception as e:
            logger.error(f"Failed to add feedback: {e}")
        finally:
            conn.close()
    
    async def get_archive_stats(self) -> Dict[str, Any]:
        """Get statistics about the solutions archive"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Total solutions
            cursor = conn.execute("SELECT COUNT(*) FROM solutions")
            total_solutions = cursor.fetchone()[0]
            
            # Solutions by type
            cursor = conn.execute(
                "SELECT solution_type, COUNT(*) FROM solutions GROUP BY solution_type"
            )
            solutions_by_type = dict(cursor.fetchall())
            
            # Average quality score
            cursor = conn.execute("SELECT AVG(quality_score) FROM solutions")
            avg_quality = cursor.fetchone()[0] or 0.0
            
            # Most used solutions
            cursor = conn.execute(
                "SELECT title, usage_count FROM solutions ORDER BY usage_count DESC LIMIT 5"
            )
            most_used = cursor.fetchall()
            
            # Solutions by agent
            cursor = conn.execute(
                "SELECT agent_id, COUNT(*) FROM solutions GROUP BY agent_id"
            )
            solutions_by_agent = dict(cursor.fetchall())
            
            return {
                "total_solutions": total_solutions,
                "solutions_by_type": solutions_by_type,
                "average_quality_score": round(avg_quality, 2),
                "most_used_solutions": most_used,
                "solutions_by_agent": solutions_by_agent,
                "archive_size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get archive stats: {e}")
            return {}
        finally:
            conn.close()

# Global instance
solutions_archive = SolutionsArchive()
