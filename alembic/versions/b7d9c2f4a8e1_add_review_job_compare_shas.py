"""add review job compare shas

Revision ID: b7d9c2f4a8e1
Revises: f4b9c1d2e3a4
Create Date: 2026-08-03 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b7d9c2f4a8e1"
down_revision: Union[str, None] = "f4b9c1d2e3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("review_jobs", sa.Column("base_sha", sa.String(length=64), nullable=True))
    op.add_column("review_jobs", sa.Column("head_sha", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("review_jobs", "head_sha")
    op.drop_column("review_jobs", "base_sha")
