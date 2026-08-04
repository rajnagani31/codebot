"""add async review pipeline progress

Revision ID: f4b9c1d2e3a4
Revises: a2b4c6d8e9f0
Create Date: 2026-07-29 23:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "f4b9c1d2e3a4"
down_revision: Union[str, None] = "a2b4c6d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "review_jobs",
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "review_jobs",
        sa.Column("processed_files", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "review_jobs",
        sa.Column("final_review_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_check_constraint(
        "ck_review_jobs_processed_files_bounds",
        "review_jobs",
        "processed_files >= 0 AND total_files >= 0 AND processed_files <= total_files",
    )
    op.create_table(
        "review_file_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "findings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["review_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "filename", name="uq_review_file_results_job_file"),
    )
    op.create_index(
        "ix_review_file_results_job_id",
        "review_file_results",
        ["job_id"],
        unique=False,
    )
    op.alter_column("review_jobs", "total_files", server_default=None)
    op.alter_column("review_jobs", "processed_files", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_review_file_results_job_id", table_name="review_file_results")
    op.drop_table("review_file_results")
    op.drop_constraint(
        "ck_review_jobs_processed_files_bounds", "review_jobs", type_="check"
    )
    op.drop_column("review_jobs", "final_review_json")
    op.drop_column("review_jobs", "processed_files")
    op.drop_column("review_jobs", "total_files")
