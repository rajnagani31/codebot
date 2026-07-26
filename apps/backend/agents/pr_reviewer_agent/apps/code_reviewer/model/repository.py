from .mixin import DateTimeMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from apps.backend.bot.application.core.database import Base
import uuid


class Repository(Base, DateTimeMixin):
    __tablename__ = "repositories"
    """
    {
        "id": 1,
        "repo_id": 987654321,
        "user_id": 10,
        "full_name": "raj/codebot",
        "owner": "raj",
        "default_branch": "main",
        "is_active": true
    }
    """
    id: Mapped[BigInteger] = mapped_column(BigInteger, primary_key=True)
    repo_id: Mapped[BigInteger] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_details.id", ondelete="CASCADE"),
        nullable=True
    )
    full_name: Mapped[str] = mapped_column(nullable=False)
    owner: Mapped[str] = mapped_column(nullable=False)
    default_branch: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)