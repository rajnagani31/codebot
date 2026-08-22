from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


Severity = Literal["critical", "high", "medium", "low", "info"]


SEVERITY_ALIASES = {
    "style": "low",
    "docs": "info",
    "documentation": "info",
    "test": "medium",
    "testing": "medium",
    "maintainability": "medium",
    "performance": "medium",
    "bug": "high",
    "security": "high",
}


class ReviewFindingDTO(BaseModel):
    severity: Severity = "info"
    category: Literal[
        "security",
        "bug",
        "performance",
        "style",
        "maintainability",
        "test",
        "docs",
        "other",
    ] = "other"
    title: str
    summary: str
    recommendation: str | None = None
    line_start: int = 1
    line_end: int | None = None

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: Any) -> str:
        if value is None:
            return "info"

        normalized = str(value).strip().lower()
        allowed = {"critical", "high", "medium", "low", "info"}
        if normalized in allowed:
            return normalized
        return SEVERITY_ALIASES.get(normalized, "info")


class FileReviewResult(BaseModel):
    filename: str
    findings: list[ReviewFindingDTO] = Field(default_factory=list)
    summary: str = ""
    skipped: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class FinalReviewResult(BaseModel):
    review_job_id: int
    total_files: int
    reviewed_files: int
    skipped_files: int
    total_findings: int
    findings_by_severity: dict[str, int]
    summary: str
    files: list[FileReviewResult]
