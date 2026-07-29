"""add github installation metadata

Revision ID: a2b4c6d8e9f0
Revises: 9ef3059f98d4
Create Date: 2026-07-28 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a2b4c6d8e9f0"
down_revision: Union[str, Sequence[str], None] = "9ef3059f98d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "repositories", sa.Column("installation_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "repositories", sa.Column("github_account_id", sa.BigInteger(), nullable=True)
    )
    op.create_index(
        op.f("ix_repositories_installation_id"),
        "repositories",
        ["installation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_repositories_installation_id"), table_name="repositories")
    op.drop_column("repositories", "github_account_id")
    op.drop_column("repositories", "installation_id")
