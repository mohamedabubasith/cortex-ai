"""add thinking to messages

Revision ID: add_thinking_to_messages
Revises: add_context_window
Create Date: 2025-12-27 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_thinking_to_messages'
down_revision = 'add_context_window'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('messages', sa.Column('thinking', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('messages', 'thinking')
