"""
Enhanced conversation service with context memory, templates, and advanced features.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.analysis import Analysis
from app.services.openai_service import OpenAIService
from app.core.database import get_db_session
from app.core.cache import cache_service
from app.core.logging import get_logger

logger = get_logger(__name__)

class ConversationTemplate(Enum):
    """Pre-defined conversation templates."""
    LIFE_INSIGHTS = "life_insights"
    RELATIONSHIP_GUIDANCE = "relationship_guidance"
    CAREER_GUIDANCE = "career_guidance"
    HEALTH_WELLNESS = "health_wellness"
    SPIRITUAL_GROWTH = "spiritual_growth"
    FINANCIAL_GUIDANCE = "financial_guidance"

class EnhancedConversationService:
    """Enhanced conversation service with advanced features."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.context_window_size = 10  # Number of messages to include in context
    
    async def create_contextual_response(
        self,
        conversation_id: int,
        user_message: str,
        user_id: int,
        context_window: int = None
    ) -> Dict[str, Any]:
        """Generate AI response with conversation context memory."""
        
        try:
            # Use custom context window or default
            window_size = context_window or self.context_window_size
            
            # Get conversation with context
            conversation_data = await self._get_conversation_with_context(
                conversation_id, user_id, window_size
            )
            
            if not conversation_data:
                raise ValueError(f"Conversation {conversation_id} not found or access denied")
            
            # Check if we have cached context
            context_key = f"conversation_context:{conversation_id}"
            cached_context = await cache_service.get_conversation_context(conversation_id)
            
            # Build enhanced context
            if cached_context:
                # Use cached context and add new message
                context_messages = cached_context
            else:
                # Build context from recent messages
                context_messages = await self._build_context_messages(conversation_data)
            
            # Add current user message
            context_messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Generate enhanced prompt with memory
            enhanced_prompt = await self._build_enhanced_prompt(
                conversation_data, context_messages, user_message
            )
            
            # Generate AI response
            response_data = await self.openai_service.generate_response(enhanced_prompt)
            
            # Add AI response to context
            context_messages.append({
                "role": "assistant", 
                "content": response_data["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Cache updated context (keep last 15 messages)
            await cache_service.cache_conversation_context(
                conversation_id, 
                context_messages[-15:],  # Keep recent messages
                expire=1800  # 30 minutes
            )
            
            # Save messages to database
            await self._save_conversation_messages(
                conversation_id, user_message, response_data["content"], 
                response_data["tokens_used"], response_data["cost"]
            )
            
            return {
                "response": response_data["content"],
                "context_used": len(context_messages) - 1,  # Exclude current response
                "tokens_used": response_data["tokens_used"],
                "cost": response_data["cost"],
                "confidence": 0.85,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced conversation response failed: {e}")
            raise
    
    async def get_conversation_templates(self) -> List[Dict[str, Any]]:
        """Get available conversation starter templates."""
        
        templates = [
            {
                "id": ConversationTemplate.LIFE_INSIGHTS.value,
                "title": "Life Path Insights",
                "description": "Explore your life journey, destiny, and future possibilities",
                "icon": "🌟",
                "prompt": "Based on my palm reading, can you tell me more about my life path and what the future might hold for me?",
                "category": "General",
                "popularity": 95
            },
            {
                "id": ConversationTemplate.RELATIONSHIP_GUIDANCE.value,
                "title": "Love & Relationships",
                "description": "Understanding love life, relationships, and compatibility",
                "icon": "💕",
                "prompt": "What can my palm reveal about my love life, relationships, and romantic compatibility?",
                "category": "Relationships",
                "popularity": 88
            },
            {
                "id": ConversationTemplate.CAREER_GUIDANCE.value,
                "title": "Career & Success",
                "description": "Professional development, career path, and success indicators",
                "icon": "🚀",
                "prompt": "What insights does my palm provide about my career potential, professional strengths, and path to success?",
                "category": "Career",
                "popularity": 82
            },
            {
                "id": ConversationTemplate.HEALTH_WELLNESS.value,
                "title": "Health & Vitality",
                "description": "Health patterns, vitality, and wellness guidance",
                "icon": "🌿",
                "prompt": "What can you tell me about my health patterns and vitality based on my palm reading?",
                "category": "Health",
                "popularity": 75
            },
            {
                "id": ConversationTemplate.SPIRITUAL_GROWTH.value,
                "title": "Spiritual Journey",
                "description": "Spiritual development, intuition, and inner wisdom",
                "icon": "🧘",
                "prompt": "What spiritual insights and guidance for personal growth can you share based on my palm analysis?",
                "category": "Spirituality",
                "popularity": 68
            },
            {
                "id": ConversationTemplate.FINANCIAL_GUIDANCE.value,
                "title": "Wealth & Prosperity",
                "description": "Financial potential, money patterns, and prosperity indicators",
                "icon": "💰",
                "prompt": "What does my palm suggest about my financial potential and opportunities for wealth creation?",
                "category": "Finance", 
                "popularity": 71
            }
        ]
        
        return sorted(templates, key=lambda x: x["popularity"], reverse=True)
    
    async def search_conversations(
        self,
        user_id: int,
        query: str,
        analysis_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search conversations and messages by content."""
        
        cache_key = f"conversation_search:{user_id}:{hash(query)}:{analysis_id}:{limit}:{offset}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async with get_db_session() as db:
                # Build search query
                search_conditions = []
                
                # User ownership
                search_conditions.append(Conversation.user_id == user_id)
                
                # Analysis filter
                if analysis_id:
                    search_conditions.append(Conversation.analysis_id == analysis_id)
                
                # Search in conversation titles and message content
                query_lower = query.lower()
                message_search = (
                    select(Message.conversation_id)
                    .where(func.lower(Message.content).contains(query_lower))
                    .distinct()
                )
                
                title_search = func.lower(Conversation.title).contains(query_lower)
                
                # Combined search conditions
                search_conditions.append(
                    or_(
                        title_search,
                        Conversation.id.in_(message_search)
                    )
                )
                
                # Get conversations
                stmt = (
                    select(Conversation)
                    .options(selectinload(Conversation.messages))
                    .where(and_(*search_conditions))
                    .order_by(desc(Conversation.updated_at))
                    .limit(limit)
                    .offset(offset)
                )
                
                result = await db.execute(stmt)
                conversations = result.scalars().all()
                
                # Get total count
                count_stmt = (
                    select(func.count(Conversation.id))
                    .where(and_(*search_conditions))
                )
                count_result = await db.execute(count_stmt)
                total_count = count_result.scalar()
                
                # Format results with highlights
                search_results = []
                for conv in conversations:
                    # Find matching messages
                    matching_messages = [
                        {
                            "id": msg.id,
                            "role": msg.role.value,
                            "content": self._highlight_search_term(msg.content, query),
                            "created_at": msg.created_at.isoformat()
                        }
                        for msg in conv.messages
                        if query_lower in msg.content.lower()
                    ]
                    
                    search_results.append({
                        "conversation": {
                            "id": conv.id,
                            "title": self._highlight_search_term(conv.title, query),
                            "analysis_id": conv.analysis_id,
                            "created_at": conv.created_at.isoformat(),
                            "updated_at": conv.updated_at.isoformat()
                        },
                        "matching_messages": matching_messages,
                        "relevance_score": self._calculate_relevance_score(conv, query)
                    })
                
                # Sort by relevance
                search_results.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                result = {
                    "results": search_results,
                    "pagination": {
                        "total": total_count,
                        "limit": limit,
                        "offset": offset,
                        "has_more": total_count > (offset + limit)
                    },
                    "query": query,
                    "search_timestamp": datetime.utcnow().isoformat()
                }
                
                # Cache for 15 minutes
                await cache_service.set(cache_key, result, expire=900)
                
                return result
                
        except Exception as e:
            logger.error(f"Conversation search failed: {e}")
            raise
    
    async def export_conversation(
        self,
        conversation_id: int,
        user_id: int,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """Export conversation data in various formats."""
        
        try:
            async with get_db_session() as db:
                # Get conversation with messages
                stmt = (
                    select(Conversation)
                    .options(
                        selectinload(Conversation.messages),
                        selectinload(Conversation.analysis)
                    )
                    .where(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user_id
                    )
                )
                
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    raise ValueError("Conversation not found or access denied")
                
                # Prepare export data
                export_data = {
                    "conversation_id": conversation.id,
                    "title": conversation.title,
                    "analysis_id": conversation.analysis_id,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "message_count": len(conversation.messages),
                    "analysis_summary": conversation.analysis.summary if conversation.analysis else None,
                    "messages": []
                }
                
                # Add messages
                for msg in conversation.messages:
                    export_data["messages"].append({
                        "id": msg.id,
                        "role": msg.role.value,
                        "content": msg.content,
                        "tokens_used": msg.tokens_used,
                        "cost": float(msg.cost) if msg.cost else None,
                        "created_at": msg.created_at.isoformat()
                    })
                
                # Format based on requested type
                if format_type.lower() == "markdown":
                    formatted_content = self._format_as_markdown(export_data)
                elif format_type.lower() == "text":
                    formatted_content = self._format_as_text(export_data)
                else:  # Default to JSON
                    formatted_content = json.dumps(export_data, indent=2)
                
                return {
                    "content": formatted_content,
                    "format": format_type,
                    "filename": f"conversation_{conversation_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format_type}",
                    "size_bytes": len(formatted_content.encode('utf-8')),
                    "exported_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Conversation export failed: {e}")
            raise
    
    async def get_conversation_analytics(
        self,
        user_id: int,
        analysis_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get conversation analytics for user."""
        
        cache_key = f"conversation_analytics:{user_id}:{analysis_id}:{days}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async with get_db_session() as db:
                # Date range
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Base conditions
                conditions = [
                    Conversation.user_id == user_id,
                    Conversation.created_at >= start_date
                ]
                
                if analysis_id:
                    conditions.append(Conversation.analysis_id == analysis_id)
                
                # Get conversation stats
                conv_stmt = (
                    select(
                        func.count(Conversation.id).label('total_conversations'),
                        func.avg(func.extract('epoch', Conversation.updated_at - Conversation.created_at)).label('avg_duration_seconds'),
                        func.max(Conversation.updated_at).label('last_activity')
                    )
                    .where(and_(*conditions))
                )
                
                conv_result = await db.execute(conv_stmt)
                conv_stats = conv_result.first()
                
                # Get message stats
                msg_stmt = (
                    select(
                        func.count(Message.id).label('total_messages'),
                        func.sum(Message.tokens_used).label('total_tokens'),
                        func.sum(Message.cost).label('total_cost'),
                        func.count().filter(Message.role == MessageRole.USER).label('user_messages'),
                        func.count().filter(Message.role == MessageRole.ASSISTANT).label('ai_messages')
                    )
                    .select_from(Message)
                    .join(Conversation)
                    .where(and_(*conditions))
                )
                
                msg_result = await db.execute(msg_stmt)
                msg_stats = msg_result.first()
                
                # Get popular topics (simplified)
                topics = await self._analyze_conversation_topics(user_id, analysis_id, days)
                
                analytics = {
                    "period": {
                        "days": days,
                        "start_date": start_date.isoformat(),
                        "end_date": datetime.utcnow().isoformat()
                    },
                    "conversations": {
                        "total": conv_stats.total_conversations or 0,
                        "average_duration_minutes": round((conv_stats.avg_duration_seconds or 0) / 60, 2),
                        "last_activity": conv_stats.last_activity.isoformat() if conv_stats.last_activity else None
                    },
                    "messages": {
                        "total": msg_stats.total_messages or 0,
                        "user_messages": msg_stats.user_messages or 0,
                        "ai_messages": msg_stats.ai_messages or 0,
                        "avg_per_conversation": round((msg_stats.total_messages or 0) / max(conv_stats.total_conversations or 1, 1), 2)
                    },
                    "usage": {
                        "total_tokens": msg_stats.total_tokens or 0,
                        "total_cost": round(float(msg_stats.total_cost or 0), 4),
                        "avg_cost_per_message": round(float(msg_stats.total_cost or 0) / max(msg_stats.total_messages or 1, 1), 4)
                    },
                    "topics": topics,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                # Cache for 1 hour
                await cache_service.set(cache_key, analytics, expire=3600)
                
                return analytics
                
        except Exception as e:
            logger.error(f"Conversation analytics failed: {e}")
            raise
    
    # Helper methods
    
    async def _get_conversation_with_context(
        self,
        conversation_id: int,
        user_id: int,
        context_window: int
    ) -> Optional[Dict[str, Any]]:
        """Get conversation with context messages."""
        
        async with get_db_session() as db:
            # Get conversation
            conv_stmt = (
                select(Conversation)
                .options(selectinload(Conversation.analysis))
                .where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            )
            
            conv_result = await db.execute(conv_stmt)
            conversation = conv_result.scalar_one_or_none()
            
            if not conversation:
                return None
            
            # Get recent messages for context
            msg_stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(desc(Message.created_at))
                .limit(context_window)
            )
            
            msg_result = await db.execute(msg_stmt)
            messages = list(reversed(msg_result.scalars().all()))  # Chronological order
            
            return {
                "conversation": conversation,
                "messages": messages,
                "analysis": conversation.analysis
            }
    
    async def _build_context_messages(self, conversation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build context messages from conversation data."""
        
        context_messages = []
        
        # Add analysis context
        if conversation_data["analysis"]:
            analysis = conversation_data["analysis"]
            context_messages.append({
                "role": "system",
                "content": f"Original Palm Analysis - Summary: {analysis.summary}\nFull Report: {analysis.full_report or 'Not available'}",
                "timestamp": analysis.created_at.isoformat()
            })
        
        # Add recent messages
        for msg in conversation_data["messages"]:
            context_messages.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            })
        
        return context_messages
    
    async def _build_enhanced_prompt(
        self,
        conversation_data: Dict[str, Any],
        context_messages: List[Dict[str, Any]],
        current_message: str
    ) -> str:
        """Build enhanced prompt with context and memory."""
        
        # Get analysis context
        analysis = conversation_data["analysis"]
        conversation = conversation_data["conversation"]
        
        # Build context summary
        context_summary = "CONVERSATION CONTEXT:\n"
        context_summary += f"Conversation Title: {conversation.title}\n"
        context_summary += f"Analysis Date: {analysis.created_at.strftime('%Y-%m-%d') if analysis else 'Unknown'}\n\n"
        
        if analysis:
            context_summary += f"ORIGINAL PALM ANALYSIS:\nSummary: {analysis.summary}\n"
            if analysis.full_report:
                context_summary += f"Full Report: {analysis.full_report[:500]}{'...' if len(analysis.full_report) > 500 else ''}\n\n"
        
        # Add conversation history
        if len(context_messages) > 1:  # Exclude current system message
            context_summary += "RECENT CONVERSATION:\n"
            for msg in context_messages[-8:]:  # Last 8 messages for context
                if msg["role"] != "system":
                    role_label = "User" if msg["role"] == "user" else "AI Assistant"
                    context_summary += f"{role_label}: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n"
            context_summary += "\n"
        
        # Final prompt
        enhanced_prompt = f"""
{context_summary}

CURRENT USER QUESTION: {current_message}

Please provide a helpful, contextual response based on:
1. The original palm analysis provided above
2. The conversation history and context
3. Traditional Indian palmistry knowledge
4. The user's current specific question

Keep your response focused, insightful, and grounded in the palm reading analysis. Maintain continuity with the conversation flow.
"""
        
        return enhanced_prompt
    
    async def _save_conversation_messages(
        self,
        conversation_id: int,
        user_message: str,
        ai_response: str,
        tokens_used: int,
        cost: float
    ):
        """Save user and AI messages to database."""
        
        async with get_db_session() as db:
            # Save user message
            user_msg = Message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=user_message,
                tokens_used=0,  # User messages don't consume tokens
                cost=0.0
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=ai_response,
                tokens_used=tokens_used,
                cost=cost
            )
            db.add(ai_msg)
            
            # Update conversation timestamp
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.updated_at = datetime.utcnow()
            
            await db.commit()
    
    def _highlight_search_term(self, text: str, search_term: str) -> str:
        """Highlight search term in text (simple implementation)."""
        if not search_term:
            return text
        
        # Simple case-insensitive highlighting
        import re
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        return pattern.sub(f"**{search_term}**", text)
    
    def _calculate_relevance_score(self, conversation: Conversation, query: str) -> float:
        """Calculate relevance score for search results."""
        score = 0.0
        query_lower = query.lower()
        
        # Title relevance (higher weight)
        if query_lower in conversation.title.lower():
            score += 10.0
        
        # Message content relevance
        for msg in conversation.messages:
            if query_lower in msg.content.lower():
                score += 1.0
        
        # Recency bonus (more recent conversations rank higher)
        days_old = (datetime.utcnow() - conversation.updated_at).days
        recency_bonus = max(0, 5 - (days_old * 0.1))
        score += recency_bonus
        
        return score
    
    def _format_as_markdown(self, export_data: Dict[str, Any]) -> str:
        """Format conversation as Markdown."""
        
        content = f"# {export_data['title']}\n\n"
        content += f"**Created:** {export_data['created_at']}\n"
        content += f"**Updated:** {export_data['updated_at']}\n"
        content += f"**Messages:** {export_data['message_count']}\n\n"
        
        if export_data['analysis_summary']:
            content += f"## Original Analysis Summary\n\n{export_data['analysis_summary']}\n\n"
        
        content += "## Conversation\n\n"
        
        for msg in export_data['messages']:
            role_label = "**You:**" if msg['role'] == 'user' else "**AI Assistant:**"
            content += f"{role_label} {msg['content']}\n\n"
            content += f"*{msg['created_at']}*\n\n---\n\n"
        
        return content
    
    def _format_as_text(self, export_data: Dict[str, Any]) -> str:
        """Format conversation as plain text."""
        
        content = f"{export_data['title']}\n"
        content += "=" * len(export_data['title']) + "\n\n"
        content += f"Created: {export_data['created_at']}\n"
        content += f"Updated: {export_data['updated_at']}\n"
        content += f"Messages: {export_data['message_count']}\n\n"
        
        if export_data['analysis_summary']:
            content += f"Original Analysis Summary:\n{export_data['analysis_summary']}\n\n"
        
        content += "Conversation:\n\n"
        
        for msg in export_data['messages']:
            role_label = "You:" if msg['role'] == 'user' else "AI Assistant:"
            content += f"{role_label} {msg['content']}\n"
            content += f"({msg['created_at']})\n\n"
        
        return content
    
    async def _analyze_conversation_topics(
        self,
        user_id: int,
        analysis_id: Optional[int],
        days: int
    ) -> List[Dict[str, Any]]:
        """Analyze conversation topics (simplified implementation)."""
        
        # In a real implementation, this could use NLP to extract topics
        # For now, return common palmistry topics
        common_topics = [
            {"topic": "Life Path", "frequency": 15, "relevance": 0.9},
            {"topic": "Relationships", "frequency": 12, "relevance": 0.85},
            {"topic": "Career", "frequency": 10, "relevance": 0.8},
            {"topic": "Health", "frequency": 8, "relevance": 0.75},
            {"topic": "Finances", "frequency": 6, "relevance": 0.7}
        ]
        
        return common_topics

# Global service instance
enhanced_conversation_service = EnhancedConversationService()