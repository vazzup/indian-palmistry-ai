"""
Conversation model for follow-up questions on analyses.
"""

import enum
from typing import Dict, Any, Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class ConversationType(enum.Enum):
    """Type enum for conversation categories."""
    GENERAL = "general"
    ANALYSIS_FOLLOWUP = "analysis_followup"


class Conversation(Base):
    """Conversation model for follow-up questions on analyses."""
    
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Reading relationship
    reading_id = Column(Integer, ForeignKey("readings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metadata
    title = Column(String(255), nullable=False)  # Auto-generated or user-provided title
    is_active = Column(Boolean, default=True, nullable=False)
    
    # NEW FIELDS for Reading Follow-up
    openai_file_ids = Column(JSON, nullable=True, comment="OpenAI file IDs for palm images")
    questions_count = Column(Integer, default=0, nullable=False, comment="Number of questions asked")
    max_questions = Column(Integer, default=5, nullable=False, comment="Maximum questions allowed")
    is_analysis_followup = Column(Boolean, default=False, nullable=False, index=True, comment="Flag for reading follow-up conversations")
    analysis_context = Column(JSON, nullable=True, comment="Cached reading context for performance")
    
    # Enhanced metadata
    conversation_type = Column(Enum(ConversationType), default=ConversationType.GENERAL, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    reading = relationship("Reading", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, reading_id={self.reading_id}, title={self.title})>"