from typing import Any

from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.core.celery import (
    celery_app,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.ai_review_service import (
    AIReviewService,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.tasks.task_helpers import (
    _run_async,
)


@celery_app.task(name="dummy_ai_review")
def dummy_ai_review(filename: str, status: str, patch: str) -> dict[str, Any]:
    result = _run_async(
        AIReviewService(use_dummy=True).review_file(
            filename=filename,
            status=status,
            patch=patch,
        )
    )
    return result.model_dump(mode="json")
