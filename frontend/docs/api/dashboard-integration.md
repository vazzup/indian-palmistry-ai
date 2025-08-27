# Dashboard API Integration Guide

## Overview

The dashboard API integration provides comprehensive data management for user analytics, analysis tracking, and real-time statistics. This document covers the implementation details, data flow, and usage patterns for the dashboard live data integration.

## Architecture Overview

```
Frontend Dashboard Components
           ↓
Dashboard Hooks (useDashboard, useAnalysesList)
           ↓
Dashboard API Client (dashboardApi)
           ↓
Backend API Endpoints (/api/v1/enhanced/dashboard)
```

## API Endpoints

### Dashboard Overview
**Endpoint:** `GET /api/v1/enhanced/dashboard`

Provides comprehensive dashboard data including overview statistics, recent activity, and analytics.

**Response Structure:**
```typescript
{
  overview: {
    total_analyses: number;
    completed_analyses: number;
    total_conversations: number;
    success_rate: number;
  };
  recent_activity: RecentActivity[];
  analytics: DashboardAnalytics;
}
```

**Usage Example:**
```typescript
import { dashboardApi } from '@/lib/api';

const dashboardData = await dashboardApi.getDashboard();
console.log(`Total analyses: ${dashboardData.overview.total_analyses}`);
```

### Analyses List
**Endpoint:** `GET /api/v1/analyses/`

Fetches paginated list of user analyses with optional filtering and sorting.

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `limit` (number): Items per page (default: 10)
- `status` (string): Filter by status ('completed', 'processing', 'failed')
- `sort` (string): Sort field and direction

**Response Structure:**
```typescript
{
  analyses: AnalysisListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
```

**Usage Example:**
```typescript
// Fetch first page with 20 items, filtered by completed status
const analyses = await dashboardApi.getAnalyses({
  page: 1,
  limit: 20,
  status: 'completed',
  sort: 'created_at:desc'
});
```

### Dashboard Statistics
**Endpoint:** `GET /api/v1/enhanced/dashboard/statistics`

Fetches detailed statistical data for analytics and reporting.

**Usage Example:**
```typescript
const statistics = await dashboardApi.getDashboardStatistics();
```

## Data Transformation

### Backend to Frontend Mapping

The integration includes comprehensive data transformation utilities to ensure consistent data formats between backend and frontend:

#### Analysis Data Transformation
```typescript
// Backend format → Frontend format
{
  id: string;                    // Direct mapping
  created_at: string;           // ISO timestamp
  status: string;               // Normalized to 'completed' | 'processing' | 'failed'
  summary?: string;             // Optional description
  conversation_count: number;   // Defaults to 0
  left_image_url?: string;      // Optional image path
  right_image_url?: string;     // Optional image path
  cost?: number;                // Optional cost in credits/currency
}
```

#### Recent Activity Transformation
```typescript
// Transforms backend activity data to consistent frontend format
{
  id: string;
  type: string;                 // Activity type (analysis, conversation, etc.)
  message: string;              // Human-readable activity description
  timestamp: string;            // ISO timestamp
  analysis_id?: string;         // Optional reference to related analysis
}
```

## Error Handling

### API Error Management

The dashboard API integration includes comprehensive error handling:

```typescript
try {
  const dashboard = await dashboardApi.getDashboard();
  // Handle success
} catch (error) {
  // Error is automatically transformed to user-friendly message
  console.error('Dashboard load failed:', error.message);
}
```

### Error Types

1. **Network Errors**: Connection issues, timeout
2. **Authentication Errors**: Invalid session, expired tokens
3. **Server Errors**: 500+ status codes with detailed messages
4. **Validation Errors**: Invalid request parameters

## Data Caching Strategy

### Hook-Level Caching

The dashboard hooks implement smart caching to optimize performance:

```typescript
// Automatic caching with manual refresh capability
const { data, loading, error, refetch } = useDashboard();

// Manual data refresh
const handleRefresh = () => {
  refetch();
};
```

### Cache Invalidation

- Data automatically refreshes on component mount
- Manual refresh available through `refetch` function
- Error states preserve previous data when possible

