"""
Pydantic schemas for conversation and message API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.message import MessageRole


class ConversationCreateRequest(BaseModel):
    """Request schema for creating a conversation."""
    title: Optional[str] = Field(None, max_length=200, description="Optional conversation title")


class ConversationUpdateRequest(BaseModel):
    """Request schema for updating a conversation."""
    title: Optional[str] = Field(None, max_length=200, description="New conversation title")


class ConversationResponse(BaseModel):
    """Response schema for conversation data."""
    id: int
    analysis_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Response schema for paginated conversation list."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    per_page: int
    has_more: bool
    analysis_id: int


class MessageResponse(BaseModel):
    """Response schema for message data."""
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response schema for paginated message list."""
    messages: List[MessageResponse]
    total: int
    page: int
    per_page: int
    has_more: bool
    conversation_id: int


class TalkRequest(BaseModel):
    """Request schema for sending a message to AI."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message to send")


class TalkResponse(BaseModel):
    """Response schema for AI conversation response."""
    user_message: MessageResponse
    assistant_message: MessageResponse
    tokens_used: int
    cost: float