from .mixin import DateTimeMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, ForeignKey
from apps.backend.bot.application.core.database import Base



class Repository(Base, DateTimeMixin):
    __tablename__ = "repositories"

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