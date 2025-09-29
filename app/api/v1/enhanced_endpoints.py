"""
Enhanced API endpoints - Dashboard and Cache utilities.
"""
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.analysis import Analysis
from app.models.conversation import Conversation
from app.models.message import Message

from app.core.cache import cache_service
from app.core.logging import get_logger
from app.utils.cache_utils import debug_user_cache, force_cache_refresh, validate_cache_consistency

logger = get_logger(__name__)

router = APIRouter(prefix="/enhanced", tags=["enhanced"])

# Dashboard Endpoints

@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user dashboard data."""

    try:
        # Get user's analyses count
        analyses_count = await db.scalar(
            select(func.count(Analysis.id)).where(Analysis.user_id == current_user.id)
        )

        # Get user's conversations count
        conversations_count = await db.scalar(
            select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
        )

        # Get recent analysis
        recent_analysis = await db.scalar(
            select(Analysis)
            .where(Analysis.user_id == current_user.id)
            .order_by(Analysis.created_at.desc())
            .limit(1)
        )

        dashboard_data = {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            },
            "statistics": {
                "total_analyses": analyses_count or 0,
                "total_conversations": conversations_count or 0,
            },
            "recent_analysis": {
                "id": recent_analysis.id,
                "status": recent_analysis.status,
                "created_at": recent_analysis.created_at.isoformat(),
            } if recent_analysis else None,
        }

        return dashboard_data

    except Exception as e:
        logger.error(f"Dashboard fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get("/dashboard/statistics")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user statistics for dashboard."""

    try:
        # Get analyses count by status
        analyses_stats = {}
        for status_val in ['pending', 'processing', 'completed', 'failed']:
            count = await db.scalar(
                select(func.count(Analysis.id))
                .where(Analysis.user_id == current_user.id)
                .where(Analysis.status == status_val)
            )
            analyses_stats[status_val] = count or 0

        # Get total messages count
        total_messages = await db.scalar(
            select(func.count(Message.id))
            .join(Conversation)
            .where(Conversation.user_id == current_user.id)
        )

        return {
            "analyses_by_status": analyses_stats,
            "total_messages": total_messages or 0,
            "account_age_days": (datetime.utcnow() - current_user.created_at).days if current_user.created_at else 0,
        }

    except Exception as e:
        logger.error(f"Statistics fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )


# Cache Management Endpoints

@router.get("/cache/debug")
async def debug_cache(
    current_user: User = Depends(get_current_user)
):
    """Debug cache state for current user."""
    try:
        debug_info = await debug_user_cache(current_user.id)
        return debug_info
    except Exception as e:
        logger.error(f"Cache debug failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to debug cache"
        )


@router.post("/cache/refresh")
async def refresh_cache(
    pattern: str = Query(None, description="Cache pattern to refresh"),
    current_user: User = Depends(get_current_user)
):
    """Refresh cache for current user or specific pattern."""
    try:
        result = await force_cache_refresh(current_user.id, pattern)
        return {
            "message": "Cache refresh completed",
            "pattern": pattern,
            "result": result
        }
    except Exception as e:
        logger.error(f"Cache refresh failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh cache"
        )


@router.get("/cache/validate-consistency")
async def validate_cache_consistency_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Validate cache consistency for current user."""
    try:
        result = await validate_cache_consistency(current_user.id)
        return result
    except Exception as e:
        logger.error(f"Cache validation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate cache consistency"
        )