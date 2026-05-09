from datetime import datetime
from enum import Enum
from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Index, MetaData, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .mixin import DateTimeMixin
# Import Base from the centralized database module
from backend.bot.application.core.database import Base


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
    __metadata__ = MetaData(info={"schema": "stores references to artifacts produced during a review job or stores only pointers to heavy artifacts."})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("review_jobs.id", ondelete="CASCADE"), nullable=False)
    artifact_type: Mapped[ArtifactTypeEnum] = mapped_column(
        SQLEnum(ArtifactTypeEnum, name="artifact_type_enum"),
        nullable=False,
    )
    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
