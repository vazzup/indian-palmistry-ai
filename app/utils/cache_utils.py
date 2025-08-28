"""
Cache utilities for testing and debugging cache invalidation.
"""

import asyncio
from typing import Dict, List, Any, Optional
from app.core.cache import cache_service, CacheKeys
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheDebugger:
    """Utility class for debugging cache operations."""
    
    @staticmethod
    async def inspect_user_cache(user_id: int) -> Dict[str, Any]:
        """Inspect all cache keys for a specific user."""
        try:
            # Get all cache keys that might be related to this user
            cache_keys_to_check = [
                CacheKeys.user_dashboard(user_id),
                CacheKeys.user_analytics(user_id),
                CacheKeys.user_preferences(user_id),
                f"user_stats:{user_id}:30",  # Common period
                f"user_stats:{user_id}:7",   # Another common period
            ]
            
            cache_status = {}
            
            for key in cache_keys_to_check:
                try:
                    value = await cache_service.get(key)
                    cache_status[key] = {
                        "exists": value is not None,
                        "type": type(value).__name__ if value else None,
                        "size_estimate": len(str(value)) if value else 0
                    }
                except Exception as e:
                    cache_status[key] = {
                        "exists": False,
                        "error": str(e)
                    }
            
            return {
                "user_id": user_id,
                "cache_keys": cache_status,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Failed to inspect cache for user {user_id}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def invalidate_and_verify(user_id: int) -> Dict[str, Any]:
        """Invalidate user cache and verify it was cleared."""
        try:
            # Get cache status before invalidation
            before = await CacheDebugger.inspect_user_cache(user_id)
            
            # Invalidate all user cache
            invalidated_count = await cache_service.invalidate_user_cache(user_id)
            
            # Wait a moment for Redis operations to complete
            await asyncio.sleep(0.1)
            
            # Get cache status after invalidation
            after = await CacheDebugger.inspect_user_cache(user_id)
            
            return {
                "user_id": user_id,
                "invalidated_count": invalidated_count,
                "before": before,
                "after": after,
                "success": all(
                    not status.get("exists", False) 
                    for status in after.get("cache_keys", {}).values()
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to invalidate and verify cache for user {user_id}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def test_cache_invalidation_flow(user_id: int) -> Dict[str, Any]:
        """Test the full cache invalidation flow."""
        try:
            results = {
                "user_id": user_id,
                "steps": []
            }
            
            # Step 1: Check initial cache state
            initial_state = await CacheDebugger.inspect_user_cache(user_id)
            results["steps"].append({
                "step": "initial_inspection",
                "result": initial_state
            })
            
            # Step 2: Create some cache entries
            await cache_service.cache_user_dashboard(user_id, {"test": "data"}, expire=300)
            await cache_service.cache_user_analytics(user_id, {"analytics": "test"}, expire=300)
            
            cache_after_creation = await CacheDebugger.inspect_user_cache(user_id)
            results["steps"].append({
                "step": "after_cache_creation",
                "result": cache_after_creation
            })
            
            # Step 3: Invalidate cache
            invalidation_result = await CacheDebugger.invalidate_and_verify(user_id)
            results["steps"].append({
                "step": "invalidation",
                "result": invalidation_result
            })
            
            # Step 4: Final verification
            final_state = await CacheDebugger.inspect_user_cache(user_id)
            results["steps"].append({
                "step": "final_verification",
                "result": final_state
            })
            
            results["overall_success"] = invalidation_result.get("success", False)
            return results
            
        except Exception as e:
            logger.error(f"Cache invalidation flow test failed for user {user_id}: {e}")
            return {"error": str(e)}


async def validate_cache_consistency(user_id: int) -> Dict[str, Any]:
    """Validate cache consistency for a user's dashboard data."""
    try:
        from app.services.user_dashboard_service import user_dashboard_service
        from app.services.analysis_service import AnalysisService
        
        # Clear cache first
        await cache_service.invalidate_user_cache(user_id)
        
        # Get fresh dashboard data (should hit database)
        dashboard_fresh = await user_dashboard_service.get_user_dashboard(user_id)
        
        # Get cached dashboard data (should hit cache)
        dashboard_cached = await user_dashboard_service.get_user_dashboard(user_id)
        
        # Get analysis count directly from service
        analysis_service = AnalysisService()
        analyses, total_analyses = await analysis_service.get_user_analyses(user_id, page=1, per_page=100)
        
        return {
            "user_id": user_id,
            "dashboard_fresh": dashboard_fresh,
            "dashboard_cached": dashboard_cached,
            "direct_analysis_count": total_analyses,
            "dashboard_analysis_count": dashboard_fresh.get("overview", {}).get("total_analyses", 0),
            "consistency_check": {
                "fresh_equals_cached": dashboard_fresh == dashboard_cached,
                "analysis_counts_match": total_analyses == dashboard_fresh.get("overview", {}).get("total_analyses", 0)
            },
            "cache_hit": dashboard_fresh == dashboard_cached  # Should be True if caching works
        }
        
    except Exception as e:
        logger.error(f"Cache consistency validation failed for user {user_id}: {e}")
        return {"error": str(e)}


# Convenience functions for API endpoints
async def debug_user_cache(user_id: int) -> Dict[str, Any]:
    """Debug cache for a specific user."""
    return await CacheDebugger.inspect_user_cache(user_id)

async def force_cache_refresh(user_id: int) -> Dict[str, Any]:
    """Force refresh cache for a user."""
    return await CacheDebugger.invalidate_and_verify(user_id)