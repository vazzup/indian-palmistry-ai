"""
Conversation service for managing palm reading conversations.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
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
        title: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation for an analysis.
        
        Args:
            analysis_id: ID of the analysis
            user_id: ID of the user creating the conversation
            title: Optional title for the conversation
            
        Returns:
            Created Conversation instance
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
                
                # Generate default title if not provided
                if not title:
                    title = f"Conversation about Palm Reading #{analysis_id}"
                
                conversation = Conversation(
                    analysis_id=analysis_id,
                    user_id=user_id,
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
    
    async def get_conversation_by_id(
        self,
        conversation_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """Get conversation by ID with user access check.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control
            
        Returns:
            Conversation instance if found and accessible
        """
        try:
            async with await self.get_session() as db:
                stmt = select(Conversation).where(
                    and_(Conversation.id == conversation_id, Conversation.user_id == user_id)
                )
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                return conversation
                
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    async def get_analysis_conversations(
        self,
        analysis_id: int,
        user_id: int,
        page: int = 1,
        per_page: int = 5
    ) -> tuple[List[Conversation], int]:
        """Get conversations for an analysis with pagination.
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID for access control
            page: Page number (1-based)
            per_page: Number of conversations per page
            
        Returns:
            Tuple of (conversations_list, total_count)
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
                    return [], 0
                
                # Get total count
                count_stmt = select(Conversation).where(Conversation.analysis_id == analysis_id)
                count_result = await db.execute(count_stmt)
                total = len(count_result.fetchall())
                
                # Get paginated results
                offset = (page - 1) * per_page
                stmt = (
                    select(Conversation)
                    .where(Conversation.analysis_id == analysis_id)
                    .order_by(desc(Conversation.created_at))
                    .limit(per_page)
                    .offset(offset)
                )
                
                result = await db.execute(stmt)
                conversations = result.scalars().all()
                
                return list(conversations), total
                
        except Exception as e:
            logger.error(f"Error getting conversations for analysis {analysis_id}: {e}")
            return [], 0
    
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
                    content=user_message
                )
                db.add(user_msg)
                await db.commit()
                await db.refresh(user_msg)
                
                # Generate AI response
                ai_response_data = await self.openai_service.generate_conversation_response(
                    analysis_summary=analysis.summary or "",
                    analysis_full_report=analysis.full_report or "",
                    conversation_history=conversation_history,
                    user_question=user_message
                )
                
                # Add AI response to database
                ai_msg = Message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=ai_response_data["response"],
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
                stmt = select(Conversation).where(
                    and_(Conversation.id == conversation_id, Conversation.user_id == user_id)
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
                stmt = select(Conversation).where(
                    and_(Conversation.id == conversation_id, Conversation.user_id == user_id)
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