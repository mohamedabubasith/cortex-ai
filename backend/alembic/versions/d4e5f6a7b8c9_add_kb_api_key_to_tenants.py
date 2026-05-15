"""add kb_api_key to tenants

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-16

Per-tenant API key for the external Cortex KB service.
Provisioned automatically on tenant creation when CORTEX_KB_URL is set.
Falls back to global CORTEX_KB_API_KEY if null.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("kb_api_key", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "kb_api_key")
