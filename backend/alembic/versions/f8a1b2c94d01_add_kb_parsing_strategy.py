"""add parsing_strategy to knowledge_bases

Revision ID: f8a1b2c94d01
Revises: add_knowledge_base_members
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a1b2c94d01"
down_revision: Union[str, Sequence[str], None] = "add_knowledge_base_members"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "knowledge_bases",
        sa.Column("parsing_strategy", sa.String(), nullable=False, server_default="fast"),
    )
    op.execute("UPDATE knowledge_bases SET status = 'completed' WHERE status = 'indexed'")
    op.execute("UPDATE knowledge_bases SET status = 'queued' WHERE status IN ('pending', 'processing', 'indexing')")


def downgrade() -> None:
    op.execute("UPDATE knowledge_bases SET status = 'indexed' WHERE status = 'completed'")
    op.execute("UPDATE knowledge_bases SET status = 'pending' WHERE status = 'queued'")
    op.drop_column("knowledge_bases", "parsing_strategy")
