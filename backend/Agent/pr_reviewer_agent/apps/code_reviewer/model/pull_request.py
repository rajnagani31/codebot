from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import DateTime, Enum as SQLEnum, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class PRStateEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PullRequest(Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "repo_id", "pr_number", name="uq_pull_requests_tenant_repo_pr"),
        Index("ix_pull_requests_repo_pr", "repo_id", "pr_number"),
        Index("ix_pull_requests_tenant_id", "tenant_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    repo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[PRStateEnum] = mapped_column(
        SQLEnum(PRStateEnum, name="pr_state_enum"),
        nullable=False,
        default=PRStateEnum.OPEN,
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )