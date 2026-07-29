"""Compatibility module for Uvicorn entrypoints.

This lets commands like:

    uvicorn agent:app --reload

work from the project root by re-exporting the real FastAPI app.
"""

from apps.backend.bot.application.main import app

# Bot service : uvicorn agent:app --reload --port 8001 (dir: PS E:\raj\codebot\codebot> )
# agent service : uvicorn apps.backend.agents.pr_reviewer_agent.apps.main:app --reload (dir: PS E:\raj\codebot\codebot> )
# agent service : python -m uvicorn apps.backend.agents.pr_reviewer_agent.apps.main:app --reload --port 8080