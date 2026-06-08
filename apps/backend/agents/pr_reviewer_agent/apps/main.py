from fastapi import FastAPI
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.routers.github import router as github

app = FastAPI()

app.include_router(github, prefix='/api')