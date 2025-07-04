import subprocess
from typing import Dict, Any
from tools.tool_cache import cache_tool_output

def git_create_branch(branch_name: str):
    """Creates a new branch in Git."""
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    print(f"Created and switched to new branch: {branch_name}")

def git_add_and_commit(message: str):
    """Adds all changes and commits them."""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    print(f"Committed changes with message: {message}")

@cache_tool_output("git_status")
def git_status(agent_id: str = "unknown") -> Dict[str, Any]:
    """Get git status with caching."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        changes = []
        
        for line in lines:
            if len(line) >= 3:
                status = line[:2]
                file_path = line[3:]
                changes.append({
                    "status": status,
                    "file": file_path
                })
        
        return {
            "success": True,
            "changes": changes,
            "clean": len(changes) == 0,
            "error": ""
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "changes": [],
            "clean": False,
            "error": f"Git status failed: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "changes": [],
            "clean": False,
            "error": str(e)
        }

@cache_tool_output("git_log")
def git_log(limit: int = 10, agent_id: str = "unknown") -> Dict[str, Any]:
    """Get git log with caching."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={limit}", "--oneline"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        commits = []
        
        for line in lines:
            if line:
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1]
                    })
        
        return {
            "success": True,
            "commits": commits,
            "error": ""
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "commits": [],
            "error": f"Git log failed: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "commits": [],
            "error": str(e)
        }

@cache_tool_output("git_diff")
def git_diff(file_path: str = None, agent_id: str = "unknown") -> Dict[str, Any]:
    """Get git diff with caching."""
    try:
        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "success": True,
            "diff": result.stdout,
            "has_changes": bool(result.stdout.strip()),
            "error": ""
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "diff": "",
            "has_changes": False,
            "error": f"Git diff failed: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "diff": "",
            "has_changes": False,
            "error": str(e)
        }

def git_create_pull_request(title: str, body: str):
    """Creates a new pull request."""
    # This is a placeholder. In a real implementation, this would use the GitHub API or a library like PyGithub.
    print(f"Creating pull request with title: {title}")
