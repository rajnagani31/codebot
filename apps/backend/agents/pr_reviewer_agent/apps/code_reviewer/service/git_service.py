


class CodeReviewService:
    def __init__(self, repository):
        self.repository = repository

    def get_pull_request(self, pr_id):
        return self.repository.get_pull_request(pr_id)