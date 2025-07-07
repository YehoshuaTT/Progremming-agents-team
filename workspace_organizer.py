#!/usr/bin/env python3
"""
Workspace Organizer for Agent Workflow System
Manages organized folder structure for each workflow run
"""

import os
import time
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any, Optional

class WorkspaceOrganizer:
    def __init__(self, base_workspace_dir: str = "workspace"):
        self.base_workspace_dir = Path(base_workspace_dir)
        self.base_workspace_dir.mkdir(exist_ok=True)
        
        # Create session-based main folder for this run
        self.session_id = self._generate_session_id()
        self.main_folder = self.base_workspace_dir / f"RUN-{self.session_id}"
        self.main_folder.mkdir(exist_ok=True)
        
        # Create subfolders
        self.artifacts_folder = self.main_folder / "artifacts"
        self.logs_folder = self.main_folder / "logs"
        self.results_folder = self.main_folder / "results"
        self.temp_folder = self.main_folder / "temp"
        
        # Create all subfolders
        for folder in [self.artifacts_folder, self.logs_folder, self.results_folder, self.temp_folder]:
            folder.mkdir(exist_ok=True)
        
        # Create session info file
        self._create_session_info()
        
        print(f"WORKSPACE: Created organized workspace at: {self.main_folder}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = int(time.time())
        return f"{timestamp}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def _create_session_info(self):
        """Create session information file"""
        session_info = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "workspace_path": str(self.main_folder),
            "subfolders": {
                "artifacts": str(self.artifacts_folder),
                "logs": str(self.logs_folder),
                "results": str(self.results_folder),
                "temp": str(self.temp_folder)
            },
            "status": "active"
        }
        
        session_file = self.main_folder / "session_info.json"
        with open(session_file, 'w') as f:
            json.dump(session_info, f, indent=2)
    
    def get_workflow_folder(self, workflow_id: str) -> Path:
        """Get dedicated folder for a specific workflow"""
        workflow_folder = self.results_folder / f"workflow-{workflow_id}"
        workflow_folder.mkdir(exist_ok=True)
        return workflow_folder
    
    def get_agent_folder(self, workflow_id: str, agent_name: str, iteration: int) -> Path:
        """Get dedicated folder for a specific agent in a workflow"""
        workflow_folder = self.get_workflow_folder(workflow_id)
        agent_folder = workflow_folder / f"{agent_name}-{iteration}"
        agent_folder.mkdir(exist_ok=True)
        return agent_folder
    
    def get_artifacts_folder(self, subfolder: Optional[str] = None) -> Path:
        """Get artifacts folder with optional subfolder"""
        if subfolder:
            folder = self.artifacts_folder / subfolder
            folder.mkdir(exist_ok=True)
            return folder
        return self.artifacts_folder
    
    def get_logs_folder(self, log_type: Optional[str] = None) -> Path:
        """Get logs folder with optional log type subfolder"""
        if log_type:
            folder = self.logs_folder / log_type
            folder.mkdir(exist_ok=True)
            return folder
        return self.logs_folder
    
    def get_temp_folder(self, subfolder: Optional[str] = None) -> Path:
        """Get temporary folder with optional subfolder"""
        if subfolder:
            folder = self.temp_folder / subfolder
            folder.mkdir(exist_ok=True)
            return folder
        return self.temp_folder
    
    def save_workflow_result(self, workflow_id: str, result: Dict[str, Any]) -> Path:
        """Save workflow result to organized location"""
        workflow_folder = self.get_workflow_folder(workflow_id)
        result_file = workflow_folder / "workflow_result.json"
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"WORKSPACE: Saved workflow result to: {result_file}")
        return result_file
    
    def save_workflow_summary(self, workflow_id: str, summary: Dict[str, Any]) -> Path:
        """Save workflow summary to organized location"""
        workflow_folder = self.get_workflow_folder(workflow_id)
        summary_file = workflow_folder / "workflow_summary.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"WORKSPACE: Saved workflow summary to: {summary_file}")
        return summary_file
    
    def create_agent_artifact(self, workflow_id: str, agent_name: str, iteration: int, 
                            artifact_name: str, content: str) -> Path:
        """Create artifact file for agent"""
        agent_folder = self.get_agent_folder(workflow_id, agent_name, iteration)
        artifact_file = agent_folder / artifact_name
        
        with open(artifact_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"WORKSPACE: Created artifact: {artifact_file}")
        return artifact_file
    
    def finalize_session(self, status: str = "completed"):
        """Finalize the workspace session"""
        session_file = self.main_folder / "session_info.json"
        
        if session_file.exists():
            with open(session_file, 'r') as f:
                session_info = json.load(f)
            
            session_info["status"] = status
            session_info["completed_at"] = datetime.now().isoformat()
            
            with open(session_file, 'w') as f:
                json.dump(session_info, f, indent=2)
        
        print(f"WORKSPACE: Session finalized with status: {status}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        import shutil
        
        if self.temp_folder.exists():
            try:
                shutil.rmtree(self.temp_folder)
                self.temp_folder.mkdir()
                print("WORKSPACE: Cleaned up temporary files")
            except Exception as e:
                print(f"WORKSPACE: Error cleaning temp files: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        summary = {
            "session_id": self.session_id,
            "main_folder": str(self.main_folder),
            "created_at": datetime.now().isoformat(),
            "folder_structure": {
                "artifacts": str(self.artifacts_folder),
                "logs": str(self.logs_folder),
                "results": str(self.results_folder),
                "temp": str(self.temp_folder)
            },
            "statistics": self._get_folder_stats()
        }
        
        return summary
    
    def _get_folder_stats(self) -> Dict[str, Any]:
        """Get statistics about folder contents"""
        stats = {
            "total_files": 0,
            "total_size_mb": 0.0,
            "workflow_count": 0,
            "artifact_count": 0
        }
        
        try:
            for item in self.main_folder.rglob("*"):
                if item.is_file():
                    stats["total_files"] += 1
                    stats["total_size_mb"] += item.stat().st_size / (1024 * 1024)
            
            # Count workflow folders
            if self.results_folder.exists():
                stats["workflow_count"] = len([f for f in self.results_folder.iterdir() if f.is_dir()])
            
            # Count artifacts
            if self.artifacts_folder.exists():
                stats["artifact_count"] = len([f for f in self.artifacts_folder.rglob("*") if f.is_file()])
        
        except Exception as e:
            print(f"WORKSPACE: Error getting folder stats: {e}")
        
        return stats
    
    @classmethod
    def get_existing_sessions(cls, base_workspace_dir: str = "workspace") -> list:
        """Get list of existing workspace sessions"""
        base_dir = Path(base_workspace_dir)
        sessions = []
        
        if base_dir.exists():
            for folder in base_dir.iterdir():
                if folder.is_dir() and folder.name.startswith("RUN-"):
                    session_info_file = folder / "session_info.json"
                    if session_info_file.exists():
                        try:
                            with open(session_info_file, 'r') as f:
                                session_info = json.load(f)
                            sessions.append(session_info)
                        except:
                            pass
        
        return sessions
    
    @classmethod
    def cleanup_old_sessions(cls, base_workspace_dir: str = "workspace", days_to_keep: int = 7) -> int:
        """Clean up old workspace sessions"""
        from datetime import timedelta
        import shutil
        
        base_dir = Path(base_workspace_dir)
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        if base_dir.exists():
            for folder in base_dir.iterdir():
                if folder.is_dir() and folder.name.startswith("RUN-"):
                    try:
                        # Check folder creation time
                        folder_time = datetime.fromtimestamp(folder.stat().st_ctime)
                        if folder_time < cutoff_date:
                            print(f"WORKSPACE: Removing old session: {folder.name}")
                            shutil.rmtree(folder)
                            removed_count += 1
                    except Exception as e:
                        print(f"WORKSPACE: Error removing session {folder.name}: {e}")
        
        print(f"WORKSPACE: Removed {removed_count} old sessions")
        return removed_count

# Global instance for easy access
_workspace_organizer = None

def get_workspace_organizer() -> WorkspaceOrganizer:
    """Get or create global workspace organizer instance"""
    global _workspace_organizer
    if _workspace_organizer is None:
        _workspace_organizer = WorkspaceOrganizer()
    return _workspace_organizer

def reset_workspace_organizer():
    """Reset global workspace organizer (for testing)"""
    global _workspace_organizer
    _workspace_organizer = None
