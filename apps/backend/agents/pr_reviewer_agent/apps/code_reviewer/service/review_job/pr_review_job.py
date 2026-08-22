from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import (
    CodeReviewRepository,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import (
    PullRequestFile,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.github_pull_request_service import (
    GitHubPullRequestService,
)


class PullRequestReviewJobService:
    def __init__(
        self,
        repository: CodeReviewRepository,
        github_service: GitHubPullRequestService | None = None,
    ):
        self.repository = repository
        self.github_service = github_service or GitHubPullRequestService()

    async def fetch_changed_files(self, pr_id: int) -> list[PullRequestFile]:
        context = self.repository.get_pull_request_review_context(pr_id)
        if context is None:
            raise ValueError(f"Pull request {pr_id} was not found")

        installation_id = context.get("installation_id")
        if installation_id is None:
            raise ValueError(
                f"Repository {context.get('repository_id')} has no GitHub installation_id"
            )

        return await self.github_service.get_pull_request_files(
            owner=context["owner"],
            repo=context["repo"],
            pull_number=context["pull_number"],
            installation_id=installation_id,
        )
