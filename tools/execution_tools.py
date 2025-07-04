import subprocess

def execute_shell_command(command: str):
    """Runs a shell (terminal) command."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        print(result.stderr)
        return result.stderr
    return result.stdout
