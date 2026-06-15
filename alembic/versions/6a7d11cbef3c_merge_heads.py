"""merge heads

Revision ID: 6a7d11cbef3c
Revises: 9513ba1e120b, 9c996666f99a
Create Date: 2026-06-15 21:28:05.766666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a7d11cbef3c'
down_revision: Union[str, Sequence[str], None] = ('9513ba1e120b', '9c996666f99a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
