from agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import CodeReviewRepository
from agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import PullRequestData


class CodeReviewService:
    def __init__(self, repository : CodeReviewRepository):
        self.repository = repository

    def create_pull_request(
            self,
            *,
            payload : dict
        ) :

        pr = payload['pull_request']

        pr_data = PullRequestData(
            repo_id=pr['base']['repo']['id'],
            pr_number=pr['number'],
            commit_sha=pr['head']['sha'],
            author=pr['user']['login'],
            state=pr['state'],
            title=pr['title'],
            description=pr["head"]['repo']['description'],
            source_branch=pr['head']['ref'],
            target_branch=pr['base']['ref'],
            url=pr['html_url'],
            closed_at=pr.get('closed_at'),
            merged_at=pr.get('merged_at')
        )

        return self.repository.create_pull_request(pr_data)
    
