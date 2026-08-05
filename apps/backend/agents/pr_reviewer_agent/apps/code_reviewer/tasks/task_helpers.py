import asyncio
import logging

import httpx
import redis.exceptions

from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import (
    CodeReviewRepository,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.ai_review_service import (
    AIReviewTemporaryError,
)
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
