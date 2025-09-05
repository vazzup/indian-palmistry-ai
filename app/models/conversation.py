"""
Conversation model for follow-up questions on analyses.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


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
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, analysis_id={self.analysis_id}, title={self.title})>"