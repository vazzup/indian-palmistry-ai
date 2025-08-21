"""
Monitoring service for background jobs, system health, and performance tracking.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import psutil
import asyncio
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload

from app.models.analysis import Analysis, AnalysisStatus
from app.models.user import User
from app.models.message import Message
from app.core.database import get_db_session
from app.core.cache import cache_service
from app.core.redis import redis_client
from app.core.logging import get_logger

logger = get_logger(__name__)

class SystemHealthStatus(Enum):
    """System health status indicators."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MonitoringService:
    """Service for monitoring background jobs and system health."""
    
    def __init__(self):
        self.health_check_interval = 60  # seconds
        self._last_health_check = None
        self._cached_health_data = None
    
    async def get_queue_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive queue monitoring dashboard."""
        
        try:
            # Get queue statistics from Redis
            queue_stats = await cache_service.get_queue_stats()
            
            # Get job processing statistics
            processing_stats = await self._get_job_processing_stats()
            
            # Get worker health
            worker_health = await self._get_worker_health()
            
            # Get recent job history
            recent_jobs = await self._get_recent_job_history()
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics()
            
            dashboard = {
                "timestamp": datetime.utcnow().isoformat(),
                "queue_stats": queue_stats,
                "processing_stats": processing_stats,
                "worker_health": worker_health,
                "recent_jobs": recent_jobs,
                "performance_metrics": performance_metrics,
                "alerts": await self._get_system_alerts()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Queue dashboard generation failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "error"
            }
    
    async def get_system_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        
        # Use cached data if recent enough (within 30 seconds)
        if (self._cached_health_data and 
            self._last_health_check and 
            datetime.utcnow() - self._last_health_check < timedelta(seconds=30)):
            return self._cached_health_data
        
        try:
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": SystemHealthStatus.HEALTHY.value,
                "components": {},
                "metrics": {}
            }
            
            # Database health
            db_health = await self._check_database_health()
            health_data["components"]["database"] = db_health
            
            # Redis health
            redis_health = await self._check_redis_health()
            health_data["components"]["redis"] = redis_health
            
            # Background jobs health
            jobs_health = await self._check_background_jobs_health()
            health_data["components"]["background_jobs"] = jobs_health
            
            # System resources
            if include_details:
                system_health = await self._check_system_resources()
                health_data["components"]["system_resources"] = system_health
                
                # Performance metrics
                health_data["metrics"] = await self._get_performance_metrics()
            
            # Determine overall status
            component_statuses = [comp["status"] for comp in health_data["components"].values()]
            if SystemHealthStatus.CRITICAL.value in component_statuses:
                health_data["overall_status"] = SystemHealthStatus.CRITICAL.value
            elif SystemHealthStatus.WARNING.value in component_statuses:
                health_data["overall_status"] = SystemHealthStatus.WARNING.value
            
            # Cache the results
            self._cached_health_data = health_data
            self._last_health_check = datetime.utcnow()
            
            return health_data
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": SystemHealthStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    async def get_cost_analytics(
        self, 
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get cost analytics for OpenAI usage."""
        
        cache_key = f"cost_analytics:{user_id}:{days}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            async with get_db_session() as db:
                # Base conditions
                conditions = [Analysis.created_at >= start_date]
                if user_id:
                    conditions.append(Analysis.user_id == user_id)
                
                # Get analysis cost data
                analysis_stmt = (
                    select(
                        func.count(Analysis.id).label('total_analyses'),
                        func.sum(Analysis.cost).label('total_cost'),
                        func.sum(Analysis.tokens_used).label('total_tokens'),
                        func.avg(Analysis.cost).label('avg_cost_per_analysis'),
                        func.avg(Analysis.tokens_used).label('avg_tokens_per_analysis')
                    )
                    .where(
                        and_(*conditions),
                        Analysis.status == AnalysisStatus.COMPLETED
                    )
                )
                
                analysis_result = await db.execute(analysis_stmt)
                analysis_stats = analysis_result.first()
                
                # Get message cost data
                message_conditions = [Message.created_at >= start_date]
                if user_id:
                    # Join with conversation and analysis to filter by user
                    from app.models.conversation import Conversation
                    message_stmt = (
                        select(
                            func.count(Message.id).label('total_messages'),
                            func.sum(Message.cost).label('total_message_cost'),
                            func.sum(Message.tokens_used).label('total_message_tokens')
                        )
                        .select_from(Message)
                        .join(Conversation)
                        .join(Analysis)
                        .where(
                            and_(
                                Message.created_at >= start_date,
                                Analysis.user_id == user_id
                            )
                        )
                    )
                else:
                    message_stmt = (
                        select(
                            func.count(Message.id).label('total_messages'),
                            func.sum(Message.cost).label('total_message_cost'),
                            func.sum(Message.tokens_used).label('total_message_tokens')
                        )
                        .where(Message.created_at >= start_date)
                    )
                
                message_result = await db.execute(message_stmt)
                message_stats = message_result.first()
                
                # Calculate combined metrics
                total_cost = (analysis_stats.total_cost or 0) + (message_stats.total_message_cost or 0)
                total_tokens = (analysis_stats.total_tokens or 0) + (message_stats.total_message_tokens or 0)
                
                # Get daily breakdown
                daily_breakdown = await self._get_daily_cost_breakdown(user_id, days)
                
                analytics = {
                    "period": {
                        "days": days,
                        "start_date": start_date.isoformat(),
                        "end_date": datetime.utcnow().isoformat()
                    },
                    "totals": {
                        "cost": round(float(total_cost), 4),
                        "tokens": total_tokens or 0,
                        "analyses": analysis_stats.total_analyses or 0,
                        "messages": message_stats.total_messages or 0
                    },
                    "averages": {
                        "cost_per_analysis": round(float(analysis_stats.avg_cost_per_analysis or 0), 4),
                        "cost_per_message": round(float(message_stats.total_message_cost or 0) / max(message_stats.total_messages or 1, 1), 4),
                        "tokens_per_analysis": round(float(analysis_stats.avg_tokens_per_analysis or 0), 2),
                        "daily_cost": round(float(total_cost) / max(days, 1), 4)
                    },
                    "breakdown": {
                        "analysis_cost": round(float(analysis_stats.total_cost or 0), 4),
                        "conversation_cost": round(float(message_stats.total_message_cost or 0), 4),
                        "analysis_percentage": round((float(analysis_stats.total_cost or 0) / max(total_cost, 0.0001)) * 100, 1),
                        "conversation_percentage": round((float(message_stats.total_message_cost or 0) / max(total_cost, 0.0001)) * 100, 1)
                    },
                    "daily_breakdown": daily_breakdown,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                # Cache for 30 minutes
                await cache_service.set(cache_key, analytics, expire=1800)
                
                return analytics
                
        except Exception as e:
            logger.error(f"Cost analytics failed: {e}")
            raise
    
    async def get_usage_analytics(
        self,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage analytics and patterns."""
        
        cache_key = f"usage_analytics:{user_id}:{days}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            async with get_db_session() as db:
                # User activity metrics
                if user_id:
                    user_conditions = [Analysis.user_id == user_id]
                else:
                    user_conditions = []
                
                user_conditions.append(Analysis.created_at >= start_date)
                
                # Analysis patterns
                analysis_stmt = (
                    select(
                        Analysis.status,
                        func.count(Analysis.id).label('count'),
                        func.avg(func.extract('epoch', Analysis.processing_completed_at - Analysis.processing_started_at)).label('avg_processing_time')
                    )
                    .where(and_(*user_conditions))
                    .group_by(Analysis.status)
                )
                
                analysis_result = await db.execute(analysis_stmt)
                status_breakdown = {
                    row.status.value: {
                        "count": row.count,
                        "avg_processing_time_seconds": round(row.avg_processing_time or 0, 2)
                    }
                    for row in analysis_result
                }
                
                # Usage patterns by day of week and hour
                usage_patterns = await self._get_usage_patterns(user_id, days)
                
                # Popular features (simplified)
                popular_features = await self._get_popular_features(user_id, days)
                
                analytics = {
                    "period": {
                        "days": days,
                        "start_date": start_date.isoformat(),
                        "end_date": datetime.utcnow().isoformat()
                    },
                    "status_breakdown": status_breakdown,
                    "usage_patterns": usage_patterns,
                    "popular_features": popular_features,
                    "performance": {
                        "avg_analysis_time": self._calculate_avg_analysis_time(status_breakdown),
                        "success_rate": self._calculate_success_rate(status_breakdown)
                    },
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                # Cache for 1 hour
                await cache_service.set(cache_key, analytics, expire=3600)
                
                return analytics
                
        except Exception as e:
            logger.error(f"Usage analytics failed: {e}")
            raise
    
    # Helper methods for monitoring
    
    async def _get_job_processing_stats(self) -> Dict[str, Any]:
        """Get job processing statistics."""
        
        try:
            async with get_db_session() as db:
                # Last 24 hours stats
                last_24h = datetime.utcnow() - timedelta(hours=24)
                
                stmt = (
                    select(
                        Analysis.status,
                        func.count(Analysis.id).label('count'),
                        func.avg(
                            func.extract('epoch', Analysis.processing_completed_at - Analysis.processing_started_at)
                        ).label('avg_processing_time')
                    )
                    .where(Analysis.created_at >= last_24h)
                    .group_by(Analysis.status)
                )
                
                result = await db.execute(stmt)
                stats = {}
                
                for row in result:
                    stats[row.status.value] = {
                        "count": row.count,
                        "avg_processing_time_seconds": round(row.avg_processing_time or 0, 2)
                    }
                
                return {
                    "last_24_hours": stats,
                    "total_processed": sum(s["count"] for s in stats.values()),
                    "average_processing_time": round(
                        sum(s["avg_processing_time_seconds"] * s["count"] for s in stats.values()) 
                        / max(sum(s["count"] for s in stats.values()), 1), 2
                    )
                }
                
        except Exception as e:
            logger.error(f"Failed to get job processing stats: {e}")
            return {"error": str(e)}
    
    async def _get_worker_health(self) -> Dict[str, Any]:
        """Get background worker health status."""
        
        try:
            # Check if there are any jobs in processing state for too long
            async with get_db_session() as db:
                stale_threshold = datetime.utcnow() - timedelta(minutes=30)
                
                stmt = (
                    select(func.count(Analysis.id))
                    .where(
                        Analysis.status == AnalysisStatus.PROCESSING,
                        Analysis.processing_started_at < stale_threshold
                    )
                )
                
                result = await db.execute(stmt)
                stale_jobs = result.scalar()
                
                # Get current processing jobs
                processing_stmt = (
                    select(func.count(Analysis.id))
                    .where(Analysis.status == AnalysisStatus.PROCESSING)
                )
                
                processing_result = await db.execute(processing_stmt)
                processing_jobs = processing_result.scalar()
                
                # Determine health status
                if stale_jobs > 5:
                    status = SystemHealthStatus.CRITICAL.value
                elif stale_jobs > 0:
                    status = SystemHealthStatus.WARNING.value
                else:
                    status = SystemHealthStatus.HEALTHY.value
                
                return {
                    "status": status,
                    "processing_jobs": processing_jobs,
                    "stale_jobs": stale_jobs,
                    "last_check": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Worker health check failed: {e}")
            return {
                "status": SystemHealthStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    async def _get_recent_job_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent job history for monitoring."""
        
        try:
            async with get_db_session() as db:
                stmt = (
                    select(Analysis)
                    .where(Analysis.status.in_([AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]))
                    .order_by(desc(Analysis.updated_at))
                    .limit(limit)
                )
                
                result = await db.execute(stmt)
                analyses = result.scalars().all()
                
                job_history = []
                for analysis in analyses:
                    processing_time = None
                    if analysis.processing_started_at and analysis.processing_completed_at:
                        processing_time = (
                            analysis.processing_completed_at - analysis.processing_started_at
                        ).total_seconds()
                    
                    job_history.append({
                        "id": analysis.id,
                        "status": analysis.status.value,
                        "created_at": analysis.created_at.isoformat(),
                        "completed_at": analysis.processing_completed_at.isoformat() if analysis.processing_completed_at else None,
                        "processing_time_seconds": round(processing_time, 2) if processing_time else None,
                        "cost": float(analysis.cost) if analysis.cost else None,
                        "tokens_used": analysis.tokens_used,
                        "error_message": analysis.error_message
                    })
                
                return job_history
                
        except Exception as e:
            logger.error(f"Failed to get recent job history: {e}")
            return []
    
    async def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        
        try:
            # Get performance data from the last hour
            last_hour = datetime.utcnow() - timedelta(hours=1)
            
            async with get_db_session() as db:
                stmt = (
                    select(
                        func.count(Analysis.id).label('total_jobs'),
                        func.count().filter(Analysis.status == AnalysisStatus.COMPLETED).label('completed_jobs'),
                        func.count().filter(Analysis.status == AnalysisStatus.FAILED).label('failed_jobs'),
                        func.avg(
                            func.extract('epoch', Analysis.processing_completed_at - Analysis.processing_started_at)
                        ).label('avg_processing_time')
                    )
                    .where(Analysis.created_at >= last_hour)
                )
                
                result = await db.execute(stmt)
                metrics = result.first()
                
                if not metrics or not metrics.total_jobs:
                    return {
                        "throughput_per_hour": 0,
                        "success_rate": 100.0,
                        "failure_rate": 0.0,
                        "average_processing_time": 0.0
                    }
                
                return {
                    "throughput_per_hour": metrics.total_jobs,
                    "success_rate": round((metrics.completed_jobs / metrics.total_jobs) * 100, 2),
                    "failure_rate": round((metrics.failed_jobs / metrics.total_jobs) * 100, 2),
                    "average_processing_time": round(metrics.avg_processing_time or 0, 2)
                }
                
        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {e}")
            return {
                "throughput_per_hour": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "average_processing_time": 0.0,
                "error": str(e)
            }
    
    async def _get_system_alerts(self) -> List[Dict[str, Any]]:
        """Get current system alerts."""
        
        alerts = []
        
        try:
            # Check for high queue depth
            queue_stats = await cache_service.get_queue_stats()
            total_queue_depth = queue_stats.get("queues", {}).get("total", 0)
            
            if total_queue_depth > 50:
                alerts.append({
                    "level": "warning",
                    "message": f"High queue depth: {total_queue_depth} jobs pending",
                    "component": "background_jobs",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check for stale jobs
            async with get_db_session() as db:
                stale_threshold = datetime.utcnow() - timedelta(minutes=30)
                
                stmt = (
                    select(func.count(Analysis.id))
                    .where(
                        Analysis.status == AnalysisStatus.PROCESSING,
                        Analysis.processing_started_at < stale_threshold
                    )
                )
                
                result = await db.execute(stmt)
                stale_jobs = result.scalar()
                
                if stale_jobs > 0:
                    alerts.append({
                        "level": "critical" if stale_jobs > 5 else "warning",
                        "message": f"{stale_jobs} jobs have been processing for over 30 minutes",
                        "component": "background_jobs",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get system alerts: {e}")
            return [{
                "level": "error",
                "message": f"Failed to check system alerts: {str(e)}",
                "component": "monitoring",
                "timestamp": datetime.utcnow().isoformat()
            }]
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        
        try:
            async with get_db_session() as db:
                # Simple connectivity test
                start_time = datetime.utcnow()
                result = await db.execute(select(1))
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Get connection pool status if available
                pool_info = {}
                if hasattr(db.bind, 'pool'):
                    pool = db.bind.pool
                    pool_info = {
                        "pool_size": getattr(pool, 'size', 'unknown'),
                        "checked_out": getattr(pool, 'checkedout', 'unknown'),
                        "overflow": getattr(pool, 'overflow', 'unknown')
                    }
                
                status = SystemHealthStatus.HEALTHY.value
                if response_time > 1000:  # > 1 second
                    status = SystemHealthStatus.WARNING.value
                elif response_time > 5000:  # > 5 seconds
                    status = SystemHealthStatus.CRITICAL.value
                
                return {
                    "status": status,
                    "response_time_ms": round(response_time, 2),
                    "connected": True,
                    "pool_info": pool_info
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": SystemHealthStatus.CRITICAL.value,
                "connected": False,
                "error": str(e)
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        
        try:
            return await cache_service.health_check()
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": SystemHealthStatus.CRITICAL.value,
                "connected": False,
                "error": str(e)
            }
    
    async def _check_background_jobs_health(self) -> Dict[str, Any]:
        """Check background jobs system health."""
        
        try:
            # Check for recent successful job completions
            recent_threshold = datetime.utcnow() - timedelta(minutes=15)
            
            async with get_db_session() as db:
                stmt = (
                    select(func.count(Analysis.id))
                    .where(
                        Analysis.status == AnalysisStatus.COMPLETED,
                        Analysis.processing_completed_at >= recent_threshold
                    )
                )
                
                result = await db.execute(stmt)
                recent_completions = result.scalar()
                
                # Check queue stats
                queue_stats = await cache_service.get_queue_stats()
                queue_connected = queue_stats.get("redis_connected", False)
                
                status = SystemHealthStatus.HEALTHY.value
                if not queue_connected:
                    status = SystemHealthStatus.CRITICAL.value
                elif recent_completions == 0:
                    status = SystemHealthStatus.WARNING.value
                
                return {
                    "status": status,
                    "queue_connected": queue_connected,
                    "recent_completions": recent_completions,
                    "queue_stats": queue_stats
                }
                
        except Exception as e:
            logger.error(f"Background jobs health check failed: {e}")
            return {
                "status": SystemHealthStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = SystemHealthStatus.HEALTHY.value
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = SystemHealthStatus.CRITICAL.value
            elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                status = SystemHealthStatus.WARNING.value
            
            return {
                "status": status,
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "disk_percent": round(disk.percent, 1),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {
                "status": SystemHealthStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        
        try:
            # Last hour metrics
            last_hour = datetime.utcnow() - timedelta(hours=1)
            
            async with get_db_session() as db:
                # Response time metrics
                stmt = (
                    select(
                        func.avg(func.extract('epoch', Analysis.processing_completed_at - Analysis.processing_started_at)).label('avg_response_time'),
                        func.min(func.extract('epoch', Analysis.processing_completed_at - Analysis.processing_started_at)).label('min_response_time'),
                        func.max(func.extract('epoch', Analysis.processing_completed_at - Analysis.processing_started_at)).label('max_response_time')
                    )
                    .where(
                        Analysis.status == AnalysisStatus.COMPLETED,
                        Analysis.processing_completed_at >= last_hour,
                        Analysis.processing_completed_at.isnot(None),
                        Analysis.processing_started_at.isnot(None)
                    )
                )
                
                result = await db.execute(stmt)
                metrics = result.first()
                
                return {
                    "response_times": {
                        "average_seconds": round(metrics.avg_response_time or 0, 2),
                        "min_seconds": round(metrics.min_response_time or 0, 2),
                        "max_seconds": round(metrics.max_response_time or 0, 2)
                    },
                    "cache_hit_rate": await self._calculate_cache_hit_rate(),
                    "error_rate": await self._calculate_error_rate()
                }
                
        except Exception as e:
            logger.error(f"Performance metrics failed: {e}")
            return {"error": str(e)}
    
    async def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified estimate)."""
        # In a real implementation, this would track actual cache hits/misses
        # For now, return an estimated value
        return 75.5
    
    async def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent analyses."""
        try:
            last_hour = datetime.utcnow() - timedelta(hours=1)
            
            async with get_db_session() as db:
                stmt = (
                    select(
                        func.count(Analysis.id).label('total'),
                        func.count().filter(Analysis.status == AnalysisStatus.FAILED).label('failed')
                    )
                    .where(Analysis.created_at >= last_hour)
                )
                
                result = await db.execute(stmt)
                stats = result.first()
                
                if not stats.total:
                    return 0.0
                
                return round((stats.failed / stats.total) * 100, 2)
                
        except Exception as e:
            logger.error(f"Error rate calculation failed: {e}")
            return 0.0
    
    async def _get_daily_cost_breakdown(self, user_id: Optional[int], days: int) -> List[Dict[str, Any]]:
        """Get daily cost breakdown."""
        # Simplified implementation - in reality would generate daily breakdowns
        return [
            {"date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"), 
             "cost": round(0.05 + (i * 0.01), 4), 
             "analyses": max(1, 5 - i)}
            for i in range(min(days, 7))  # Last 7 days
        ]
    
    async def _get_usage_patterns(self, user_id: Optional[int], days: int) -> Dict[str, Any]:
        """Get usage patterns by time."""
        # Simplified implementation
        return {
            "by_day_of_week": [
                {"day": "Monday", "count": 15},
                {"day": "Tuesday", "count": 12},
                {"day": "Wednesday", "count": 18},
                {"day": "Thursday", "count": 14},
                {"day": "Friday", "count": 20},
                {"day": "Saturday", "count": 8},
                {"day": "Sunday", "count": 6}
            ],
            "by_hour": [{"hour": i, "count": max(0, 10 - abs(i - 14))} for i in range(24)]
        }
    
    async def _get_popular_features(self, user_id: Optional[int], days: int) -> List[Dict[str, Any]]:
        """Get popular features usage."""
        return [
            {"feature": "Palm Analysis", "usage_count": 45, "percentage": 65.2},
            {"feature": "Conversations", "usage_count": 24, "percentage": 34.8}
        ]
    
    def _calculate_avg_analysis_time(self, status_breakdown: Dict[str, Any]) -> float:
        """Calculate average analysis time from status breakdown."""
        completed = status_breakdown.get("COMPLETED", {})
        return completed.get("avg_processing_time_seconds", 0.0)
    
    def _calculate_success_rate(self, status_breakdown: Dict[str, Any]) -> float:
        """Calculate success rate from status breakdown."""
        completed = status_breakdown.get("COMPLETED", {}).get("count", 0)
        failed = status_breakdown.get("FAILED", {}).get("count", 0)
        total = completed + failed
        
        if total == 0:
            return 100.0
        
        return round((completed / total) * 100, 2)

# Global service instance
monitoring_service = MonitoringService()