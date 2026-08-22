""" add test table

Revision ID: 9513ba1e120b
Revises: bab6f82cd4ca
Create Date: 2026-06-15 21:05:47.489201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9513ba1e120b'
down_revision: Union[str, Sequence[str], None] = 'bab6f82cd4ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
