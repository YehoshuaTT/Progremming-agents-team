"""
Progress Tracker for Intelligent Agent System

This module provides real-time progress tracking, documentation generation,
and status monitoring for multi-agent development projects. It maintains
detailed records of all activities, decisions, and outcomes.

Key Features:
- Real-time progress tracking
- Automatic documentation generation
- Status monitoring and reporting
- Milestone tracking
- Performance analytics
- Integration with orchestrator and plan generator

Status: Ready for integration
Dependencies: intelligent_orchestrator.py, plan_generator.py
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import sqlite3
import aiofiles
from pathlib import Path

from .intelligent_orchestrator import IntelligentOrchestrator
from .plan_generator import ProjectPlan, Task, Feature, Milestone, TaskStatus, Priority

logger = logging.getLogger(__name__)

class ActivityType(Enum):
    """Types of activities that can be tracked"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    FEATURE_COMPLETED = "feature_completed"
    MILESTONE_REACHED = "milestone_reached"
    DECISION_MADE = "decision_made"
    CONSULTATION_STARTED = "consultation_started"
    CONSULTATION_COMPLETED = "consultation_completed"
    ESCALATION_TRIGGERED = "escalation_triggered"
    USER_APPROVAL_REQUESTED = "user_approval_requested"
    USER_APPROVAL_RECEIVED = "user_approval_received"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_EVENT = "system_event"

class ReportType(Enum):
    """Types of reports that can be generated"""
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    MILESTONE_REPORT = "milestone_report"
    FEATURE_REPORT = "feature_report"
    PERFORMANCE_REPORT = "performance_report"
    RISK_REPORT = "risk_report"
    COMPREHENSIVE = "comprehensive"

@dataclass
class Activity:
    """Represents a tracked activity"""
    id: str
    type: ActivityType
    description: str
    agent_id: Optional[str]
    task_id: Optional[str]
    feature_id: Optional[str]
    milestone_id: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'type': self.type.value
        }

@dataclass
class ProgressSnapshot:
    """Represents a snapshot of project progress"""
    timestamp: datetime
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    total_features: int
    completed_features: int
    milestones_reached: int
    total_milestones: int
    overall_progress_percentage: float
    estimated_completion_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'estimated_completion_date': self.estimated_completion_date.isoformat() if self.estimated_completion_date else None
        }

@dataclass
class PerformanceMetrics:
    """Performance metrics for agents and system"""
    agent_id: str
    tasks_completed: int
    average_task_duration: float
    success_rate: float
    consultation_frequency: float
    escalation_frequency: float
    quality_score: float
    period_start: datetime
    period_end: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat()
        }

class ProgressTracker:
    """Main class for tracking project progress and generating reports"""
    
    def __init__(self, orchestrator: IntelligentOrchestrator, db_path: str = "progress_tracker.db"):
        self.orchestrator = orchestrator
        self.db_path = db_path
        self.activities: List[Activity] = []
        self.current_plan: Optional[ProjectPlan] = None
        self.progress_snapshots: List[ProgressSnapshot] = []
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for storing progress data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                description TEXT NOT NULL,
                agent_id TEXT,
                task_id TEXT,
                feature_id TEXT,
                milestone_id TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                duration_seconds REAL,
                success BOOLEAN,
                error_message TEXT
            )
        ''')
        
        # Create progress snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_tasks INTEGER,
                completed_tasks INTEGER,
                in_progress_tasks INTEGER,
                blocked_tasks INTEGER,
                total_features INTEGER,
                completed_features INTEGER,
                milestones_reached INTEGER,
                total_milestones INTEGER,
                overall_progress_percentage REAL,
                estimated_completion_date TEXT
            )
        ''')
        
        # Create performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                agent_id TEXT,
                tasks_completed INTEGER,
                average_task_duration REAL,
                success_rate REAL,
                consultation_frequency REAL,
                escalation_frequency REAL,
                quality_score REAL,
                period_start TEXT,
                period_end TEXT,
                PRIMARY KEY (agent_id, period_start)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def set_project_plan(self, plan: ProjectPlan):
        """Set the current project plan for tracking"""
        self.current_plan = plan
        logger.info(f"Project plan set: {plan.project_name}")
        
        # Record system event
        self.track_activity(
            type=ActivityType.SYSTEM_EVENT,
            description=f"Project plan loaded: {plan.project_name}",
            metadata={'plan_details': plan.to_dict()}
        )
    
    def track_activity(self, 
                      type: ActivityType, 
                      description: str,
                      agent_id: Optional[str] = None,
                      task_id: Optional[str] = None,
                      feature_id: Optional[str] = None,
                      milestone_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      duration_seconds: Optional[float] = None,
                      success: bool = True,
                      error_message: Optional[str] = None) -> str:
        """Track a new activity"""
        
        activity_id = f"activity_{datetime.now().timestamp()}_{len(self.activities)}"
        
        activity = Activity(
            id=activity_id,
            type=type,
            description=description,
            agent_id=agent_id,
            task_id=task_id,
            feature_id=feature_id,
            milestone_id=milestone_id,
            timestamp=datetime.now(),
            metadata=metadata or {},
            duration_seconds=duration_seconds,
            success=success,
            error_message=error_message
        )
        
        self.activities.append(activity)
        self._save_activity_to_db(activity)
        
        # Update progress snapshot if significant activity
        if type in [ActivityType.TASK_COMPLETED, ActivityType.FEATURE_COMPLETED, ActivityType.MILESTONE_REACHED]:
            self._update_progress_snapshot()
        
        logger.info(f"Activity tracked: {type.value} - {description}")
        return activity_id
    
    def _save_activity_to_db(self, activity: Activity):
        """Save activity to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activities (
                id, type, description, agent_id, task_id, feature_id, milestone_id,
                timestamp, metadata, duration_seconds, success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            activity.id,
            activity.type.value,
            activity.description,
            activity.agent_id,
            activity.task_id,
            activity.feature_id,
            activity.milestone_id,
            activity.timestamp.isoformat(),
            json.dumps(activity.metadata),
            activity.duration_seconds,
            activity.success,
            activity.error_message
        ))
        
        conn.commit()
        conn.close()
    
    def _update_progress_snapshot(self):
        """Update the current progress snapshot"""
        if not self.current_plan:
            return
        
        # Calculate current progress
        total_tasks = len(self.current_plan.tasks)
        completed_tasks = len([t for t in self.current_plan.tasks if t.status == TaskStatus.COMPLETED])
        in_progress_tasks = len([t for t in self.current_plan.tasks if t.status == TaskStatus.IN_PROGRESS])
        blocked_tasks = len([t for t in self.current_plan.tasks if t.status == TaskStatus.BLOCKED])
        
        total_features = len(self.current_plan.features)
        completed_features = self._count_completed_features()
        
        total_milestones = len(self.current_plan.milestones)
        milestones_reached = self._count_reached_milestones()
        
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Estimate completion date
        if completed_tasks > 0 and in_progress_tasks > 0:
            remaining_tasks = total_tasks - completed_tasks
            avg_completion_rate = completed_tasks / len(self.activities) if self.activities else 1
            estimated_days = remaining_tasks / avg_completion_rate
            estimated_completion = datetime.now() + timedelta(days=estimated_days)
        else:
            estimated_completion = None
        
        snapshot = ProgressSnapshot(
            timestamp=datetime.now(),
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            total_features=total_features,
            completed_features=completed_features,
            milestones_reached=milestones_reached,
            total_milestones=total_milestones,
            overall_progress_percentage=overall_progress,
            estimated_completion_date=estimated_completion
        )
        
        self.progress_snapshots.append(snapshot)
        self._save_progress_snapshot_to_db(snapshot)
    
    def _save_progress_snapshot_to_db(self, snapshot: ProgressSnapshot):
        """Save progress snapshot to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO progress_snapshots (
                timestamp, total_tasks, completed_tasks, in_progress_tasks, blocked_tasks,
                total_features, completed_features, milestones_reached, total_milestones,
                overall_progress_percentage, estimated_completion_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            snapshot.timestamp.isoformat(),
            snapshot.total_tasks,
            snapshot.completed_tasks,
            snapshot.in_progress_tasks,
            snapshot.blocked_tasks,
            snapshot.total_features,
            snapshot.completed_features,
            snapshot.milestones_reached,
            snapshot.total_milestones,
            snapshot.overall_progress_percentage,
            snapshot.estimated_completion_date.isoformat() if snapshot.estimated_completion_date else None
        ))
        
        conn.commit()
        conn.close()
    
    def _count_completed_features(self) -> int:
        """Count completed features based on task completion"""
        if not self.current_plan:
            return 0
        
        completed_features = 0
        for feature in self.current_plan.features:
            feature_tasks = [t for t in self.current_plan.tasks if t.feature_id == feature.id]
            if feature_tasks and all(t.status == TaskStatus.COMPLETED for t in feature_tasks):
                completed_features += 1
        
        return completed_features
    
    def _count_reached_milestones(self) -> int:
        """Count reached milestones based on deliverables"""
        if not self.current_plan:
            return 0
        
        reached_milestones = 0
        for milestone in self.current_plan.milestones:
            # Check if all deliverables are completed
            deliverable_features = [f for f in self.current_plan.features if f.name in milestone.deliverables]
            if deliverable_features and all(self._is_feature_completed(f) for f in deliverable_features):
                reached_milestones += 1
        
        return reached_milestones
    
    def _is_feature_completed(self, feature: Feature) -> bool:
        """Check if a feature is completed"""
        if not self.current_plan:
            return False
        
        feature_tasks = [t for t in self.current_plan.tasks if t.feature_id == feature.id]
        return len(feature_tasks) > 0 and all(t.status == TaskStatus.COMPLETED for t in feature_tasks)
    
    async def generate_report(self, report_type: ReportType, period_days: int = 7) -> Dict[str, Any]:
        """Generate a progress report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Filter activities for the period
        period_activities = [
            a for a in self.activities 
            if start_date <= a.timestamp <= end_date
        ]
        
        # Generate report based on type
        if report_type == ReportType.DAILY_SUMMARY:
            report = await self._generate_daily_summary(period_activities)
        elif report_type == ReportType.WEEKLY_REPORT:
            report = await self._generate_weekly_report(period_activities)
        elif report_type == ReportType.MILESTONE_REPORT:
            report = await self._generate_milestone_report(period_activities)
        elif report_type == ReportType.FEATURE_REPORT:
            report = await self._generate_feature_report(period_activities)
        elif report_type == ReportType.PERFORMANCE_REPORT:
            report = await self._generate_performance_report(period_activities)
        elif report_type == ReportType.RISK_REPORT:
            report = await self._generate_risk_report(period_activities)
        elif report_type == ReportType.COMPREHENSIVE:
            report = await self._generate_comprehensive_report(period_activities)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Add common report metadata
        report['metadata'] = {
            'report_type': report_type.value,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'total_activities': len(period_activities)
        }
        
        return report
    
    async def _generate_daily_summary(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate daily summary report"""
        if not activities:
            return {'message': 'No activities recorded for this period'}
        
        # Count activities by type
        activity_counts = {}
        for activity in activities:
            activity_counts[activity.type.value] = activity_counts.get(activity.type.value, 0) + 1
        
        # Get recent progress
        latest_snapshot = self.progress_snapshots[-1] if self.progress_snapshots else None
        
        # Active agents
        active_agents = list(set(a.agent_id for a in activities if a.agent_id))
        
        return {
            'activity_summary': activity_counts,
            'active_agents': active_agents,
            'latest_progress': latest_snapshot.to_dict() if latest_snapshot else None,
            'key_achievements': [
                a.description for a in activities 
                if a.type in [ActivityType.TASK_COMPLETED, ActivityType.FEATURE_COMPLETED, ActivityType.MILESTONE_REACHED]
            ][:10]  # Top 10 achievements
        }
    
    async def _generate_weekly_report(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate weekly progress report"""
        daily_summary = await self._generate_daily_summary(activities)
        
        # Calculate weekly trends
        completed_tasks = len([a for a in activities if a.type == ActivityType.TASK_COMPLETED])
        blocked_tasks = len([a for a in activities if a.type == ActivityType.TASK_BLOCKED])
        consultations = len([a for a in activities if a.type == ActivityType.CONSULTATION_STARTED])
        escalations = len([a for a in activities if a.type == ActivityType.ESCALATION_TRIGGERED])
        
        # Performance indicators
        success_rate = len([a for a in activities if a.success]) / len(activities) if activities else 0
        
        return {
            **daily_summary,
            'weekly_metrics': {
                'completed_tasks': completed_tasks,
                'blocked_tasks': blocked_tasks,
                'consultations': consultations,
                'escalations': escalations,
                'success_rate': success_rate
            },
            'trends': self._calculate_trends(activities),
            'recommendations': self._generate_recommendations(activities)
        }
    
    async def _generate_milestone_report(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate milestone progress report"""
        if not self.current_plan:
            return {'error': 'No project plan available'}
        
        milestone_progress = []
        for milestone in self.current_plan.milestones:
            # Check deliverables completion
            deliverable_features = [f for f in self.current_plan.features if f.name in milestone.deliverables]
            completed_deliverables = [f for f in deliverable_features if self._is_feature_completed(f)]
            
            progress_percentage = (len(completed_deliverables) / len(deliverable_features)) * 100 if deliverable_features else 0
            
            milestone_progress.append({
                'milestone': milestone.name,
                'due_date': milestone.due_date.isoformat(),
                'progress_percentage': progress_percentage,
                'completed_deliverables': len(completed_deliverables),
                'total_deliverables': len(deliverable_features),
                'status': 'completed' if progress_percentage == 100 else 'in_progress'
            })
        
        return {
            'milestone_progress': milestone_progress,
            'overall_milestone_completion': self._count_reached_milestones() / len(self.current_plan.milestones) * 100,
            'next_milestone': self._get_next_milestone(),
            'milestone_activities': [
                a.to_dict() for a in activities if a.type == ActivityType.MILESTONE_REACHED
            ]
        }
    
    async def _generate_feature_report(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate feature progress report"""
        if not self.current_plan:
            return {'error': 'No project plan available'}
        
        feature_progress = []
        for feature in self.current_plan.features:
            feature_tasks = [t for t in self.current_plan.tasks if t.feature_id == feature.id]
            completed_tasks = [t for t in feature_tasks if t.status == TaskStatus.COMPLETED]
            
            progress_percentage = (len(completed_tasks) / len(feature_tasks)) * 100 if feature_tasks else 0
            
            feature_progress.append({
                'feature': feature.name,
                'priority': feature.priority.value,
                'progress_percentage': progress_percentage,
                'completed_tasks': len(completed_tasks),
                'total_tasks': len(feature_tasks),
                'estimated_hours': feature.estimated_hours,
                'status': 'completed' if progress_percentage == 100 else 'in_progress'
            })
        
        return {
            'feature_progress': feature_progress,
            'completed_features': self._count_completed_features(),
            'total_features': len(self.current_plan.features),
            'high_priority_features': [
                f for f in feature_progress 
                if f['priority'] == Priority.HIGH.value
            ]
        }
    
    async def _generate_performance_report(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate agent performance report"""
        agent_performance = {}
        
        for agent_id in set(a.agent_id for a in activities if a.agent_id):
            agent_activities = [a for a in activities if a.agent_id == agent_id]
            
            completed_tasks = len([a for a in agent_activities if a.type == ActivityType.TASK_COMPLETED])
            success_rate = len([a for a in agent_activities if a.success]) / len(agent_activities) if agent_activities else 0
            
            # Calculate average duration for completed tasks
            task_durations = [a.duration_seconds for a in agent_activities if a.duration_seconds]
            avg_duration = sum(task_durations) / len(task_durations) if task_durations else 0
            
            agent_performance[agent_id] = {
                'total_activities': len(agent_activities),
                'completed_tasks': completed_tasks,
                'success_rate': success_rate,
                'average_task_duration': avg_duration,
                'consultations': len([a for a in agent_activities if a.type == ActivityType.CONSULTATION_STARTED]),
                'escalations': len([a for a in agent_activities if a.type == ActivityType.ESCALATION_TRIGGERED])
            }
        
        return {
            'agent_performance': agent_performance,
            'top_performers': self._get_top_performers(agent_performance),
            'performance_trends': self._calculate_performance_trends(activities)
        }
    
    async def _generate_risk_report(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate risk assessment report"""
        risks = []
        
        # Identify risks from activities
        blocked_tasks = [a for a in activities if a.type == ActivityType.TASK_BLOCKED]
        if blocked_tasks:
            risks.append({
                'risk': 'Task Blockages',
                'severity': 'high' if len(blocked_tasks) > 3 else 'medium',
                'count': len(blocked_tasks),
                'description': f'{len(blocked_tasks)} tasks are currently blocked'
            })
        
        errors = [a for a in activities if not a.success]
        if errors:
            risks.append({
                'risk': 'Error Rate',
                'severity': 'high' if len(errors) / len(activities) > 0.1 else 'medium',
                'count': len(errors),
                'description': f'{len(errors)} activities failed'
            })
        
        escalations = [a for a in activities if a.type == ActivityType.ESCALATION_TRIGGERED]
        if escalations:
            risks.append({
                'risk': 'Frequent Escalations',
                'severity': 'medium',
                'count': len(escalations),
                'description': f'{len(escalations)} escalations triggered'
            })
        
        return {
            'identified_risks': risks,
            'risk_level': self._calculate_overall_risk_level(risks),
            'mitigation_suggestions': self._generate_mitigation_suggestions(risks)
        }
    
    async def _generate_comprehensive_report(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate comprehensive report with all sections"""
        return {
            'executive_summary': await self._generate_daily_summary(activities),
            'progress_overview': await self._generate_weekly_report(activities),
            'milestone_status': await self._generate_milestone_report(activities),
            'feature_progress': await self._generate_feature_report(activities),
            'performance_analysis': await self._generate_performance_report(activities),
            'risk_assessment': await self._generate_risk_report(activities)
        }
    
    def _calculate_trends(self, activities: List[Activity]) -> Dict[str, Any]:
        """Calculate trends from activities"""
        # Group activities by day
        daily_activities = {}
        for activity in activities:
            day = activity.timestamp.date()
            if day not in daily_activities:
                daily_activities[day] = []
            daily_activities[day].append(activity)
        
        # Calculate daily completion rates
        daily_completions = []
        for day, day_activities in daily_activities.items():
            completions = len([a for a in day_activities if a.type == ActivityType.TASK_COMPLETED])
            daily_completions.append(completions)
        
        # Calculate trend
        if len(daily_completions) > 1:
            recent_avg = sum(daily_completions[-3:]) / min(3, len(daily_completions))
            overall_avg = sum(daily_completions) / len(daily_completions)
            trend = 'increasing' if recent_avg > overall_avg else 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'completion_trend': trend,
            'daily_completions': daily_completions,
            'average_daily_completions': sum(daily_completions) / len(daily_completions) if daily_completions else 0
        }
    
    def _generate_recommendations(self, activities: List[Activity]) -> List[str]:
        """Generate recommendations based on activities"""
        recommendations = []
        
        # Check for blocked tasks
        blocked_tasks = [a for a in activities if a.type == ActivityType.TASK_BLOCKED]
        if blocked_tasks:
            recommendations.append("Address blocked tasks to improve velocity")
        
        # Check success rate
        success_rate = len([a for a in activities if a.success]) / len(activities) if activities else 0
        if success_rate < 0.9:
            recommendations.append("Investigate causes of failures to improve success rate")
        
        # Check escalation rate
        escalations = [a for a in activities if a.type == ActivityType.ESCALATION_TRIGGERED]
        if len(escalations) / len(activities) > 0.1:
            recommendations.append("High escalation rate - consider process improvements")
        
        return recommendations
    
    def _get_next_milestone(self) -> Optional[Dict[str, Any]]:
        """Get the next upcoming milestone"""
        if not self.current_plan:
            return None
        
        unreached_milestones = []
        for milestone in self.current_plan.milestones:
            deliverable_features = [f for f in self.current_plan.features if f.name in milestone.deliverables]
            if not all(self._is_feature_completed(f) for f in deliverable_features):
                unreached_milestones.append(milestone)
        
        if unreached_milestones:
            # Return the earliest unreached milestone
            next_milestone = min(unreached_milestones, key=lambda m: m.due_date)
            return {
                'name': next_milestone.name,
                'due_date': next_milestone.due_date.isoformat(),
                'deliverables': next_milestone.deliverables
            }
        
        return None
    
    def _get_top_performers(self, agent_performance: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get top performing agents"""
        performers = []
        for agent_id, performance in agent_performance.items():
            score = (performance['completed_tasks'] * 0.4 + 
                    performance['success_rate'] * 0.6)
            performers.append({
                'agent_id': agent_id,
                'score': score,
                'completed_tasks': performance['completed_tasks'],
                'success_rate': performance['success_rate']
            })
        
        return sorted(performers, key=lambda x: x['score'], reverse=True)[:5]
    
    def _calculate_performance_trends(self, activities: List[Activity]) -> Dict[str, Any]:
        """Calculate performance trends"""
        # Simple trend calculation - can be enhanced
        recent_activities = activities[-50:] if len(activities) > 50 else activities
        recent_success_rate = len([a for a in recent_activities if a.success]) / len(recent_activities) if recent_activities else 0
        
        overall_success_rate = len([a for a in activities if a.success]) / len(activities) if activities else 0
        
        return {
            'recent_success_rate': recent_success_rate,
            'overall_success_rate': overall_success_rate,
            'trend': 'improving' if recent_success_rate > overall_success_rate else 'declining'
        }
    
    def _calculate_overall_risk_level(self, risks: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level"""
        if not risks:
            return 'low'
        
        high_risks = [r for r in risks if r['severity'] == 'high']
        if high_risks:
            return 'high'
        
        medium_risks = [r for r in risks if r['severity'] == 'medium']
        if len(medium_risks) > 2:
            return 'high'
        elif medium_risks:
            return 'medium'
        
        return 'low'
    
    def _generate_mitigation_suggestions(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation suggestions"""
        suggestions = []
        
        for risk in risks:
            if risk['risk'] == 'Task Blockages':
                suggestions.append("Review blocked tasks and allocate resources to resolve blockers")
            elif risk['risk'] == 'Error Rate':
                suggestions.append("Implement code review processes and improve testing")
            elif risk['risk'] == 'Frequent Escalations':
                suggestions.append("Provide additional training or adjust task assignments")
        
        return suggestions
    
    async def export_report(self, report: Dict[str, Any], filename: str, format: str = 'json'):
        """Export report to file"""
        filepath = self.reports_dir / filename
        
        if format.lower() == 'json':
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps(report, indent=2))
        elif format.lower() == 'html':
            html_content = self._generate_html_report(report)
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(html_content)
        
        logger.info(f"Report exported to {filepath}")
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Progress Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Progress Report</h1>
            <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="section">
                <h2>Report Data</h2>
                <pre>{json.dumps(report, indent=2)}</pre>
            </div>
        </body>
        </html>
        """
        return html
    
    async def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time project status"""
        if not self.current_plan:
            return {'error': 'No project plan available'}
        
        # Get latest progress
        latest_snapshot = self.progress_snapshots[-1] if self.progress_snapshots else None
        
        # Get recent activities
        recent_activities = self.activities[-20:] if len(self.activities) > 20 else self.activities
        
        # Get active agents
        active_agents = list(set(a.agent_id for a in recent_activities if a.agent_id))
        
        return {
            'project_name': self.current_plan.project_name,
            'current_progress': latest_snapshot.to_dict() if latest_snapshot else None,
            'recent_activities': [a.to_dict() for a in recent_activities],
            'active_agents': active_agents,
            'next_milestone': self._get_next_milestone(),
            'last_updated': datetime.now().isoformat()
        }

# Example usage
async def main():
    """Example usage of the progress tracker"""
    from .intelligent_orchestrator import IntelligentOrchestrator
    from .plan_generator import PlanGenerator
    
    # Create orchestrator and plan generator
    orchestrator = IntelligentOrchestrator()
    plan_generator = PlanGenerator(orchestrator)
    
    # Generate a sample plan
    plan = await plan_generator.generate_plan(
        "Sample project",
        {'project_name': 'Test Project', 'features': ['authentication', 'crud']}
    )
    
    # Create progress tracker
    tracker = ProgressTracker(orchestrator)
    tracker.set_project_plan(plan)
    
    # Track some activities
    tracker.track_activity(
        ActivityType.TASK_STARTED,
        "Started authentication implementation",
        agent_id="coder",
        task_id="task_1"
    )
    
    tracker.track_activity(
        ActivityType.TASK_COMPLETED,
        "Completed authentication implementation",
        agent_id="coder",
        task_id="task_1",
        duration_seconds=3600
    )
    
    # Generate report
    report = await tracker.generate_report(ReportType.DAILY_SUMMARY)
    print(f"Generated report: {report}")
    
    # Export report
    await tracker.export_report(report, "daily_report.json")

if __name__ == "__main__":
    asyncio.run(main())
