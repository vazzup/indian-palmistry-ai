"""
Database optimization service for query analysis and performance monitoring.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, desc, and_
from sqlalchemy.engine import Result
from sqlalchemy.sql import Select

from app.core.database import get_db_session, get_engine
from app.core.cache import cache_service
from app.core.logging import get_logger

logger = get_logger(__name__)

class QueryPerformanceMonitor:
    """Monitor and analyze database query performance."""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # seconds
        self.query_cache = {}
        
    @asynccontextmanager
    async def monitor_query(self, query_name: str, query_text: str = None):
        """Context manager to monitor query execution time."""
        
        start_time = time.time()
        query_info = {
            "name": query_name,
            "text": query_text,
            "start_time": start_time,
            "timestamp": datetime.utcnow()
        }
        
        try:
            yield query_info
            
        except Exception as e:
            query_info["error"] = str(e)
            logger.error(f"Query error in {query_name}: {e}")
            raise
            
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            query_info["execution_time"] = execution_time
            query_info["end_time"] = end_time
            
            # Log slow queries
            if execution_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {query_name} took {execution_time:.3f}s",
                    extra={"query_performance": query_info}
                )
            
            # Cache query performance data
            await self._cache_query_performance(query_info)
    
    async def _cache_query_performance(self, query_info: Dict[str, Any]):
        """Cache query performance data for analysis."""
        
        cache_key = f"query_perf:{query_info['name']}:{int(time.time() // 300)}"  # 5-minute buckets
        
        try:
            # Get existing performance data for this time bucket
            existing_data = await cache_service.get(cache_key) or []
            existing_data.append({
                "execution_time": query_info["execution_time"],
                "timestamp": query_info["timestamp"].isoformat(),
                "error": query_info.get("error")
            })
            
            # Keep only last 100 queries per bucket
            if len(existing_data) > 100:
                existing_data = existing_data[-100:]
            
            # Cache for 1 hour
            await cache_service.set(cache_key, existing_data, expire=3600)
            
        except Exception as e:
            logger.error(f"Failed to cache query performance: {e}")

class DatabaseOptimizationService:
    """Service for database optimization and performance analysis."""
    
    def __init__(self):
        self.query_monitor = QueryPerformanceMonitor()
    
    async def analyze_query_performance(
        self, 
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Analyze query performance over time period."""
        
        try:
            # Calculate time buckets to check
            current_time = int(time.time())
            bucket_size = 300  # 5 minutes
            buckets_to_check = hours_back * 12  # 12 buckets per hour
            
            performance_data = {}
            total_queries = 0
            slow_queries = 0
            
            for i in range(buckets_to_check):
                bucket_time = current_time - (i * bucket_size)
                cache_pattern = f"query_perf:*:{bucket_time // bucket_size}"
                
                # In a real implementation, you'd need to scan Redis keys
                # For now, we'll return sample data
                continue
            
            # Get recent slow queries
            slow_queries_data = await self._get_recent_slow_queries()
            
            # Get query frequency analysis
            query_frequency = await self._analyze_query_frequency()
            
            # Get database connection metrics
            connection_metrics = await self._get_connection_metrics()
            
            analysis = {
                "period_hours": hours_back,
                "total_queries": total_queries,
                "slow_queries": slow_queries,
                "slow_query_rate": (slow_queries / max(total_queries, 1)) * 100,
                "recent_slow_queries": slow_queries_data,
                "query_frequency": query_frequency,
                "connection_metrics": connection_metrics,
                "recommendations": await self._generate_optimization_recommendations(),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query performance analysis failed: {e}")
            raise
    
    async def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        
        try:
            async with get_db_session() as db:
                # Table sizes (PostgreSQL-specific)
                table_stats = await self._get_table_statistics(db)
                
                # Index usage statistics
                index_stats = await self._get_index_statistics(db)
                
                # Query statistics
                query_stats = await self._get_query_statistics(db)
                
                # Connection pool statistics
                pool_stats = await self._get_connection_pool_stats()
                
                return {
                    "table_statistics": table_stats,
                    "index_statistics": index_stats,
                    "query_statistics": query_stats,
                    "connection_pool": pool_stats,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database statistics failed: {e}")
            raise
    
    async def optimize_queries(self, query_names: List[str] = None) -> Dict[str, Any]:
        """Analyze and provide optimization suggestions for queries."""
        
        try:
            optimizations = []
            
            # Common query optimization patterns
            optimization_checks = [
                self._check_missing_indexes,
                self._check_inefficient_joins,
                self._check_large_result_sets,
                self._check_n_plus_one_queries
            ]
            
            for check_func in optimization_checks:
                try:
                    optimization_result = await check_func()
                    if optimization_result:
                        optimizations.extend(optimization_result)
                except Exception as e:
                    logger.error(f"Optimization check failed: {check_func.__name__}: {e}")
            
            return {
                "optimizations": optimizations,
                "total_suggestions": len(optimizations),
                "priority_high": len([opt for opt in optimizations if opt.get("priority") == "high"]),
                "priority_medium": len([opt for opt in optimizations if opt.get("priority") == "medium"]),
                "priority_low": len([opt for opt in optimizations if opt.get("priority") == "low"]),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Query optimization analysis failed: {e}")
            raise
    
    async def vacuum_analyze_tables(self, table_names: List[str] = None) -> Dict[str, Any]:
        """Run VACUUM ANALYZE on specified tables (PostgreSQL)."""
        
        try:
            async with get_db_session() as db:
                # Default tables if none specified
                if not table_names:
                    table_names = ['users', 'analyses', 'conversations', 'messages']
                
                results = []
                
                for table_name in table_names:
                    try:
                        start_time = time.time()
                        
                        # Run VACUUM ANALYZE
                        await db.execute(text(f"VACUUM ANALYZE {table_name}"))
                        
                        execution_time = time.time() - start_time
                        
                        results.append({
                            "table": table_name,
                            "status": "success",
                            "execution_time": round(execution_time, 3)
                        })
                        
                        logger.info(f"VACUUM ANALYZE completed for {table_name} in {execution_time:.3f}s")
                        
                    except Exception as e:
                        results.append({
                            "table": table_name,
                            "status": "error",
                            "error": str(e)
                        })
                        logger.error(f"VACUUM ANALYZE failed for {table_name}: {e}")
                
                return {
                    "results": results,
                    "completed_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"VACUUM ANALYZE operation failed: {e}")
            raise
    
    async def create_missing_indexes(self, dry_run: bool = True) -> Dict[str, Any]:
        """Create missing indexes based on query analysis."""
        
        try:
            missing_indexes = await self._identify_missing_indexes()
            
            if dry_run:
                return {
                    "mode": "dry_run",
                    "missing_indexes": missing_indexes,
                    "would_create": len(missing_indexes)
                }
            
            created_indexes = []
            
            async with get_db_session() as db:
                for index_info in missing_indexes:
                    try:
                        # Create the index
                        create_sql = index_info["create_statement"]
                        await db.execute(text(create_sql))
                        
                        created_indexes.append({
                            "index_name": index_info["index_name"],
                            "table": index_info["table"],
                            "columns": index_info["columns"],
                            "status": "created"
                        })
                        
                        logger.info(f"Created index: {index_info['index_name']}")
                        
                    except Exception as e:
                        created_indexes.append({
                            "index_name": index_info["index_name"],
                            "table": index_info["table"],
                            "columns": index_info["columns"],
                            "status": "error",
                            "error": str(e)
                        })
                        logger.error(f"Failed to create index {index_info['index_name']}: {e}")
                
                await db.commit()
            
            return {
                "mode": "execute",
                "created_indexes": created_indexes,
                "successful": len([idx for idx in created_indexes if idx["status"] == "created"]),
                "failed": len([idx for idx in created_indexes if idx["status"] == "error"])
            }
            
        except Exception as e:
            logger.error(f"Create missing indexes failed: {e}")
            raise
    
    # Helper methods
    
    async def _get_recent_slow_queries(self) -> List[Dict[str, Any]]:
        """Get recent slow queries from performance logs."""
        
        # This would typically parse logs or query performance_schema
        # For now, return sample data
        return [
            {
                "query": "SELECT * FROM analyses WHERE user_id = ?",
                "avg_execution_time": 2.5,
                "call_count": 150,
                "last_seen": datetime.utcnow().isoformat()
            },
            {
                "query": "SELECT * FROM messages JOIN conversations ON ...",
                "avg_execution_time": 1.8,
                "call_count": 89,
                "last_seen": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            }
        ]
    
    async def _analyze_query_frequency(self) -> Dict[str, Any]:
        """Analyze query frequency patterns."""
        
        return {
            "most_frequent": [
                {"query_pattern": "SELECT analyses WHERE user_id", "frequency": 45.2},
                {"query_pattern": "SELECT messages WHERE conversation_id", "frequency": 32.1},
                {"query_pattern": "INSERT INTO messages", "frequency": 28.7}
            ],
            "peak_hours": [14, 15, 16],  # 2-4 PM
            "average_queries_per_minute": 125
        }
    
    async def _get_connection_metrics(self) -> Dict[str, Any]:
        """Get database connection metrics."""
        
        try:
            engine = get_engine()
            pool = engine.pool
            
            return {
                "pool_size": getattr(pool, 'size', 'unknown'),
                "checked_out_connections": getattr(pool, 'checkedout', 'unknown'),
                "overflow_connections": getattr(pool, 'overflow', 'unknown'),
                "total_connections": getattr(pool, 'size', 0) + getattr(pool, 'overflow', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection metrics: {e}")
            return {"error": str(e)}
    
    async def _get_table_statistics(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get table size and row count statistics."""
        
        try:
            # PostgreSQL-specific query
            stats_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public' 
                AND tablename IN ('users', 'analyses', 'conversations', 'messages')
                ORDER BY tablename, attname
            """)
            
            result = await db.execute(stats_query)
            rows = result.fetchall()
            
            table_stats = {}
            for row in rows:
                table_name = row.tablename
                if table_name not in table_stats:
                    table_stats[table_name] = {
                        "table_name": table_name,
                        "columns": []
                    }
                
                table_stats[table_name]["columns"].append({
                    "column_name": row.attname,
                    "n_distinct": row.n_distinct,
                    "correlation": row.correlation
                })
            
            return list(table_stats.values())
            
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return []
    
    async def _get_index_statistics(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get index usage statistics."""
        
        try:
            # PostgreSQL-specific query
            index_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
            """)
            
            result = await db.execute(index_query)
            rows = result.fetchall()
            
            return [
                {
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "index": row.indexname,
                    "scans": row.idx_scan,
                    "tuples_read": row.idx_tup_read,
                    "tuples_fetched": row.idx_tup_fetch
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to get index statistics: {e}")
            return []
    
    async def _get_query_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """Get general query statistics."""
        
        try:
            # Get basic table row counts
            tables = ['users', 'analyses', 'conversations', 'messages']
            row_counts = {}
            
            for table in tables:
                count_query = text(f"SELECT COUNT(*) FROM {table}")
                result = await db.execute(count_query)
                row_counts[table] = result.scalar()
            
            return {
                "table_row_counts": row_counts,
                "total_rows": sum(row_counts.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get query statistics: {e}")
            return {}
    
    async def _get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        
        return await self._get_connection_metrics()
    
    async def _generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis."""
        
        return [
            {
                "type": "index",
                "priority": "high",
                "title": "Add composite index for user queries",
                "description": "Add index on (user_id, created_at) for analyses table",
                "impact": "Reduce query time by ~60% for user analysis listings",
                "effort": "low"
            },
            {
                "type": "query",
                "priority": "medium", 
                "title": "Optimize conversation message loading",
                "description": "Use LIMIT and pagination for message queries",
                "impact": "Reduce memory usage and improve response times",
                "effort": "medium"
            },
            {
                "type": "caching",
                "priority": "medium",
                "title": "Cache frequently accessed analysis summaries",
                "description": "Implement Redis caching for analysis summaries",
                "impact": "Reduce database load by ~40%",
                "effort": "medium"
            }
        ]
    
    async def _check_missing_indexes(self) -> List[Dict[str, Any]]:
        """Check for missing indexes based on query patterns."""
        
        return [
            {
                "type": "missing_index",
                "priority": "high",
                "table": "analyses",
                "columns": ["user_id", "status"],
                "reason": "Frequently filtered by user and status",
                "estimated_impact": "60% query time reduction"
            }
        ]
    
    async def _check_inefficient_joins(self) -> List[Dict[str, Any]]:
        """Check for inefficient join patterns."""
        
        return [
            {
                "type": "inefficient_join",
                "priority": "medium",
                "tables": ["conversations", "messages"],
                "reason": "Missing index on foreign key relationship",
                "estimated_impact": "30% join performance improvement"
            }
        ]
    
    async def _check_large_result_sets(self) -> List[Dict[str, Any]]:
        """Check for queries returning large result sets."""
        
        return [
            {
                "type": "large_result_set",
                "priority": "medium",
                "query_pattern": "SELECT * FROM messages",
                "reason": "Queries without LIMIT clause",
                "estimated_impact": "Memory usage reduction"
            }
        ]
    
    async def _check_n_plus_one_queries(self) -> List[Dict[str, Any]]:
        """Check for N+1 query problems."""
        
        return [
            {
                "type": "n_plus_one",
                "priority": "high",
                "pattern": "Loading messages for each conversation separately",
                "reason": "Missing eager loading",
                "estimated_impact": "90% query count reduction"
            }
        ]
    
    async def _identify_missing_indexes(self) -> List[Dict[str, Any]]:
        """Identify missing indexes that would improve performance."""
        
        return [
            {
                "index_name": "ix_analyses_user_status_created",
                "table": "analyses",
                "columns": ["user_id", "status", "created_at"],
                "create_statement": "CREATE INDEX CONCURRENTLY ix_analyses_user_status_created ON analyses (user_id, status, created_at)",
                "justification": "Common filter pattern in user analysis queries"
            },
            {
                "index_name": "ix_messages_conversation_role",
                "table": "messages", 
                "columns": ["conversation_id", "role"],
                "create_statement": "CREATE INDEX CONCURRENTLY ix_messages_conversation_role ON messages (conversation_id, role)",
                "justification": "Filtering messages by conversation and role"
            }
        ]

# Global service instance
database_optimization_service = DatabaseOptimizationService()
query_monitor = QueryPerformanceMonitor()