"""
Enhanced API endpoints with advanced filtering, pagination, and monitoring features.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.analysis import Analysis
from app.models.conversation import Conversation
from app.models.message import Message

from app.services.advanced_palm_service import advanced_palm_service, PalmLineType
from app.services.enhanced_conversation_service import enhanced_conversation_service, ConversationTemplate
from app.services.monitoring_service import monitoring_service
from app.services.user_dashboard_service import user_dashboard_service

from app.utils.pagination import (
    PaginationParams, AdvancedQueryBuilder, pagination_service,
    CommonFilters, create_pagination_params, FilterParams, SortParams,
    PaginationService
)

from app.core.cache import cache_service
from app.core.logging import get_logger
from app.utils.cache_utils import debug_user_cache, force_cache_refresh, validate_cache_consistency

logger = get_logger(__name__)

router = APIRouter(prefix="/enhanced", tags=["enhanced"])

# Advanced Analysis Endpoints

@router.post("/analyses/{analysis_id}/advanced-analysis")
async def get_advanced_analysis(
    analysis_id: int,
    line_types: List[PalmLineType],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specialized analysis for specific palm lines."""
    
    try:
        result = await advanced_palm_service.analyze_specific_lines(
            analysis_id=analysis_id,
            line_types=line_types,
            user_id=current_user.id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result,
                "message": f"Advanced analysis completed for {len(line_types)} line types"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Advanced analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Advanced analysis failed")

@router.post("/analyses/compare")
async def compare_analyses(
    analysis_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare multiple analyses for temporal insights."""
    
    if len(analysis_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 analyses required for comparison")
    
    if len(analysis_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 analyses allowed for comparison")
    
    try:
        result = await advanced_palm_service.compare_analyses(
            analysis_ids=analysis_ids,
            user_id=current_user.id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result,
                "message": f"Comparison completed for {len(analysis_ids)} analyses"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis comparison failed: {e}")
        raise HTTPException(status_code=500, detail="Analysis comparison failed")

@router.get("/analyses/history")
async def get_analysis_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get user's analysis history with trends."""
    
    try:
        result = await advanced_palm_service.get_user_analysis_history(
            user_id=current_user.id,
            limit=limit
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result,
                "message": "Analysis history retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Analysis history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis history")

# Enhanced Conversation Endpoints

@router.get("/conversations/templates")
async def get_conversation_templates():
    """Get available conversation starter templates."""
    
    try:
        templates = await enhanced_conversation_service.get_conversation_templates()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": templates,
                "message": f"Retrieved {len(templates)} conversation templates"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversation templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation templates")

@router.post("/conversations/{conversation_id}/enhanced-talk")
async def enhanced_conversation_talk(
    conversation_id: int,
    message: str,
    context_window: Optional[int] = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send message with enhanced context memory."""
    
    try:
        result = await enhanced_conversation_service.create_contextual_response(
            conversation_id=conversation_id,
            user_message=message,
            user_id=current_user.id,
            context_window=context_window
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result,
                "message": "Enhanced response generated successfully"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Enhanced conversation failed: {e}")
        raise HTTPException(status_code=500, detail="Enhanced conversation failed")

@router.get("/conversations/search")
async def search_conversations(
    query: str = Query(..., min_length=3),
    analysis_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search conversations and messages."""
    
    try:
        result = await enhanced_conversation_service.search_conversations(
            user_id=current_user.id,
            query=query,
            analysis_id=analysis_id,
            limit=limit,
            offset=(page - 1) * limit
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result,
                "message": f"Found {len(result['results'])} matching conversations"
            }
        )
        
    except Exception as e:
        logger.error(f"Conversation search failed: {e}")
        raise HTTPException(status_code=500, detail="Conversation search failed")

@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: int,
    format_type: str = Query("json", regex="^(json|markdown|text)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export conversation data."""
    
    try:
        result = await enhanced_conversation_service.export_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            format_type=format_type
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result,
                "message": f"Conversation exported as {format_type}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Conversation export failed: {e}")
        raise HTTPException(status_code=500, detail="Conversation export failed")

@router.get("/conversations/analytics")
async def get_conversation_analytics(
    analysis_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation analytics for user."""
    
    try:
        result = await enhanced_conversation_service.get_conversation_analytics(
            user_id=current_user.id,
            analysis_id=analysis_id,
            days=days
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result,
                "message": f"Analytics retrieved for last {days} days"
            }
        )
        
    except Exception as e:
        logger.error(f"Conversation analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation analytics")

# Monitoring and Admin Endpoints

@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive monitoring dashboard (admin only)."""
    
    # In a real implementation, you'd check for admin role
    # For now, allow all authenticated users
    
    try:
        dashboard_data = await monitoring_service.get_queue_dashboard()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": dashboard_data,
                "message": "Monitoring dashboard retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Monitoring dashboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring dashboard")

@router.get("/monitoring/health")
async def get_system_health(
    include_details: bool = Query(True),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get system health status."""
    
    try:
        health_data = await monitoring_service.get_system_health(include_details=include_details)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": health_data,
                "message": f"System status: {health_data.get('overall_status', 'unknown')}"
            }
        )
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail="System health check failed")

@router.get("/monitoring/cost-analytics")
async def get_cost_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cost analytics for user."""
    
    try:
        analytics = await monitoring_service.get_cost_analytics(
            user_id=current_user.id,
            days=days
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": analytics,
                "message": f"Cost analytics for last {days} days"
            }
        )
        
    except Exception as e:
        logger.error(f"Cost analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cost analytics")

@router.get("/monitoring/usage-analytics")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage analytics for user."""
    
    try:
        analytics = await monitoring_service.get_usage_analytics(
            user_id=current_user.id,
            days=days
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": analytics,
                "message": f"Usage analytics for last {days} days"
            }
        )
        
    except Exception as e:
        logger.error(f"Usage analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage analytics")

# User Dashboard Endpoints

@router.get("/conversations")
async def get_user_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    analysis_id: Optional[int] = Query(None, description="Filter by analysis ID"),
    sort: Optional[str] = Query("created_at_desc", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for the current user with pagination and filtering."""
    
    try:
        from sqlalchemy.orm import selectinload
        from sqlalchemy import desc, asc, select
        
        # Build query - join with Analysis to filter by user
        query = select(Conversation).join(Analysis).where(
            Analysis.user_id == current_user.id
        ).options(selectinload(Conversation.analysis))
        
        # Apply analysis filter if specified
        if analysis_id:
            query = query.where(Conversation.analysis_id == analysis_id)
        
        # Apply sorting
        if sort == "created_at_desc":
            query = query.order_by(desc(Conversation.created_at))
        elif sort == "created_at_asc":
            query = query.order_by(asc(Conversation.created_at))
        elif sort == "updated_at_desc":
            query = query.order_by(desc(Conversation.updated_at))
        else:
            query = query.order_by(desc(Conversation.created_at))
        
        # Execute query to get total count - join with Analysis to filter by user
        from sqlalchemy import func
        total_result = await db.execute(
            select(func.count(Conversation.id)).join(Analysis).where(
                Analysis.user_id == current_user.id
            )
        )
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        # Format conversations
        conversations_data = []
        for conv in conversations:
            conversations_data.append({
                "id": conv.id,
                "title": conv.title,
                "analysis_id": conv.analysis_id,
                "analysis_title": conv.analysis.summary[:100] + "..." if conv.analysis and conv.analysis.summary else None,
                "message_count": conv.message_count or 0,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "is_active": conv.is_active if hasattr(conv, 'is_active') else True,
            })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "conversations": conversations_data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        logger.error(f"Get user conversations failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")

@router.get("/dashboard")
async def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive user dashboard."""
    
    try:
        dashboard_data = await user_dashboard_service.get_user_dashboard(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": dashboard_data,
                "message": "Dashboard retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"User dashboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard")

@router.get("/dashboard/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences and settings."""
    
    try:
        preferences = await user_dashboard_service.get_user_preferences(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": preferences,
                "message": "Preferences retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Get preferences failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve preferences")

@router.put("/dashboard/preferences")
async def update_user_preferences(
    preferences_update: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences."""
    
    try:
        updated_preferences = await user_dashboard_service.update_user_preferences(
            user_id=current_user.id,
            preferences_update=preferences_update
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": updated_preferences,
                "message": "Preferences updated successfully"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update preferences failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

@router.get("/dashboard/statistics")
async def get_user_statistics(
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user statistics."""
    
    try:
        statistics = await user_dashboard_service.get_user_statistics(
            user_id=current_user.id,
            period_days=period_days
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": statistics,
                "message": f"Statistics for last {period_days} days"
            }
        )
        
    except Exception as e:
        logger.error(f"User statistics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.get("/dashboard/achievements")
async def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user achievements and milestones."""
    
    try:
        achievements = await user_dashboard_service.get_user_achievements(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": achievements,
                "message": f"Retrieved {achievements['total_achievements']} achievements"
            }
        )
        
    except Exception as e:
        logger.error(f"User achievements failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve achievements")

@router.get("/dashboard/export-data")
async def export_user_data(
    include_analyses: bool = Query(True),
    include_conversations: bool = Query(True),
    format_type: str = Query("json", regex="^(json)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export user data for GDPR compliance."""
    
    try:
        export_result = await user_dashboard_service.export_user_data(
            user_id=current_user.id,
            include_analyses=include_analyses,
            include_conversations=include_conversations,
            format_type=format_type
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": export_result,
                "message": "User data exported successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"User data export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to export user data")

# Advanced Pagination Endpoints

@router.get("/analyses/advanced")
async def get_analyses_with_advanced_filtering(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    
    # Pagination parameters
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    
    # Common filter shortcuts
    status: Optional[str] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    min_cost: Optional[float] = Query(None),
    max_cost: Optional[float] = Query(None),
    
    # Sorting
    sort: Optional[str] = Query(None, description="Sort by field:direction (e.g., created_at:desc)")
):
    """Get analyses with advanced filtering and pagination."""
    
    try:
        # Create pagination parameters
        pagination = create_pagination_params(page=page, limit=limit)
        
        # Create query builder
        query_builder = AdvancedQueryBuilder(Analysis)
        
        # Add user filter (always required)
        query_builder.filters.append(Analysis.user_id == current_user.id)
        
        # Apply common filters
        if status:
            from app.models.analysis import AnalysisStatus
            try:
                status_enum = AnalysisStatus(status.upper())
                query_builder.filters.append(Analysis.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if created_after:
            query_builder.filters.append(Analysis.created_at >= created_after)
        
        if created_before:
            query_builder.filters.append(Analysis.created_at <= created_before)
        
        if min_cost is not None:
            query_builder.filters.append(Analysis.cost >= min_cost)
        
        if max_cost is not None:
            query_builder.filters.append(Analysis.cost <= max_cost)
        
        # Apply sorting
        if sort:
            sorts = PaginationService.parse_sorts_from_params({"sort": sort})
            for sort_param in sorts:
                if sort_param.field in CommonFilters.ANALYSIS_FILTERS['allowed_sort_fields']:
                    query_builder.add_sort(sort_param)
        else:
            # Default sort
            for default_sort in CommonFilters.ANALYSIS_FILTERS['default_sort']:
                query_builder.add_sort(default_sort)
        
        # Execute paginated query
        def serialize_analysis(analysis):
            return {
                "id": analysis.id,
                "status": analysis.status.value,
                "summary": analysis.summary,
                "cost": float(analysis.cost) if analysis.cost else None,
                "tokens_used": analysis.tokens_used,
                "created_at": analysis.created_at.isoformat(),
                "updated_at": analysis.updated_at.isoformat(),
                "processing_started_at": analysis.processing_started_at.isoformat() if analysis.processing_started_at else None,
                "processing_completed_at": analysis.processing_completed_at.isoformat() if analysis.processing_completed_at else None
            }
        
        result = await pagination_service.paginate(
            db=db,
            query_builder=query_builder,
            pagination=pagination,
            serialize_item=serialize_analysis
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": result.dict(),
                "message": f"Retrieved {len(result.items)} analyses"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced analyses filtering failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analyses")

# Cache Management Endpoints

@router.post("/cache/invalidate")
async def invalidate_cache_keys(
    keys: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invalidate specific cache keys (admin only)."""
    
    # In production, you'd check for admin role
    try:
        invalidated = []
        for key in keys:
            # Only allow invalidation of user's own cache keys or system keys
            if key.startswith(f"user:{current_user.id}") or key.startswith("system:"):
                success = await cache_service.delete(key)
                invalidated.append({"key": key, "success": success})
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {"invalidated": invalidated},
                "message": f"Processed {len(invalidated)} cache keys"
            }
        )
        
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(status_code=500, detail="Cache invalidation failed")

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cache statistics."""
    
    try:
        health_data = await cache_service.health_check()
        queue_stats = await cache_service.get_queue_stats()
        
        stats = {
            "redis_health": health_data,
            "queue_stats": queue_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": stats,
                "message": "Cache statistics retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Cache stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")

# Cache Debugging Endpoints

@router.get("/cache/debug")
async def debug_user_cache_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug cache entries for current user."""
    
    try:
        cache_debug = await debug_user_cache(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": cache_debug,
                "message": f"Cache debug completed for user {current_user.id}"
            }
        )
        
    except Exception as e:
        logger.error(f"Cache debug failed: {e}")
        raise HTTPException(status_code=500, detail="Cache debug failed")

@router.post("/cache/refresh")
async def force_cache_refresh_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Force refresh cache for current user."""
    
    try:
        refresh_result = await force_cache_refresh(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": refresh_result,
                "message": f"Cache refresh completed for user {current_user.id}"
            }
        )
        
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Cache refresh failed")

@router.get("/cache/validate-consistency")
async def validate_cache_consistency_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate cache consistency for current user."""
    
    try:
        consistency_result = await validate_cache_consistency(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": consistency_result,
                "message": f"Cache consistency validation completed for user {current_user.id}"
            }
        )
        
    except Exception as e:
        logger.error(f"Cache consistency validation failed: {e}")
        raise HTTPException(status_code=500, detail="Cache consistency validation failed")