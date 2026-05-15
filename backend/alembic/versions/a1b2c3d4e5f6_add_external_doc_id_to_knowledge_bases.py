"""add external_doc_id to knowledge_bases

Revision ID: a1b2c3d4e5f6
Revises: f8a1b2c94d01
Create Date: 2026-05-16

Adds external_doc_id column to knowledge_bases table.
Populated when a document is uploaded via the external Cortex KB service.
Null for legacy records processed by the local Haystack pipeline.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f8a1b2c94d01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "knowledge_bases",
        sa.Column("external_doc_id", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("knowledge_bases", "external_doc_id")
