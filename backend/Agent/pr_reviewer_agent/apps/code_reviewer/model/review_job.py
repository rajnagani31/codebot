from datetime import datetime
from enum import Enum
from id import id4

from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Index, SmallInteger, String, MetaData
from sqlalchemy.dialects.postgresql import id as PGid
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from .mixin import DateTimeMixin

Base = declarative_base()


class ReviewJobStatusEnum(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class ReviewJob(Base, DateTimeMixin):
    __tablename__ = "review_jobs"
    __table_args__ = (
        Index("ix_review_jobs_status_queued_at", "status", "queued_at"),
        Index("ix_review_jobs_pr_id_queued_at", "pr_id", "queued_at"),
    )
    __metadata__ = MetaData(info={"schema_disc": "tracks review job lifecycle"})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=id4)
    pr_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ReviewJobStatusEnum] = mapped_column(
        SQLEnum(ReviewJobStatusEnum, name="review_job_status_enum"),
        nullable=False,
        default=ReviewJobStatusEnum.QUEUED,
    )
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
