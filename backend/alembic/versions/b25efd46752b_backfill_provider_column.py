"""backfill provider column

Revision ID: b25efd46752b
Revises: b62339da4745
Create Date: 2026-01-06 14:15:09.283435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b25efd46752b'
down_revision: Union[str, Sequence[str], None] = 'b62339da4745'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE llm_configurations SET provider = 'openai' WHERE provider IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    pass
