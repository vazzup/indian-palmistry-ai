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
down_revision: Union[str, None] = 'rename_analyses_to_readings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add performance indexes."""
    
    # Check if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    is_sqlite = 'sqlite' in str(bind.engine.url)
    
    # Helper function to safely create indexes
    def safe_create_index(name, table, columns, **kwargs):
        try:
            op.create_index(name, table, columns, **kwargs)
        except Exception as e:
            if "already exists" in str(e):
                print(f"Index {name} already exists, skipping...")
            else:
                raise
    
    # Users table indexes
    safe_create_index('ix_users_email_lower', 'users', [sa.text('lower(email)')])
    safe_create_index('ix_users_created_at', 'users', ['created_at'])
    safe_create_index('ix_users_updated_at', 'users', ['updated_at'])
    safe_create_index('ix_users_is_active', 'users', ['is_active'])
    
    # Readings table indexes (renamed from analyses)
    safe_create_index('ix_readings_user_id_status', 'readings', ['user_id', 'status'])
    safe_create_index('ix_readings_status_created_at', 'readings', ['status', 'created_at'])
    safe_create_index('ix_readings_user_id_created_at', 'readings', ['user_id', 'created_at'])
    safe_create_index('ix_readings_processing_started_at', 'readings', ['processing_started_at'])
    safe_create_index('ix_readings_processing_completed_at', 'readings', ['processing_completed_at'])
    safe_create_index('ix_readings_cost', 'readings', ['cost'])
    safe_create_index('ix_readings_tokens_used', 'readings', ['tokens_used'])
    
    # Conversations table indexes
    safe_create_index('ix_conversations_reading_id', 'conversations', ['reading_id'])
    safe_create_index('ix_conversations_updated_at', 'conversations', ['updated_at'])
    
    # PostgreSQL-specific full text search indexes
    if not is_sqlite:
        safe_create_index('ix_conversations_title_gin', 'conversations', [sa.text("to_tsvector('english', title)")], postgresql_using='gin')
        safe_create_index('ix_messages_content_gin', 'messages', [sa.text("to_tsvector('english', content)")], postgresql_using='gin')
    
    # Messages table indexes (check if they already exist)
    safe_create_index('ix_messages_cost', 'messages', ['cost'])
    safe_create_index('ix_messages_tokens_used', 'messages', ['tokens_used'])
    
    # Partial indexes for common queries (PostgreSQL only)
    if not is_sqlite:
        safe_create_index(
            'ix_readings_active_processing', 
            'readings', 
            ['user_id', 'created_at'],
            postgresql_where=sa.text("status IN ('QUEUED', 'PROCESSING')")
        )
        
        safe_create_index(
            'ix_readings_completed_with_cost',
            'readings',
            ['user_id', 'cost', 'created_at'],
            postgresql_where=sa.text("status = 'COMPLETED' AND cost IS NOT NULL")
        )

def downgrade() -> None:
    """Remove performance indexes."""
    
    # Check if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    is_sqlite = 'sqlite' in str(bind.engine.url)
    
    # Helper function to safely drop indexes
    def safe_drop_index(name):
        try:
            op.drop_index(name)
        except Exception as e:
            if "no such index" in str(e).lower() or "does not exist" in str(e).lower():
                print(f"Index {name} does not exist, skipping...")
            else:
                raise
    
    # Remove all the indexes we created
    safe_drop_index('ix_users_email_lower')
    safe_drop_index('ix_users_created_at')
    safe_drop_index('ix_users_updated_at')
    safe_drop_index('ix_users_is_active')
    
    safe_drop_index('ix_readings_user_id_status')
    safe_drop_index('ix_readings_status_created_at')
    safe_drop_index('ix_readings_user_id_created_at')
    safe_drop_index('ix_readings_processing_started_at')
    safe_drop_index('ix_readings_processing_completed_at')
    safe_drop_index('ix_readings_cost')
    safe_drop_index('ix_readings_tokens_used')
    
    safe_drop_index('ix_conversations_reading_id')
    safe_drop_index('ix_conversations_updated_at')
    
    # PostgreSQL-specific indexes
    if not is_sqlite:
        safe_drop_index('ix_conversations_title_gin')
        safe_drop_index('ix_messages_content_gin')
        safe_drop_index('ix_readings_active_processing')
        safe_drop_index('ix_readings_completed_with_cost')
    
    safe_drop_index('ix_messages_cost')
    safe_drop_index('ix_messages_tokens_used')