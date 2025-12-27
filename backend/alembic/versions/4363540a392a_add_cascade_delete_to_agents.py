"""add_cascade_delete_to_agents

Revision ID: 4363540a392a
Revises: add_context_window
Create Date: 2025-12-27 21:33:01.947255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4363540a392a'
down_revision: Union[str, Sequence[str], None] = 'add_thinking_to_messages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Chat Sessions
    op.drop_constraint('chat_sessions_agent_id_fkey', 'chat_sessions', type_='foreignkey')
    op.create_foreign_key('chat_sessions_agent_id_fkey', 'chat_sessions', 'projects', ['agent_id'], ['id'], ondelete='CASCADE')
    
    # Project Members
    op.drop_constraint('project_members_agent_id_fkey', 'project_members', type_='foreignkey')
    op.create_foreign_key('project_members_agent_id_fkey', 'project_members', 'projects', ['agent_id'], ['id'], ondelete='CASCADE')
    
    # Association Tables
    op.drop_constraint('agent_knowledge_bases_agent_id_fkey', 'agent_knowledge_bases', type_='foreignkey')
    op.create_foreign_key('agent_knowledge_bases_agent_id_fkey', 'agent_knowledge_bases', 'projects', ['agent_id'], ['id'], ondelete='CASCADE')
    
    op.drop_constraint('agent_database_connections_agent_id_fkey', 'agent_database_connections', type_='foreignkey')
    op.create_foreign_key('agent_database_connections_agent_id_fkey', 'agent_database_connections', 'projects', ['agent_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # Revert to default (no cascade)
    op.drop_constraint('chat_sessions_agent_id_fkey', 'chat_sessions', type_='foreignkey')
    op.create_foreign_key('chat_sessions_agent_id_fkey', 'chat_sessions', 'projects', ['agent_id'], ['id'])
    
    op.drop_constraint('project_members_agent_id_fkey', 'project_members', type_='foreignkey')
    op.create_foreign_key('project_members_agent_id_fkey', 'project_members', 'projects', ['agent_id'], ['id'])
    
    op.drop_constraint('agent_knowledge_bases_agent_id_fkey', 'agent_knowledge_bases', type_='foreignkey')
    op.create_foreign_key('agent_knowledge_bases_agent_id_fkey', 'agent_knowledge_bases', 'projects', ['agent_id'], ['id'])
    
    op.drop_constraint('agent_database_connections_agent_id_fkey', 'agent_database_connections', type_='foreignkey')
    op.create_foreign_key('agent_database_connections_agent_id_fkey', 'agent_database_connections', 'projects', ['agent_id'], ['id'])
