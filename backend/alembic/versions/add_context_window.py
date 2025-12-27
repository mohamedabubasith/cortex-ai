"""add context window

Revision ID: add_context_window
Revises: add_analytics_audit
Create Date: 2025-12-23 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_context_window'
down_revision = 'add_analytics_audit'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('llm_configurations', sa.Column('context_window', sa.Integer(), nullable=True, default=128000))


def downgrade():
    op.drop_column('llm_configurations', 'context_window')
