"""change chate user table name to user details

Revision ID: 39371c2f34bc
Revises:
Create Date: 2026-03-30 18:15:28.317193
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '39371c2f34bc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the table
    op.rename_table('chat_users', 'user_details')

    # Rename indexes to match new table name
    op.execute('ALTER INDEX ix_chat_users_email RENAME TO ix_user_details_email')
    op.execute('ALTER INDEX ix_chat_users_public_id RENAME TO ix_user_details_public_id')
    op.execute('ALTER INDEX ix_chat_users_session_label RENAME TO ix_user_details_session_label')
    op.execute('ALTER INDEX ix_chat_users_user_type RENAME TO ix_user_details_user_type')


def downgrade() -> None:
    op.execute('ALTER INDEX ix_user_details_user_type RENAME TO ix_chat_users_user_type')
    op.execute('ALTER INDEX ix_user_details_session_label RENAME TO ix_chat_users_session_label')
    op.execute('ALTER INDEX ix_user_details_public_id RENAME TO ix_chat_users_public_id')
    op.execute('ALTER INDEX ix_user_details_email RENAME TO ix_chat_users_email')

    op.rename_table('user_details', 'chat_users')
