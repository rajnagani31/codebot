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

            # Check Pr is available or not
            existing_pr = session.execute(
            select(PullRequest).where(
                PullRequest.pr_number == pr_data.pr_number
                        )
            ).scalar_one_or_none()

            if existing_pr:
                existing_pr.commit_sha = pr_data.commit_sha
                existing_pr.state = pr_data.state
                existing_pr.title = pr_data.title
                existing_pr.description = pr_data.description
                existing_pr.closed_at = pr_data.closed_at
                existing_pr.merged_at = pr_data.merged_at

                session.commit()
                session.refresh(existing_pr)
                return existing_pr

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
                url=pr_data.url,
                closed_at=pr_data.closed_at,
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