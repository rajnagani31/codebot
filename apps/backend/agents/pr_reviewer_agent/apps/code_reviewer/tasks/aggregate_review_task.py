import logging
from collections import Counter
from typing import Any

from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.core.celery import (
    celery_app,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.review_schema import (
    FileReviewResult,
    FinalReviewResult,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.tasks.task_helpers import (
    _error_code,
    _repository,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="aggregate_review")
def aggregate_review(
    self, file_reviews: list[dict[str, Any]], review_job_id: int
) -> dict[str, Any]:
    repository = _repository()
    try:
        parsed_reviews = [
            FileReviewResult.model_validate(file_review)
            for file_review in file_reviews
        ]
        severity_counts: Counter[str] = Counter()
        for file_review in parsed_reviews:
            severity_counts.update(finding.severity for finding in file_review.findings)

        total_findings = sum(len(file_review.findings) for file_review in parsed_reviews)
        skipped_files = sum(1 for file_review in parsed_reviews if file_review.skipped)
        final_review = FinalReviewResult(
            review_job_id=review_job_id,
            total_files=len(parsed_reviews),
            reviewed_files=len(parsed_reviews) - skipped_files,
            skipped_files=skipped_files,
            total_findings=total_findings,
            findings_by_severity=dict(severity_counts),
            summary=(
                f"Reviewed {len(parsed_reviews) - skipped_files} files, skipped "
                f"{skipped_files}, found {total_findings} findings."
            ),
            files=parsed_reviews,
        )
        final_review_dict = final_review.model_dump(mode="json")
        repository.mark_review_job_succeeded(review_job_id, final_review_dict)
        logger.info(
            "ReviewJob succeeded",
            extra={
                "review_job_id": review_job_id,
                "total_files": len(parsed_reviews),
                "total_findings": total_findings,
            },
        )
        return final_review_dict
    except Exception as exc:
        repository.mark_review_job_failed(review_job_id, _error_code(exc))
        logger.exception(
            "ReviewJob failed during aggregation",
            extra={"review_job_id": review_job_id, "error_code": _error_code(exc)},
        )
        raise
