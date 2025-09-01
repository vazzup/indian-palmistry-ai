"""
Analysis model for palm reading analyses.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class AnalysisStatus(enum.Enum):
    """Status enum for analysis processing."""
    QUEUED = "queued"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    """Analysis model for palm reading analyses."""
    
    __tablename__ = "analyses"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User relationship (nullable for anonymous uploads)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Image paths
    left_image_path = Column(String(500), nullable=True)
    right_image_path = Column(String(500), nullable=True)
    left_thumbnail_path = Column(String(500), nullable=True)
    right_thumbnail_path = Column(String(500), nullable=True)
    
    # Analysis results
    summary = Column(Text, nullable=True)  # Available pre-login
    full_report = Column(Text, nullable=True)  # Available post-login only
    
    # Job tracking
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.QUEUED, nullable=False, index=True)
    job_id = Column(String(255), nullable=True, index=True)  # Celery job ID
    error_message = Column(Text, nullable=True)
    
    # Processing metadata
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    tokens_used = Column(Integer, default=0)  # OpenAI token usage
    cost = Column(Float, default=0.0)  # Cost tracking
    
    # NEW FIELDS for OpenAI Files API
    openai_file_ids = Column(JSON, nullable=True, comment="OpenAI file IDs for reuse")
    has_followup_conversation = Column(Boolean, default=False, nullable=False, index=True, comment="Quick check for follow-up availability")
    followup_questions_count = Column(Integer, default=0, nullable=False, comment="Total follow-up questions asked")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # Relationship disabled - User model now uses 'readings' relationship
    # user = relationship("User", back_populates="analyses")
    # Conversation relationship disabled - Conversations now use reading_id
    # conversations = relationship("Conversation", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, user_id={self.user_id}, status={self.status.value})>"