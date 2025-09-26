"""
Top-level user conversations API endpoints.

These endpoints provide access to conversations for the current user's analysis
without requiring the analysis_id in the URL, supporting the single reading architecture.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
    MessageListResponse,
    TalkRequest,
    TalkResponse
)
from app.services.conversation_service import ConversationService
from app.services.analysis_service import AnalysisService
from app.models.user import User
from app.dependencies.auth import get_current_user, verify_csrf_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["user_conversations"])


@router.get("/", response_model=ConversationListResponse)
async def get_user_conversations(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    sort: str = Query("updated_at_desc", description="Sort order")
) -> ConversationListResponse:
    """Get all conversations for the current user's analysis.

    Returns conversations for the user's current analysis in the single reading model.
    This endpoint automatically finds the user's current analysis and returns its conversations.
    """
    try:
        # First, get the user's current analysis
        analysis_service = AnalysisService()
        current_analysis = await analysis_service.get_current_analysis(current_user.id)

        if not current_analysis:
            # No current analysis, return empty list
            return ConversationListResponse(
                conversations=[],
                total=0
            )

        # Get conversations for the current analysis
        conversation_service = ConversationService()
        conversations = await conversation_service.get_conversations_for_analysis(
            analysis_id=current_analysis.id,
            user_id=current_user.id
        )

        # Convert to response objects
        conversation_responses = []
        for conv in conversations:
            logger.info(f"Debug: Conversation {conv.id} - created_at={conv.created_at}, updated_at={conv.updated_at}, last_message_at={conv.last_message_at}")
            conversation_responses.append(ConversationResponse.from_conversation(conv, current_user.id))

        # Apply sorting
        if sort == "updated_at_desc":
            conversation_responses.sort(key=lambda c: c.updated_at, reverse=True)
        elif sort == "updated_at_asc":
            conversation_responses.sort(key=lambda c: c.updated_at)
        elif sort == "created_at_desc":
            conversation_responses.sort(key=lambda c: c.created_at, reverse=True)
        elif sort == "created_at_asc":
            conversation_responses.sort(key=lambda c: c.created_at)

        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_conversations = conversation_responses[start_idx:end_idx]

        logger.info(f"Retrieved {len(paginated_conversations)} conversations for user {current_user.id} (analysis {current_analysis.id})")

        return ConversationListResponse(
            conversations=paginated_conversations,
            total=len(conversation_responses)
        )

    except Exception as e:
        logger.error(f"Error getting conversations for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations"
        )


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Items per page")
) -> MessageListResponse:
    """Get messages for a conversation without requiring analysis_id.

    Automatically validates that the conversation belongs to the user's current analysis.
    Returns messages ordered chronologically (oldest first).
    """
    logger.info(f"GET user messages endpoint called: conversation_id={conversation_id}, user_id={current_user.id}")

    try:
        # Get user's current analysis
        analysis_service = AnalysisService()
        current_analysis = await analysis_service.get_current_analysis(current_user.id)

        if not current_analysis:
            logger.warning(f"User {current_user.id} has no current analysis")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current analysis found"
            )

        conversation_service = ConversationService()

        # Verify conversation exists and belongs to user
        logger.info(f"Looking for conversation {conversation_id} for user {current_user.id}")
        conversation = await conversation_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id
        )

        logger.info(f"Conversation found: {conversation is not None}")
        if conversation:
            logger.info(f"Conversation analysis_id: {conversation.analysis_id}, current_analysis: {current_analysis.id}")

        # Verify conversation belongs to current analysis
        if not conversation or conversation.analysis_id != current_analysis.id:
            logger.warning(f"Conversation not found or analysis mismatch: conversation={conversation is not None}, analysis_id_match={conversation.analysis_id == current_analysis.id if conversation else False}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        logger.info(f"Getting messages for conversation {conversation_id}, page={page}, per_page={per_page}")
        messages, total = await conversation_service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )

        logger.info(f"Retrieved {len(messages) if messages else 0} messages, total={total}")

        message_responses = [MessageResponse.model_validate(m) for m in messages]

        has_more = page * per_page < total

        return MessageListResponse(
            messages=message_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_more=has_more,
            conversation_id=conversation_id
        )

    except HTTPException as he:
        logger.warning(f"HTTP exception in get_conversation_messages: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error getting messages for conversation {conversation_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.post("/{conversation_id}/talk", response_model=TalkResponse, dependencies=[Depends(verify_csrf_token)])
async def talk_to_ai(
    conversation_id: int,
    talk_data: TalkRequest,
    current_user: User = Depends(get_current_user)
) -> TalkResponse:
    """Send a message and get AI response without requiring analysis_id.

    Automatically validates that the conversation belongs to the user's current analysis.
    Adds the user's message to the conversation and generates an AI response
    based on the palm analysis and conversation history. Requires CSRF token.
    """
    logger.info(f"POST user talk endpoint called: conversation_id={conversation_id}, user_id={current_user.id}")

    try:
        # Get user's current analysis
        analysis_service = AnalysisService()
        current_analysis = await analysis_service.get_current_analysis(current_user.id)

        if not current_analysis:
            logger.warning(f"User {current_user.id} has no current analysis")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current analysis found"
            )

        conversation_service = ConversationService()

        # Verify conversation exists and belongs to user's current analysis
        conversation = await conversation_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id
        )

        if not conversation or conversation.analysis_id != current_analysis.id:
            logger.warning(f"Conversation not found or analysis mismatch for conversation {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Add message and get AI response
        result = await conversation_service.add_message_and_respond(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_message=talk_data.message
        )

        logger.info(
            f"Added message pair to conversation {conversation_id}, "
            f"tokens: {result.get('tokens_used', 0)}"
        )

        return TalkResponse(
            user_message=MessageResponse.model_validate(result["user_message"]),
            assistant_message=MessageResponse.model_validate(result["assistant_message"]),
            tokens_used=result.get("tokens_used", 0),
            cost=result.get("cost", 0.0)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user talk endpoint for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )