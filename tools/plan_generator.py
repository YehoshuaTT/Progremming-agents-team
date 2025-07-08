"""
Plan Generator for Intelligent Agent System

This module provides comprehensive project planning capabilities, including
feature analysis, technology stack recommendations, task breakdown, and
milestone planning. It works with the orchestrator to create detailed
project plans that agents can execute.

Key Features:
- Feature decomposition and analysis
- Technology stack recommendations
- Task breakdown and dependency mapping
- Milestone and timeline planning
- Resource allocation planning
- Risk assessment and mitigation
- Integration with agent consultation system

Status: Ready for integration
Dependencies: intelligent_orchestrator.py, certainty_framework.py
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import yaml

from .intelligent_orchestrator import IntelligentOrchestrator, AgentConsultationResult
from .certainty_framework import CertaintyFramework, DecisionType, CertaintyLevel, create_decision

logger = logging.getLogger(__name__)

class ProjectType(Enum):
    """Types of projects that can be planned"""
    WEB_APPLICATION = "web_application"
    MOBILE_APPLICATION = "mobile_application"
    DESKTOP_APPLICATION = "desktop_application"
    API_SERVICE = "api_service"
    MICROSERVICE = "microservice"
    LIBRARY = "library"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"
    INTEGRATION = "integration"
    MIGRATION = "migration"

class TechStack(Enum):
    """Common technology stacks"""
    REACT_NODE = "react_node"
    ANGULAR_NODE = "angular_node"
    VUE_NODE = "vue_node"
    DJANGO_PYTHON = "django_python"
    FLASK_PYTHON = "flask_python"
    SPRING_JAVA = "spring_java"
    DOTNET_CORE = "dotnet_core"
    RAILS_RUBY = "rails_ruby"
    LARAVEL_PHP = "laravel_php"
    NEXTJS = "nextjs"
    NUXTJS = "nuxtjs"

class Priority(Enum):
    """Task and feature priorities"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    """Status of tasks in the plan"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Feature:
    """Represents a feature in the project plan"""
    id: str
    name: str
    description: str
    priority: Priority
    estimated_hours: int
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    user_stories: List[str] = field(default_factory=list)
    technical_requirements: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['priority'] = self.priority.value  # Convert enum to string
        return data

@dataclass
class Task:
    """Represents a task in the project plan"""
    id: str
    feature_id: str
    title: str
    description: str
    assigned_agent: Optional[str]
    estimated_hours: int
    priority: Priority
    status: TaskStatus
    dependencies: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['priority'] = self.priority.value  # Convert enum to string
        data['status'] = self.status.value  # Convert enum to string
        data['created_at'] = self.created_at.isoformat()
        data['due_date'] = self.due_date.isoformat() if self.due_date else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

@dataclass
class Milestone:
    """Represents a milestone in the project plan"""
    id: str
    name: str
    description: str
    due_date: datetime
    deliverables: List[str]
    dependencies: List[str] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'due_date': self.due_date.isoformat()
        }

@dataclass
class ProjectPlan:
    """Complete project plan with all components"""
    project_name: str
    project_type: ProjectType
    tech_stack: TechStack
    features: List[Feature]
    tasks: List[Task]
    milestones: List[Milestone]
    estimated_duration_weeks: int
    team_size: int
    budget_estimate: Optional[float] = None
    risk_assessment: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_name': self.project_name,
            'project_type': self.project_type.value,
            'tech_stack': self.tech_stack.value,
            'features': [f.to_dict() for f in self.features],
            'tasks': [t.to_dict() for t in self.tasks],
            'milestones': [m.to_dict() for m in self.milestones],
            'estimated_duration_weeks': self.estimated_duration_weeks,
            'team_size': self.team_size,
            'budget_estimate': self.budget_estimate,
            'risk_assessment': self.risk_assessment,
            'assumptions': self.assumptions,
            'constraints': self.constraints,
            'created_at': self.created_at.isoformat()
        }

