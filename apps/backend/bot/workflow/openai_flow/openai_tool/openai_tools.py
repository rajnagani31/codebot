import os
import subprocess
from dataclasses import dataclass

from langchain_core.tools import tool

from apps.backend.bot.application.service.web_search_service import WebSearchService

# @tool
# def get_current_weather(location: str) -> str:
#     """Get the current weather in a given location."""
#     return f"Weather data is not connected yet for {location}."


@tool
def apply_command(command: str) -> str:
    """Execute a shell command and return stdout and stderr."""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
    )
    return (
        f"Command: {command}\n"
        f"Exit Code: {result.returncode}\n\n"
        f"Output:\n{result.stdout}\n\n"
        f"Error:\n{result.stderr}"
    )


PROJECT_ROOT = os.getcwd()


@tool
def list_directory(path: str = ".") -> str:
    """List files and directories relative to the current project root."""
    full_path = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(full_path):
        return f"Path does not exist: {path}"
    return "\n".join(sorted(os.listdir(full_path)))


@tool
def create_directory(path: str) -> str:
    """Create a directory."""
    os.makedirs(path, exist_ok=True)
    return f"Directory created: {path}"


@tool
def read_file(path: str) -> str:
    """Read file content from the local workspace."""
    with open(path, "r", encoding="utf-8") as file_obj:
        return file_obj.read()


@tool
def two_sum(a: int, b: int) -> int:
    """Return the sum of two numbers."""
    return a + b


@dataclass(slots=True)
class ToolCapabilities:
    web_search_enabled: bool = False


@dataclass(slots=True)
class ToolExecutionContext:
    web_search_service: WebSearchService | None = None


def build_tools(
    *,
    capabilities: ToolCapabilities,
    execution_context: ToolExecutionContext,
) -> list:
    tools = []

    if capabilities.web_search_enabled:
        if execution_context.web_search_service is None:
            raise ValueError(
                "web_search_service is required when web search tools are enabled"
            )

        @tool
        async def web_search(query: str) -> dict:
            """Search the web for current sources and return short summaries with URLs."""
            return {"query": query}

        @tool
        async def read_web_page(url: str) -> dict:
            """Read a specific web page and return a short summary of its contents."""
            return {"url": url}

        tools.extend([web_search, read_web_page])

    return tools

