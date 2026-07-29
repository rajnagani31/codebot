from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.pull_request import PullRequest
from sqlalchemy import select
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.repository import Repository
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import PullRequestData
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.review_job import ReviewJob


class CodeReviewRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_pull_request(self, pr_data: PullRequestData):
        session = self.session_factory()

        try:
            # breakpoint()
            repo = self.get_or_create_repository(session, pr_data)
            print('repo_data', pr_data.repo_id)
            print('owner', pr_data.owner)
            print("full_name", pr_data.full_name)

            repo_id = repo.id
            pr_number = pr_data.pr_number
            pr = self.get_pull_request(session, repo_id, pr_number)

            if pr:
                pr.commit_sha = pr_data.commit_sha
                pr.state = pr_data.state
                pr.title = pr_data.title
                pr.pr_action = pr_data.pr_action
                pr.description = pr_data.description
                pr.closed_at = pr_data.closed_at
                pr.merged_at = pr_data.merged_at

            else:
                
                pr = PullRequest(
                    repo_id=repo.id,
                    pr_number=pr_data.pr_number,
                    commit_sha=pr_data.commit_sha,
                    author=pr_data.author,
                    state=pr_data.state,
                    pr_action = pr_data.pr_action,
                    title=pr_data.title,
                    description=pr_data.description,
                    source_branch=pr_data.source_branch,
                    target_branch=pr_data.target_branch,
                    url=pr_data.url,
                    closed_at=pr_data.closed_at,
                    merged_at=pr_data.merged_at,
                )

                session.add(pr)
                session.flush()

                review_job = ReviewJob(
                    pr_id=pr.id,
                    status=pr_data.review_job.status,
                    attempts=pr_data.review_job.attempts,
                    queued_at=pr_data.review_job.queued_at,
                    )                           

                session.add(review_job)

            session.commit()
            session.refresh(pr)
            return pr


        except Exception:
            session.rollback()
            raise 

        finally:
            session.close()

    def get_or_create_repository(self,session, pr_data):
        try:
            data = pr_data
            pr_repo = session.execute(
                select(Repository).where(
                Repository.repo_id == data.repo_id,
                Repository.is_active == True
                )
            ).scalar_one_or_none()
            print("pr_repo_dataadadasd", pr_repo)
            if pr_repo:
                return pr_repo

            # TODO : This query might be change in further away becaue create repo data when user select and able or anable repository
            pr_repo_instance = Repository(
                repo_id = data.repo_id,
                user_id = 1,   # TODO : Still need set Auth service
                full_name = data.full_name,
                owner = data.owner,
                default_branch = data.default_branch,
                is_active = True,
                )

            session.add(pr_repo_instance)
            session.flush()   # gets ID without commit
            print("answe instance:",pr_repo_instance)
            return pr_repo_instance

        except Exception as e:
            print("Repository Error:", e)
            raise

    def get_pull_request(self,session, repo_id, pr_number):
        try:
            pr_instance = session.execute(
                select(PullRequest).where(
                    PullRequest.repo_id == repo_id,
                    PullRequest.pr_number == pr_number
                )
            ).scalar_one_or_none()

            return pr_instance

        except Exception as e:
            raise RuntimeError(f'ERROR {e}') from e
            