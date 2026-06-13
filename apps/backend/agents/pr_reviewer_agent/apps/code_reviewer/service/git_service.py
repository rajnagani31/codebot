from ast import Str
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import CodeReviewRepository
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import PullRequestData
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.pr_resolver import PrResolver, PullRequestAction

class CodeReviewService:
    def __init__(self, repository : CodeReviewRepository):
        self.repository = repository

        
    def process_webhook(
            self,
            *,
            payload : dict,
            action : Str
    ):
        pr_data = self._build_pr_data(payload)
        print("actionaction", action)

        match action:

            case PullRequestAction.OPENED:
                print('case  open', PullRequestAction.OPENED.value)
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.READY_FOR_REVIEW:
                print('case review',PullRequestAction.READY_FOR_REVIEW.value)
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.SYNCHRONIZE:
                print('case SYNCHRONIZE',PullRequestAction.SYNCHRONIZE.value)
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.REOPENED:
                print('case REOPENED',PullRequestAction.REOPENED.value)
                return self.repository.save_pull_request(pr_data)

            case PullRequestAction.CLOSED:
                print('case CLOSED',PullRequestAction.CLOSED.value)
                return self.repository.save_pull_request(
                    pr_data,
                    payload["pull_request"]["merged"]
                )

            case PullRequestAction.UNKNOWN:
                return None

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

        # Extract required fields – ``full_name`` should be a string, not the full repo dict.
        # ``owner`` is the login of the repository owner.
        full_name = pr.get("head", {}).get("repo", {}).get("full_name")
        owner = pr.get("base", {}).get("repo", {}).get("owner", {}).get("login")
        default_branch = pr.get("base", {}).get("repo", {}).get("default_branch")

        return PullRequestData(
            repo_id=pr["base"]["repo"]["id"],
            pr_number=pr["number"],
            commit_sha=pr["head"]["sha"],
            author=pr["user"]["login"],
            full_name=full_name,
            owner=owner,
            state=pr["state"],
            title=pr["title"],
            description=pr["head"]["repo"]["description"],
            source_branch=pr["head"]["ref"],
            target_branch=pr["base"]["ref"],
            url=pr["html_url"],
            closed_at=pr.get("closed_at"),
            merged_at=pr.get("merged_at"),
            default_branch=default_branch,
        )


    def handle_opened(
        self,
        pr_data: PullRequestData
    ):
        return self.repository.create_pr(pr_data)
    
    def handle_ready_for_review(
        self,
        pr_data: PullRequestData
    ):
        repo_id = pr_data.repo_id
        pr_number = pr_data.pr_number
        return self.repository.mark_ready_for_review(
            repo_id,
            pr_number
        )
    
    def handle_synchronize(
        self,
        pr_data: PullRequestData
    ):
        pr_repo_id = pr_data.repo_id,
        pr_number = pr_data.pr_number,
        pr_commit_sha = pr_data.commit_sha
        return self.repository.update_commit_sha(
            pr_repo_id,
            pr_number,
            pr_commit_sha
        )
    

    def handle_closed(
        self,
        pr_data: PullRequestData,
        merged: bool
    ):
        if merged:
            return self.repository.mark_merged(pr_data)

        return self.repository.mark_closed(pr_data)
    
    def handle_reopened(
        self,
        pr_data: PullRequestData
    ):
        return self.repository.mark_reopened(pr_data)