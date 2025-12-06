"""Add analytics and audit log models

Revision ID: add_analytics_audit
Revises: 3a62c878bb11
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_analytics_audit'
down_revision = '3a62c878bb11'
branch_labels = None
depends_on = None

def upgrade():
    # Analytics table
    op.create_table(
        'analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),  # chat, kb_upload, kb_query, etc.
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_analytics_user_id', 'analytics', ['user_id'])
    op.create_index('ix_analytics_event_type', 'analytics', ['event_type'])
    op.create_index('ix_analytics_created_at', 'analytics', ['created_at'])
    
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),  # create, update, delete, access
        sa.Column('resource_type', sa.String(), nullable=False),  # agent, kb, llm_config, etc.
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('analytics')