## Security Considerations

### Authentication Requirements

All dashboard endpoints require authenticated users:

```typescript
// Automatic session management through axios interceptors
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Include session cookies
});
```

### Data Sanitization

All data from backend is sanitized before use in components:

```typescript
// Automatic data validation and sanitization
const sanitizedAnalysis = sanitizeAnalysisData(backendAnalysis);
```

## Performance Optimizations

### Request Optimization

1. **Pagination**: Large datasets are paginated to reduce load time
2. **Selective Loading**: Only required data fields are fetched
3. **Error Resilience**: Graceful degradation on partial failures

### Frontend Optimization

1. **Memoization**: Hook results are memoized to prevent unnecessary re-renders
2. **Loading States**: Progressive loading with skeleton states
3. **Error Boundaries**: Isolated error handling prevents app crashes

## Integration Examples

### Basic Dashboard Component

```typescript
import { useDashboard } from '@/hooks/useDashboard';

export default function DashboardPage() {
  const { data, loading, error } = useDashboard();

  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <EmptyState />;

  return (
    <div>
      <StatsOverview stats={data.overview} />
      <RecentActivity activities={data.recent_activity} />
      <AnalyticsCharts analytics={data.analytics} />
    </div>
  );
}
```

### Analyses List with Pagination

```typescript
import { useAnalysesList } from '@/hooks/useDashboard';

export default function AnalysesPage() {
  const [page, setPage] = useState(1);
  const { data, loading, error } = useAnalysesList({ 
    page, 
    limit: 10,
    status: 'completed' 
  });

  return (
    <div>
      {data?.analyses.map(analysis => (
        <AnalysisCard key={analysis.id} analysis={analysis} />
      ))}
      <Pagination 
        current={page}
        total={data?.total_pages || 0}
        onChange={setPage}
      />
    </div>
  );
}
```

## Monitoring and Debugging

### Debug Logging

Enable debug mode for detailed API logging:

```typescript
// Development environment logging
if (process.env.NODE_ENV === 'development') {
  console.log('Dashboard API Request:', endpoint, params);
  console.log('Dashboard API Response:', data);
}
```

### Error Tracking

All API errors are logged with context:

```typescript
console.error('Dashboard API Error:', {
  endpoint: '/api/v1/enhanced/dashboard',
  error: error.message,
  timestamp: new Date().toISOString(),
  userAgent: navigator.userAgent
});
```

## Testing Strategy

### Unit Tests
- API client function tests
- Data transformation utility tests
- Hook behavior tests

### Integration Tests
- Component integration with hooks
- Error handling scenarios
- Loading state management

### E2E Tests
- Complete dashboard user journey
- Cross-browser compatibility
- Performance benchmarks

## Migration Guide

### From Static Data to Live API

1. Replace static data imports with dashboard hooks
2. Update components to handle loading and error states
3. Implement proper error boundaries
4. Test with actual backend data

### Backwards Compatibility

The integration maintains backwards compatibility with existing components through:
- Consistent data structure interfaces
- Graceful fallbacks for missing data
- Optional fields with sensible defaults

## Troubleshooting

### Common Issues

**Issue: Dashboard data not loading**
- Check authentication status
- Verify API endpoint accessibility
- Review network connectivity

**Issue: Stale data displayed**
- Use `refetch()` function to force refresh
- Check cache invalidation logic
- Verify component re-render triggers

**Issue: Performance degradation**
- Review pagination settings
- Check for unnecessary re-renders
- Optimize data transformation logic

### Debug Commands

```bash
# Check API connectivity
curl -X GET http://localhost:8000/api/v1/enhanced/dashboard \
  -H "Cookie: sessionid=your-session-id"

# Monitor network requests in browser dev tools
# Check console for detailed error logs
```

## Future Enhancements

### Planned Features
1. Real-time data updates via WebSocket
2. Advanced filtering and search capabilities
3. Custom dashboard layout configuration
4. Export functionality for analytics data

### API Evolution
- Version management for breaking changes
- Backwards compatibility guarantees
- Migration tools for schema updates