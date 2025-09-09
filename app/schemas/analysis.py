"""
Analysis schemas for request/response validation.
"""

import json
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer, field_validator
from app.models.analysis import AnalysisStatus


class AnalysisCreateRequest(BaseModel):
    """Request schema for creating new analysis (multipart form data)."""
    # Note: Files are handled separately in FastAPI endpoint
    pass


class AnalysisResponse(BaseModel):
    """Response schema for analysis data."""
    
    id: int = Field(..., description="Analysis ID")
    user_id: Optional[int] = Field(None, description="User ID (null for anonymous)")
    left_image_path: Optional[str] = Field(None, description="Path to left palm image")
    right_image_path: Optional[str] = Field(None, description="Path to right palm image")
    left_thumbnail_path: Optional[str] = Field(None, description="Path to left palm thumbnail")
    right_thumbnail_path: Optional[str] = Field(None, description="Path to right palm thumbnail")
    summary: Optional[str] = Field(None, description="Analysis summary (available pre-login)")
    full_report: Optional[str] = Field(None, description="Full analysis report (requires login)")
    key_features: Optional[list[str]] = Field(None, description="Key features observed in palm")
    strengths: Optional[list[str]] = Field(None, description="Personal strengths identified")
    guidance: Optional[list[str]] = Field(None, description="Life guidance and recommendations")
    status: AnalysisStatus = Field(..., description="Analysis processing status")
    job_id: Optional[str] = Field(None, description="Background job ID")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    processing_started_at: Optional[datetime] = Field(None, description="When processing started")
    processing_completed_at: Optional[datetime] = Field(None, description="When processing completed")
    tokens_used: int = Field(default=0, description="OpenAI tokens used")
    cost: float = Field(default=0.0, description="Cost of analysis")
    created_at: datetime = Field(..., description="When analysis was created")
    updated_at: Optional[datetime] = Field(None, description="When analysis was last updated")
    
    # Conversation state
    conversation_mode: Literal['analysis', 'chat'] = Field(default='analysis', description="Current view mode for this analysis")
    conversation_id: Optional[int] = Field(None, description="Associated conversation ID if exists")
    
    @field_serializer('created_at', 'updated_at', 'processing_started_at', 'processing_completed_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO string."""
        return dt.isoformat() if dt else None
    
    @field_serializer('status')
    def serialize_status(self, status: AnalysisStatus) -> str:
        """Serialize status enum to string."""
        return status.value
    
    @field_validator('key_features', 'strengths', 'guidance', mode='before')
    @classmethod
    def parse_json_array(cls, v):
        """Parse JSON string arrays from database into Python lists."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v
    
    @classmethod
    def from_analysis(cls, analysis, conversation=None):
        """Create AnalysisResponse from Analysis model and optional Conversation."""
        # Convert the analysis model to dict
        analysis_dict = {
            'id': analysis.id,
            'user_id': analysis.user_id,
            'left_image_path': analysis.left_image_path,
            'right_image_path': analysis.right_image_path,
            'left_thumbnail_path': analysis.left_thumbnail_path,
            'right_thumbnail_path': analysis.right_thumbnail_path,
            'summary': analysis.summary,
            'full_report': analysis.full_report,
            'key_features': analysis.key_features,
            'strengths': analysis.strengths,
            'guidance': analysis.guidance,
            'status': analysis.status,
            'job_id': analysis.job_id,
            'error_message': analysis.error_message,
            'processing_started_at': analysis.processing_started_at,
            'processing_completed_at': analysis.processing_completed_at,
            'tokens_used': analysis.tokens_used,
            'cost': analysis.cost,
            'created_at': analysis.created_at,
            'updated_at': analysis.updated_at,
            'conversation_mode': 'chat' if conversation else 'analysis',
            'conversation_id': conversation.id if conversation else None
        }
        return cls(**analysis_dict)
    
    class Config:
        from_attributes = True


class AnalysisStatusResponse(BaseModel):
    """Response schema for analysis status polling."""
    
    analysis_id: int = Field(..., description="Analysis ID")
    status: str = Field(..., description="Current analysis status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    message: str = Field(..., description="Human-readable status message")
    result: Optional[dict] = Field(None, description="Analysis result when completed")


class AnalysisListResponse(BaseModel):
    """Response schema for listing user analyses."""
    
    analyses: list[AnalysisResponse] = Field(..., description="List of analyses")
    total: int = Field(..., description="Total number of analyses")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of analyses per page")
    has_more: bool = Field(..., description="Whether there are more analyses")


class AnalysisSummaryResponse(BaseModel):
    """Response schema for anonymous analysis summary."""
    
    analysis_id: int = Field(..., description="Analysis ID")
    summary: Optional[str] = Field(None, description="Analysis summary")
    status: str = Field(..., description="Analysis status")
    created_at: str = Field(..., description="When analysis was created")
    requires_login: bool = Field(default=True, description="Whether full report requires login")