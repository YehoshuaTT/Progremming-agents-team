import os

def read_file(path: str):
    """Reads the content of a specific file."""
    with open(path, "r") as f:
        return f.read()

def write_file(path: str, content: str):
    """Writes content to a specific file."""
    with open(path, "w") as f:
        f.write(content)
