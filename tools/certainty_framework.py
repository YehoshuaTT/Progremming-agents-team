"""
Certainty-Based Decision Making Framework
Implements intelligent decision thresholds and agent confidence analysis
"""

import json
import asyncio
import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
import statistics

logger = logging.getLogger(__name__)

class DecisionType(Enum):
    ARCHITECTURE = "architecture"
    FEATURE_DESIGN = "feature_design"
    IMPLEMENTATION = "implementation"
    UI_DESIGN = "ui_design"
    STYLING = "styling"
    SECURITY = "security"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    SYSTEM_CHANGE = "system_change"

class CertaintyLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class EscalationReason(Enum):
    LOW_CONFIDENCE = "low_confidence"
    CONFLICTING_OPINIONS = "conflicting_opinions"
    SECURITY_CONCERN = "security_concern"
    USER_REQUIREMENT_UNCLEAR = "user_requirement_unclear"
    PERFORMANCE_IMPACT = "performance_impact"
    COMPLEXITY_HIGH = "complexity_high"

class AgentRole(Enum):
    ARCHITECT = "architect"
    PRODUCT_ANALYST = "product_analyst"
    DEVELOPER = "developer"
    UI_DESIGNER = "ui_designer"
    QA_ENGINEER = "qa_engineer"
    SECURITY_ENGINEER = "security_engineer"
    DEVOPS = "devops"
    TECH_WRITER = "tech_writer"
    REVIEWER = "reviewer"
    LIBRARIAN = "librarian"

