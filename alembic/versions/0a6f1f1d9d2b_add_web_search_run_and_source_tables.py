"""add web search run and source tables

Revision ID: 0a6f1f1d9d2b
Revises: 39371c2f34bc
Create Date: 2026-04-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0a6f1f1d9d2b"
down_revision = "39371c2f34bc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "web_search_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(length=512), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"]),
        sa.ForeignKeyConstraint(["thread_id"], ["chat_threads.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user_details.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_web_search_runs_message_id"), "web_search_runs", ["message_id"], unique=False)
    op.create_index(op.f("ix_web_search_runs_query"), "web_search_runs", ["query"], unique=False)
    op.create_index(op.f("ix_web_search_runs_status"), "web_search_runs", ["status"], unique=False)
    op.create_index(op.f("ix_web_search_runs_thread_id"), "web_search_runs", ["thread_id"], unique=False)
    op.create_index(op.f("ix_web_search_runs_user_id"), "web_search_runs", ["user_id"], unique=False)

    op.create_table(
        "web_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["web_search_runs.id"]),
        sa.ForeignKeyConstraint(["thread_id"], ["chat_threads.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user_details.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_web_sources_domain"), "web_sources", ["domain"], unique=False)
    op.create_index(op.f("ix_web_sources_message_id"), "web_sources", ["message_id"], unique=False)
    op.create_index(op.f("ix_web_sources_run_id"), "web_sources", ["run_id"], unique=False)
    op.create_index(op.f("ix_web_sources_thread_id"), "web_sources", ["thread_id"], unique=False)
    op.create_index(op.f("ix_web_sources_user_id"), "web_sources", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_web_sources_user_id"), table_name="web_sources")
    op.drop_index(op.f("ix_web_sources_thread_id"), table_name="web_sources")
    op.drop_index(op.f("ix_web_sources_run_id"), table_name="web_sources")
    op.drop_index(op.f("ix_web_sources_message_id"), table_name="web_sources")
    op.drop_index(op.f("ix_web_sources_domain"), table_name="web_sources")
    op.drop_table("web_sources")

    op.drop_index(op.f("ix_web_search_runs_user_id"), table_name="web_search_runs")
    op.drop_index(op.f("ix_web_search_runs_thread_id"), table_name="web_search_runs")
    op.drop_index(op.f("ix_web_search_runs_status"), table_name="web_search_runs")
    op.drop_index(op.f("ix_web_search_runs_query"), table_name="web_search_runs")
    op.drop_index(op.f("ix_web_search_runs_message_id"), table_name="web_search_runs")
    op.drop_table("web_search_runs")
