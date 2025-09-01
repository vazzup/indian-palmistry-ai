"""
Pydantic schemas for conversation and message API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.message import MessageType, MessageRole


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
    message_type: MessageType
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


# Follow-up specific schemas
class FollowupStatusResponse(BaseModel):
    """
    Response schema for follow-up conversation status.
    
    Provides comprehensive information about the availability and current state
    of follow-up questions for a specific palm reading analysis.
    
    **Usage Context:**
    This schema is returned by the `GET /analyses/{id}/followup/status` endpoint
    and should be used to determine whether follow-up questions are available
    and what the current usage status is.
    
    **Business Rules:**
    - followup_available is True only when analysis_completed is True
    - questions_remaining = max_questions - questions_asked
    - has_openai_files indicates if palm images are uploaded for AI context
    - total_followup_questions tracks lifetime usage across all conversations
    
    **Example Response:**
    ```json
    {
        "analysis_id": 123,
        "analysis_completed": true,
        "followup_available": true,
        "followup_conversation_exists": false,
        "conversation_id": null,
        "questions_asked": 0,
        "questions_remaining": 5,
        "max_questions": 5,
        "has_openai_files": false,
        "total_followup_questions": 0
    }
    ```
    
    **Field Descriptions:**
    - analysis_id: ID of the palm reading analysis
    - analysis_completed: Whether the analysis has finished processing
    - followup_available: Whether follow-up questions can be asked
    - followup_conversation_exists: Whether a conversation thread already exists
    - conversation_id: ID of existing conversation (null if none exists)
    - questions_asked: Number of questions used in current conversation
    - questions_remaining: Number of questions left in current conversation
    - max_questions: Maximum questions allowed per analysis (typically 5)
    - has_openai_files: Whether palm images are uploaded to OpenAI for context
    - total_followup_questions: Total questions asked across all time
    """
    analysis_id: int = Field(..., description="ID of the palm reading analysis")
    analysis_completed: bool = Field(..., description="Whether the analysis has finished processing")
    followup_available: bool = Field(..., description="Whether follow-up questions can be asked")
    followup_conversation_exists: bool = Field(..., description="Whether a conversation thread already exists")
    conversation_id: Optional[int] = Field(None, description="ID of existing conversation (null if none exists)")
    questions_asked: int = Field(..., ge=0, description="Number of questions used in current conversation")
    questions_remaining: int = Field(..., ge=0, description="Number of questions left in current conversation")
    max_questions: int = Field(..., ge=1, le=10, description="Maximum questions allowed per analysis")
    has_openai_files: bool = Field(..., description="Whether palm images are uploaded to OpenAI")
    total_followup_questions: int = Field(..., ge=0, description="Total questions asked across all time")


class FollowupQuestionRequest(BaseModel):
    """
    Request schema for asking a follow-up question about a palm reading.
    
    This schema validates user questions to ensure they meet quality and security
    standards before being processed by the AI system.
    
    **Validation Rules:**
    - Length: 10-500 characters
    - Content: Must be related to palmistry
    - Security: No prompt injection attempts
    - Topics: Only palmistry-related questions allowed
    
    **Valid Question Examples:**
    ```json
    {
        "question": "What does my heart line reveal about my emotional nature?"
    }
    ```
    
    ```json
    {
        "question": "Can you explain the meaning of the mount of Venus in my palm?"
    }
    ```
    
    ```json
    {
        "question": "How do the lines on my fingers relate to my personality traits?"
    }
    ```
    
    **Invalid Examples (will be rejected):**
    - Too short: "Hi" (< 10 characters)
    - Too long: [> 500 characters]
    - Non-palmistry: "What's the weather like?"
    - Medical advice: "Can you diagnose my condition?"
    - Prompt injection: "Ignore previous instructions..."
    - Future predictions: "When will I get married?"
    
    **Security Features:**
    - Prompt injection detection and blocking
    - Content filtering for inappropriate topics
    - Automatic validation of palmistry relevance
    - Protection against context manipulation attempts
    """
    question: str = Field(
        ..., 
        min_length=10, 
        max_length=500, 
        description="Follow-up question about the palm reading (must be palmistry-related)",
        example="What does my heart line reveal about my emotional nature and approach to relationships?"
    )


class FollowupQuestionResponse(BaseModel):
    """
    Response schema for follow-up question and AI answer.
    
    Contains the complete question-answer exchange along with usage metrics
    and processing information for transparency and billing purposes.
    
    **Response Structure:**
    - user_message: The user's question with metadata
    - assistant_message: AI-generated palmistry response with context
    - questions_remaining: How many questions are left for this analysis
    - tokens_used: OpenAI API token consumption for cost tracking
    - cost: Estimated cost of this interaction in USD
    - processing_time: Time taken to generate the response in seconds
    
    **Example Response:**
    ```json
    {
        "user_message": {
            "id": 101,
            "conversation_id": 456,
            "message_type": "USER",
            "content": "What does my heart line reveal about my emotional nature?",
            "created_at": "2025-08-30T10:45:00Z"
        },
        "assistant_message": {
            "id": 102,
            "conversation_id": 456,
            "message_type": "ASSISTANT",
            "content": "Looking at your palm images, I can see that your heart line shows several distinctive characteristics...\n\n**Heart Line Analysis:**\nYour heart line appears deep and well-defined, which traditionally indicates...\n\n**Emotional Characteristics:**\nThe curve and length of your heart line suggests...",
            "tokens_used": 234,
            "cost": 0.0070,
            "processing_time": 2.1,
            "created_at": "2025-08-30T10:45:02Z"
        },
        "questions_remaining": 4,
        "tokens_used": 234,
        "cost": 0.0070,
        "processing_time": 2.1
    }
    ```
    
    **AI Response Features:**
    - Context-aware: Uses original palm images and analysis
    - Conversational: References previous questions in the same conversation
    - Educational: Explains palmistry principles and interpretations
    - Visual: Describes what the AI sees in the specific palm images
    - Structured: Often uses headers and bullet points for clarity
    
    **Usage Metrics:**
    - tokens_used: For API cost tracking and usage monitoring
    - cost: Estimated cost in USD (approximate, based on current OpenAI pricing)
    - processing_time: Includes AI processing and response formatting time
    - questions_remaining: Helps users manage their question allowance
    """
    user_message: MessageResponse = Field(..., description="The user's question message with metadata")
    assistant_message: MessageResponse = Field(..., description="AI-generated palmistry response with analysis")
    questions_remaining: int = Field(..., ge=0, description="Number of questions left for this analysis")
    tokens_used: int = Field(..., ge=0, description="OpenAI API tokens consumed for this response")
    cost: float = Field(..., ge=0, description="Estimated cost in USD for this interaction")
    processing_time: float = Field(..., ge=0, description="Time taken to generate response in seconds")


class FollowupConversationResponse(BaseModel):
    """
    Response schema for follow-up conversation details.
    
    Returned when a new follow-up conversation is created for a palm reading analysis.
    Contains all the information needed to start asking questions in the conversation.
    
    **Creation Process:**
    1. Validates that the analysis is completed and belongs to the user
    2. Uploads palm images to OpenAI Files API for visual context
    3. Creates conversation record with cached analysis context
    4. Sets up question limits and tracking
    
    **Example Response:**
    ```json
    {
        "id": 456,
        "analysis_id": 123,
        "title": "Questions about your palm reading",
        "questions_count": 0,
        "max_questions": 5,
        "openai_file_ids": {
            "left_palm": "file-abc123def456",
            "right_palm": "file-ghi789jkl012"
        },
        "created_at": "2025-08-30T10:30:00Z",
        "last_message_at": null,
        "is_active": true
    }
    ```
    
    **Key Information:**
    - id: Use this conversation ID for all future question requests
    - analysis_id: Reference to the original palm reading
    - questions_count: Starts at 0, increments with each question asked
    - max_questions: Typically 5, represents the question limit
    - openai_file_ids: File references for AI to access palm images
    - created_at: When the conversation was started
    - is_active: Whether the conversation accepts new questions
    
    **Next Steps After Creation:**
    1. Use the conversation ID to ask questions via POST /followup/{conversation_id}/ask
    2. Monitor questions_count to track usage
    3. Use GET /followup/{conversation_id}/history to view past Q&A
    """
    id: int = Field(..., description="Unique conversation ID for future question requests")
    analysis_id: int = Field(..., description="ID of the original palm reading analysis")
    title: str = Field(..., description="Auto-generated or custom conversation title")
    questions_count: int = Field(..., ge=0, description="Current number of questions asked")
    max_questions: int = Field(..., ge=1, le=10, description="Maximum questions allowed")
    openai_file_ids: Optional[dict] = Field(None, description="OpenAI file IDs for uploaded palm images")
    created_at: datetime = Field(..., description="When the conversation was created")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message in conversation")
    is_active: bool = Field(..., description="Whether the conversation accepts new questions")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 456,
                "analysis_id": 123,
                "title": "Questions about your palm reading",
                "questions_count": 0,
                "max_questions": 5,
                "openai_file_ids": {
                    "left_palm": "file-abc123def456",
                    "right_palm": "file-ghi789jkl012"
                },
                "created_at": "2025-08-30T10:30:00Z",
                "last_message_at": None,
                "is_active": True
            }
        }


class FollowupHistoryResponse(BaseModel):
    """
    Response schema for follow-up conversation history.
    
    Provides complete conversation history including all questions and answers
    exchanged between the user and AI about their palm reading.
    
    **History Structure:**
    - conversation: Basic conversation metadata and settings
    - messages: Chronological list of all questions and AI responses
    - questions_asked/remaining: Current usage statistics
    - analysis_context: Cached context from original palm reading (if available)
    
    **Example Response:**
    ```json
    {
        "conversation": {
            "id": 456,
            "analysis_id": 123,
            "title": "Questions about your palm reading",
            "questions_count": 2,
            "max_questions": 5,
            "created_at": "2025-08-30T10:30:00Z",
            "is_active": true
        },
        "messages": [
            {
                "id": 101,
                "message_type": "USER",
                "content": "What does my heart line reveal about my emotional nature?",
                "created_at": "2025-08-30T10:45:00Z"
            },
            {
                "id": 102,
                "message_type": "ASSISTANT",
                "content": "Looking at your palm images, your heart line shows...",
                "tokens_used": 187,
                "cost": 0.0056,
                "processing_time": 1.8,
                "created_at": "2025-08-30T10:45:02Z"
            },
            {
                "id": 103,
                "message_type": "USER",
                "content": "How does the mount of Venus relate to what you mentioned?",
                "created_at": "2025-08-30T11:00:00Z"
            },
            {
                "id": 104,
                "message_type": "ASSISTANT",
                "content": "Building on the heart line analysis, the mount of Venus...",
                "tokens_used": 203,
                "cost": 0.0061,
                "processing_time": 2.3,
                "created_at": "2025-08-30T11:00:03Z"
            }
        ],
        "questions_asked": 2,
        "questions_remaining": 3,
        "analysis_context": {
            "summary": "Your palm shows strong life and heart lines...",
            "full_report": "Detailed Analysis: Life Line: Strong and deep..."
        }
    }
    ```
    
    **Message Chronology:**
    - Messages are returned in chronological order (oldest first)
    - Each question is immediately followed by its AI response
    - User messages contain the original question text
    - Assistant messages include the full AI response with context
    
    **Usage for Frontend:**
    - Display messages in chat-like interface
    - Show usage statistics (questions asked/remaining)
    - Use analysis_context for additional reference information
    - Track conversation metadata for user experience
    
    **Pagination:**
    - Default limit: 20 messages (10 Q&A pairs)
    - Use limit parameter to control response size
    - For large conversations, implement pagination in frontend
    """
    conversation: FollowupConversationResponse = Field(..., description="Conversation metadata and settings")
    messages: List[MessageResponse] = Field(..., description="Chronological list of questions and AI responses")
    questions_asked: int = Field(..., ge=0, description="Number of questions asked in this conversation")
    questions_remaining: int = Field(..., ge=0, description="Number of questions remaining for this analysis")
    analysis_context: Optional[dict] = Field(None, description="Cached context from original palm reading analysis")