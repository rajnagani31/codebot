import asyncio
import logging
from collections import Counter
from typing import Any

import httpx
import redis.exceptions
from celery import chord

from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import (
    CodeReviewRepository,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import (
    PullRequestFile,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.review_schema import (
    FileReviewResult,
    FinalReviewResult,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.ai_review_service import (
    AIReviewService,
    AIReviewTemporaryError,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.github_pull_request_service import (
    GitHubPullRequestService,
)
from apps.backend.bot.application.core.celery import celery_app
from apps.backend.bot.application.core.database import SessionLocal

logger = logging.getLogger(__name__)


class NonRetryableReviewError(RuntimeError):
    pass


def _repository() -> CodeReviewRepository:
    return CodeReviewRepository(SessionLocal)


def _run_async(awaitable):
    return asyncio.run(awaitable)


def _error_code(exc: BaseException) -> str:
    status_code = getattr(getattr(exc, "response", None), "status_code", None)
    if status_code == 401:
        return "INVALID_INSTALLATION"
    if status_code == 403:
        return "PERMISSION_DENIED"
    if status_code == 404:
        return "REPOSITORY_NOT_FOUND"
    if isinstance(exc, AIReviewTemporaryError):
        return "AI_TEMPORARY_FAILURE"
    if isinstance(exc, httpx.HTTPStatusError):
        return f"GITHUB_HTTP_{status_code}"
    if isinstance(exc, httpx.HTTPError):
        return "NETWORK_ERROR"
    return exc.__class__.__name__.upper()[:64]


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, AIReviewTemporaryError):
        return True
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(exc, redis.exceptions.RedisError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {408, 409, 425, 429, 500, 502, 503, 504}
    return False


@celery_app.task(
    bind=True,
    name="review_pull_request",
    autoretry_for=(httpx.TimeoutException, httpx.NetworkError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def review_pull_request(self, review_job_id: int) -> dict[str, Any]:
    repository = _repository()
    logger.info("[ReviewJob started]", extra={"review_job_id": review_job_id})
    repository.mark_review_job_running(review_job_id)

    try:
        context = repository.get_review_job_context(review_job_id)
        if context is None:
            raise NonRetryableReviewError("review job context not found")
        if context.get("installation_id") is None:
            raise NonRetryableReviewError("repository has no installation_id")

        owner = context["owner"]
        repo = context["repo"]
        pull_number = context["pull_number"]
        installation_id = context["installation_id"]
        base_sha = context.get("base_sha")
        head_sha = context.get("head_sha")

        github_service = GitHubPullRequestService()
        if base_sha and head_sha:
            files = _run_async(
                github_service.get_changed_files_between_commits(
                    owner=owner,
                    repo=repo,
                    before_sha=base_sha,
                    after_sha=head_sha,
                    installation_id=installation_id,
                )
            )
        else:
            files = _run_async(
                github_service.get_pull_request_files(
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                    installation_id=installation_id,
                )
            )
        file_payloads = [file.model_dump(mode="json") for file in files]
        repository.set_review_job_total_files(review_job_id, len(file_payloads))
        logger.info(
            "Fetched files",
            extra={"review_job_id": review_job_id, "total_files": len(file_payloads)},
        )

        if not file_payloads:
            aggregate_review.delay([], review_job_id)
            return {"review_job_id": review_job_id, "total_files": 0}

        logger.info(
            "Dispatching review tasks",
            extra={"review_job_id": review_job_id, "total_files": len(file_payloads)},
        )
        header = [review_file.s(review_job_id, file_data) for file_data in file_payloads]
        async_result = chord(header)(aggregate_review.s(review_job_id))
        return {
            "review_job_id": review_job_id,
            "total_files": len(file_payloads),
            "chord_id": async_result.id,
        }
    except Exception as exc:
        if _is_retryable(exc) and self.request.retries < 3:
            raise self.retry(exc=exc, countdown=30)
        repository.mark_review_job_failed(review_job_id, _error_code(exc))
        logger.exception(
            "ReviewJob failed",
            extra={"review_job_id": review_job_id, "error_code": _error_code(exc)},
        )
        raise


@celery_app.task(
    bind=True,
    name="review_file",
    autoretry_for=(AIReviewTemporaryError, httpx.TimeoutException, httpx.NetworkError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def review_file(self, review_job_id: int, file_data: dict[str, Any]) -> dict[str, Any]:
    repository = _repository()
    file = PullRequestFile.model_validate(file_data)

    try:
        if file.patch is None:
            result = FileReviewResult(
                filename=file.filename,
                summary="Skipped because GitHub did not provide a text patch.",
                skipped=True,
                metadata={"status": file.status, "reason": "missing_patch_or_binary"},
            )
        else:
            result = _run_async(
                AIReviewService().review_file(
                    filename=file.filename,
                    status=file.status,
                    patch=file.patch,
                )
            )

        result_dict = result.model_dump(mode="json")
        repository.save_file_review_result(
            review_job_id=review_job_id,
            filename=result.filename,
            status="skipped" if result.skipped else "reviewed",
            findings=result_dict["findings"],
            summary=result.summary,
            metadata=result.metadata,
        )
        repository.increment_processed_files(review_job_id)
        return result_dict
    except Exception as exc:
        if _is_retryable(exc) and self.request.retries < 3:
            raise self.retry(exc=exc, countdown=30)
        repository.mark_review_job_failed(review_job_id, _error_code(exc))
        raise


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
