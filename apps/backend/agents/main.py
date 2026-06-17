from fastapi import FastAPI
from pr_reviewer_agent.apps.code_reviewer.routers.github import router as github

app = FastAPI()

app.include_router(github, prefix='/api')