class PlanGenerator:
    """Main class for generating comprehensive project plans"""
    
    def __init__(self, orchestrator: IntelligentOrchestrator):
        self.orchestrator = orchestrator
        self.certainty_framework = CertaintyFramework()
        self.tech_stack_templates = self._load_tech_stack_templates()
        self.feature_templates = self._load_feature_templates()
        
    def _load_tech_stack_templates(self) -> Dict[TechStack, Dict[str, Any]]:
        """Load technology stack templates and recommendations"""
        return {
            TechStack.REACT_NODE: {
                'frontend': ['React', 'Redux', 'Material-UI', 'Axios'],
                'backend': ['Node.js', 'Express', 'MongoDB', 'JWT'],
                'tools': ['Webpack', 'Babel', 'ESLint', 'Jest'],
                'deployment': ['Docker', 'Nginx', 'PM2'],
                'estimated_setup_hours': 16,
                'complexity_factor': 1.0
            },
            TechStack.DJANGO_PYTHON: {
                'frontend': ['Django Templates', 'Bootstrap', 'jQuery'],
                'backend': ['Django', 'PostgreSQL', 'Redis', 'Celery'],
                'tools': ['pip', 'Black', 'pytest', 'Django Debug Toolbar'],
                'deployment': ['Gunicorn', 'Nginx', 'PostgreSQL'],
                'estimated_setup_hours': 12,
                'complexity_factor': 0.8
            },
            TechStack.NEXTJS: {
                'frontend': ['Next.js', 'React', 'Tailwind CSS', 'SWR'],
                'backend': ['Next.js API Routes', 'Prisma', 'PostgreSQL'],
                'tools': ['TypeScript', 'ESLint', 'Prettier', 'Jest'],
                'deployment': ['Vercel', 'Supabase', 'Railway'],
                'estimated_setup_hours': 10,
                'complexity_factor': 0.7
            }
        }
    
    def _load_feature_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load common feature templates"""
        return {
            'user_authentication': {
                'tasks': ['Login UI', 'Registration UI', 'Password Reset', 'Session Management'],
                'estimated_hours': 24,
                'dependencies': ['database_setup'],
                'acceptance_criteria': [
                    'Users can register with email/password',
                    'Users can login and logout',
                    'Password reset functionality works',
                    'Session persistence across browser restarts'
                ]
            },
            'crud_operations': {
                'tasks': ['Create UI', 'Read/List UI', 'Update UI', 'Delete UI', 'API Endpoints'],
                'estimated_hours': 32,
                'dependencies': ['database_setup', 'authentication'],
                'acceptance_criteria': [
                    'Users can create new items',
                    'Users can view item lists and details',
                    'Users can update existing items',
                    'Users can delete items with confirmation'
                ]
            },
            'search_functionality': {
                'tasks': ['Search UI', 'Search API', 'Filters', 'Pagination'],
                'estimated_hours': 28,
                'dependencies': ['crud_operations'],
                'acceptance_criteria': [
                    'Users can search by keywords',
                    'Search results are paginated',
                    'Filters work correctly',
                    'Search performance is acceptable'
                ]
            },
            'file_upload': {
                'tasks': ['Upload UI', 'File Processing', 'Storage Setup', 'Validation'],
                'estimated_hours': 20,
                'dependencies': ['authentication'],
                'acceptance_criteria': [
                    'Users can upload supported file types',
                    'File size limits are enforced',
                    'Files are stored securely',
                    'Upload progress is shown'
                ]
            },
            'notifications': {
                'tasks': ['Notification Service', 'Email Templates', 'Push Notifications', 'Preferences'],
                'estimated_hours': 36,
                'dependencies': ['authentication'],
                'acceptance_criteria': [
                    'Users receive relevant notifications',
                    'Email notifications work',
                    'Users can manage notification preferences',
                    'Notifications are delivered reliably'
                ]
            }
        }
    
    async def generate_plan(self, project_description: str, requirements: Dict[str, Any]) -> ProjectPlan:
        """Generate a comprehensive project plan"""
        logger.info(f"Generating plan for project: {project_description}")
        
        # Step 1: Analyze project type and requirements
        project_analysis = await self._analyze_project_requirements(project_description, requirements)
        
        # Step 2: Recommend technology stack
        tech_stack_decision = await self._recommend_technology_stack(project_analysis)
        
        # Step 3: Extract and analyze features
        features = await self._extract_features(project_analysis, requirements)
        
        # Step 4: Break down features into tasks
        tasks = await self._generate_tasks(features, tech_stack_decision)
        
        # Step 5: Create milestones
        milestones = await self._create_milestones(features, tasks)
        
        # Step 6: Estimate timeline and resources
        timeline_estimate = await self._estimate_timeline(tasks, tech_stack_decision)
        
        # Step 7: Assess risks and constraints
        risk_assessment = await self._assess_risks(project_analysis, tech_stack_decision)
        
        # Create the final plan
        plan = ProjectPlan(
            project_name=project_analysis['project_name'],
            project_type=project_analysis['project_type'],
            tech_stack=tech_stack_decision,
            features=features,
            tasks=tasks,
            milestones=milestones,
            estimated_duration_weeks=timeline_estimate['duration_weeks'],
            team_size=timeline_estimate['recommended_team_size'],
            budget_estimate=timeline_estimate.get('budget_estimate'),
            risk_assessment=risk_assessment['risks'],
            assumptions=risk_assessment['assumptions'],
            constraints=risk_assessment['constraints']
        )
        
        logger.info(f"Plan generated successfully with {len(features)} features and {len(tasks)} tasks")
        return plan
    
    async def _analyze_project_requirements(self, description: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project requirements and classify the project"""
        
        # Consult agents for project analysis
        consultation_result = await self.orchestrator.consult_agents(
            query=f"Analyze project requirements: {description}",
            agents=['product_analyst', 'architect'],
            context={'requirements': requirements}
        )
        
        # Determine project type based on description and requirements
        project_type = self._classify_project_type(description, requirements)
        
        # Extract key information
        analysis = {
            'project_name': requirements.get('project_name', 'Unnamed Project'),
            'project_type': project_type,
            'target_users': requirements.get('target_users', 'general'),
            'scale': requirements.get('scale', 'medium'),
            'timeline': requirements.get('timeline', 'flexible'),
            'budget': requirements.get('budget', 'moderate'),
            'consultation_result': consultation_result
        }
        
        return analysis
    
    def _classify_project_type(self, description: str, requirements: Dict[str, Any]) -> ProjectType:
        """Classify the project type based on description and requirements"""
        description_lower = description.lower()
        
        # Simple classification logic - can be enhanced with ML
        if 'web' in description_lower or 'website' in description_lower:
            return ProjectType.WEB_APPLICATION
        elif 'mobile' in description_lower or 'app' in description_lower:
            return ProjectType.MOBILE_APPLICATION
        elif 'api' in description_lower or 'service' in description_lower:
            return ProjectType.API_SERVICE
        elif 'desktop' in description_lower:
            return ProjectType.DESKTOP_APPLICATION
        elif 'library' in description_lower or 'package' in description_lower:
            return ProjectType.LIBRARY
        elif 'data' in description_lower or 'pipeline' in description_lower:
            return ProjectType.DATA_PIPELINE
        elif 'ml' in description_lower or 'machine learning' in description_lower:
            return ProjectType.MACHINE_LEARNING
        else:
            return ProjectType.WEB_APPLICATION  # Default
    
    async def _recommend_technology_stack(self, project_analysis: Dict[str, Any]) -> TechStack:
        """Recommend the best technology stack for the project"""
        
        # Create a decision for technology stack
        decision = create_decision(
            agent_name="plan_generator",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=80.0,
            content="Recommend technology stack based on project requirements",
            reasoning="Need to select appropriate technology stack for project success"
        )
        
        # Consult architect and senior developers
        consultation_result = await self.orchestrator.consult_agents(
            query=f"Recommend technology stack for {project_analysis['project_type'].value} project",
            agents=['architect', 'coder'],
            context=project_analysis
        )
        
        # Simple recommendation logic - can be enhanced
        project_type = project_analysis['project_type']
        scale = project_analysis['scale']
        timeline = project_analysis['timeline']
        
        if project_type == ProjectType.WEB_APPLICATION:
            if timeline == 'fast' or scale == 'small':
                return TechStack.NEXTJS
            elif scale == 'large':
                return TechStack.REACT_NODE
            else:
                return TechStack.DJANGO_PYTHON
        elif project_type == ProjectType.API_SERVICE:
            if scale == 'large':
                return TechStack.SPRING_JAVA
            else:
                return TechStack.FLASK_PYTHON
        else:
            return TechStack.REACT_NODE  # Default
    
    async def _extract_features(self, project_analysis: Dict[str, Any], requirements: Dict[str, Any]) -> List[Feature]:
        """Extract and analyze features from requirements"""
        features = []
        
        # Get feature list from requirements
        feature_list = requirements.get('features', [])
        
        # Consult product analyst for feature analysis
        consultation_result = await self.orchestrator.consult_agents(
            query=f"Analyze features for {project_analysis['project_name']}",
            agents=['product_analyst'],
            context={'features': feature_list, 'project_analysis': project_analysis}
        )
        
        # Process each feature
        for i, feature_desc in enumerate(feature_list):
            feature_id = f"feature_{i+1}"
            
            # Check if it's a common feature template
            template = self.feature_templates.get(feature_desc.lower().replace(' ', '_'))
            
            if template:
                feature = Feature(
                    id=feature_id,
                    name=feature_desc,
                    description=f"Implement {feature_desc} functionality",
                    priority=Priority.HIGH,
                    estimated_hours=template['estimated_hours'],
                    dependencies=template['dependencies'],
                    acceptance_criteria=template['acceptance_criteria']
                )
            else:
                # Create custom feature
                feature = Feature(
                    id=feature_id,
                    name=feature_desc,
                    description=f"Implement {feature_desc} functionality",
                    priority=Priority.MEDIUM,
                    estimated_hours=20,  # Default estimate
                    dependencies=[],
                    acceptance_criteria=[f"{feature_desc} works as expected"]
                )
            
            features.append(feature)
        
        # Add core features based on project type
        core_features = self._get_core_features(project_analysis['project_type'])
        features.extend(core_features)
        
        return features
    
    def _get_core_features(self, project_type: ProjectType) -> List[Feature]:
        """Get core features required for the project type"""
        core_features = []
        
        if project_type == ProjectType.WEB_APPLICATION:
            core_features.extend([
                Feature(
                    id="core_setup",
                    name="Project Setup",
                    description="Initial project setup and configuration",
                    priority=Priority.CRITICAL,
                    estimated_hours=8,
                    dependencies=[],
                    acceptance_criteria=["Project structure is created", "Build system is configured"]
                ),
                Feature(
                    id="core_database",
                    name="Database Setup",
                    description="Database design and setup",
                    priority=Priority.CRITICAL,
                    estimated_hours=12,
                    dependencies=["core_setup"],
                    acceptance_criteria=["Database is configured", "Schema is created"]
                )
            ])
        
        return core_features
    
    async def _generate_tasks(self, features: List[Feature], tech_stack: TechStack) -> List[Task]:
        """Generate tasks from features"""
        tasks = []
        task_counter = 1
        
        # Get tech stack info
        tech_info = self.tech_stack_templates.get(tech_stack, {})
        
        for feature in features:
            # Check if feature has template tasks
            template = self.feature_templates.get(feature.name.lower().replace(' ', '_'))
            
            if template:
                template_tasks = template['tasks']
            else:
                # Generate generic tasks
                template_tasks = ['Design', 'Implementation', 'Testing', 'Documentation']
            
            # Create tasks for this feature
            for task_name in template_tasks:
                task = Task(
                    id=f"task_{task_counter}",
                    feature_id=feature.id,
                    title=f"{task_name} - {feature.name}",
                    description=f"Complete {task_name.lower()} for {feature.name}",
                    assigned_agent=self._suggest_agent_for_task(task_name, tech_stack),
                    estimated_hours=feature.estimated_hours // len(template_tasks),
                    priority=feature.priority,
                    status=TaskStatus.PENDING,
                    dependencies=feature.dependencies.copy()
                )
                tasks.append(task)
                task_counter += 1
        
        return tasks
    
    def _suggest_agent_for_task(self, task_name: str, tech_stack: TechStack) -> str:
        """Suggest the best agent for a task"""
        task_lower = task_name.lower()
        
        if 'design' in task_lower or 'ui' in task_lower:
            return 'ux_ui_designer'
        elif 'test' in task_lower:
            return 'tester'
        elif 'documentation' in task_lower:
            return 'technical_writer'
        elif 'api' in task_lower or 'backend' in task_lower:
            return 'coder'
        elif 'security' in task_lower:
            return 'security_specialist'
        elif 'deploy' in task_lower:
            return 'devops'
        else:
            return 'coder'  # Default
    
    async def _create_milestones(self, features: List[Feature], tasks: List[Task]) -> List[Milestone]:
        """Create project milestones"""
        milestones = []
        
        # Group features by priority and dependencies
        critical_features = [f for f in features if f.priority == Priority.CRITICAL]
        high_priority_features = [f for f in features if f.priority == Priority.HIGH]
        
        # Create milestones based on feature groups
        if critical_features:
            milestones.append(Milestone(
                id="milestone_1",
                name="Foundation Complete",
                description="Core infrastructure and setup complete",
                due_date=datetime.now() + timedelta(weeks=2),
                deliverables=[f.name for f in critical_features],
                completion_criteria=["All critical features implemented", "Basic functionality works"]
            ))
        
        if high_priority_features:
            milestones.append(Milestone(
                id="milestone_2",
                name="Core Features Complete",
                description="Main application features implemented",
                due_date=datetime.now() + timedelta(weeks=6),
                deliverables=[f.name for f in high_priority_features],
                completion_criteria=["All high priority features implemented", "User acceptance tests pass"]
            ))
        
        # Final milestone
        milestones.append(Milestone(
            id="milestone_final",
            name="Project Complete",
            description="All features implemented and tested",
            due_date=datetime.now() + timedelta(weeks=10),
            deliverables=[f.name for f in features],
            completion_criteria=["All features complete", "All tests pass", "Documentation complete"]
        ))
        
        return milestones
    
    async def _estimate_timeline(self, tasks: List[Task], tech_stack: TechStack) -> Dict[str, Any]:
        """Estimate project timeline and resource requirements"""
        
        # Calculate total effort
        total_hours = sum(task.estimated_hours for task in tasks)
        
        # Get complexity factor from tech stack
        tech_info = self.tech_stack_templates.get(tech_stack, {})
        complexity_factor = tech_info.get('complexity_factor', 1.0)
        
        # Apply complexity adjustment
        adjusted_hours = total_hours * complexity_factor
        
        # Add buffer for unknowns (20%)
        buffered_hours = adjusted_hours * 1.2
        
        # Calculate timeline based on team size
        recommended_team_size = min(max(2, int(buffered_hours / 160)), 8)  # 2-8 people
        duration_weeks = int(buffered_hours / (recommended_team_size * 40))  # 40 hours per week per person
        
        return {
            'total_hours': total_hours,
            'adjusted_hours': adjusted_hours,
            'buffered_hours': buffered_hours,
            'duration_weeks': duration_weeks,
            'recommended_team_size': recommended_team_size,
            'budget_estimate': buffered_hours * 75  # $75 per hour estimate
        }
    
    async def _assess_risks(self, project_analysis: Dict[str, Any], tech_stack: TechStack) -> Dict[str, Any]:
        """Assess project risks and constraints"""
        
        # Consult agents for risk assessment
        consultation_result = await self.orchestrator.consult_agents(
            query=f"Assess risks for {project_analysis['project_type'].value} project using {tech_stack.value}",
            agents=['architect', 'security_specialist'],
            context=project_analysis
        )
        
        # Common risks based on project type and tech stack
        risks = []
        assumptions = []
        constraints = []
        
        # Project type specific risks
        if project_analysis['project_type'] == ProjectType.WEB_APPLICATION:
            risks.extend([
                "Browser compatibility issues",
                "Performance under load",
                "Security vulnerabilities"
            ])
        
        # Tech stack specific risks
        if tech_stack == TechStack.REACT_NODE:
            risks.extend([
                "Rapid ecosystem changes",
                "Bundle size growth",
                "SEO challenges"
            ])
        
        # Common assumptions
        assumptions.extend([
            "Team has necessary skills",
            "Requirements are stable",
            "Third-party services are available"
        ])
        
        # Common constraints
        constraints.extend([
            "Budget limitations",
            "Timeline constraints",
            "Resource availability"
        ])
        
        return {
            'risks': risks,
            'assumptions': assumptions,
            'constraints': constraints,
            'consultation_result': consultation_result
        }
    
    async def update_plan(self, plan: ProjectPlan, updates: Dict[str, Any]) -> ProjectPlan:
        """Update an existing project plan"""
        logger.info(f"Updating plan for {plan.project_name}")
        
        # Update features if provided
        if 'features' in updates:
            new_features = updates['features']
            for feature_data in new_features:
                feature = Feature(**feature_data)
                plan.features.append(feature)
        
        # Update tasks if provided
        if 'tasks' in updates:
            new_tasks = updates['tasks']
            for task_data in new_tasks:
                task = Task(**task_data)
                plan.tasks.append(task)
        
        # Recalculate timeline
        timeline_estimate = await self._estimate_timeline(plan.tasks, plan.tech_stack)
        plan.estimated_duration_weeks = timeline_estimate['duration_weeks']
        plan.team_size = timeline_estimate['recommended_team_size']
        
        return plan
    
    async def export_plan(self, plan: ProjectPlan, filepath: str, format: str = 'json'):
        """Export project plan to file"""
        plan_data = plan.to_dict()
        
        if format.lower() == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2)
        elif format.lower() == 'yaml':
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(plan_data, f, default_flow_style=False)
        
        logger.info(f"Plan exported to {filepath} in {format} format")
    
    async def import_plan(self, filepath: str, format: str = 'json') -> ProjectPlan:
        """Import project plan from file"""
        plan_data = None
        
        if format.lower() == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
        elif format.lower() == 'yaml':
            with open(filepath, 'r', encoding='utf-8') as f:
                plan_data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if plan_data is None:
            raise ValueError("Failed to load plan data")
        
        # Reconstruct plan objects
        features = [Feature(**f) for f in plan_data['features']]
        tasks = [Task(**t) for t in plan_data['tasks']]
        milestones = [Milestone(**m) for m in plan_data['milestones']]
        
        plan = ProjectPlan(
            project_name=plan_data['project_name'],
            project_type=ProjectType(plan_data['project_type']),
            tech_stack=TechStack(plan_data['tech_stack']),
            features=features,
            tasks=tasks,
            milestones=milestones,
            estimated_duration_weeks=plan_data['estimated_duration_weeks'],
            team_size=plan_data['team_size'],
            budget_estimate=plan_data.get('budget_estimate'),
            risk_assessment=plan_data.get('risk_assessment', []),
            assumptions=plan_data.get('assumptions', []),
            constraints=plan_data.get('constraints', [])
        )
        
        logger.info(f"Plan imported from {filepath}")
        return plan

