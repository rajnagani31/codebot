from enum import Enum
from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, String, UniqueConstraint, MetaData
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
# Import Base from the centralized database module
from apps.backend.bot.application.core.database import Base
from .mixin import DateTimeMixin


class PRStateEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PullRequest(Base, DateTimeMixin):
    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("repo_id", "pr_number", name="uq_pull_requests_tenant_repo_pr"),
        Index("ix_pull_requests_repo_pr", "repo_id", "pr_number"),
    )
    __metadata__ = MetaData(info={"schema_disc": "is root aggregate for pr context"})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_details.id", ondelete = "CASCADE"), nullable=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repositories.id", ondelete = "CASCADE"), nullable=True)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=True)
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=True)
    author: Mapped[str] = mapped_column(String(255), nullable=True)
    state: Mapped[PRStateEnum] = mapped_column(
        SQLEnum(PRStateEnum, name="pr_state_enum"),
        nullable=True,
        default=PRStateEnum.OPEN,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    source_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    target_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    