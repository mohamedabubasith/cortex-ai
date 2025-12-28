"""Add agent audit logs table

Revision ID: add_agent_audit_logs
Revises: add_analytics_audit
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_agent_audit_logs'
down_revision = 'add_analytics_audit'
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_audit_logs table
    op.create_table('agent_audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('model_name', sa.String(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('llm_response', sa.Text(), nullable=True),
        sa.Column('tool_calls', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('rag_context', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('agent_audit_logs')
