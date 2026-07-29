from datetime import datetime
from enum import Enum
from pydoc import describe
from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Index, MetaData, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .mixin import DateTimeMixin
# Import Base from the centralized database module
from apps.backend.bot.application.core.database import Base


class ArtifactTypeEnum(str, Enum):
    RAW_DIFF = "raw_diff" 
    PROMPT = "prompt"
    MODEL_RESPONSE = "model_response"
    REPORT_EXPORT = "report_export"
    LOG = "log"
    OTHER = "other"


class ArtifactRef(Base, DateTimeMixin):
    __tablename__ = "artifact_refs"
    __table_args__ = (
        Index("ix_artifact_refs_job_id_type", "job_id", "artifact_type"),
        UniqueConstraint("job_id", "artifact_type", "artifact_uri", name="uq_artifact_refs_job_type_uri"),
    )
    __metadata__ = MetaData(info={"schema": "Stores references/URIs to heavy review data like diff, prompt, model response, logs."})
    """
    Enum role:
    raw_diff - Full PR diff file/link/object-storage path
    prompt - Prompt sent to AI model
    model_response - Prompt sent to AI model
    report_export - Final generated JSON/Markdown report
    log - Job execution logs
    other - anything extra

    # might see data
    {
    "job_id": 1001,
    "artifact_type": "raw_diff",
    "artifact_uri": "s3://codebot/reviews/1001/raw_diff.patch",
    "checksum": "sha256:abc..."
    }

    {
    "job_id": 1001,
    "artifact_type": "model_response",
    "artifact_uri": "db://review_artifacts/1001/model_response.json"
    }

    # Why use this table instead of storing everything in DB?
    Because raw diffs, full prompts, logs, and model responses can become very large. 
    This table is designed to keep only references/URIs, 
    while the actual large content can be in S3, file storage, blob table, or object storage. 
    The model metadata says it stores references to artifacts produced during a job and pointers to heavy artifacts. 
    """
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("review_jobs.id", ondelete="CASCADE"), nullable=False)
    artifact_type: Mapped[ArtifactTypeEnum] = mapped_column(
        SQLEnum(ArtifactTypeEnum, name="artifact_type_enum"),
        nullable=False,
    )
    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
