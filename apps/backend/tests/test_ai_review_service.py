import asyncio

from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.ai_review_service import (
    AIReviewService,
)


def test_review_file_returns_dummy_result_when_enabled() -> None:
    service = AIReviewService(api_key=None, use_dummy=True)

    result = asyncio.run(
        service.review_file(
            filename="sample.py",
            status="modified",
            patch="diff --git a/sample.py b/sample.py\n+print('hello')",
        )
    )

    assert result.filename == "sample.py"
    assert result.metadata["provider"] == "dummy"
    assert result.summary.startswith("Dummy AI review")
    assert result.findings
