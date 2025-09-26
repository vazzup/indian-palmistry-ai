"""single_reading_refactor_add_is_current_and_multiple_conversations

Revision ID: 75749e4e479b
Revises: 4421d6bfe6b9
Create Date: 2025-09-24 18:22:49.929630

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75749e4e479b'
down_revision = '4421d6bfe6b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_current column to analyses table for soft delete approach
    op.add_column('analyses', sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'))

    # Create unique index to enforce only one current analysis per user
    # SQLite syntax for partial unique index
    from sqlalchemy import text
    from alembic import context

    if context.get_bind().dialect.name == 'sqlite':
        # For SQLite, create the index manually with proper syntax
        op.execute('CREATE UNIQUE INDEX idx_user_current_analysis ON analyses(user_id) WHERE is_current = 1')
    else:
        # For PostgreSQL
        op.create_index('idx_user_current_analysis', 'analyses', ['user_id'], unique=True,
                       postgresql_where=text('is_current = true'))

    # For existing data: mark the most recent analysis as current for each user
    # First, set all analyses to not current
    op.execute("UPDATE analyses SET is_current = false")

    # Then mark the most recent one for each user as current
    op.execute("""
        UPDATE analyses
        SET is_current = true
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
                FROM analyses
                WHERE user_id IS NOT NULL
            ) ranked
            WHERE rn = 1
        )
    """)

    # Remove one-to-one constraint from conversations to analyses (already allows multiple)
    # The existing relationship already supports multiple conversations per analysis

    # Add title column to conversations table if it doesn't exist (it already exists based on model)
    # No need to add as the column already exists in the model


def downgrade() -> None:
    # Remove unique index
    op.drop_index('idx_user_current_analysis', table_name='analyses')

    # Remove is_current column
    op.drop_column('analyses', 'is_current')