"""add: datetime flag for PR close_at and merged_at

Revision ID: 912c7e3e3b41
Revises: d3a4d0ac1396
Create Date: 2026-06-01 23:21:01.620300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '912c7e3e3b41'
down_revision: Union[str, Sequence[str], None] = 'd3a4d0ac1396'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
