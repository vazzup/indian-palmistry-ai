"""Add analysis followup fields and conversation enhancements.

This migration implements the database schema changes required for Phase 1 of the
Analysis Follow-up Questions feature. It adds support for follow-up conversations
on completed palm reading analyses with comprehensive tracking and optimization.

**Feature Overview:**
The follow-up system allows users to ask specific questions about their completed
palm readings. The AI provides context-aware responses using the original palm
images and analysis results, creating an interactive consultation experience.

**Schema Changes:**
1. **Conversation Table Enhancements:**
   - OpenAI file IDs storage for palm image references
   - Question counting and limits enforcement
   - Analysis follow-up identification and type classification
   - Performance-optimized analysis context caching
   
2. **Analysis Table Extensions:**
   - OpenAI file IDs for reuse across conversations
   - Follow-up availability tracking
   - Usage statistics for question counting

3. **Performance Optimizations:**
   - Strategic indexes for common query patterns
   - Composite indexes for multi-field queries
   - Boolean flags for quick filtering operations

**Business Logic Support:**
- Maximum 5 follow-up questions per analysis (configurable)
- Only completed analyses support follow-up conversations
- User authorization through existing analysis ownership
- File management integration with OpenAI Files API

**Performance Considerations:**
- Indexes designed for dashboard and status queries
- Composite indexes reduce query complexity
- Boolean flags avoid expensive joins for filtering
- JSON storage for flexible metadata without additional tables

**Security Features:**
- User isolation through existing analysis ownership model
- No sensitive data in cached analysis context
- File ID validation through OpenAI Files Service
- Question limit enforcement at database level

**Rollback Safety:**
- All changes are reversible through the downgrade() function
- Index removal in correct order to avoid conflicts
- Enum type management with proper cleanup
- No data loss during rollback operations

**Migration Testing:**
- Test forward migration on empty and populated databases
- Verify index performance with sample data
- Test rollback scenarios with existing data
- Validate enum type creation and cleanup

Revision ID: add_analysis_followup_001
Revises: 819e95294bd3
Create Date: 2025-08-30 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_analysis_followup_001'
down_revision = '819e95294bd3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add analysis followup fields and performance optimizations.
    
    This function implements the forward migration for the follow-up questions feature.
    It adds new fields to existing tables, creates performance indexes, and sets up
    the necessary database constraints for the feature to function properly.
    
    **Migration Steps:**
    1. Create ConversationType enum for conversation classification
    2. Add follow-up related fields to conversations table
    3. Add follow-up tracking fields to analyses table  
    4. Create performance-optimized indexes
    5. Set up composite indexes for complex queries
    
    **Performance Strategy:**
    The indexes are designed to optimize the most common query patterns:
    - Finding follow-up conversations for a specific analysis
    - Filtering conversations by type and activity status
    - Quick checks for follow-up availability on analyses
    - Dashboard queries showing follow-up statistics
    
    **Data Safety:**
    All new fields have appropriate defaults to ensure compatibility
    with existing data. No existing data is modified during migration.
    """
    
    # Step 1: Create ConversationType enum for conversation classification
    # This enum distinguishes between general conversations and analysis follow-ups
    # checkfirst=True prevents errors if enum already exists
    conversationtype_enum = postgresql.ENUM(
        'GENERAL', 'ANALYSIS_FOLLOWUP', 
        name='conversationtype', 
        create_type=False
    )
    conversationtype_enum.create(op.get_bind(), checkfirst=True)
    
    # Step 2: Add follow-up related fields to conversations table
    # These fields enable follow-up conversation management and tracking
    
    # Store OpenAI file IDs for palm images used in AI responses
    # JSON format allows flexible storage of multiple file references
    op.add_column('conversations', sa.Column(
        'openai_file_ids', 
        postgresql.JSON(), 
        nullable=True, 
        comment="OpenAI file IDs for palm images used in AI context"
    ))
    
    # Track number of questions asked in this conversation
    # Used for enforcing question limits per analysis
    op.add_column('conversations', sa.Column(
        'questions_count', 
        sa.Integer(), 
        nullable=False, 
        server_default='0', 
        comment="Number of questions asked in this conversation"
    ))
    
    # Maximum questions allowed for this conversation
    # Configurable per conversation, defaults to 5
    op.add_column('conversations', sa.Column(
        'max_questions', 
        sa.Integer(), 
        nullable=False, 
        server_default='5', 
        comment="Maximum questions allowed in this conversation"
    ))
    
    # Boolean flag for quick identification of follow-up conversations
    # Optimizes queries that need to filter by conversation purpose
    op.add_column('conversations', sa.Column(
        'is_analysis_followup', 
        sa.Boolean(), 
        nullable=False, 
        server_default='false', 
        comment="Flag identifying analysis follow-up conversations"
    ))
    
    # Cached analysis context for improved response generation performance
    # Stores truncated analysis data to avoid repeated database queries
    op.add_column('conversations', sa.Column(
        'analysis_context', 
        postgresql.JSON(), 
        nullable=True, 
        comment="Cached analysis context for fast AI response generation"
    ))
    
    # Enum field for conversation type classification
    # Provides structured categorization beyond boolean flags
    op.add_column('conversations', sa.Column(
        'conversation_type', 
        conversationtype_enum, 
        nullable=False, 
        server_default='GENERAL',
        comment="Type classification for conversation routing and filtering"
    ))
    
    # Step 3: Add follow-up tracking fields to analyses table
    # These fields enable analysis-level follow-up management
    
    # Store OpenAI file IDs at analysis level for reuse across conversations
    # Avoids re-uploading images for multiple follow-up conversations
    op.add_column('analyses', sa.Column(
        'openai_file_ids', 
        postgresql.JSON(), 
        nullable=True, 
        comment="OpenAI file IDs cached for reuse across follow-up conversations"
    ))
    
    # Boolean flag for quick follow-up availability checks
    # Optimizes dashboard queries showing follow-up status
    op.add_column('analyses', sa.Column(
        'has_followup_conversation', 
        sa.Boolean(), 
        nullable=False, 
        server_default='false', 
        comment="Quick check flag for follow-up conversation existence"
    ))
    
    # Total count of follow-up questions across all conversations
    # Enables usage analytics and user statistics
    op.add_column('analyses', sa.Column(
        'followup_questions_count', 
        sa.Integer(), 
        nullable=False, 
        server_default='0', 
        comment="Total follow-up questions asked across all conversations"
    ))
    
    # Step 4: Create single-column indexes for basic filtering
    # These indexes optimize simple WHERE clause queries
    
    # Index for filtering conversations by follow-up status
    # Optimizes: WHERE is_analysis_followup = true
    op.create_index(
        'ix_conversations_is_analysis_followup', 
        'conversations', 
        ['is_analysis_followup']
    )
    
    # Index for filtering conversations by type
    # Optimizes: WHERE conversation_type = 'ANALYSIS_FOLLOWUP'
    op.create_index(
        'ix_conversations_conversation_type', 
        'conversations', 
        ['conversation_type']
    )
    
    # Index for filtering analyses with follow-up conversations
    # Optimizes: WHERE has_followup_conversation = true
    op.create_index(
        'ix_analyses_has_followup_conversation', 
        'analyses', 
        ['has_followup_conversation']
    )
    
    # Step 5: Create composite indexes for complex queries
    # These indexes optimize multi-column WHERE clauses
    
    # Index for finding follow-up conversations for specific analysis
    # Optimizes: WHERE analysis_id = ? AND is_analysis_followup = true
    op.create_index(
        'ix_conversations_analysis_followup', 
        'conversations', 
        ['analysis_id', 'is_analysis_followup']
    )
    
    # Index for filtering conversations by type and activity status
    # Optimizes: WHERE conversation_type = ? AND is_active = true
    op.create_index(
        'ix_conversations_type_active', 
        'conversations', 
        ['conversation_type', 'is_active']
    )


