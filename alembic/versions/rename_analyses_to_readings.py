"""Rename analyses to readings for consistent nomenclature

Revision ID: rename_analyses_to_readings
Revises: add_analysis_followup_001
Create Date: 2025-09-01 07:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Engine
import sqlite3


# revision identifiers, used by Alembic.
revision = 'rename_analyses_to_readings'
down_revision = 'add_analysis_followup_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename analyses table to readings and update all references."""
    
    # Get database connection to check if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    
    if isinstance(bind.engine, Engine) and 'sqlite' in str(bind.engine.url):
        # SQLite approach - create new table and copy data
        upgrade_sqlite()
    else:
        # PostgreSQL approach - use ALTER TABLE
        upgrade_postgresql()


def upgrade_sqlite() -> None:
    """SQLite-specific upgrade using table recreation."""
    
    # Drop existing readings table if it exists (from failed migration attempts)
    op.execute("DROP TABLE IF EXISTS readings")
    op.execute("DROP TABLE IF EXISTS conversations_new")
    
    # Create new readings table with exact same structure as analyses
    op.create_table('readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('left_image_path', sa.String(length=500), nullable=True),
        sa.Column('right_image_path', sa.String(length=500), nullable=True),
        sa.Column('left_thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('right_thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('full_report', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('job_id', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('openai_file_ids', sa.JSON(), nullable=True),
        sa.Column('has_followup_conversation', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('followup_questions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for readings table
    op.create_index(op.f('ix_readings_id'), 'readings', ['id'], unique=False)
    op.create_index(op.f('ix_readings_user_id'), 'readings', ['user_id'], unique=False)
    op.create_index(op.f('ix_readings_status'), 'readings', ['status'], unique=False)
    op.create_index(op.f('ix_readings_created_at'), 'readings', ['created_at'], unique=False)
    
    # Copy data from analyses to readings
    op.execute('INSERT INTO readings SELECT * FROM analyses')
    
    # Create new conversations table with reading_id
    op.create_table('conversations_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reading_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('openai_file_ids', sa.JSON(), nullable=True),
        sa.Column('questions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_questions', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_analysis_followup', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('analysis_context', sa.JSON(), nullable=True),
        sa.Column('conversation_type', sa.Enum('GENERAL', 'ANALYSIS_FOLLOWUP', name='conversationtype'), nullable=False, server_default='GENERAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['reading_id'], ['readings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for new conversations table
    op.create_index(op.f('ix_conversations_new_reading_id'), 'conversations_new', ['reading_id'], unique=False)
    op.create_index(op.f('ix_conversations_new_created_at'), 'conversations_new', ['created_at'], unique=False)
    op.create_index(op.f('ix_conversations_new_last_message_at'), 'conversations_new', ['last_message_at'], unique=False)
    op.create_index(op.f('ix_conversations_new_is_analysis_followup'), 'conversations_new', ['is_analysis_followup'], unique=False)
    op.create_index(op.f('ix_conversations_new_conversation_type'), 'conversations_new', ['conversation_type'], unique=False)
    
    # Copy conversations data with renamed foreign key
    op.execute('INSERT INTO conversations_new (id, reading_id, title, is_active, openai_file_ids, questions_count, max_questions, is_analysis_followup, analysis_context, conversation_type, created_at, updated_at, last_message_at) SELECT id, analysis_id, title, is_active, openai_file_ids, questions_count, max_questions, is_analysis_followup, analysis_context, conversation_type, created_at, updated_at, last_message_at FROM conversations')
    
    # Drop old tables
    op.drop_table('conversations')
    op.drop_table('analyses')
    
    # Rename new conversations table
    op.rename_table('conversations_new', 'conversations')


def upgrade_postgresql() -> None:
    """PostgreSQL-specific upgrade using ALTER TABLE."""
    
    # Rename the analyses table to readings
    op.rename_table('analyses', 'readings')
    
    # Rename the foreign key column in conversations table
    op.alter_column('conversations', 'analysis_id', new_column_name='reading_id')
    
    # Update foreign key constraint name if needed
    op.drop_constraint('conversations_analysis_id_fkey', 'conversations', type_='foreignkey')
    op.create_foreign_key('conversations_reading_id_fkey', 'conversations', 'readings', ['reading_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Revert readings table back to analyses."""
    
    bind = op.get_bind()
    
    if isinstance(bind.engine, Engine) and 'sqlite' in str(bind.engine.url):
        downgrade_sqlite()
    else:
        downgrade_postgresql()


def downgrade_sqlite() -> None:
    """SQLite-specific downgrade."""
    
    # Create analyses table with exact same structure as original
    op.create_table('analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('left_image_path', sa.String(length=500), nullable=True),
        sa.Column('right_image_path', sa.String(length=500), nullable=True),
        sa.Column('left_thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('right_thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('full_report', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('job_id', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('openai_file_ids', sa.JSON(), nullable=True),
        sa.Column('has_followup_conversation', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('followup_questions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_analyses_id'), 'analyses', ['id'], unique=False)
    op.create_index(op.f('ix_analyses_user_id'), 'analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_analyses_status'), 'analyses', ['status'], unique=False)
    op.create_index(op.f('ix_analyses_created_at'), 'analyses', ['created_at'], unique=False)
    
    # Copy data back
    op.execute('INSERT INTO analyses SELECT * FROM readings')
    
    # Create conversations with analysis_id
    op.create_table('conversations_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('openai_file_ids', sa.JSON(), nullable=True),
        sa.Column('questions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_questions', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_analysis_followup', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('analysis_context', sa.JSON(), nullable=True),
        sa.Column('conversation_type', sa.Enum('GENERAL', 'ANALYSIS_FOLLOWUP', name='conversationtype'), nullable=False, server_default='GENERAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy conversations data back
    op.execute('INSERT INTO conversations_old (id, analysis_id, title, is_active, openai_file_ids, questions_count, max_questions, is_analysis_followup, analysis_context, conversation_type, created_at, updated_at, last_message_at) SELECT id, reading_id, title, is_active, openai_file_ids, questions_count, max_questions, is_analysis_followup, analysis_context, conversation_type, created_at, updated_at, last_message_at FROM conversations')
    
    # Drop new tables
    op.drop_table('conversations')
    op.drop_table('readings')
    
    # Rename back
    op.rename_table('conversations_old', 'conversations')


def downgrade_postgresql() -> None:
    """PostgreSQL-specific downgrade."""
    
    # Rename the readings table back to analyses
    op.rename_table('readings', 'analyses')
    
    # Rename the foreign key column back
    op.alter_column('conversations', 'reading_id', new_column_name='analysis_id')
    
    # Update foreign key constraint
    op.drop_constraint('conversations_reading_id_fkey', 'conversations', type_='foreignkey')
    op.create_foreign_key('conversations_analysis_id_fkey', 'conversations', 'analyses', ['analysis_id'], ['id'], ondelete='CASCADE')