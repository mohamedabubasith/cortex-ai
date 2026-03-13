"""add knowledge_base_members table

Revision ID: add_knowledge_base_members
Revises: e9aaa70eda28
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_knowledge_base_members'
down_revision: Union[str, Sequence[str], None] = 'e9aaa70eda28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'knowledge_base_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('kb_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['kb_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_base_members_kb_id', 'knowledge_base_members', ['kb_id'])
    op.create_index('ix_knowledge_base_members_user_id', 'knowledge_base_members', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_knowledge_base_members_user_id', table_name='knowledge_base_members')
    op.drop_index('ix_knowledge_base_members_kb_id', table_name='knowledge_base_members')
    op.drop_table('knowledge_base_members')
