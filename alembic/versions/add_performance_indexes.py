"""Add performance indexes for Phase 3 optimizations

Revision ID: add_performance_indexes
Revises: 819e95294bd3
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = 'add_performance_indexes'
down_revision: Union[str, None] = '819e95294bd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add performance indexes."""
    
    # Users table indexes
    op.create_index('ix_users_email_lower', 'users', [sa.text('lower(email)')])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_updated_at', 'users', ['updated_at'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    
    # Analyses table indexes
    op.create_index('ix_analyses_user_id_status', 'analyses', ['user_id', 'status'])
    op.create_index('ix_analyses_status_created_at', 'analyses', ['status', 'created_at'])
    op.create_index('ix_analyses_user_id_created_at', 'analyses', ['user_id', 'created_at'])
    op.create_index('ix_analyses_processing_started_at', 'analyses', ['processing_started_at'])
    op.create_index('ix_analyses_processing_completed_at', 'analyses', ['processing_completed_at'])
    op.create_index('ix_analyses_cost', 'analyses', ['cost'])
    op.create_index('ix_analyses_tokens_used', 'analyses', ['tokens_used'])
    
    # Conversations table indexes
    op.create_index('ix_conversations_user_id_analysis_id', 'conversations', ['user_id', 'analysis_id'])
    op.create_index('ix_conversations_analysis_id', 'conversations', ['analysis_id'])
    op.create_index('ix_conversations_user_id_updated_at', 'conversations', ['user_id', 'updated_at'])
    op.create_index('ix_conversations_title_gin', 'conversations', [sa.text("to_tsvector('english', title)")], postgresql_using='gin')
    
    # Messages table indexes  
    op.create_index('ix_messages_conversation_id_created_at', 'messages', ['conversation_id', 'created_at'])
    op.create_index('ix_messages_role', 'messages', ['role'])
    op.create_index('ix_messages_cost', 'messages', ['cost'])
    op.create_index('ix_messages_tokens_used', 'messages', ['tokens_used'])
    op.create_index('ix_messages_content_gin', 'messages', [sa.text("to_tsvector('english', content)")], postgresql_using='gin')
    
    # Partial indexes for common queries
    op.create_index(
        'ix_analyses_active_processing', 
        'analyses', 
        ['user_id', 'created_at'],
        postgresql_where=sa.text("status IN ('QUEUED', 'PROCESSING')")
    )
    
    op.create_index(
        'ix_analyses_completed_with_cost',
        'analyses',
        ['user_id', 'cost', 'created_at'],
        postgresql_where=sa.text("status = 'COMPLETED' AND cost IS NOT NULL")
    )

def downgrade() -> None:
    """Remove performance indexes."""
    
    # Remove all the indexes we created
    op.drop_index('ix_users_email_lower')
    op.drop_index('ix_users_created_at')
    op.drop_index('ix_users_updated_at')
    op.drop_index('ix_users_is_active')
    
    op.drop_index('ix_analyses_user_id_status')
    op.drop_index('ix_analyses_status_created_at')
    op.drop_index('ix_analyses_user_id_created_at')
    op.drop_index('ix_analyses_processing_started_at')
    op.drop_index('ix_analyses_processing_completed_at')
    op.drop_index('ix_analyses_cost')
    op.drop_index('ix_analyses_tokens_used')
    
    op.drop_index('ix_conversations_user_id_analysis_id')
    op.drop_index('ix_conversations_analysis_id')
    op.drop_index('ix_conversations_user_id_updated_at')
    op.drop_index('ix_conversations_title_gin')
    
    op.drop_index('ix_messages_conversation_id_created_at')
    op.drop_index('ix_messages_role')
    op.drop_index('ix_messages_cost')
    op.drop_index('ix_messages_tokens_used')
    op.drop_index('ix_messages_content_gin')
    
    op.drop_index('ix_analyses_active_processing')
    op.drop_index('ix_analyses_completed_with_cost')