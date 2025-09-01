"""
Analysis API endpoints for palm reading functionality.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request, Query, status
from app.schemas.analysis import (
    AnalysisResponse, 
    AnalysisStatusResponse, 
    AnalysisListResponse,
    AnalysisSummaryResponse
)
from app.schemas.conversation import (
    FollowupStatusResponse,
    FollowupQuestionRequest, 
    FollowupQuestionResponse,
    FollowupConversationResponse,
    FollowupHistoryResponse,
    MessageResponse
)
from app.services.analysis_service import AnalysisService
from app.services.analysis_followup_service import AnalysisFollowupService, AnalysisFollowupServiceError
from app.models.analysis import AnalysisStatus
from app.models.user import User
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    left_image: Optional[UploadFile] = File(None),
    right_image: Optional[UploadFile] = File(None),
    start_analysis: Optional[bool] = Form(True),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AnalysisResponse:
    """Create new palm analysis (up to 2 images) with optional analysis start.
    
    Accepts multipart form data with optional left_image and right_image files.
    At least one image is required. Analysis can be created anonymously or by logged-in users.
    
    Args:
        left_image: Optional left palm image file
        right_image: Optional right palm image file  
        start_analysis: Whether to start analysis processing immediately (default: True)
        current_user: Current authenticated user (optional for anonymous uploads)
        
    Returns:
        AnalysisResponse: Created analysis object with job_id if started
    """
    try:
        # Validate at least one image is provided
        if not left_image and not right_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one palm image is required"
            )
        
        analysis_service = AnalysisService()
        
        # Create analysis record and save images
        analysis = await analysis_service.create_analysis(
            user_id=current_user.id if current_user else None,
            left_image=left_image,
            right_image=right_image,
            start_analysis=start_analysis if start_analysis is not None else True
        )
        
        logger.info(f"Created analysis {analysis.id} for user {current_user.id if current_user else 'anonymous'}, start_analysis={start_analysis}")
        
        return AnalysisResponse.model_validate(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analysis"
        )


@router.post("/{analysis_id}/start", response_model=AnalysisResponse)
async def start_analysis(
    analysis_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AnalysisResponse:
    """Start processing for an existing analysis.
    
    Triggers background job processing for an analysis that was uploaded 
    but not yet started. Validates that the analysis exists, belongs to 
    the current user (if authenticated), and hasn't already been started.
    
    Args:
        analysis_id: ID of the analysis to start processing
        current_user: Current authenticated user (optional for anonymous analyses)
        
    Returns:
        AnalysisResponse: Updated analysis object with job_id
    """
    try:
        analysis_service = AnalysisService()
        
        # Start the analysis
        analysis = await analysis_service.start_analysis(
            analysis_id=analysis_id,
            user_id=current_user.id if current_user else None
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or you don't have permission to start it"
            )
        
        logger.info(f"Started analysis {analysis_id} for user {current_user.id if current_user else 'anonymous'}")
        
        return AnalysisResponse.model_validate(analysis)
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle business logic errors (e.g., already started)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start analysis"
        )


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: int) -> AnalysisStatusResponse:
    """Get current status of analysis job for polling.
    
    This endpoint can be used by the frontend to poll for analysis progress.
    It's available to both authenticated and anonymous users.
    """
    try:
        analysis_service = AnalysisService()
        analysis = await analysis_service.get_analysis_status(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Calculate progress percentage
        progress_map = {
            AnalysisStatus.QUEUED: 10,
            AnalysisStatus.PROCESSING: 50,
            AnalysisStatus.COMPLETED: 100,
            AnalysisStatus.FAILED: 0
        }
        progress = progress_map.get(analysis.status, 0)
        
        # Generate human-readable message
        message_map = {
            AnalysisStatus.QUEUED: "Analysis is queued for processing",
            AnalysisStatus.PROCESSING: "Analyzing palm images...",
            AnalysisStatus.COMPLETED: "Analysis completed successfully",
            AnalysisStatus.FAILED: "Analysis failed"
        }
        message = message_map.get(analysis.status, "Unknown status")
        
        return AnalysisStatusResponse(
            analysis_id=analysis.id,
            status=analysis.status.value,
            progress=progress,
            error_message=analysis.error_message,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis status"
        )


@router.get("/{analysis_id}/summary", response_model=AnalysisSummaryResponse)
async def get_analysis_summary(analysis_id: int) -> AnalysisSummaryResponse:
    """Get analysis summary (available without authentication).
    
    Returns the summary portion of the analysis which is available to anonymous users.
    Full reports require authentication.
    """
    try:
        analysis_service = AnalysisService()
        analysis = await analysis_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return AnalysisSummaryResponse(
            analysis_id=analysis.id,
            summary=analysis.summary,
            status=analysis.status.value,
            created_at=analysis.created_at.isoformat(),
            requires_login=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis summary {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis summary"
        )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
) -> AnalysisResponse:
    """Get full analysis details (requires authentication).
    
    Returns complete analysis including the full report, which is only available
    to authenticated users who own the analysis.
    """
    try:
        analysis_service = AnalysisService()
        analysis = await analysis_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Check if user owns this analysis or if it's anonymous and user is authenticated
        if analysis.user_id and analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this analysis"
            )
        
        return AnalysisResponse.model_validate(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis"
        )


@router.get("/", response_model=AnalysisListResponse)
async def list_user_analyses(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(5, ge=1, le=20, description="Items per page")
) -> AnalysisListResponse:
    """List analyses for the current user with pagination.
    
    Returns analyses ordered by creation date (most recent first).
    """
    try:
        analysis_service = AnalysisService()
        analyses, total = await analysis_service.get_user_analyses(
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
        analysis_responses = [AnalysisResponse.model_validate(a) for a in analyses]
        
        has_more = page * per_page < total
        
        return AnalysisListResponse(
            analyses=analysis_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error listing analyses for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list analyses"
        )


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Delete an analysis and all associated data.
    
    Only the owner of the analysis can delete it. This will remove the analysis,
    all associated images, conversations, and messages.
    """
    try:
        analysis_service = AnalysisService()
        success = await analysis_service.delete_analysis(
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or you don't have permission to delete it"
            )
        
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis"
        )


