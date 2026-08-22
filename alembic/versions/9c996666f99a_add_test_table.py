""" add test table

Revision ID: 9c996666f99a
Revises: bab6f82cd4ca
Create Date: 2026-06-15 20:18:42.864389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c996666f99a'
down_revision: Union[str, Sequence[str], None] = 'bab6f82cd4ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