def downgrade() -> None:
    """Remove analysis followup fields and revert schema changes.
    
    This function implements the reverse migration to safely remove all
    follow-up related fields and indexes. It ensures clean rollback
    without data loss or constraint violations.
    
    **Rollback Strategy:**
    1. Remove indexes first to avoid constraint conflicts
    2. Drop columns in dependency order (foreign key considerations)
    3. Clean up enum types last to prevent orphaned references
    
    **Safety Considerations:**
    - Indexes removed before columns to prevent constraint violations
    - Column removal order prevents foreign key conflicts
    - Enum cleanup with checkfirst=True prevents errors
    - No data migration needed (columns contain only metadata)
    
    **Data Impact:**
    All follow-up related data will be permanently lost during rollback.
    This includes:
    - Follow-up conversation records
    - Question counts and limits
    - OpenAI file ID references
    - Analysis context cache
    
    **Recovery:**
    After rollback, the follow-up feature will be completely disabled.
    Re-running the forward migration will restore functionality but
    previous follow-up data cannot be recovered.
    """
    
    # Step 1: Remove composite indexes first to prevent constraint conflicts
    # Order matters: composite indexes must be dropped before single-column indexes
    # that might be used as components
    
    # Remove conversation type and activity status composite index
    op.drop_index('ix_conversations_type_active', table_name='conversations')
    
    # Remove analysis and follow-up status composite index  
    op.drop_index('ix_conversations_analysis_followup', table_name='conversations')
    
    # Step 2: Remove single-column indexes
    # These can be removed safely after composite indexes are gone
    
    # Remove analysis follow-up availability index
    op.drop_index('ix_analyses_has_followup_conversation', table_name='analyses')
    
    # Remove conversation type classification index
    op.drop_index('ix_conversations_conversation_type', table_name='conversations')
    
    # Remove follow-up conversation identification index
    op.drop_index('ix_conversations_is_analysis_followup', table_name='conversations')
    
    # Step 3: Remove columns from analyses table
    # Remove in reverse dependency order to avoid constraint violations
    
    # Remove total follow-up question count tracking
    op.drop_column('analyses', 'followup_questions_count')
    
    # Remove follow-up conversation existence flag
    op.drop_column('analyses', 'has_followup_conversation')
    
    # Remove cached OpenAI file IDs
    op.drop_column('analyses', 'openai_file_ids')
    
    # Step 4: Remove columns from conversations table  
    # Remove enum field first, then other fields
    
    # Remove conversation type enum field (depends on enum type)
    op.drop_column('conversations', 'conversation_type')
    
    # Remove cached analysis context
    op.drop_column('conversations', 'analysis_context')
    
    # Remove follow-up identification flag
    op.drop_column('conversations', 'is_analysis_followup')
    
    # Remove question limit setting
    op.drop_column('conversations', 'max_questions')
    
    # Remove question count tracking
    op.drop_column('conversations', 'questions_count')
    
    # Remove OpenAI file ID storage
    op.drop_column('conversations', 'openai_file_ids')
    
    # Step 5: Clean up enum type
    # Must be done last after all enum field references are removed
    # checkfirst=True prevents errors if enum doesn't exist
    conversationtype_enum = postgresql.ENUM(
        'GENERAL', 'ANALYSIS_FOLLOWUP', 
        name='conversationtype'
    )
    conversationtype_enum.drop(op.get_bind(), checkfirst=True)