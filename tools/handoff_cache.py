#!/usr/bin/env python3
"""
Handoff Packet Caching System
Provides persistent storage and retrieval of agent handoff packets with workflow resumption
"""

import json
import time
import os
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import pickle
import gzip
from collections import defaultdict

from .handoff_system import HandoffPacket, TaskStatus, NextStepSuggestion

class WorkflowState(Enum):
    """Workflow state enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RESUMED = "resumed"

@dataclass
class WorkflowSession:
    """Workflow session with handoff packet history"""
    session_id: str
    workflow_name: str
    started_at: float
    updated_at: float
    state: WorkflowState
    handoff_packets: List[HandoffPacket]
    current_agent: str
    next_suggested_agent: str
    completion_percentage: float
    checkpoints: List[str]  # Task IDs that are checkpoints
    version: int = 1
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def add_handoff_packet(self, packet: HandoffPacket) -> None:
        """Add a handoff packet to the session"""
        self.handoff_packets.append(packet)
        self.updated_at = time.time()
        
        # Update current agent based on the packet
        self.current_agent = packet.agent_name
        
        # Update completion percentage based on status
        if packet.status == TaskStatus.SUCCESS:
            self.completion_percentage = min(100.0, self.completion_percentage + 10.0)
        elif packet.status == TaskStatus.FAILURE:
            self.state = WorkflowState.FAILED
        
        # Check if this is a checkpoint
        if packet.completed_task_id in self.checkpoints:
            self.metadata[f"checkpoint_{packet.completed_task_id}"] = {
                "timestamp": packet.timestamp,
                "agent": packet.agent_name,
                "status": packet.status.value
            }

    def is_resumable(self) -> bool:
        """Check if workflow can be resumed"""
        return self.state in [WorkflowState.PAUSED, WorkflowState.FAILED] and len(self.handoff_packets) > 0

    def get_last_successful_checkpoint(self) -> Optional[HandoffPacket]:
        """Get the last successful checkpoint for resumption"""
        for packet in reversed(self.handoff_packets):
            if packet.status == TaskStatus.SUCCESS and packet.completed_task_id in self.checkpoints:
                return packet
        return None

class HandoffCacheManager:
    """Manages handoff packet caching and workflow state persistence"""
    
    def __init__(self, cache_dir: str = "cache/handoff", max_sessions: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_sessions = max_sessions
        
        # In-memory cache for active sessions
        self.active_sessions: Dict[str, WorkflowSession] = {}
        self.session_lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "sessions_created": 0,
            "sessions_resumed": 0,
            "packets_cached": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "checkpoints_created": 0,
            "workflows_completed": 0,
            "workflows_failed": 0
        }
        
        # Load existing sessions
        self._load_existing_sessions()

    def _load_existing_sessions(self) -> None:
        """Load existing sessions from disk"""
        try:
            for session_file in self.cache_dir.glob("*.pkl.gz"):
                try:
                    with gzip.open(session_file, 'rb') as f:
                        session = pickle.load(f)
                        if isinstance(session, WorkflowSession):
                            self.active_sessions[session.session_id] = session
                except Exception as e:
                    print(f"Warning: Could not load session {session_file}: {e}")
        except Exception as e:
            print(f"Warning: Could not load sessions: {e}")

    def create_workflow_session(self, workflow_name: str, initial_agent: str) -> str:
        """Create a new workflow session"""
        with self.session_lock:
            session_id = self._generate_session_id(workflow_name)
            
            session = WorkflowSession(
                session_id=session_id,
                workflow_name=workflow_name,
                started_at=time.time(),
                updated_at=time.time(),
                state=WorkflowState.ACTIVE,
                handoff_packets=[],
                current_agent=initial_agent,
                next_suggested_agent="",
                completion_percentage=0.0,
                checkpoints=[]
            )
            
            self.active_sessions[session_id] = session
            self.stats["sessions_created"] += 1
            
            # Persist to disk
            self._persist_session(session)
            
            return session_id

    def add_handoff_packet(self, session_id: str, packet: HandoffPacket, is_checkpoint: bool = False) -> bool:
        """Add a handoff packet to a session"""
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Mark as checkpoint if needed
            if is_checkpoint:
                session.checkpoints.append(packet.completed_task_id)
                self.stats["checkpoints_created"] += 1
            
            session.add_handoff_packet(packet)
            self.stats["packets_cached"] += 1
            
            # Update workflow state based on packet
            if packet.status == TaskStatus.SUCCESS and session.completion_percentage >= 100:
                session.state = WorkflowState.COMPLETED
                self.stats["workflows_completed"] += 1
            elif packet.status == TaskStatus.FAILURE:
                session.state = WorkflowState.FAILED
                self.stats["workflows_failed"] += 1
            
            # Persist to disk
            self._persist_session(session)
            
            return True

    def get_session(self, session_id: str) -> Optional[WorkflowSession]:
        """Get a workflow session"""
        with self.session_lock:
            if session_id in self.active_sessions:
                self.stats["cache_hits"] += 1
                return self.active_sessions[session_id]
            
            # Try to load from disk
            session = self._load_session_from_disk(session_id)
            if session:
                self.active_sessions[session_id] = session
                self.stats["cache_hits"] += 1
                return session
            
            self.stats["cache_misses"] += 1
            return None

    def pause_workflow(self, session_id: str) -> bool:
        """Pause a workflow session"""
        with self.session_lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.state = WorkflowState.PAUSED
                session.updated_at = time.time()
                self._persist_session(session)
                return True
            return False

    def resume_workflow(self, session_id: str) -> Optional[HandoffPacket]:
        """Resume a workflow session from last checkpoint"""
        with self.session_lock:
            session = self.get_session(session_id)
            if not session or not session.is_resumable():
                return None
            
            # Get last successful checkpoint
            last_checkpoint = session.get_last_successful_checkpoint()
            if not last_checkpoint:
                # No checkpoint, resume from beginning
                return None
            
            # Resume the workflow
            session.state = WorkflowState.RESUMED
            session.updated_at = time.time()
            self.stats["sessions_resumed"] += 1
            
            # Persist state
            self._persist_session(session)
            
            return last_checkpoint

    def get_workflow_history(self, session_id: str) -> List[HandoffPacket]:
        """Get the complete handoff packet history for a workflow"""
        session = self.get_session(session_id)
        if session:
            return session.handoff_packets.copy()
        return []

    def get_active_workflows(self) -> List[str]:
        """Get list of active workflow session IDs"""
        with self.session_lock:
            return [
                session_id for session_id, session in self.active_sessions.items()
                if session.state == WorkflowState.ACTIVE
            ]

    def get_resumable_workflows(self) -> List[str]:
        """Get list of resumable workflow session IDs"""
        with self.session_lock:
            return [
                session_id for session_id, session in self.active_sessions.items()
                if session.is_resumable()
            ]

    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions"""
        with self.session_lock:
            current_time = time.time()
            cutoff_time = current_time - (max_age_days * 24 * 3600)
            
            expired_sessions = []
            for session_id, session in self.active_sessions.items():
                if session.updated_at < cutoff_time and session.state in [WorkflowState.COMPLETED, WorkflowState.FAILED]:
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                # Remove from disk
                session_file = self.cache_dir / f"{session_id}.pkl.gz"
                if session_file.exists():
                    session_file.unlink()
            
            return len(expired_sessions)

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.session_lock:
            stats = self.stats.copy()
            stats["active_sessions"] = len(self.active_sessions)
            stats["total_disk_sessions"] = len(list(self.cache_dir.glob("*.pkl.gz")))
            
            # Calculate hit rate
            total_requests = stats["cache_hits"] + stats["cache_misses"]
            stats["hit_rate"] = (stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return stats

    def _generate_session_id(self, workflow_name: str) -> str:
        """Generate a unique session ID"""
        timestamp = str(time.time())
        unique_string = f"{workflow_name}_{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _persist_session(self, session: WorkflowSession) -> None:
        """Persist session to disk"""
        try:
            session_file = self.cache_dir / f"{session.session_id}.pkl.gz"
            with gzip.open(session_file, 'wb') as f:
                pickle.dump(session, f)
        except Exception as e:
            print(f"Warning: Could not persist session {session.session_id}: {e}")

    def _load_session_from_disk(self, session_id: str) -> Optional[WorkflowSession]:
        """Load session from disk"""
        try:
            session_file = self.cache_dir / f"{session_id}.pkl.gz"
            if session_file.exists():
                with gzip.open(session_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load session {session_id}: {e}")
        return None

# Global instance
_handoff_cache_manager = None

def get_handoff_cache_manager() -> HandoffCacheManager:
    """Get the global handoff cache manager instance"""
    global _handoff_cache_manager
    if _handoff_cache_manager is None:
        _handoff_cache_manager = HandoffCacheManager()
    return _handoff_cache_manager

def create_workflow_session(workflow_name: str, initial_agent: str) -> str:
    """Create a new workflow session"""
    return get_handoff_cache_manager().create_workflow_session(workflow_name, initial_agent)

def add_handoff_packet(session_id: str, packet: HandoffPacket, is_checkpoint: bool = False) -> bool:
    """Add a handoff packet to a session"""
    return get_handoff_cache_manager().add_handoff_packet(session_id, packet, is_checkpoint)

def resume_workflow(session_id: str) -> Optional[HandoffPacket]:
    """Resume a workflow session"""
    return get_handoff_cache_manager().resume_workflow(session_id)

def get_workflow_history(session_id: str) -> List[HandoffPacket]:
    """Get workflow history"""
    return get_handoff_cache_manager().get_workflow_history(session_id)
