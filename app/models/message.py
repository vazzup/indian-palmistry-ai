"""
Message model for conversation messages.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class MessageRole(enum.Enum):
    """Role enum for message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(enum.Enum):
    """Type enum for message purpose."""
    INITIAL_READING = "initial_reading"  # First AI message with analysis summary
    USER_QUESTION = "user_question"      # User follow-up questions
    AI_RESPONSE = "ai_response"          # AI responses to questions


class Message(Base):
    """Message model for conversation messages."""
    
    __tablename__ = "messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Conversation relationship
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(Enum(MessageRole), nullable=False, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.USER_QUESTION, index=True)
    analysis_data = Column(JSON, nullable=True)  # Store full analysis data for initial reading modal
    
    # Processing metadata
    tokens_used = Column(Integer, default=0)  # Tokens used for AI responses
    cost = Column(Float, default=0.0)  # Cost for AI responses
    processing_time = Column(Float, nullable=True)  # Time taken for AI response
    
    # Status
    is_edited = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role.value})>"