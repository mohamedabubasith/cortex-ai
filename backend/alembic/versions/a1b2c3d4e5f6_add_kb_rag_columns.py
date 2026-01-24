"""add_kb_rag_columns

Revision ID: a1b2c3d4e5f6
Revises: 0cbc3eed9c98
Create Date: 2026-01-24 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '0cbc3eed9c98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('knowledge_bases', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('knowledge_bases', sa.Column('chunk_size', sa.Integer(), nullable=True))
    op.add_column('knowledge_bases', sa.Column('chunk_overlap', sa.Integer(), nullable=True))
    op.add_column('knowledge_bases', sa.Column('embedding_model', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('knowledge_bases', 'embedding_model')
    op.drop_column('knowledge_bases', 'chunk_overlap')
    op.drop_column('knowledge_bases', 'chunk_size')
    op.drop_column('knowledge_bases', 'file_size')
