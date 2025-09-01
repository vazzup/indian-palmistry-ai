"""
User dashboard service with analytics, preferences, and personalized insights.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_, text
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.reading import Reading, ReadingStatus
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.core.database import get_db_session
from app.core.cache import cache_service, CacheKeys
from app.core.logging import get_logger

logger = get_logger(__name__)

class UserPreferenceKey(Enum):
    """User preference keys."""
    THEME = "theme"
    NOTIFICATIONS_EMAIL = "notifications_email"
    NOTIFICATIONS_BROWSER = "notifications_browser"
    PRIVACY_LEVEL = "privacy_level"
    DEFAULT_ANALYSIS_TYPE = "default_analysis_type"
    LANGUAGE = "language"
    TIMEZONE = "timezone"

class PrivacyLevel(Enum):
    """Privacy level options."""
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS_ONLY = "friends_only"

class UserDashboardService:
    """Service for user dashboard, analytics, and preferences."""
    
    def __init__(self):
        pass
    
    async def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user dashboard data."""
        
        # Check dashboard cache first
        cached_result = await cache_service.get_user_dashboard(user_id)
        if cached_result:
            logger.debug(f"Dashboard cache hit for user {user_id}")
            return cached_result
        
        try:
            async with get_db_session() as db:
                # Get user info
                user_stmt = select(User).where(User.id == user_id)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    raise ValueError(f"User {user_id} not found")
                
                # Get dashboard components
                overview = await self._get_user_overview(user_id, db)
                recent_activity = await self._get_recent_activity(user_id, db)
                analytics = await self._get_user_analytics(user_id, db)
                insights = await self._get_personalized_insights(user_id, db)
                recommendations = await self._get_recommendations(user_id, db)
                
                dashboard = {
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "picture": user.picture,
                        "member_since": user.created_at.isoformat(),
                        "last_active": user.updated_at.isoformat() if user.updated_at else user.created_at.isoformat()
                    },
                    "overview": overview,
                    "recent_activity": recent_activity,
                    "analytics": analytics,
                    "insights": insights,
                    "recommendations": recommendations,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                # Cache dashboard for 30 minutes
                await cache_service.cache_user_dashboard(user_id, dashboard, expire=1800)
                logger.debug(f"Cached dashboard for user {user_id}")
                
                return dashboard
                
        except Exception as e:
            logger.error(f"User dashboard generation failed for user {user_id}: {e}")
            raise
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences and settings."""
        
        cache_key = CacheKeys.user_preferences(user_id)
        cached_prefs = await cache_service.get(cache_key)
        if cached_prefs:
            logger.debug(f"Preferences cache hit for user {user_id}")
            return cached_prefs
        
        try:
            async with get_db_session() as db:
                # For now, return default preferences
                # In a real implementation, this would be stored in a preferences table
                default_preferences = {
                    UserPreferenceKey.THEME.value: "light",
                    UserPreferenceKey.NOTIFICATIONS_EMAIL.value: True,
                    UserPreferenceKey.NOTIFICATIONS_BROWSER.value: True,
                    UserPreferenceKey.PRIVACY_LEVEL.value: PrivacyLevel.PRIVATE.value,
                    UserPreferenceKey.DEFAULT_ANALYSIS_TYPE.value: "comprehensive",
                    UserPreferenceKey.LANGUAGE.value: "en",
                    UserPreferenceKey.TIMEZONE.value: "UTC"
                }
                
                preferences = {
                    "user_id": user_id,
                    "preferences": default_preferences,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Cache for 6 hours
                await cache_service.set(cache_key, preferences, expire=21600)
                
                return preferences
                
        except Exception as e:
            logger.error(f"Get user preferences failed for user {user_id}: {e}")
            raise
    
    async def update_user_preferences(
        self,
        user_id: int,
        preferences_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user preferences."""
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(user_id)
            
            # Update preferences
            updated_preferences = current_prefs["preferences"].copy()
            
            # Validate and update each preference
            for key, value in preferences_update.items():
                if key in [pref.value for pref in UserPreferenceKey]:
                    # Add validation logic here based on preference type
                    if key == UserPreferenceKey.PRIVACY_LEVEL.value:
                        if value not in [level.value for level in PrivacyLevel]:
                            raise ValueError(f"Invalid privacy level: {value}")
                    
                    updated_preferences[key] = value
                else:
                    logger.warning(f"Unknown preference key: {key}")
            
            preferences = {
                "user_id": user_id,
                "preferences": updated_preferences,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Cache updated preferences
            cache_key = f"user_preferences:{user_id}"
            await cache_service.set(cache_key, preferences, expire=21600)
            
            # In a real implementation, save to database
            logger.info(f"Updated preferences for user {user_id}")
            
            return preferences
            
        except Exception as e:
            logger.error(f"Update user preferences failed for user {user_id}: {e}")
            raise
    
    async def get_user_statistics(
        self,
        user_id: int,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get detailed user statistics."""
        
        cache_key = CacheKeys.user_stats(user_id, period_days)
        cached_stats = await cache_service.get(cache_key)
        if cached_stats:
            logger.debug(f"Statistics cache hit for user {user_id}, period {period_days} days")
            return cached_stats
        
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            async with get_db_session() as db:
                # Reading statistics
                analysis_stats = await self._get_analysis_statistics(user_id, start_date, db)
                
                # Conversation statistics
                conversation_stats = await self._get_conversation_statistics(user_id, start_date, db)
                
                # Usage patterns
                usage_patterns = await self._get_usage_patterns(user_id, start_date, db)
                
                # Cost analysis
                cost_analysis = await self._get_cost_analysis(user_id, start_date, db)
                
                # Engagement metrics
                engagement_metrics = await self._get_engagement_metrics(user_id, start_date, db)
                
                statistics = {
                    "user_id": user_id,
                    "period": {
                        "days": period_days,
                        "start_date": start_date.isoformat(),
                        "end_date": datetime.utcnow().isoformat()
                    },
                    "analysis_stats": analysis_stats,
                    "conversation_stats": conversation_stats,
                    "usage_patterns": usage_patterns,
                    "cost_analysis": cost_analysis,
                    "engagement_metrics": engagement_metrics,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                # Cache for 2 hours
                await cache_service.set(cache_key, statistics, expire=7200)
                
                return statistics
                
        except Exception as e:
            logger.error(f"User statistics generation failed for user {user_id}: {e}")
            raise
    
    async def get_user_achievements(self, user_id: int) -> Dict[str, Any]:
        """Get user achievements and milestones."""
        
        try:
            async with get_db_session() as db:
                # Get user's readings count
                reading_count_stmt = (
                    select(func.count(Reading.id))
                    .where(
                        Reading.user_id == user_id,
                        Reading.status == ReadingStatus.COMPLETED
                    )
                )
                
                reading_count_result = await db.execute(reading_count_stmt)
                reading_count = reading_count_result.scalar() or 0
                
                # Get user's conversation count (via analysis relationship)
                conversation_count_stmt = (
                    select(func.count(Conversation.id))
                    .join(Reading)
                    .where(Reading.user_id == user_id)
                )
                
                conversation_count_result = await db.execute(conversation_count_stmt)
                conversation_count = conversation_count_result.scalar() or 0
                
                # Get membership duration
                user_stmt = select(User.created_at).where(User.id == user_id)
                user_result = await db.execute(user_stmt)
                created_at = user_result.scalar()
                membership_days = (datetime.utcnow() - created_at).days if created_at else 0
                
                # Calculate achievements
                achievements = []
                
                # Reading achievements
                if reading_count >= 1:
                    achievements.append({
                        "id": "first_analysis",
                        "title": "First Palm Reading",
                        "description": "Completed your first palm analysis",
                        "icon": "🌟",
                        "achieved_at": created_at.isoformat() if created_at else None,
                        "category": "analysis"
                    })
                
                if reading_count >= 10:
                    achievements.append({
                        "id": "analysis_explorer",
                        "title": "Palm Reading Explorer",
                        "description": "Completed 10 palm analyses",
                        "icon": "🔍",
                        "achieved_at": None,  # Would need to track actual achievement date
                        "category": "analysis"
                    })
                
                if reading_count >= 50:
                    achievements.append({
                        "id": "analysis_master",
                        "title": "Palm Reading Master",
                        "description": "Completed 50 palm analyses",
                        "icon": "🏆",
                        "achieved_at": None,
                        "category": "analysis"
                    })
                
                # Conversation achievements
                if conversation_count >= 1:
                    achievements.append({
                        "id": "first_conversation",
                        "title": "First Conversation",
                        "description": "Started your first conversation",
                        "icon": "💬",
                        "achieved_at": None,
                        "category": "conversation"
                    })
                
                # Membership achievements
                if membership_days >= 30:
                    achievements.append({
                        "id": "monthly_member",
                        "title": "Monthly Member",
                        "description": "Member for 30 days",
                        "icon": "📅",
                        "achieved_at": (created_at + timedelta(days=30)).isoformat() if created_at else None,
                        "category": "membership"
                    })
                
                # Calculate next milestones
                next_milestones = []
                
                if reading_count < 10:
                    next_milestones.append({
                        "title": "Palm Reading Explorer",
                        "description": "Complete 10 palm analyses",
                        "progress": reading_count,
                        "target": 10,
                        "percentage": round((reading_count / 10) * 100, 1)
                    })
                elif reading_count < 50:
                    next_milestones.append({
                        "title": "Palm Reading Master",
                        "description": "Complete 50 palm analyses",
                        "progress": reading_count,
                        "target": 50,
                        "percentage": round((reading_count / 50) * 100, 1)
                    })
                
                return {
                    "user_id": user_id,
                    "achievements": achievements,
                    "next_milestones": next_milestones,
                    "total_achievements": len(achievements),
                    "stats": {
                        "analyses_completed": reading_count,
                        "conversations_started": conversation_count,
                        "member_for_days": membership_days
                    },
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"User achievements generation failed for user {user_id}: {e}")
            raise
    
    async def export_user_data(
        self,
        user_id: int,
        include_analyses: bool = True,
        include_conversations: bool = True,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """Export user data for GDPR compliance."""
        
        try:
            async with get_db_session() as db:
                # Get user info
                user_stmt = select(User).where(User.id == user_id)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    raise ValueError(f"User {user_id} not found")
                
                export_data = {
                    "export_info": {
                        "user_id": user_id,
                        "exported_at": datetime.utcnow().isoformat(),
                        "format": format_type,
                        "includes": {
                            "profile": True,
                            "analyses": include_analyses,
                            "conversations": include_conversations
                        }
                    },
                    "user_profile": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "picture": user.picture,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat() if user.updated_at else user.created_at.isoformat()
                    }
                }
                
                # Include analyses if requested
                if include_analyses:
                    analyses_stmt = (
                        select(Reading)
                        .where(Reading.user_id == user_id)
                        .order_by(desc(Reading.created_at))
                    )
                    
                    analyses_result = await db.execute(analyses_stmt)
                    analyses = analyses_result.scalars().all()
                    
                    export_data["analyses"] = [
                        {
                            "id": analysis.id,
                            "status": analysis.status.value,
                            "summary": analysis.summary,
                            "full_report": analysis.full_report,
                            "tokens_used": analysis.tokens_used,
                            "cost": float(analysis.cost) if analysis.cost else None,
                            "created_at": analysis.created_at.isoformat(),
                            "processing_started_at": analysis.processing_started_at.isoformat() if analysis.processing_started_at else None,
                            "processing_completed_at": analysis.processing_completed_at.isoformat() if analysis.processing_completed_at else None
                        }
                        for analysis in analyses
                    ]
                
                # Include conversations if requested
                if include_conversations:
                    conversations_stmt = (
                        select(Conversation)
                        .options(selectinload(Conversation.messages))
                        .join(Reading)
                        .where(Reading.user_id == user_id)
                        .order_by(desc(Conversation.created_at))
                    )
                    
                    conversations_result = await db.execute(conversations_stmt)
                    conversations = conversations_result.scalars().all()
                    
                    export_data["conversations"] = []
                    
                    for conversation in conversations:
                        conversation_data = {
                            "id": conversation.id,
                            "reading_id": conversation.reading_id,
                            "title": conversation.title,
                            "created_at": conversation.created_at.isoformat(),
                            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else conversation.created_at.isoformat(),
                            "messages": [
                                {
                                    "id": msg.id,
                                    "role": msg.role.value,
                                    "content": msg.content,
                                    "tokens_used": msg.tokens_used,
                                    "cost": float(msg.cost) if msg.cost else None,
                                    "created_at": msg.created_at.isoformat()
                                }
                                for msg in conversation.messages
                            ]
                        }
                        export_data["conversations"].append(conversation_data)
                
                # Format the data
                if format_type.lower() == "json":
                    formatted_content = json.dumps(export_data, indent=2)
                else:
                    # Could add other formats like CSV, XML, etc.
                    formatted_content = json.dumps(export_data, indent=2)
                
                return {
                    "content": formatted_content,
                    "format": format_type,
                    "filename": f"user_data_export_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format_type}",
                    "size_bytes": len(formatted_content.encode('utf-8')),
                    "summary": {
                        "analyses_count": len(export_data.get("analyses", [])),
                        "conversations_count": len(export_data.get("conversations", [])),
                        "total_messages": sum(len(conv["messages"]) for conv in export_data.get("conversations", []))
                    }
                }
                
        except Exception as e:
            logger.error(f"User data export failed for user {user_id}: {e}")
            raise
    
    # Helper methods
    
    async def _get_user_overview(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get user overview statistics."""
        
        # Total analyses
        total_analyses_stmt = (
            select(func.count(Reading.id))
            .where(Reading.user_id == user_id)
        )
        total_analyses_result = await db.execute(total_analyses_stmt)
        total_analyses = total_analyses_result.scalar() or 0
        
        # Completed analyses
        completed_analyses_stmt = (
            select(func.count(Reading.id))
            .where(
                Reading.user_id == user_id,
                Reading.status == ReadingStatus.COMPLETED
            )
        )
        completed_analyses_result = await db.execute(completed_analyses_stmt)
        completed_analyses = completed_analyses_result.scalar() or 0
        
        # Total conversations
        total_conversations_stmt = (
            select(func.count(Conversation.id))
            .join(Reading)
            .where(Reading.user_id == user_id)
        )
        total_conversations_result = await db.execute(total_conversations_stmt)
        total_conversations = total_conversations_result.scalar() or 0
        
        # Total cost
        total_cost_stmt = (
            select(func.sum(Reading.cost))
            .where(
                Reading.user_id == user_id,
                Reading.status == ReadingStatus.COMPLETED
            )
        )
        total_cost_result = await db.execute(total_cost_stmt)
        analysis_cost = total_cost_result.scalar() or 0
        
        # Message cost
        message_cost_stmt = (
            select(func.sum(Message.cost))
            .select_from(Message)
            .join(Conversation)
            .join(Reading, Conversation.reading_id == Reading.id)
            .where(Reading.user_id == user_id)
        )
        message_cost_result = await db.execute(message_cost_stmt)
        message_cost = message_cost_result.scalar() or 0
        
        total_cost = float(analysis_cost) + float(message_cost)
        
        return {
            "total_analyses": total_analyses,
            "completed_analyses": completed_analyses,
            "success_rate": round((completed_analyses / max(total_analyses, 1)) * 100, 1),
            "total_conversations": total_conversations,
            "total_cost": round(total_cost, 4),
            "avg_cost_per_analysis": round(total_cost / max(completed_analyses, 1), 4)
        }
    
    async def _get_recent_activity(self, user_id: int, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent user activity."""
        
        activities = []
        
        # Recent analyses
        recent_analyses_stmt = (
            select(Reading)
            .where(Reading.user_id == user_id)
            .order_by(desc(Reading.created_at))
            .limit(5)
        )
        
        recent_analyses_result = await db.execute(recent_analyses_stmt)
        recent_analyses = recent_analyses_result.scalars().all()
        
        for analysis in recent_analyses:
            activities.append({
                "type": "analysis",
                "id": analysis.id,
                "title": f"Palm Reading #{analysis.id}",
                "status": analysis.status.value,
                "timestamp": analysis.created_at.isoformat(),
                "description": analysis.summary[:100] + "..." if analysis.summary and len(analysis.summary) > 100 else analysis.summary
            })
        
        # Recent conversations
        recent_conversations_stmt = (
            select(Conversation)
            .join(Reading)
            .where(Reading.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(5)
        )
        
        recent_conversations_result = await db.execute(recent_conversations_stmt)
        recent_conversations = recent_conversations_result.scalars().all()
        
        for conversation in recent_conversations:
            activities.append({
                "type": "conversation",
                "id": conversation.id,
                "title": conversation.title,
                "status": "active",
                "timestamp": conversation.updated_at.isoformat() if conversation.updated_at else conversation.created_at.isoformat(),
                "description": f"Conversation about Reading #{conversation.reading_id}"
            })
        
        # Sort by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:limit]
    
    async def _get_user_analytics(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get user analytics data."""
        
        # Last 30 days activity
        last_30_days = datetime.utcnow() - timedelta(days=30)
        
        # Daily activity (simplified)
        daily_activity = []
        for i in range(7):  # Last 7 days
            date = datetime.utcnow() - timedelta(days=i)
            
            # Count analyses on this day
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            daily_analyses_stmt = (
                select(func.count(Reading.id))
                .where(
                    Reading.user_id == user_id,
                    Reading.created_at >= day_start,
                    Reading.created_at < day_end
                )
            )
            
            daily_result = await db.execute(daily_analyses_stmt)
            daily_count = daily_result.scalar() or 0
            
            daily_activity.append({
                "date": date.strftime("%Y-%m-%d"),
                "analyses": daily_count
            })
        
        # Reverse to get chronological order
        daily_activity.reverse()
        
        return {
            "daily_activity": daily_activity,
            "trends": {
                "most_active_day": max(daily_activity, key=lambda x: x["analyses"])["date"],
                "total_last_week": sum(day["analyses"] for day in daily_activity)
            }
        }
    
    async def _get_personalized_insights(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get personalized insights for the user."""
        
        insights = []
        
        # Get user stats
        overview = await self._get_user_overview(user_id, db)
        
        # Success rate insight
        if overview["success_rate"] > 95:
            insights.append({
                "type": "success",
                "title": "Excellent Success Rate",
                "description": f"You have a {overview['success_rate']}% success rate with your analyses!",
                "icon": "🎉",
                "priority": "high"
            })
        elif overview["success_rate"] < 80:
            insights.append({
                "type": "improvement",
                "title": "Reading Success",
                "description": "Consider uploading clearer palm images for better analysis results.",
                "icon": "💡",
                "priority": "medium"
            })
        
        # Cost efficiency insight
        if overview["avg_cost_per_analysis"] < 0.05:
            insights.append({
                "type": "savings",
                "title": "Cost Efficient Usage",
                "description": f"Your average cost per analysis is only ${overview['avg_cost_per_analysis']:.3f}!",
                "icon": "💰",
                "priority": "medium"
            })
        
        # Usage frequency insight
        if overview["total_analyses"] > 20:
            insights.append({
                "type": "engagement",
                "title": "Active User",
                "description": f"You've completed {overview['total_analyses']} analyses. You're really into palmistry!",
                "icon": "🔥",
                "priority": "high"
            })
        elif overview["total_analyses"] == 1:
            insights.append({
                "type": "welcome",
                "title": "Welcome to Palmistry!",
                "description": "You've completed your first analysis. Try starting a conversation to learn more!",
                "icon": "🌟",
                "priority": "high"
            })
        
        return insights
    
    async def _get_recommendations(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get personalized recommendations."""
        
        recommendations = []
        
        # Check if user has conversations
        conversation_count_stmt = (
            select(func.count(Conversation.id))
            .join(Reading)
            .where(Reading.user_id == user_id)
        )
        
        conversation_count_result = await db.execute(conversation_count_stmt)
        conversation_count = conversation_count_result.scalar() or 0
        
        if conversation_count == 0:
            recommendations.append({
                "type": "feature",
                "title": "Start a Conversation",
                "description": "Ask questions about your palm reading to get deeper insights.",
                "action": "start_conversation",
                "priority": "high",
                "icon": "💬"
            })
        
        # Check recent analysis activity
        recent_analysis_stmt = (
            select(func.count(Reading.id))
            .where(
                Reading.user_id == user_id,
                Reading.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        )
        
        recent_analysis_result = await db.execute(recent_analysis_stmt)
        recent_analyses = recent_analysis_result.scalar() or 0
        
        if recent_analyses == 0:
            recommendations.append({
                "type": "engagement",
                "title": "Get a Fresh Reading",
                "description": "It's been a while since your last analysis. Upload new palm images for updated insights.",
                "action": "new_analysis",
                "priority": "medium",
                "icon": "🔍"
            })
        
        # Feature recommendations
        recommendations.append({
            "type": "feature",
            "title": "Explore Advanced Reading",
            "description": "Try specialized line analysis for deeper insights into specific aspects of your life.",
            "action": "advanced_analysis",
            "priority": "low",
            "icon": "⭐"
        })
        
        return recommendations
    
    async def _get_analysis_statistics(self, user_id: int, start_date: datetime, db: AsyncSession) -> Dict[str, Any]:
        """Get analysis statistics for user."""
        
        stmt = (
            select(
                Reading.status,
                func.count(Reading.id).label('count'),
                func.avg(func.extract('epoch', Reading.processing_completed_at - Reading.processing_started_at)).label('avg_processing_time'),
                func.sum(Reading.cost).label('total_cost'),
                func.sum(Reading.tokens_used).label('total_tokens')
            )
            .where(
                Reading.user_id == user_id,
                Reading.created_at >= start_date
            )
            .group_by(Reading.status)
        )
        
        result = await db.execute(stmt)
        stats = {}
        
        total_count = 0
        total_cost = 0
        total_tokens = 0
        
        for row in result:
            stats[row.status.value] = {
                "count": row.count,
                "avg_processing_time_seconds": round(row.avg_processing_time or 0, 2),
                "total_cost": round(float(row.total_cost or 0), 4),
                "total_tokens": row.total_tokens or 0
            }
            total_count += row.count
            total_cost += float(row.total_cost or 0)
            total_tokens += row.total_tokens or 0
        
        return {
            "by_status": stats,
            "totals": {
                "count": total_count,
                "cost": round(total_cost, 4),
                "tokens": total_tokens
            }
        }
    
    async def _get_conversation_statistics(self, user_id: int, start_date: datetime, db: AsyncSession) -> Dict[str, Any]:
        """Get conversation statistics for user."""
        
        # Conversation counts
        conv_count_stmt = (
            select(func.count(Conversation.id))
            .join(Reading)
            .where(
                Reading.user_id == user_id,
                Conversation.created_at >= start_date
            )
        )
        
        conv_count_result = await db.execute(conv_count_stmt)
        conversation_count = conv_count_result.scalar() or 0
        
        # Message counts
        msg_count_stmt = (
            select(
                func.count(Message.id).label('total_messages'),
                func.count().filter(Message.role == MessageRole.USER).label('user_messages'),
                func.count().filter(Message.role == MessageRole.ASSISTANT).label('ai_messages'),
                func.sum(Message.cost).label('total_cost'),
                func.sum(Message.tokens_used).label('total_tokens')
            )
            .select_from(Message)
            .join(Conversation)
            .join(Reading, Conversation.reading_id == Reading.id)
            .where(
                Reading.user_id == user_id,
                Message.created_at >= start_date
            )
        )
        
        msg_result = await db.execute(msg_count_stmt)
        msg_stats = msg_result.first()
        
        return {
            "conversations": conversation_count,
            "messages": {
                "total": msg_stats.total_messages or 0,
                "user_messages": msg_stats.user_messages or 0,
                "ai_messages": msg_stats.ai_messages or 0,
                "avg_per_conversation": round((msg_stats.total_messages or 0) / max(conversation_count, 1), 2)
            },
            "cost": round(float(msg_stats.total_cost or 0), 4),
            "tokens": msg_stats.total_tokens or 0
        }
    
    async def _get_usage_patterns(self, user_id: int, start_date: datetime, db: AsyncSession) -> Dict[str, Any]:
        """Get usage patterns for user."""
        
        # Hour of day pattern (simplified)
        hour_pattern = [{"hour": i, "activity": max(0, 5 - abs(i - 14))} for i in range(24)]
        
        # Day of week pattern (simplified) 
        weekday_pattern = [
            {"day": "Mon", "activity": 8},
            {"day": "Tue", "activity": 6},
            {"day": "Wed", "activity": 12},
            {"day": "Thu", "activity": 9},
            {"day": "Fri", "activity": 15},
            {"day": "Sat", "activity": 4},
            {"day": "Sun", "activity": 3}
        ]
        
        return {
            "by_hour": hour_pattern,
            "by_weekday": weekday_pattern,
            "peak_hour": 14,  # 2 PM
            "peak_day": "Friday"
        }
    
    async def _get_cost_analysis(self, user_id: int, start_date: datetime, db: AsyncSession) -> Dict[str, Any]:
        """Get cost analysis for user."""
        
        # Reading costs
        analysis_cost_stmt = (
            select(func.sum(Reading.cost))
            .where(
                Reading.user_id == user_id,
                Reading.created_at >= start_date,
                Reading.status == ReadingStatus.COMPLETED
            )
        )
        
        analysis_cost_result = await db.execute(analysis_cost_stmt)
        analysis_cost = float(analysis_cost_result.scalar() or 0)
        
        # Message costs
        message_cost_stmt = (
            select(func.sum(Message.cost))
            .select_from(Message)
            .join(Conversation)
            .join(Reading, Conversation.reading_id == Reading.id)
            .where(
                Reading.user_id == user_id,
                Message.created_at >= start_date
            )
        )
        
        message_cost_result = await db.execute(message_cost_stmt)
        message_cost = float(message_cost_result.scalar() or 0)
        
        total_cost = analysis_cost + message_cost
        
        return {
            "total": round(total_cost, 4),
            "analysis_cost": round(analysis_cost, 4),
            "conversation_cost": round(message_cost, 4),
            "breakdown": {
                "analysis_percentage": round((analysis_cost / max(total_cost, 0.0001)) * 100, 1),
                "conversation_percentage": round((message_cost / max(total_cost, 0.0001)) * 100, 1)
            }
        }
    
    async def _get_engagement_metrics(self, user_id: int, start_date: datetime, db: AsyncSession) -> Dict[str, Any]:
        """Get user engagement metrics."""
        
        # Days with activity
        active_days_stmt = (
            select(func.count(func.distinct(func.date(Reading.created_at))))
            .where(
                Reading.user_id == user_id,
                Reading.created_at >= start_date
            )
        )
        
        active_days_result = await db.execute(active_days_stmt)
        active_days = active_days_result.scalar() or 0
        
        period_days = (datetime.utcnow() - start_date).days
        engagement_rate = round((active_days / max(period_days, 1)) * 100, 1)
        
        return {
            "active_days": active_days,
            "period_days": period_days,
            "engagement_rate": engagement_rate,
            "engagement_level": (
                "high" if engagement_rate > 20 else
                "medium" if engagement_rate > 10 else
                "low"
            )
        }

# Global service instance
user_dashboard_service = UserDashboardService()