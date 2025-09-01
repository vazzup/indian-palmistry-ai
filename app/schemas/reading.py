"""
Reading schemas for request/response validation.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from app.models.reading import ReadingStatus


class ReadingCreateRequest(BaseModel):
    """Request schema for creating new reading (multipart form data)."""
    # Note: Files are handled separately in FastAPI endpoint
    pass


class ReadingResponse(BaseModel):
    """Response schema for reading data."""
    
    id: int = Field(..., description="Reading ID")
    user_id: Optional[int] = Field(None, description="User ID (null for anonymous)")
    left_image_path: Optional[str] = Field(None, description="Path to left palm image")
    right_image_path: Optional[str] = Field(None, description="Path to right palm image")
    left_thumbnail_path: Optional[str] = Field(None, description="Path to left palm thumbnail")
    right_thumbnail_path: Optional[str] = Field(None, description="Path to right palm thumbnail")
    summary: Optional[str] = Field(None, description="Reading summary (available pre-login)")
    full_report: Optional[str] = Field(None, description="Full reading report (requires login)")
    status: ReadingStatus = Field(..., description="Reading processing status")
    job_id: Optional[str] = Field(None, description="Background job ID")
    error_message: Optional[str] = Field(None, description="Error message if reading failed")
    processing_started_at: Optional[datetime] = Field(None, description="When processing started")
    processing_completed_at: Optional[datetime] = Field(None, description="When processing completed")
    tokens_used: int = Field(default=0, description="OpenAI tokens used")
    cost: float = Field(default=0.0, description="Cost of reading processing")
    created_at: datetime = Field(..., description="When reading was created")
    updated_at: Optional[datetime] = Field(None, description="When reading was last updated")
    
    @field_serializer('created_at', 'updated_at', 'processing_started_at', 'processing_completed_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO string."""
        return dt.isoformat() if dt else None
    
    @field_serializer('status')
    def serialize_status(self, status: ReadingStatus) -> str:
        """Serialize status enum to string."""
        return status.value
    
    class Config:
        from_attributes = True


class ReadingStatusResponse(BaseModel):
    """Response schema for reading status polling."""
    
    reading_id: int = Field(..., description="Reading ID")
    status: str = Field(..., description="Current reading status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    message: str = Field(..., description="Human-readable status message")


class ReadingListResponse(BaseModel):
    """Response schema for listing user readings."""
    
    readings: list[ReadingResponse] = Field(..., description="List of readings")
    total: int = Field(..., description="Total number of readings")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of readings per page")
    has_more: bool = Field(..., description="Whether there are more readings")


class ReadingSummaryResponse(BaseModel):
    """Response schema for anonymous reading summary."""
    
    reading_id: int = Field(..., description="Reading ID")
    summary: Optional[str] = Field(None, description="Reading summary")
    status: str = Field(..., description="Reading status")
    created_at: str = Field(..., description="When reading was created")
    requires_login: bool = Field(default=True, description="Whether full report requires login")