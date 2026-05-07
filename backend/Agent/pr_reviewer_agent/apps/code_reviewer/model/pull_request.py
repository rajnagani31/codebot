from datetime import datetime
from enum import Enum
from id import id
from mixin import DateTimeMixin
from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, Index, Integer, String, UniqueConstraint, MetaData
from sqlalchemy.dialects.postgresql import id as PGid
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class PRStateEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PullRequest(Base, DateTimeMixin):
    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "repo_id", "pr_number", name="uq_pull_requests_tenant_repo_pr"),
        Index("ix_pull_requests_repo_pr", "repo_id", "pr_number"),
        Index("ix_pull_requests_tenant_id", "tenant_id"),
    )
    __metadata__ = MetaData(info={"schema_disc": "is root aggregate for pr context"})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=True)
    repo_id: Mapped[int] = mapped_column(Integer, nullable=True)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=True)
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=True)
    author: Mapped[str] = mapped_column(String(255), nullable=True)
    state: Mapped[PRStateEnum] = mapped_column(
        SQLEnum(PRStateEnum, name="pr_state_enum"),
        nullable=True,
        default=PRStateEnum.OPEN,
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)