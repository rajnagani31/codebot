from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.pull_request import PullRequest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


class CodeReviewRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create_pull_request(self, pr_data):
        session = self.session_factory()
        try:
            # closed = 'closed'
            # Convert pr_data dict to PullRequest model instance
            pr_instance = PullRequest(
                repo_id=pr_data.repo_id,
                pr_number=pr_data.pr_number,
                commit_sha=pr_data.commit_sha,
                author=pr_data.author,
                state=pr_data.state,
                title=pr_data.title,
                description=pr_data.description,
                source_branch=pr_data.source_branch,
                target_branch=pr_data.target_branch,
                url=pr_data.url ,
                closed_at=pr_data.closed_at ,
                merged_at=pr_data.merged_at
            )
            # pr_data = PullRequest(**pr_data)
            session.add(pr_instance)
            session.commit()
            return pr_instance
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()