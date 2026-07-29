from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.pull_request import (
    PullRequest,
)
from sqlalchemy import select
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.repository import (
    Repository,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import (
    PullRequestData,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.review_job import (
    ReviewJob,
)


class CodeReviewRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_pull_request(self, pr_data: PullRequestData):
        session = self.session_factory()

        try:
            # breakpoint()
            repo = self.get_or_create_repository(session, pr_data)
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
                    pr_action=pr_data.pr_action,
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

    def save_installation_repositories(self, payload: dict):
        session = self.session_factory()

        try:
            installation = payload.get("installation") or {}
            installation_id = installation.get("id")
            account = installation.get("account") or {}
            github_account_id = account.get("id")
            repositories = (
                payload.get("repositories") or payload.get("repositories_added") or []
            )
            repositories_removed = payload.get("repositories_removed") or []

            saved_repositories = []
            for repository_data in repositories:
                saved_repositories.append(
                    self.upsert_repository_from_github(
                        session,
                        repository_data,
                        installation_id=installation_id,
                        github_account_id=github_account_id,
                    )
                )

            for repository_data in repositories_removed:
                self.mark_repository_inactive(session, repository_data.get("id"))

            if payload.get("action") == "deleted":
                for repository_data in repositories:
                    self.mark_repository_inactive(session, repository_data.get("id"))

            session.commit()
            return saved_repositories

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def get_repository_by_github_repo_id(self, repo_id: int):
        session = self.session_factory()
        try:
            return session.execute(
                select(Repository).where(
                    Repository.repo_id == repo_id, Repository.is_active == True
                )
            ).scalar_one_or_none()
        finally:
            session.close()

    def get_or_create_repository(self, session, pr_data):
        try:
            data = pr_data
            pr_repo = session.execute(
                select(Repository).where(
                    Repository.repo_id == data.repo_id, Repository.is_active == True
                )
            ).scalar_one_or_none()
            if pr_repo:
                self._update_repository_metadata(
                    pr_repo,
                    installation_id=data.installation_id,
                    github_account_id=data.github_account_id,
                    full_name=data.full_name,
                    owner=data.owner,
                    default_branch=data.default_branch,
                )
                return pr_repo

            # TODO : This query might be change in further away becaue create repo data when user select and able or anable repository
            pr_repo_instance = Repository(
                repo_id=data.repo_id,
                installation_id=data.installation_id,
                github_account_id=data.github_account_id,
                user_id=1,  # TODO : Still need set Auth service
                full_name=data.full_name,
                owner=data.owner,
                default_branch=data.default_branch,
                is_active=True,
            )

            session.add(pr_repo_instance)
            session.flush()  # gets ID without commit
            return pr_repo_instance

        except Exception as e:
            print("Repository Error:", e)
            raise

    def upsert_repository_from_github(
        self,
        session,
        repository_data: dict,
        *,
        installation_id: int | None,
        github_account_id: int | None,
    ):
        repo_id = repository_data.get("id")
        pr_repo = session.execute(
            select(Repository).where(
                Repository.repo_id == repo_id, Repository.is_active == True
            )
        ).scalar_one_or_none()

        owner_data = repository_data.get("owner") or {}
        owner = (
            owner_data.get("login")
            or repository_data.get("full_name", "").split("/")[0]
        )

        if pr_repo:
            self._update_repository_metadata(
                pr_repo,
                installation_id=installation_id,
                github_account_id=github_account_id,
                full_name=repository_data.get("full_name"),
                owner=owner,
                default_branch=repository_data.get("default_branch"),
            )
            return pr_repo

        pr_repo = Repository(
            repo_id=repo_id,
            installation_id=installation_id,
            github_account_id=github_account_id,
            user_id=1,  # TODO: connect to authenticated owner when onboarding exists.
            full_name=repository_data.get("full_name"),
            owner=owner,
            default_branch=repository_data.get("default_branch"),
            is_active=True,
        )
        session.add(pr_repo)
        session.flush()
        return pr_repo

    def mark_repository_inactive(self, session, repo_id: int | None) -> None:
        if repo_id is None:
            return

        pr_repo = session.execute(
            select(Repository).where(Repository.repo_id == repo_id)
        ).scalar_one_or_none()

        if pr_repo:
            pr_repo.is_active = False

    def _update_repository_metadata(
        self,
        repository: Repository,
        *,
        installation_id: int | None = None,
        github_account_id: int | None = None,
        full_name: str | None = None,
        owner: str | None = None,
        default_branch: str | None = None,
    ) -> None:
        if installation_id is not None:
            repository.installation_id = installation_id
        if github_account_id is not None:
            repository.github_account_id = github_account_id
        if full_name:
            repository.full_name = full_name
        if owner:
            repository.owner = owner
        if default_branch:
            repository.default_branch = default_branch

    def get_pull_request(self, session, repo_id, pr_number):
        try:
            pr_instance = session.execute(
                select(PullRequest).where(
                    PullRequest.repo_id == repo_id, PullRequest.pr_number == pr_number
                )
            ).scalar_one_or_none()

            return pr_instance

        except Exception as e:
            raise RuntimeError(f"ERROR {e}") from e

    def get_pull_request_review_context(self, pr_id: int):
        session = self.session_factory()
        try:
            pr = session.execute(
                select(PullRequest).where(PullRequest.id == pr_id)
            ).scalar_one_or_none()
            if pr is None:
                return None

            repository = session.execute(
                select(Repository).where(Repository.id == pr.repo_id)
            ).scalar_one_or_none()
            if repository is None:
                return None

            return {
                "pull_request_id": pr.id,
                "pull_number": pr.pr_number,
                "repository_id": repository.id,
                "github_repo_id": repository.repo_id,
                "full_name": repository.full_name,
                "owner": repository.owner,
                "repo": (
                    repository.full_name.split("/", 1)[1]
                    if "/" in repository.full_name
                    else repository.full_name
                ),
                "installation_id": repository.installation_id,
            }

        finally:
            session.close()