@dataclass
class AgentDecision:
    """Represents a decision made by an agent"""
    agent_id: str
    decision_type: DecisionType
    certainty_level: float  # 0-100
    decision_content: str
    reasoning: str
    alternative_options: List[str] = field(default_factory=list)
    requires_consultation: bool = False
    escalation_reason: Optional[EscalationReason] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def get_certainty_category(self) -> CertaintyLevel:
        """Get the certainty category based on percentage"""
        if self.certainty_level >= 90:
            return CertaintyLevel.VERY_HIGH
        elif self.certainty_level >= 80:
            return CertaintyLevel.HIGH
        elif self.certainty_level >= 65:
            return CertaintyLevel.MEDIUM
        elif self.certainty_level >= 45:
            return CertaintyLevel.LOW
        else:
            return CertaintyLevel.VERY_LOW

    def should_escalate(self) -> bool:
        """Determine if this decision should be escalated"""
        return (
            self.certainty_level < 65 or
            self.requires_consultation or
            self.escalation_reason is not None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

class CertaintyFramework:
    """
    Central framework for managing certainty thresholds and agent confidence
    """
    
    def __init__(self, config_file: str = "agent_decisions.yaml"):
        self.config_file = config_file
        self.certainty_thresholds = self._load_thresholds()
        self.agent_weights = self._load_agent_weights()
        self.decision_history: List[AgentDecision] = []
        self.agent_consultations: Dict[str, List[AgentDecision]] = {}
        
    def _load_thresholds(self) -> Dict[DecisionType, Dict[str, float]]:
        """Load certainty thresholds from configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('certainty_thresholds', self._default_thresholds())
            else:
                return self._default_thresholds()
        except Exception as e:
            logger.warning(f"Failed to load thresholds from {self.config_file}: {e}")
            return self._default_thresholds()
    
    def _default_thresholds(self) -> Dict[DecisionType, Dict[str, float]]:
        """Default certainty thresholds"""
        return {
            DecisionType.ARCHITECTURE: {
                'ping_pong_exit': 90,      # Very high for architecture
                'escalation_trigger': 70,   # Architecture disagreements are critical
                'user_notification': 60,    # User needs to know about arch issues
                'auto_decision': 40         # Low threshold for auto decisions
            },
            DecisionType.FEATURE_DESIGN: {
                'ping_pong_exit': 85,
                'escalation_trigger': 65,
                'user_notification': 50,
                'auto_decision': 35
            },
            DecisionType.IMPLEMENTATION: {
                'ping_pong_exit': 80,
                'escalation_trigger': 60,
                'user_notification': 45,
                'auto_decision': 30
            },
            DecisionType.UI_DESIGN: {
                'ping_pong_exit': 75,
                'escalation_trigger': 55,
                'user_notification': 40,
                'auto_decision': 25
            },
            DecisionType.STYLING: {
                'ping_pong_exit': 70,
                'escalation_trigger': 50,
                'user_notification': 35,
                'auto_decision': 20
            },
            DecisionType.SECURITY: {
                'ping_pong_exit': 95,      # Extremely high for security
                'escalation_trigger': 85,   # Security is critical
                'user_notification': 75,    # Always notify user of security decisions
                'auto_decision': 60         # Higher threshold for auto security decisions
            },
            DecisionType.TESTING: {
                'ping_pong_exit': 80,
                'escalation_trigger': 60,
                'user_notification': 45,
                'auto_decision': 30
            },
            DecisionType.DEPLOYMENT: {
                'ping_pong_exit': 90,      # High for deployment
                'escalation_trigger': 75,   # Deployment issues are critical
                'user_notification': 65,    # User should know about deployment
                'auto_decision': 50         # Higher threshold for auto deployment
            },
            DecisionType.SYSTEM_CHANGE: {
                'ping_pong_exit': 95,      # Extremely high for system changes
                'escalation_trigger': 80,   # System changes are critical
                'user_notification': 70,    # Always notify user of system changes
                'auto_decision': 55         # Higher threshold for auto system changes
            }
        }
    
    def _load_agent_weights(self) -> Dict[DecisionType, Dict[str, float]]:
        """Load agent weights for different decision types"""
        return {
            DecisionType.ARCHITECTURE: {
                'architect': 1.0,
                'senior_developer': 0.8,
                'security_engineer': 0.7,
                'devops': 0.6,
                'junior_developer': 0.4
            },
            DecisionType.SECURITY: {
                'security_engineer': 1.0,
                'architect': 0.8,
                'senior_developer': 0.6,
                'devops': 0.7,
                'junior_developer': 0.3
            },
            DecisionType.UI_DESIGN: {
                'ui_designer': 1.0,
                'product_analyst': 0.8,
                'ux_researcher': 0.9,
                'developer': 0.5,
                'architect': 0.4
            },
            DecisionType.IMPLEMENTATION: {
                'senior_developer': 1.0,
                'developer': 0.8,
                'architect': 0.7,
                'code_reviewer': 0.9,
                'junior_developer': 0.5
            }
        }
    
    async def evaluate_decision(self, decision: AgentDecision) -> Dict[str, Any]:
        """Evaluate a decision based on certainty thresholds"""
        self.decision_history.append(decision)
        
        thresholds = self.certainty_thresholds.get(decision.decision_type, self._default_thresholds()[DecisionType.IMPLEMENTATION])
        
        evaluation = {
            'decision_id': decision.agent_id,
            'certainty_level': decision.certainty_level,
            'certainty_category': decision.get_certainty_category().value,
            'should_escalate': decision.should_escalate(),
            'requires_consultation': decision.requires_consultation,
            'next_actions': [],
            'thresholds_used': thresholds
        }
        
        # Determine next actions based on certainty level
        if decision.certainty_level < thresholds['user_notification']:
            evaluation['next_actions'].append('request_user_approval')
        elif decision.certainty_level < thresholds['escalation_trigger']:
            evaluation['next_actions'].append('consult_peers')
        elif decision.certainty_level < thresholds['ping_pong_exit']:
            evaluation['next_actions'].append('escalate_to_supervisor')
        else:
            evaluation['next_actions'].append('proceed_with_confidence')
            
        return evaluation
    
    async def initiate_consultation(self, 
                                  requesting_agent: str,
                                  decision: AgentDecision,
                                  target_agents: List[str]) -> str:
        """Initiate consultation with target agents"""
        consultation_id = f"consultation_{len(self.agent_consultations)}"
        
        self.agent_consultations[consultation_id] = [decision]
        
        # In a real implementation, this would send messages to target agents
        logger.info(f"Initiated consultation {consultation_id} with agents: {target_agents}")
        
        return consultation_id
    
    async def add_consultation_response(self, consultation_id: str, 
                                      response_decision: AgentDecision) -> Dict[str, Any]:
        """Add a response to an ongoing consultation"""
        if consultation_id not in self.agent_consultations:
            return {'error': 'Consultation not found'}
        
        self.agent_consultations[consultation_id].append(response_decision)
        
        # Analyze consensus
        decisions = self.agent_consultations[consultation_id]
        consensus_result = await self._analyze_consensus(decisions)
        
        return {
            'consultation_id': consultation_id,
            'response_added': True,
            'consensus_analysis': consensus_result,
            'total_responses': len(decisions)
        }
    
    async def _analyze_consensus(self, decisions: List[AgentDecision]) -> Dict[str, Any]:
        """Analyze consensus among multiple decisions"""
        if not decisions:
            return {'consensus': 'no_decisions'}
        
        # Calculate average certainty
        avg_certainty = sum(d.certainty_level for d in decisions) / len(decisions)
        
        # Calculate weighted certainty if agent weights are available
        decision_type = decisions[0].decision_type
        agent_weights = self.agent_weights.get(decision_type, {})
        
        if agent_weights:
            weighted_sum = sum(
                d.certainty_level * agent_weights.get(d.agent_id, 0.5)
                for d in decisions
            )
            weight_sum = sum(agent_weights.get(d.agent_id, 0.5) for d in decisions)
            weighted_certainty = weighted_sum / weight_sum if weight_sum > 0 else avg_certainty
        else:
            weighted_certainty = avg_certainty
        
        # Check for conflicting decisions
        unique_decisions = set(d.decision_content for d in decisions)
        has_conflict = len(unique_decisions) > 1
        
        # Determine consensus strength
        thresholds = self.certainty_thresholds.get(decision_type, self._default_thresholds()[DecisionType.IMPLEMENTATION])
        
        if weighted_certainty >= thresholds['ping_pong_exit']:
            consensus_strength = 'strong'
        elif weighted_certainty >= thresholds['escalation_trigger']:
            consensus_strength = 'moderate'
        else:
            consensus_strength = 'weak'
        
        return {
            'consensus_strength': consensus_strength,
            'average_certainty': avg_certainty,
            'weighted_certainty': weighted_certainty,
            'has_conflict': has_conflict,
            'decision_count': len(decisions),
            'participating_agents': [d.agent_id for d in decisions],
            'unique_decisions': list(unique_decisions),
            'recommended_action': self._get_recommended_action(weighted_certainty, thresholds)
        }
    
    def _get_recommended_action(self, certainty: float, thresholds: Dict[str, float]) -> str:
        """Get recommended action based on certainty and thresholds"""
        if certainty >= thresholds['ping_pong_exit']:
            return 'proceed_with_decision'
        elif certainty >= thresholds['escalation_trigger']:
            return 'escalate_to_supervisor'
        elif certainty >= thresholds['user_notification']:
            return 'consult_additional_agents'
        else:
            return 'request_user_approval'
    
    async def should_escalate_to_user(self, decision: AgentDecision) -> bool:
        """Determine if a decision should be escalated to user"""
        if decision.escalation_reason in [
                EscalationReason.SECURITY_CONCERN,
                EscalationReason.USER_REQUIREMENT_UNCLEAR,
                EscalationReason.PERFORMANCE_IMPACT
        ]:
            return True
        
        thresholds = self.certainty_thresholds.get(decision.decision_type, self._default_thresholds()[DecisionType.IMPLEMENTATION])
        return decision.certainty_level < thresholds['user_notification']
    
    async def get_decision_history(self, agent_name: Optional[str] = None, 
                                 decision_type: Optional[DecisionType] = None) -> List[AgentDecision]:
        """Get filtered decision history"""
        history = self.decision_history.copy()
        
        if agent_name:
            history = [d for d in history if d.agent_id == agent_name]
        
        if decision_type:
            history = [d for d in history if d.decision_type == decision_type]
        
        return history
    
    async def get_active_consultations(self) -> Dict[str, List[AgentDecision]]:
        """Get all active consultations"""
        return self.agent_consultations.copy()
    
    async def export_decision_log(self, filepath: str):
        """Export decision log to file"""
        log_data = {
            'decision_history': [d.to_dict() for d in self.decision_history],
            'active_consultations': {
                k: [d.to_dict() for d in v] 
                for k, v in self.agent_consultations.items()
            },
            'thresholds': {k.value: v for k, v in self.certainty_thresholds.items()},
            'agent_weights': {k.value: v for k, v in self.agent_weights.items()},
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"Decision log exported to {filepath}")

def create_decision(agent_name: str, 
                   decision_type: DecisionType, 
                   certainty: float,
                   content: str,
                   reasoning: str,
                   alternatives: Optional[List[str]] = None) -> AgentDecision:
    """Helper function to create an agent decision"""
    return AgentDecision(
        agent_id=agent_name,
        decision_type=decision_type,
        certainty_level=certainty,
        decision_content=content,
        reasoning=reasoning,
        alternative_options=alternatives or []
    )

# Example usage
if __name__ == "__main__":
    async def demo_certainty_framework():
        framework = CertaintyFramework()
        
        # Create a test decision
        decision = create_decision(
            agent_name="architect",
            decision_type=DecisionType.ARCHITECTURE,
            certainty=75.0,
            content="Use microservices architecture",
            reasoning="Better scalability for multi-user system",
            alternatives=["Monolithic", "Serverless"]
        )
        
        # Evaluate the decision
        result = await framework.evaluate_decision(decision)
        print(f"Decision evaluation: {result}")
    
    import asyncio
    asyncio.run(demo_certainty_framework())
