from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .mixin import DateTimeMixin

# Import Base from the centralized database module
from apps.backend.bot.application.core.database import Base


class ReviewReport(Base, DateTimeMixin):
    __tablename__ = "review_reports"
    __metadata__ = MetaData(info={"schema": "Stores final AI review summary: risk score, totals, model info."})
    """
    What to store in 
    - risk_score -> {risk_score : 7.5}, numric also allow(12345.12)size, but we also use (1.00 to 10.00)
    - totals_json -> {
                    "total_findings": 6,
                    "critical": 1,
                    "high": 2,
                    "medium": 2,
                    "low": 1,
                    "info": 0,
                    "security": 1,
                    "bug": 3,
                    "performance": 1,
                    "style": 1
                    }

    - model_info_json -> {
                    "provider": "openai",
                    "model": "gpt-4.1",
                    "prompt_tokens": 12000,
                    "completion_tokens": 3000,
                    "total_tokens": 15000,
                    "temperature": 0.2,
                    "review_version": "v1"
                    }

    
    """
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    totals_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    model_info_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)