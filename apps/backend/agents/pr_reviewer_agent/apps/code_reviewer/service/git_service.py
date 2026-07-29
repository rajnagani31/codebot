from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import (
    CodeReviewRepository,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import (
    PullRequestData,
    ReviewJobData,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.pr_resolver import (
    PullRequestAction,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.model.review_job import (
    ReviewJobStatusEnum,
)
from datetime import UTC, datetime


class CodeReviewService:
    def __init__(self, repository: CodeReviewRepository):
        self.repository = repository

    def process_webhook(self, *, payload: dict, action: PullRequestAction | str):
        if action == PullRequestAction.UNKNOWN:
            return None

        pr_data = self._build_pr_data(payload)

        match action:

            case PullRequestAction.OPENED:
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.READY_FOR_REVIEW:
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.SYNCHRONIZE:
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.REOPENED:
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.CLOSED:
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.UNKNOWN:
                return None

    def process_installation_webhook(self, *, payload: dict):
        return self.repository.save_installation_repositories(payload)

    def _build_pr_data(self, payload: dict) -> PullRequestData:
        """Build a PullRequestData object from the incoming GitHub webhook payload.

        The webhook can contain different top‑level structures depending on the event type.
        For pull‑request events the payload includes a ``pull_request`` key; for other events
        (e.g. ``ping``) it may be absent. We safely extract the PR dictionary and raise a clear
        error if it is missing.
        """
        pr = payload.get("pull_request")
        if pr is None:
            raise ValueError("Webhook payload does not contain 'pull_request' data")

        # Extract required fields safely to avoid KeyError and TypeError on nested structures.
        base_repo = pr.get("base", {}).get("repo", {}) or {}
        head_repo = pr.get("head", {}).get("repo", {}) or {}

        repo_id = base_repo.get("id")
        installation_id = (payload.get("installation") or {}).get("id")
        github_account_id = (
            (payload.get("installation") or {}).get("account") or {}
        ).get("id")
        pr_number = pr.get("number")
        commit_sha = pr.get("head", {}).get("sha")
        author = pr.get("user", {}).get("login")

        # Determine the standardized PR state (e.g. CLOSED vs MERGED)
        pr_action = payload.get("action")
        raw_state = pr.get("state")
        is_merged = pr.get("merged", False)
        state = "merged" if raw_state == "closed" and is_merged else raw_state

        title = pr.get("title")
        description = pr.get("body") or base_repo.get("description")
        source_branch = pr.get("head", {}).get("ref")
        target_branch = pr.get("base", {}).get("ref")
        url = pr.get("html_url")

        # Extract optional fields safely
        full_name = base_repo.get("full_name")
        owner = base_repo.get("owner", {}).get("login")
        default_branch = base_repo.get("default_branch")

        # review job

        review_job = ReviewJobData(
            status=ReviewJobStatusEnum.QUEUED,
            attempts=0,
            queued_at=datetime.now(UTC),
        )

        return PullRequestData(
            repo_id=repo_id,
            installation_id=installation_id,
            github_account_id=github_account_id,
            pr_number=pr_number,
            pr_action=pr_action,
            commit_sha=commit_sha,
            author=author,
            full_name=full_name,
            owner=owner,
            state=state,
            title=title,
            description=description,
            source_branch=source_branch,
            target_branch=target_branch,
            url=url,
            closed_at=pr.get("closed_at"),
            merged_at=pr.get("merged_at"),
            default_branch=default_branch,
            review_job=review_job,
        )
