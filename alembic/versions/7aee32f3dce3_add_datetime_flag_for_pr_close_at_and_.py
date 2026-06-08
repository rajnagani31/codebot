"""add: datetime flag for PR close_at and merged_at

Revision ID: 7aee32f3dce3
Revises: 3863dc99faa5
Create Date: 2026-06-01 23:36:19.344299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7aee32f3dce3'
down_revision: Union[str, Sequence[str], None] = '3863dc99faa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
