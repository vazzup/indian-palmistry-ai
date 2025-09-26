"""
Conversation service for managing palm reading conversations.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from app.models.conversation import Conversation, ConversationMode
from app.models.message import Message, MessageRole, MessageType
from app.models.analysis import Analysis
from app.services.openai_service import OpenAIService
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing palm reading conversations."""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize conversation service."""
        self.db = db
        self.openai_service = OpenAIService()
        
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db:
            return self.db
        return AsyncSessionLocal()
    
    async def create_conversation(
        self,
        analysis_id: int,
        user_id: int,
        title: Optional[str] = None,
        auto_generate_title: bool = False,
        first_message: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation for an analysis.

        Now supports multiple conversations per analysis. Optionally auto-generates
        titles from the first message using OpenAI.

        Args:
            analysis_id: ID of the analysis
            user_id: ID of the user creating the conversation
            title: Optional title for the conversation
            auto_generate_title: Whether to auto-generate title from first message
            first_message: First message content for title generation

        Returns:
            Conversation instance (newly created)
        """
        try:
            async with await self.get_session() as db:
                # Verify analysis exists and belongs to user
                analysis_stmt = select(Analysis).where(
                    and_(Analysis.id == analysis_id, Analysis.user_id == user_id)
                )
                analysis_result = await db.execute(analysis_stmt)
                analysis = analysis_result.scalar_one_or_none()
                
                if not analysis:
                    raise ValueError("Analysis not found or access denied")
                
                # Auto-generate title from first message if requested
                if auto_generate_title and first_message and not title:
                    title = await self._generate_conversation_title(first_message)

                # Generate default title if not provided
                if not title:
                    conversation_count = await self._get_conversation_count_for_analysis(db, analysis_id)
                    title = f"Conversation {conversation_count + 1}"
                
                conversation = Conversation(
                    analysis_id=analysis_id,
                    title=title
                )
                
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)
                
                logger.info(f"Created conversation {conversation.id} for analysis {analysis_id}")
                return conversation
                
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def initialize_conversation_with_reading(
        self,
        analysis_id: int,
        user_id: int,
        first_question: str
    ) -> Dict[str, Any]:
        """Initialize a conversation with first Q&A.

        Creates conversation with:
        1. User's first question
        2. AI response with full analysis context

        Args:
            analysis_id: ID of the analysis
            user_id: ID of the user
            first_question: User's first question

        Returns:
            Dictionary with conversation, user message and assistant response
        """
        try:
            async with await self.get_session() as db:
                # Verify analysis exists and belongs to user
                analysis_stmt = select(Analysis).where(
                    and_(Analysis.id == analysis_id, Analysis.user_id == user_id)
                )
                analysis_result = await db.execute(analysis_stmt)
                analysis = analysis_result.scalar_one_or_none()
                
                if not analysis:
                    raise ValueError("Analysis not found or access denied")
                
                # Create new conversation with auto-generated title
                title = await self._generate_conversation_title(first_question)

                conversation = Conversation(
                    analysis_id=analysis_id,
                    title=title,
                    mode=ConversationMode.CHAT,
                    has_initial_message=False
                )
                
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)
                
                logger.info(f"Created conversation {conversation.id} for analysis {analysis_id}")
                
                # Prepare full analysis data for the modal
                analysis_data = {
                    "summary": analysis.summary,
                    "full_report": analysis.full_report,
                    "key_features": json.loads(analysis.key_features) if analysis.key_features else [],
                    "strengths": json.loads(analysis.strengths) if analysis.strengths else [],
                    "guidance": json.loads(analysis.guidance) if analysis.guidance else [],
                    "created_at": analysis.created_at.isoformat(),
                    "processing_time": None
                }
                
                if analysis.processing_started_at and analysis.processing_completed_at:
                    processing_time = (analysis.processing_completed_at - analysis.processing_started_at).total_seconds()
                    analysis_data["processing_time"] = processing_time
                
                # Add user's first question
                user_msg = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.USER,
                    content=first_question,
                    message_type=MessageType.USER_QUESTION
                )
                db.add(user_msg)
                
                await db.commit()
                await db.refresh(user_msg)
                
                # Generate AI response to the first question with full context
                ai_response_data = await self._generate_contextual_response(
                    analysis, first_question, []
                )
                
                # Add AI response
                ai_msg = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=ai_response_data["response"],
                    message_type=MessageType.AI_RESPONSE,
                    tokens_used=ai_response_data.get("tokens_used", 0),
                    cost=ai_response_data.get("cost", 0.0)
                )
                db.add(ai_msg)
                await db.commit()
                await db.refresh(ai_msg)
                
                logger.info(
                    f"Initialized conversation {conversation.id} with {ai_response_data.get('tokens_used', 0)} tokens"
                )
                
                return {
                    "conversation": conversation,
                    "user_message": user_msg,
                    "assistant_message": ai_msg,
                    "tokens_used": ai_response_data.get("tokens_used", 0),
                    "cost": ai_response_data.get("cost", 0.0)
                }
                
        except Exception as e:
            logger.error(f"Error initializing conversation: {e}")
            raise
    
    async def _generate_contextual_response(
        self,
        analysis: Analysis,
        user_question: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Generate AI response with full analysis context.
        
        Args:
            analysis: Analysis model with full data
            user_question: User's question
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Use assistant thread if available for better context
            if hasattr(analysis, 'thread_id') and analysis.thread_id:
                return await self.openai_service.generate_conversation_response_with_assistant(
                    thread_id=analysis.thread_id,
                    user_question=user_question
                )
            else:
                # CRITICAL FIX: Use OpenAI Responses API with full visual context
                # This method includes palm images (via file_ids) along with complete analysis data
                # Previously was calling non-existent method and falling back to text-only responses
                return await self.openai_service.generate_conversation_response_with_images(
                    analysis_summary=analysis.summary or "",
                    analysis_full_report=analysis.full_report or "",
                    key_features=json.loads(analysis.key_features) if analysis.key_features else [],
                    strengths=json.loads(analysis.strengths) if analysis.strengths else [],
                    guidance=json.loads(analysis.guidance) if analysis.guidance else [],
                    left_file_id=analysis.left_file_id,  # OpenAI file ID for left palm image
                    right_file_id=analysis.right_file_id,  # OpenAI file ID for right palm image
                    conversation_history=conversation_history,
                    user_question=user_question
                )
                
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            # IMPORTANT: Re-raise exception instead of using dangerous fallback
            # Previous implementation silently fell back to text-only response, masking bugs
            raise
    
    async def get_conversation_by_id(
        self,
        conversation_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """Get conversation by ID with user access check.
        
        IMPORTANT: Conversations don't have a direct user_id field. 
        Ownership is validated through the associated Analysis.user_id.
        This was previously attempting to check Conversation.user_id which doesn't exist.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control
            
        Returns:
            Conversation instance if found and accessible, None if not found or access denied
        """
        try:
            async with await self.get_session() as db:
                logger.info(f"ConversationService debug: Looking for conversation_id={conversation_id} for user_id={user_id}")
                
                # FIXED: Join with Analysis to check ownership through analysis.user_id
                # Previously was checking non-existent Conversation.user_id field
                stmt = (
                    select(Conversation)
                    .join(Analysis, Conversation.analysis_id == Analysis.id)
                    .where(
                        and_(
                            Conversation.id == conversation_id,
                            Analysis.user_id == user_id
                        )
                    )
                )
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                logger.info(f"ConversationService debug: Conversation found: {conversation is not None}")
                if conversation:
                    logger.info(f"ConversationService debug: Conversation analysis_id: {conversation.analysis_id}")
                
                return conversation
                
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    async def get_analysis_conversation(
        self,
        analysis_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """Get the single conversation for an analysis (one-to-one relationship).
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID for access control
            
        Returns:
            Conversation instance if found, None otherwise
        """
        try:
            async with await self.get_session() as db:
                # Verify access to analysis
                analysis_stmt = select(Analysis).where(
                    and_(Analysis.id == analysis_id, Analysis.user_id == user_id)
                )
                analysis_result = await db.execute(analysis_stmt)
                analysis = analysis_result.scalar_one_or_none()
                
                if not analysis:
                    return None
                
                # Get the single conversation for this analysis
                stmt = select(Conversation).where(Conversation.analysis_id == analysis_id)
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                return conversation
                
        except Exception as e:
            logger.error(f"Error getting conversation for analysis {analysis_id}: {e}")
            return None
    
    async def get_conversation_messages(
        self,
        conversation_id: int,
        user_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[List[Message], int]:
        """Get messages for a conversation with pagination.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control
            page: Page number (1-based) 
            per_page: Number of messages per page
            
        Returns:
            Tuple of (messages_list, total_count)
        """
        try:
            async with await self.get_session() as db:
                # Verify access to conversation
                conversation = await self.get_conversation_by_id(conversation_id, user_id)
                if not conversation:
                    return [], 0
                
                # Get total count
                count_stmt = select(Message).where(Message.conversation_id == conversation_id)
                count_result = await db.execute(count_stmt)
                total = len(count_result.fetchall())
                
                # Get paginated results (oldest first for conversations)
                offset = (page - 1) * per_page
                stmt = (
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                    .limit(per_page)
                    .offset(offset)
                )
                
                result = await db.execute(stmt)
                messages = result.scalars().all()
                
                return list(messages), total
                
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            return [], 0
    
    async def add_message_and_respond(
        self,
        conversation_id: int,
        user_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """Add user message and generate AI response.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            user_message: User's message content
            
        Returns:
            Dictionary with user and assistant messages
        """
        try:
            async with await self.get_session() as db:
                # Verify access to conversation
                conversation = await self.get_conversation_by_id(conversation_id, user_id)
                if not conversation:
                    raise ValueError("Conversation not found or access denied")
                
                # Get the analysis for context
                analysis_stmt = select(Analysis).where(Analysis.id == conversation.analysis_id)
                analysis_result = await db.execute(analysis_stmt)
                analysis = analysis_result.scalar_one_or_none()
                
                if not analysis:
                    raise ValueError("Associated analysis not found")
                
                # Get conversation history
                messages_stmt = (
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                )
                messages_result = await db.execute(messages_stmt)
                existing_messages = messages_result.scalars().all()
                
                # Format conversation history for OpenAI
                conversation_history = []
                for msg in existing_messages:
                    conversation_history.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
                
                # Add user message to database
                user_msg = Message(
                    conversation_id=conversation_id,
                    role=MessageRole.USER,
                    content=user_message,
                    message_type=MessageType.USER_QUESTION
                )
                db.add(user_msg)
                await db.commit()
                await db.refresh(user_msg)
                
                # Generate AI response using unified contextual response method
                # This ensures consistent conversation flow regardless of whether
                # the analysis has a thread_id (assistant mode) or not (fallback mode)
                ai_response_data = await self._generate_contextual_response(
                    analysis, user_message, conversation_history
                )
                
                # Add AI response to database
                ai_msg = Message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=ai_response_data["response"],
                    message_type=MessageType.AI_RESPONSE,
                    tokens_used=ai_response_data.get("tokens_used", 0),
                    cost=ai_response_data.get("cost", 0.0)
                )
                db.add(ai_msg)
                await db.commit()
                await db.refresh(ai_msg)
                
                logger.info(
                    f"Added message pair to conversation {conversation_id}, "
                    f"tokens: {ai_response_data.get('tokens_used', 0)}"
                )
                
                return {
                    "user_message": user_msg,
                    "assistant_message": ai_msg,
                    "tokens_used": ai_response_data.get("tokens_used", 0),
                    "cost": ai_response_data.get("cost", 0.0)
                }
                
        except Exception as e:
            logger.error(f"Error adding message and responding: {e}")
            raise
    
    async def update_conversation_title(
        self,
        conversation_id: int,
        user_id: int,
        new_title: str
    ) -> bool:
        """Update conversation title.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control
            new_title: New title for the conversation
            
        Returns:
            True if updated successfully
        """
        try:
            async with await self.get_session() as db:
                # Join with Analysis to check ownership through analysis.user_id
                stmt = (
                    select(Conversation)
                    .join(Analysis, Conversation.analysis_id == Analysis.id)
                    .where(
                        and_(
                            Conversation.id == conversation_id,
                            Analysis.user_id == user_id
                        )
                    )
                )
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return False
                
                conversation.title = new_title
                await db.commit()
                
                logger.info(f"Updated conversation {conversation_id} title")
                return True
                
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return False
    
    async def delete_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """Delete a conversation and all its messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control
            
        Returns:
            True if deleted successfully
        """
        try:
            async with await self.get_session() as db:
                # Join with Analysis to check ownership through analysis.user_id
                stmt = (
                    select(Conversation)
                    .join(Analysis, Conversation.analysis_id == Analysis.id)
                    .where(
                        and_(
                            Conversation.id == conversation_id,
                            Analysis.user_id == user_id
                        )
                    )
                )
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return False
                
                # Delete conversation (messages will cascade)
                await db.delete(conversation)
                await db.commit()
                
                logger.info(f"Deleted conversation {conversation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False

    async def get_conversations_for_analysis(
        self,
        analysis_id: int,
        user_id: int
    ) -> List[Conversation]:
        """Get all conversations for an analysis.

        Args:
            analysis_id: Analysis ID
            user_id: User ID for access control

        Returns:
            List of conversations
        """
        try:
            async with await self.get_session() as db:
                # Join with Analysis to check ownership
                stmt = (
                    select(Conversation)
                    .join(Analysis, Conversation.analysis_id == Analysis.id)
                    .where(
                        and_(
                            Conversation.analysis_id == analysis_id,
                            Analysis.user_id == user_id
                        )
                    )
                    .order_by(desc(Conversation.created_at))
                )
                result = await db.execute(stmt)
                conversations = result.scalars().all()

                return list(conversations)

        except Exception as e:
            logger.error(f"Error getting conversations for analysis {analysis_id}: {e}")
            return []

    async def _generate_conversation_title(self, first_message: str) -> str:
        """Generate a conversation title from the first message using OpenAI.

        Args:
            first_message: The first message content

        Returns:
            Generated title (fallback to default if generation fails)
        """
        try:
            prompt = f"""Generate a short, descriptive title (2-4 words) for a palmistry conversation based on this question:

"{first_message}"

Examples:
- "What does my palm say about love?" → "Love & Relationships"
- "Will I be successful in business?" → "Business Success"
- "When will I get married?" → "Marriage Timing"
- "What's my career path?" → "Career Guidance"

Return only the title, no quotes or explanations."""

            title = await self.openai_service.generate_simple_completion(prompt, max_tokens=10)

            # Clean up the response
            title = title.strip().replace('"', '').replace("'", "")

            # Validate length
            if len(title) > 50:
                title = title[:47] + "..."

            return title or "General Questions"

        except Exception as e:
            logger.warning(f"Failed to generate conversation title: {e}")
            return "General Questions"

    async def _get_conversation_count_for_analysis(self, db: AsyncSession, analysis_id: int) -> int:
        """Get the number of conversations for an analysis.

        Args:
            db: Database session
            analysis_id: Analysis ID

        Returns:
            Number of conversations
        """
        try:
            stmt = select(Conversation).where(Conversation.analysis_id == analysis_id)
            result = await db.execute(stmt)
            conversations = result.scalars().all()
            return len(conversations)

        except Exception as e:
            logger.error(f"Error getting conversation count for analysis {analysis_id}: {e}")
            return 0