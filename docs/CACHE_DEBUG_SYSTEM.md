# Cache Debug System Documentation

## Overview

The Cache Debug System provides comprehensive debugging and management capabilities for Redis cache operations in the Indian Palmistry AI application. This system includes API endpoints, utilities, and frontend components for cache monitoring and troubleshooting.

## Backend Implementation

### Cache Debug API Endpoints

#### `/api/v1/cache/debug` (GET)
Returns detailed cache debug information including:
- Total cache keys
- User-specific cache key counts
- Pattern breakdown by cache type
- Memory usage statistics
- Cache hit/miss ratios

#### `/api/v1/cache/refresh` (POST)
Refreshes cache for the current user:
- Invalidates user-specific cached data
- Returns count of invalidated keys
- Supports pattern-based refresh with `pattern` parameter

#### `/api/v1/cache/validate-consistency` (GET)
Validates cache consistency between cache and database:
- Checks for data inconsistencies
- Provides recommendations for fixing issues
- Returns detailed inconsistency reports

### Cache Service Enhancements (`app/core/cache.py`)

Added comprehensive cache management methods:

```python
class CacheService:
    async def get_cache_debug_info(self) -> dict
    async def refresh_user_cache(self, user_id: int, pattern: Optional[str] = None) -> dict
    async def validate_consistency(self, user_id: int) -> dict
    async def get_cache_pattern_stats(self) -> dict
    async def clear_pattern(self, pattern: str) -> int
```

### Cache Utilities (`app/utils/cache_utils.py`)

New utility module providing:
- Cache key validation and sanitization
- Pattern matching and key filtering
- Cache health monitoring utilities
- Debug information collection helpers

```python
def validate_cache_key(key: str) -> bool
def extract_user_id_from_key(key: str) -> Optional[int]
def get_pattern_stats(redis_client, patterns: List[str]) -> Dict[str, int]
def collect_debug_info(redis_client) -> dict
```

## Frontend Integration

### Cache Debug Components

#### `CacheDebugPanel` Component
- Real-time cache statistics display
- User-friendly cache refresh controls
- Visual cache consistency indicators
- Debug information in developer-friendly format

#### `DataConsistencyChecker` Component
- Automated consistency validation
- Issue reporting with user-friendly messages
- Refresh recommendations and controls
- Integration with error boundaries

### API Client Extensions (`frontend/src/lib/api.ts`)

Added cache management API methods:

```typescript
export const cacheApi = {
  getCacheDebug(): Promise<CacheDebugInfo>
  refreshCache(): Promise<RefreshResult>
  validateCacheConsistency(): Promise<ConsistencyReport>
  refreshCachePattern(pattern: string): Promise<PatternRefreshResult>
}
```

### Cache Management Hooks (`frontend/src/hooks/useDashboard.ts`)

Added specialized hooks for cache operations:

```typescript
export function useCacheDebug() {
  // Real-time cache debug information
  // Cache refresh with progress tracking
  // Consistency validation with error handling
}

export function useCacheRefresh() {
  // Pattern-based cache refresh
  // Automatic re-validation after refresh
  // User feedback during operations
}
```

## API Security and Rate Limiting

### Endpoint Protection
- All cache debug endpoints require authentication
- Rate limiting applied to prevent abuse
- CSRF protection for state-changing operations
- User-scoped access to prevent data leakage

### Error Handling
- Comprehensive error messages for debugging
- Graceful fallback when Redis is unavailable
- Logging of all cache operations for audit

## Usage Examples

### Backend Usage

```python
# Get comprehensive cache debug info
debug_info = await cache_service.get_cache_debug_info()

# Refresh specific user cache
result = await cache_service.refresh_user_cache(user_id, "dashboard:*")

# Validate cache consistency
validation = await cache_service.validate_consistency(user_id)
```

### Frontend Usage

```typescript
// Use cache debug hook
const { debugInfo, loading, error, fetchCacheInfo, refreshCache } = useCacheDebug();

// Refresh specific cache pattern
await refreshCache("dashboard:*");

// Validate consistency
const validation = await validateConsistency();
```

### API Usage

```bash
# Get cache debug information
curl -X GET http://localhost:8000/api/v1/cache/debug \
  -H "Authorization: Bearer <token>"

# Refresh user cache
curl -X POST http://localhost:8000/api/v1/cache/refresh \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"pattern": "dashboard:*"}'

# Validate cache consistency
curl -X GET http://localhost:8000/api/v1/cache/validate-consistency \
  -H "Authorization: Bearer <token>"
```

## Performance Impact

### Monitoring
- Cache debug operations are optimized to minimize Redis load
- Pattern matching uses efficient Redis SCAN operations
- Results are cached to prevent repeated expensive operations

### Resource Usage
- Debug operations use separate Redis connections to avoid blocking
- Memory usage is monitored and reported in debug info
- CPU-intensive operations are rate-limited

## Troubleshooting

### Common Issues

1. **High Cache Miss Ratio**
   - Check cache key patterns for consistency
   - Verify TTL settings are appropriate
   - Consider warming cache during low-traffic periods

2. **Memory Usage High**
   - Review cache key patterns for efficiency
   - Implement automatic cleanup of expired keys
   - Consider shorter TTL for non-critical data

3. **Consistency Validation Failures**
   - Check database query performance
   - Verify cache invalidation logic
   - Review concurrent access patterns

### Debug Commands

```bash
# Check cache health
./health.sh

# Monitor cache usage
./logs.sh redis

# Test cache endpoints
curl http://localhost:8000/api/v1/cache/debug
```

## Integration with Existing Systems

### Dashboard Integration
- Cache debug panel integrated into development dashboard
- Real-time cache statistics display
- One-click cache refresh capabilities

### Error Boundaries
- Cache errors are caught and handled gracefully
- User-friendly error messages with recovery suggestions
- Automatic retry mechanisms for transient failures

### Monitoring Integration
- Cache metrics included in system monitoring
- Alerting for cache performance issues
- Integration with health check endpoints

## Future Enhancements

### Planned Features
- Visual cache usage graphs and trends
- Automated cache warming strategies  
- Advanced pattern-based cache management
- Integration with external monitoring tools

### Performance Optimizations
- Lazy loading of debug information
- Caching of debug results with smart invalidation
- Background cache health monitoring
- Predictive cache preloading

This cache debug system provides comprehensive tools for managing, monitoring, and troubleshooting Redis cache operations in the Indian Palmistry AI application, ensuring optimal performance and reliability.