# Example usage
async def main():
    """Example usage of the plan generator"""
    from .intelligent_orchestrator import IntelligentOrchestrator
    
    orchestrator = IntelligentOrchestrator()
    
    # Register some agents
    orchestrator.register_agent("product_analyst", ["analysis", "requirements"], 0.9)
    orchestrator.register_agent("architect", ["architecture", "design"], 0.9)
    orchestrator.register_agent("coder", ["implementation", "coding"], 0.8)
    
    # Create plan generator
    plan_generator = PlanGenerator(orchestrator)
    
    # Generate a plan
    plan = await plan_generator.generate_plan(
        project_description="Task management web application",
        requirements={
            'project_name': 'TaskMaster Pro',
            'features': ['user authentication', 'task creation', 'task assignment', 'notifications'],
            'scale': 'medium',
            'timeline': 'moderate',
            'budget': 'moderate'
        }
    )
    
    print(f"Generated plan for {plan.project_name}")
    print(f"Features: {len(plan.features)}")
    print(f"Tasks: {len(plan.tasks)}")
    print(f"Estimated duration: {plan.estimated_duration_weeks} weeks")
    print(f"Team size: {plan.team_size}")
    
    # Export the plan
    await plan_generator.export_plan(plan, 'taskmaster_plan.json')

if __name__ == "__main__":
    asyncio.run(main())
