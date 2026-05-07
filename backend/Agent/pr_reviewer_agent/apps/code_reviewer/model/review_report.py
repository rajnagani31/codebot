from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from .mixin import DateTimeMixin


Base = declarative_base()


class ReviewReport(Base, DateTimeMixin):
    __tablename__ = "review_reports"
    __metadata__ = MetaData(info={"schema": "stores aggregate output for pr context"})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    totals_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    model_info_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)