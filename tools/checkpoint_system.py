"""
Advanced Error Handling and Recovery System
Task Checkpointing Implementation
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

@dataclass
class TaskCheckpoint:
    """Represents a checkpoint of task execution state"""
    task_id: str
    workflow_id: str
    agent_name: str
    checkpoint_id: str
    timestamp: str
    progress_percentage: float
    state_data: Dict[str, Any]
    intermediate_results: Dict[str, Any]
    dependencies_completed: List[str]
    context: Dict[str, Any]
    retry_count: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskCheckpoint':
        """Create checkpoint from dictionary"""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert checkpoint to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskCheckpoint':
        """Create checkpoint from JSON string"""
        return cls.from_dict(json.loads(json_str))

class CheckpointManager:
    """Manages task checkpoints - creation, storage, and retrieval"""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.active_checkpoints: Dict[str, TaskCheckpoint] = {}
        
        # Load existing checkpoints
        self._load_existing_checkpoints()
    
    def create_checkpoint(self, 
                         task_id: str,
                         workflow_id: str,
                         agent_name: str,
                         progress_percentage: float,
                         state_data: Dict[str, Any],
                         intermediate_results: Dict[str, Any],
                         dependencies_completed: List[str],
                         context: Dict[str, Any]) -> TaskCheckpoint:
        """Create a new checkpoint"""
        
        # Generate unique checkpoint ID
        checkpoint_id = self._generate_checkpoint_id(task_id, workflow_id)
        
        checkpoint = TaskCheckpoint(
            task_id=task_id,
            workflow_id=workflow_id,
            agent_name=agent_name,
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now().isoformat(),
            progress_percentage=progress_percentage,
            state_data=state_data,
            intermediate_results=intermediate_results,
            dependencies_completed=dependencies_completed,
            context=context
        )
        
        # Store in memory and disk
        self.active_checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)
        
        return checkpoint
    
    def update_checkpoint(self, checkpoint_id: str, **updates) -> Optional[TaskCheckpoint]:
        """Update an existing checkpoint"""
        if checkpoint_id not in self.active_checkpoints:
            return None
        
        checkpoint = self.active_checkpoints[checkpoint_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(checkpoint, key):
                setattr(checkpoint, key, value)
        
        # Update timestamp
        checkpoint.timestamp = datetime.now().isoformat()
        
        # Save to disk
        self._save_checkpoint(checkpoint)
        
        return checkpoint
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[TaskCheckpoint]:
        """Retrieve a checkpoint by ID"""
        return self.active_checkpoints.get(checkpoint_id)
    
    def get_latest_checkpoint(self, task_id: str) -> Optional[TaskCheckpoint]:
        """Get the most recent checkpoint for a task"""
        task_checkpoints = [
            cp for cp in self.active_checkpoints.values()
            if cp.task_id == task_id
        ]
        
        if not task_checkpoints:
            return None
        
        # Return the most recent checkpoint
        return max(task_checkpoints, key=lambda cp: cp.timestamp)
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint"""
        if checkpoint_id not in self.active_checkpoints:
            return False
        
        # Remove from memory
        del self.active_checkpoints[checkpoint_id]
        
        # Remove from disk
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
        
        return True
    
    def cleanup_completed_task(self, task_id: str):
        """Remove all checkpoints for a completed task"""
        checkpoints_to_remove = [
            cp.checkpoint_id for cp in self.active_checkpoints.values()
            if cp.task_id == task_id
        ]
        
        for checkpoint_id in checkpoints_to_remove:
            self.delete_checkpoint(checkpoint_id)
    
    def cleanup_old_checkpoints(self, max_age_hours: int = 24):
        """Remove checkpoints older than specified hours"""
        current_time = datetime.now()
        
        checkpoints_to_remove = []
        for checkpoint in self.active_checkpoints.values():
            checkpoint_time = datetime.fromisoformat(checkpoint.timestamp)
            age_hours = (current_time - checkpoint_time).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                checkpoints_to_remove.append(checkpoint.checkpoint_id)
        
        for checkpoint_id in checkpoints_to_remove:
            self.delete_checkpoint(checkpoint_id)
    
    def list_checkpoints(self, workflow_id: Optional[str] = None) -> List[TaskCheckpoint]:
        """List all checkpoints, optionally filtered by workflow"""
        checkpoints = list(self.active_checkpoints.values())
        
        if workflow_id:
            checkpoints = [cp for cp in checkpoints if cp.workflow_id == workflow_id]
        
        return sorted(checkpoints, key=lambda cp: cp.timestamp, reverse=True)
    
    def _generate_checkpoint_id(self, task_id: str, workflow_id: str) -> str:
        """Generate a unique checkpoint ID"""
        timestamp = str(int(time.time() * 1000))
        data = f"{task_id}_{workflow_id}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _save_checkpoint(self, checkpoint: TaskCheckpoint):
        """Save checkpoint to disk"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            f.write(checkpoint.to_json())
    
    def _load_existing_checkpoints(self):
        """Load existing checkpoints from disk"""
        if not self.checkpoint_dir.exists():
            return
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                
                checkpoint = TaskCheckpoint.from_dict(checkpoint_data)
                self.active_checkpoints[checkpoint.checkpoint_id] = checkpoint
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error loading checkpoint {checkpoint_file}: {e}")
                # Remove corrupted checkpoint file
                checkpoint_file.unlink()

# Global checkpoint manager instance
checkpoint_manager = CheckpointManager()