# Follow-up Question Endpoints

@router.get("/{analysis_id}/followup/status", response_model=FollowupStatusResponse)
async def get_followup_status(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FollowupStatusResponse:
    """
    Get follow-up conversation status for an analysis.
    
    Returns comprehensive status information about follow-up question availability,
    including question limits, usage counts, and conversation state. This endpoint
    should be called before attempting to start a follow-up conversation or ask questions.
    
    **Business Logic:**
    - Only completed analyses support follow-up questions
    - Each analysis allows up to 5 follow-up questions by default
    - Users can only access their own analyses
    - OpenAI file upload status affects conversation availability
    
    **Usage Example:**
    ```python
    # Check if follow-up is available for analysis ID 123
    response = await client.get("/api/v1/analyses/123/followup/status")
    if response["followup_available"] and not response["followup_conversation_exists"]:
        # Start a new conversation
        await client.post("/api/v1/analyses/123/followup/start")
    ```
    
    Args:
        analysis_id: ID of the analysis to check status for
        current_user: Authenticated user making the request
        db: Database session for data access
        
    Returns:
        FollowupStatusResponse: Comprehensive status information including:
            - analysis_completed: Whether the analysis is finished
            - followup_available: Whether follow-up questions can be asked
            - followup_conversation_exists: Whether a conversation already exists
            - questions_asked/remaining: Usage statistics
            - has_openai_files: Whether palm images are uploaded to OpenAI
            
    Raises:
        HTTPException(404): Analysis not found or not owned by user
        HTTPException(500): Internal server error
        
    **Response Example:**
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
        "has_openai_files": true,
        "total_followup_questions": 0
    }
    ```
    """
    try:
        followup_service = AnalysisFollowupService()
        
        status_info = await followup_service.get_followup_status(
            analysis_id=analysis_id,
            user_id=current_user.id,
            db=db
        )
        
        return FollowupStatusResponse(**status_info)
        
    except AnalysisFollowupServiceError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error getting follow-up status for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get follow-up status"
        )


