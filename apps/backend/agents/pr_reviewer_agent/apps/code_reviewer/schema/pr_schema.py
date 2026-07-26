from pydantic import BaseModel
from datetime import datetime
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.review_job import ReviewJobStatusEnum

class ReviewJobData(BaseModel):
    """
     {
    "id": 1001,
    "pr_id": 25,
    "status": "queued",
    "attempts": 0,
    "queued_at": "2026-07-19T10:00:00Z"
    }
    """
    status: ReviewJobStatusEnum
    attempts : int
    queued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None

class PullRequestData(BaseModel):
    repo_id: int
    pr_number: int
    commit_sha: str
    author: str
    state: str
    title: str
    description: str | None
    source_branch: str
    target_branch: str
    url: str
    closed_at: datetime | None
    merged_at: datetime | None
    full_name: str | None = None
    owner: str | None = None
    default_branch: str | None = None
    pr_action: str
    review_job: ReviewJobData | None = None