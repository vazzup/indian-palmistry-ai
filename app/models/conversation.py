"""
Conversation model for follow-up questions on analyses.
"""

import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class ConversationMode(enum.Enum):
    """Mode enum for conversation display."""
    ANALYSIS = "analysis"  # Show full analysis view
    CHAT = "chat"         # Show chat interface


class Conversation(Base):
    """Conversation model for follow-up questions on analyses."""
    
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Analysis relationship
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metadata
    title = Column(String(255), nullable=False)  # Auto-generated or user-provided title
    is_active = Column(Boolean, default=True, nullable=False)
    mode = Column(Enum(ConversationMode), nullable=False, default=ConversationMode.CHAT, index=True)
    has_initial_message = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, analysis_id={self.analysis_id}, title={self.title})>"