@router.post("/{analysis_id}/followup/start", response_model=FollowupConversationResponse)
async def start_followup_conversation(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FollowupConversationResponse:
    """
    Start a follow-up conversation for an analysis.
    
    Creates a new conversation thread that enables users to ask specific questions
    about their completed palm reading. This endpoint handles the complex process
    of setting up the conversation context, including uploading palm images to
    OpenAI's Files API for visual reference in AI responses.
    
    **Key Features:**
    - Uploads palm images to OpenAI Files API for visual context
    - Creates conversation with cached analysis context for performance
    - Sets up question limits and tracking
    - Validates analysis ownership and completion status
    - Handles file re-upload if previous files are no longer accessible
    
    **Business Logic:**
    - Only works with completed analyses owned by the current user
    - Returns existing conversation if one already exists (idempotent)
    - Automatically uploads palm images to OpenAI for AI context
    - Caches analysis summary/report for improved response time
    
    **Usage Example:**
    ```python
    # Start a follow-up conversation for analysis 123
    response = await client.post("/api/v1/analyses/123/followup/start")
    conversation_id = response["id"]
    
    # Now you can ask questions using the conversation_id
    await client.post(
        f"/api/v1/analyses/123/followup/{conversation_id}/ask",
        json={"question": "What does my heart line indicate about relationships?"}
    )
    ```
    
    Args:
        analysis_id: ID of the completed analysis to create conversation for
        current_user: Authenticated user who owns the analysis
        db: Database session for transaction management
        
    Returns:
        FollowupConversationResponse: Created conversation details including:
            - id: Conversation ID for future question requests
            - analysis_id: Reference to the original analysis
            - title: Auto-generated conversation title
            - questions_count: Current question count (starts at 0)
            - max_questions: Maximum questions allowed (typically 5)
            - openai_file_ids: File IDs for uploaded palm images
            - created_at: Conversation creation timestamp
            - is_active: Whether conversation accepts new questions
            
    Raises:
        HTTPException(404): Analysis not found or not completed
        HTTPException(403): Analysis not owned by current user
        HTTPException(400): Analysis not eligible for follow-up or other validation error
        HTTPException(500): Internal server error (e.g., OpenAI API failure)
        
    **Response Example:**
    ```json
    {
        "id": 456,
        "analysis_id": 123,
        "title": "Questions about your palm reading",
        "questions_count": 0,
        "max_questions": 5,
        "openai_file_ids": {
            "left_palm": "file-abc123",
            "right_palm": "file-def456"
        },
        "created_at": "2025-08-30T10:30:00Z",
        "last_message_at": null,
        "is_active": true
    }
    ```
    """
    try:
        followup_service = AnalysisFollowupService()
        
        conversation = await followup_service.create_followup_conversation(
            analysis_id=analysis_id,
            user_id=current_user.id,
            db=db
        )
        
        logger.info(f"Started follow-up conversation {conversation.id} for analysis {analysis_id}")
        
        return FollowupConversationResponse.model_validate(conversation)
        
    except AnalysisFollowupServiceError as e:
        if "not found" in str(e).lower() or "not completed" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "not owned" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error starting follow-up conversation for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start follow-up conversation"
        )


