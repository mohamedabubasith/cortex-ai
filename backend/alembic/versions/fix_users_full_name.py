"""fix users full_name

Revision ID: fix_users_full_name
Revises: add_context_window
Create Date: 2025-12-27 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_users_full_name'
down_revision = 'add_context_window'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column exists to be safe, or just try to add it. 
    # Since we know it's missing from the error, we'll add it.
    # We use nullable=True because existing rows won't have this data.
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))


def downgrade():
    op.drop_column('users', 'full_name')
