"""
SQLAlchemy database models for users, readings, and conversations.
"""

from .base import Base
from .user import User
from .reading import Reading, ReadingStatus
from .conversation import Conversation, ConversationType
from .message import Message, MessageType, MessageRole

# Keep Analysis imports for backward compatibility during migration
from .analysis import Analysis, AnalysisStatus

__all__ = [
    "Base",
    "User", 
    "Reading",
    "ReadingStatus",
    "Conversation",
    "ConversationType",
    "Message",
    "MessageType",
    "MessageRole",
    # Legacy aliases for backward compatibility
    "Analysis",
    "AnalysisStatus"
]