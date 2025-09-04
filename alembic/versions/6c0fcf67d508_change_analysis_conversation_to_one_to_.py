"""change_analysis_conversation_to_one_to_one

Revision ID: 6c0fcf67d508
Revises: add_performance_indexes
Create Date: 2025-09-03 17:07:49.828943

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c0fcf67d508'
down_revision = 'add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add unique constraint on conversations.analysis_id to enforce one-to-one relationship
    # First, remove any duplicate conversations per analysis (keep the oldest one)
    op.execute("""
        DELETE FROM conversations 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM conversations 
            GROUP BY analysis_id
        )
    """)
    
    # Add unique constraint
    op.create_unique_constraint('uq_conversations_analysis_id', 'conversations', ['analysis_id'])


def downgrade() -> None:
    # Remove unique constraint to allow multiple conversations per analysis
    op.drop_constraint('uq_conversations_analysis_id', 'conversations', type_='unique')