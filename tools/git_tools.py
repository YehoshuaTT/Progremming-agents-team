import subprocess

def git_create_branch(branch_name: str):
    """Creates a new branch in Git."""
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    print(f"Created and switched to new branch: {branch_name}")

def git_add_and_commit(message: str):
    """Adds all changes and commits them."""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    print(f"Committed changes with message: {message}")

def git_create_pull_request(title: str, body: str):
    """Creates a new pull request."""
    # This is a placeholder. In a real implementation, this would use the GitHub API or a library like PyGithub.
    print(f"Creating pull request with title: {title}")
