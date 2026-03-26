from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph import graph
from langchain_core.tools import tool
import os,sys
import subprocess

import requests

# from openai_tool import ai


@tool
def get_current_weather(location: str) -> str:
    """Get the current weather in a given location"""

    # TODO!: Do an actual API Call
    print("🔨 Tool Called: get_weather", location)
    
    # url = f"https://wttr.in/{location}?format=%C+%t"
    # response = requests.get(url, timeout=5)
    response = {'status_code': 200, 'text': 'Sunny, 25°C'}  # Mocked response
    if response['status_code'] == 200:
        return f"The weather in {location} is {response['text']}."
    return "Something went wrong"

import subprocess

@tool
def apply_command(command: str):
    """Execute a system command"""

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        output = result.stdout
        error = result.stderr

        return f"""
Command: {command}
Exit Code: {result.returncode}

Output:
{output}

Error:
{error}
"""

    except Exception as e:
        return str(e)
    
import os

PROJECT_ROOT = "/home/ubuntu/Documents/test/cli/neroCLI"

@tool
def list_directory(path: str = "."):
    """List files and directories relative to project root"""
    print(f"🔨 Tool Called: list_directory with path '{path}'")
    full_path = os.path.join(PROJECT_ROOT, path)
    print(f"Resolved full path: {full_path}")  # Debug print to check path resolution
    if not os.path.exists(full_path):
        return f"Path does not exist: {path}"

    return "\n".join(os.listdir(full_path))

@tool
def create_directory(path: str):
    """Create a directory."""
    print(f"🔨 Tool Called: create_directory with path '{path}'")
    import os
    os.makedirs(path, exist_ok=True)
    return f"Directory created: {path}"

@tool
def read_file(path: str):
    """Read file content."""
    print(f"🔨 Tool Called: read_file with path '{path}'")
    with open(path, "r") as f:
        return f.read()
    


@tool
def two_sum(a: int, b: int) -> int:
    """Return the sum of two numbers"""
    return a + b

@tool
def update_file_data(path: str, new_content: str):
    """Update file content."""
    print(f"🔨 Tool Called: update_file_data with path '{path}'")
    with open(path, "w") as f:
        f.write(new_content)
    return f"File updated: {path}"
# apply_command("python3 openai_tool/openai_tool_graph.py")