from pydantic import BaseModel
from datetime import datetime

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