"""
Conversation API endpoints for palm reading follow-up discussions.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
    TalkRequest,
    TalkResponse,
    ConversationUpdateRequest
)
from app.services.conversation_service import ConversationService
from app.models.user import User
from app.dependencies.auth import get_current_user, verify_csrf_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyses/{analysis_id}/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    analysis_id: int,
    conversation_data: ConversationCreateRequest,
    current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """Create a new conversation for an analysis.
    
    Creates a new conversation thread for follow-up questions about a palm reading analysis.
    Only the analysis owner can create conversations.
    """
    try:
        conversation_service = ConversationService()
        
        conversation = await conversation_service.create_conversation(
            analysis_id=analysis_id,
            user_id=current_user.id,
            title=conversation_data.title
        )
        
        logger.info(f"Created conversation {conversation.id} for analysis {analysis_id}")
        
        return ConversationResponse.model_validate(conversation)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating conversation for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(5, ge=1, le=20, description="Items per page")
) -> ConversationListResponse:
    """List conversations for an analysis with pagination.
    
    Returns conversations ordered by creation date (most recent first).
    Only the analysis owner can view conversations.
    """
    try:
        conversation_service = ConversationService()
        
        conversations, total = await conversation_service.get_analysis_conversations(
            analysis_id=analysis_id,
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
        conversation_responses = [ConversationResponse.model_validate(c) for c in conversations]
        
        has_more = page * per_page < total
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_more=has_more,
            analysis_id=analysis_id
        )
        
    except Exception as e:
        logger.error(f"Error listing conversations for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    analysis_id: int,
    conversation_id: int,
    current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """Get conversation details.
    
    Returns conversation information for the specified conversation.
    Only the conversation owner can view it.
    """
    try:
        conversation_service = ConversationService()
        
        conversation = await conversation_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if conversation.analysis_id != analysis_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return ConversationResponse.model_validate(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    analysis_id: int,
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Items per page")
) -> MessageListResponse:
    """Get messages for a conversation with pagination.
    
    Returns messages ordered chronologically (oldest first).
    Only the conversation owner can view messages.
    """
    try:
        conversation_service = ConversationService()
        
        # Verify conversation exists and belongs to analysis
        conversation = await conversation_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation or conversation.analysis_id != analysis_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages, total = await conversation_service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.post("/{conversation_id}/talk", response_model=TalkResponse, dependencies=[Depends(verify_csrf_token)])
async def talk_to_ai(
    analysis_id: int,
    conversation_id: int,
    talk_data: TalkRequest,
    current_user: User = Depends(get_current_user)
) -> TalkResponse:
    """Send a message and get AI response.
    
    Adds the user's message to the conversation and generates an AI response
    based on the palm analysis and conversation history. Requires CSRF token.
    """
    try:
        conversation_service = ConversationService()
        
        # Verify conversation exists and belongs to analysis
        conversation = await conversation_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation or conversation.analysis_id != analysis_id:
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
        logger.error(f"Error in talk endpoint for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.put("/{conversation_id}", response_model=ConversationResponse, dependencies=[Depends(verify_csrf_token)])
async def update_conversation(
    analysis_id: int,
    conversation_id: int,
    update_data: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """Update conversation metadata.
    
    Updates conversation title and other metadata. Requires CSRF token.
    Only the conversation owner can update it.
    """
    try:
        conversation_service = ConversationService()
        
        # Update title if provided
        if update_data.title is not None:
            success = await conversation_service.update_conversation_title(
                conversation_id=conversation_id,
                user_id=current_user.id,
                new_title=update_data.title
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        
        # Return updated conversation
        conversation = await conversation_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation or conversation.analysis_id != analysis_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return ConversationResponse.model_validate(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/{conversation_id}")
async def delete_conversation(
    analysis_id: int,
    conversation_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Delete a conversation and all its messages.
    
    Permanently deletes the conversation and all associated messages.
    Only the conversation owner can delete it.
    """
    try:
        conversation_service = ConversationService()
        
        # Verify conversation exists and belongs to analysis first
        conversation = await conversation_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation or conversation.analysis_id != analysis_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        success = await conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        logger.info(f"Deleted conversation {conversation_id}")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )