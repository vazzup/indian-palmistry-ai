#!/usr/bin/env python3
"""
Test script to validate the dashboard cache invalidation fix.

This script simulates the cache invalidation workflow to ensure
the dashboard data consistency issue is resolved.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.cache import cache_service
from app.services.user_dashboard_service import user_dashboard_service
from app.services.analysis_service import AnalysisService
from app.utils.cache_utils import CacheDebugger, validate_cache_consistency
from app.core.database import init_db
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_cache_invalidation():
    """Test the cache invalidation implementation."""
    
    print("🧪 Testing Dashboard Cache Invalidation Fix")
    print("=" * 50)
    
    # Test user ID (adjust based on your test data)
    test_user_id = 1
    
    try:
        # Initialize database connection
        await init_db()
        await cache_service.connect()
        
        print(f"📋 Testing with user ID: {test_user_id}")
        
        # Step 1: Clear any existing cache
        print("\n1️⃣ Clearing existing cache...")
        initial_clear = await cache_service.invalidate_user_cache(test_user_id)
        print(f"   ✅ Cleared {initial_clear} cache entries")
        
        # Step 2: Get fresh dashboard data (this should create cache)
        print("\n2️⃣ Getting fresh dashboard data...")
        dashboard_data = await user_dashboard_service.get_user_dashboard(test_user_id)
        total_analyses = dashboard_data.get("overview", {}).get("total_analyses", 0)
        print(f"   📊 Dashboard shows {total_analyses} total analyses")
        
        # Step 3: Verify cache was created
        print("\n3️⃣ Verifying cache was created...")
        cache_inspection = await CacheDebugger.inspect_user_cache(test_user_id)
        dashboard_cached = cache_inspection.get("cache_keys", {}).get(f"user_dashboard:{test_user_id}", {}).get("exists", False)
        print(f"   📦 Dashboard cache exists: {dashboard_cached}")
        
        # Step 4: Simulate analysis creation (this should invalidate cache)
        print("\n4️⃣ Simulating analysis creation...")
        analysis_service = AnalysisService()
        await analysis_service._invalidate_user_cache(test_user_id)
        print("   🗑️ Cache invalidation triggered")
        
        # Step 5: Verify cache was invalidated
        print("\n5️⃣ Verifying cache was invalidated...")
        await asyncio.sleep(0.1)  # Small delay for Redis operations
        post_invalidation = await CacheDebugger.inspect_user_cache(test_user_id)
        dashboard_exists_after = post_invalidation.get("cache_keys", {}).get(f"user_dashboard:{test_user_id}", {}).get("exists", False)
        print(f"   🚫 Dashboard cache exists after invalidation: {dashboard_exists_after}")
        
        # Step 6: Get dashboard data again (should be fresh from DB)
        print("\n6️⃣ Getting dashboard data after invalidation...")
        fresh_dashboard = await user_dashboard_service.get_user_dashboard(test_user_id)
        fresh_total = fresh_dashboard.get("overview", {}).get("total_analyses", 0)
        print(f"   📊 Fresh dashboard shows {fresh_total} total analyses")
        
        # Step 7: Validate consistency
        print("\n7️⃣ Running full consistency validation...")
        consistency_result = await validate_cache_consistency(test_user_id)
        is_consistent = consistency_result.get("consistency_check", {}).get("analysis_counts_match", False)
        print(f"   ✅ Data consistency: {'PASS' if is_consistent else 'FAIL'}")
        
        # Step 8: Test the full invalidation flow
        print("\n8️⃣ Testing full invalidation flow...")
        flow_test = await CacheDebugger.test_cache_invalidation_flow(test_user_id)
        flow_success = flow_test.get("overall_success", False)
        print(f"   🔄 Invalidation flow test: {'PASS' if flow_success else 'FAIL'}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 4
        
        if not dashboard_exists_after:
            print("✅ Cache invalidation works correctly")
            tests_passed += 1
        else:
            print("❌ Cache invalidation failed")
            
        if dashboard_cached:
            print("✅ Cache creation works correctly")
            tests_passed += 1
        else:
            print("❌ Cache creation failed")
            
        if is_consistent:
            print("✅ Data consistency maintained")
            tests_passed += 1
        else:
            print("❌ Data consistency issues detected")
            
        if flow_success:
            print("✅ Full invalidation flow working")
            tests_passed += 1
        else:
            print("❌ Full invalidation flow has issues")
        
        print(f"\n🎯 Overall Result: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! Cache invalidation fix is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Please check the implementation.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Cache test failed: {e}", exc_info=True)
        return False
    
    finally:
        await cache_service.close()

async def main():
    """Main test function."""
    success = await test_cache_invalidation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())