@router.post("/{analysis_id}/followup/{conversation_id}/ask", response_model=FollowupQuestionResponse)
async def ask_followup_question(
    analysis_id: int,
    conversation_id: int,
    question_data: FollowupQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FollowupQuestionResponse:
    """
    Ask a follow-up question about the palm reading.
    
    Processes a user's question with full contextual awareness, including the original
    palm images, analysis results, and conversation history. The AI response is generated
    using GPT-4o with vision capabilities, providing detailed palmistry insights based
    on the user's specific palm features.
    
    **Key Features:**
    - Comprehensive validation of question content and security
    - Context-aware AI responses using palm images and analysis history
    - Question limit enforcement (5 questions per analysis by default)
    - Prompt injection protection and content filtering
    - Performance monitoring (tokens, cost, processing time)
    - Conversation history integration for coherent multi-turn dialogue
    
    **Question Validation:**
    - Length: 10-1000 characters
    - Content: Must be palmistry-related
    - Security: Prompt injection protection
    - Topics: Only palmistry, no medical/legal/financial advice
    - Predictions: Discourages specific future event predictions
    
    **AI Response Context:**
    - Original palm images uploaded to OpenAI
    - Complete analysis summary and detailed report
    - All previous questions and answers in conversation
    - Traditional palmistry knowledge base
    - Visual analysis of palm features
    
    **Usage Example:**
    ```python
    # Ask a specific question about palm features
    response = await client.post(
        \"/api/v1/analyses/123/followup/456/ask\",
        json={
            \"question\": \"What does the length and depth of my heart line indicate about my emotional nature?\"
        }
    )
    print(f\"AI Answer: {response['assistant_message']['content']}\")
    print(f\"Questions remaining: {response['questions_remaining']}\")
    print(f\"Processing cost: ${response['cost']:.4f}\")
    ```
    
    Args:
        analysis_id: ID of the analysis (used for validation and security)
        conversation_id: ID of the follow-up conversation containing context
        question_data: Request payload containing the question text
        current_user: Authenticated user who owns the analysis
        db: Database session for transaction management
        
    Returns:
        FollowupQuestionResponse: Complete question-answer exchange with metadata:
            - user_message: The user's question with timestamp and metadata
            - assistant_message: AI response with full palmistry analysis
            - questions_remaining: Number of questions left in this conversation
            - tokens_used: OpenAI API token consumption for this interaction
            - cost: Estimated API cost for this request
            - processing_time: Time taken to generate the response
            
    Raises:
        HTTPException(400): Invalid question format, content, or validation error
        HTTPException(404): Conversation not found or not accessible by user
        HTTPException(429): Maximum questions exceeded for this analysis
        HTTPException(500): Internal server error or OpenAI API failure
        
    **Request Example:**
    ```json
    {
        \"question\": \"Can you explain what the three main lines in my palm indicate about my personality and life path?\"
    }
    ```
    
    **Response Example:**
    ```json
    {
        \"user_message\": {
            \"id\": 123,
            \"conversation_id\": 456,
            \"message_type\": \"USER\",
            \"content\": \"Can you explain what the three main lines...\",
            \"created_at\": \"2025-08-30T10:45:00Z\"
        },
        \"assistant_message\": {
            \"id\": 124,
            \"conversation_id\": 456,
            \"message_type\": \"ASSISTANT\",
            \"content\": \"Looking at your palm images, I can see three distinct main lines...\\n\\n**Heart Line**: Your heart line shows...\\n\\n**Head Line**: The head line in your palm indicates...\\n\\n**Life Line**: Your life line suggests...\",
            \"tokens_used\": 245,
            \"cost\": 0.0074,
            \"processing_time\": 2.3,
            \"created_at\": \"2025-08-30T10:45:02Z\"
        },
        \"questions_remaining\": 4,
        \"tokens_used\": 245,
        \"cost\": 0.0074,
        \"processing_time\": 2.3
    }
    ```
    
    **Security Notes:**
    - Questions are validated for prompt injection attempts
    - Only palmistry-related questions are allowed
    - Medical, legal, and financial advice requests are blocked
    - User can only access their own analyses and conversations
    """
    try:
        followup_service = AnalysisFollowupService()
        
        result = await followup_service.ask_followup_question(
            conversation_id=conversation_id,
            user_id=current_user.id,
            question=question_data.question,
            db=db
        )
        
        logger.info(f"Processed follow-up question for conversation {conversation_id}")
        
        return FollowupQuestionResponse(
            user_message=MessageResponse.model_validate(result["user_message"]),
            assistant_message=MessageResponse.model_validate(result["assistant_message"]),
            questions_remaining=result["questions_remaining"],
            tokens_used=result["tokens_used"],
            cost=result["cost"],
            processing_time=result["processing_time"]
        )
        
    except AnalysisFollowupServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "not accessible" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "maximum" in error_msg or "questions allowed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error processing follow-up question for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question"
        )


@router.get("/{analysis_id}/followup/{conversation_id}/history", response_model=FollowupHistoryResponse)
async def get_followup_history(
    analysis_id: int,
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of messages to return")
) -> FollowupHistoryResponse:
    """
    Get conversation history for a follow-up conversation.
    
    Returns the conversation details and message history with proper
    authentication and authorization checks.
    
    Args:
        analysis_id: ID of the analysis (for validation)
        conversation_id: ID of the follow-up conversation
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of messages to return
        
    Returns:
        FollowupHistoryResponse: Conversation and message history
    """
    try:
        followup_service = AnalysisFollowupService()
        
        result = await followup_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=current_user.id,
            db=db,
            limit=limit
        )
        
        message_responses = [MessageResponse.model_validate(msg) for msg in result["messages"]]
        
        return FollowupHistoryResponse(
            conversation=FollowupConversationResponse.model_validate(result["conversation"]),
            messages=message_responses,
            questions_asked=result["questions_asked"],
            questions_remaining=result["questions_remaining"],
            analysis_context=result["analysis_context"]
        )
        
    except AnalysisFollowupServiceError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error getting follow-up history for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation history"
        )