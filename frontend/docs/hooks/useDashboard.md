# Dashboard Hooks Documentation

## Overview

The dashboard hooks provide a comprehensive React hooks interface for managing dashboard data, analytics, and user analysis listings. These hooks handle data fetching, loading states, error management, and provide utilities for data transformation.

## Hooks Reference

### useDashboard()

Primary hook for fetching and managing complete dashboard data including overview statistics, recent activity, and analytics.

```typescript
import { useDashboard } from '@/hooks/useDashboard';

const { data, loading, error, refetch } = useDashboard();
```

**Returns:**
```typescript
{
  data: DashboardData | null;     // Complete dashboard data
  loading: boolean;               // Loading state indicator
  error: string | null;           // Error message if request failed
  refetch: () => Promise<void>;   // Manual refresh function
}
```

**Data Structure:**
```typescript
interface DashboardData {
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
export default function DashboardOverview() {
  const { data, loading, error, refetch } = useDashboard();

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  if (!data) return <EmptyState />;

  return (
    <div>
      <h1>Dashboard Overview</h1>
      <div className="stats-grid">
        <StatCard 
          title="Total Analyses" 
          value={data.overview.total_analyses} 
        />
        <StatCard 
          title="Success Rate" 
          value={`${data.overview.success_rate}%`} 
        />
      </div>
      <RecentActivity activities={data.recent_activity} />
    </div>
  );
}
```

### useAnalysesList(options?)

Hook for fetching paginated list of user analyses with filtering and sorting capabilities.

```typescript
import { useAnalysesList } from '@/hooks/useDashboard';

const { data, loading, error, refetch } = useAnalysesList({
  page: 1,
  limit: 10,
  status: 'completed',
  sort: 'created_at:desc'
});
```

**Parameters:**
```typescript
interface AnalysesListOptions {
  page?: number;      // Page number (default: 1)
  limit?: number;     // Items per page (default: 10)
  status?: string;    // Filter by status
  sort?: string;      // Sort field and direction
}
```

**Returns:**
```typescript
{
  data: AnalysesListResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}
```

**Data Structure:**
```typescript
interface AnalysesListResponse {
  analyses: AnalysisListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface AnalysisListItem {
  id: string;
  created_at: string;
  status: 'completed' | 'processing' | 'failed';
  summary?: string;
  conversation_count: number;
  left_image_url?: string;
  right_image_url?: string;
  cost?: number;
}
```

**Usage Example:**
```typescript
export default function AnalysesList() {
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  
  const { data, loading, error, refetch } = useAnalysesList({
    page: currentPage,
    limit: 20,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    sort: 'created_at:desc'
  });

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleStatusFilter = (status: string) => {
    setStatusFilter(status);
    setCurrentPage(1); // Reset to first page
  };

  if (loading) return <AnalysesListSkeleton />;
  if (error) return <ErrorMessage error={error} onRetry={refetch} />;
  if (!data || data.analyses.length === 0) return <EmptyAnalysesList />;

  return (
    <div>
      <div className="filters">
        <StatusFilter onChange={handleStatusFilter} value={statusFilter} />
      </div>
      
      <div className="analyses-grid">
        {data.analyses.map(analysis => (
          <AnalysisCard key={analysis.id} analysis={analysis} />
        ))}
      </div>
      
      <Pagination
        current={data.page}
        total={data.total_pages}
        onChange={handlePageChange}
      />
    </div>
  );
}
```

### useDashboardStatistics()

Hook for fetching detailed dashboard statistics and analytics data.

```typescript
import { useDashboardStatistics } from '@/hooks/useDashboard';

const { data, loading, error, refetch } = useDashboardStatistics();
```

**Returns:**
```typescript
{
  data: any | null;               // Statistics data from backend
  loading: boolean;               // Loading state
  error: string | null;           // Error message if failed
  refetch: () => Promise<void>;   // Manual refresh function
}
```

**Usage Example:**
```typescript
export default function AnalyticsDashboard() {
  const { data, loading, error, refetch } = useDashboardStatistics();

  if (loading) return <StatisticsLoading />;
  if (error) return <StatisticsError onRetry={refetch} />;
  if (!data) return <NoStatisticsAvailable />;

  return (
    <div>
      <h2>Analytics Dashboard</h2>
      <ChartsContainer statistics={data} />
    </div>
  );
}
```

## Utility Functions

### Data Transformation

#### transformAnalysisData(backendAnalysis)

Transforms backend analysis data to consistent frontend format.

```typescript
import { transformAnalysisData } from '@/hooks/useDashboard';

const frontendAnalysis = transformAnalysisData(backendData);
```

#### sanitizeAnalysisData(analysis)

Validates and sanitizes analysis data with fallbacks for missing fields.

```typescript
import { sanitizeAnalysisData } from '@/hooks/useDashboard';

const safeAnalysis = sanitizeAnalysisData(untrustedData);
```

#### transformRecentActivity(activity)

Transforms backend activity data to frontend format.

```typescript
import { transformRecentActivity } from '@/hooks/useDashboard';

const activities = transformRecentActivity(backendActivities);
```

### Date and Time Utilities

#### formatAnalysisDate(dateString, includeTime?)

Formats ISO date strings to user-friendly format.

```typescript
import { formatAnalysisDate } from '@/hooks/useDashboard';

const formatted = formatAnalysisDate('2024-01-15T10:30:00Z'); // "Jan 15, 2024"
const withTime = formatAnalysisDate('2024-01-15T10:30:00Z', true); // "Jan 15, 2024 10:30 AM"
```

#### getRelativeTime(timestamp)

Gets relative time string (e.g., "2 hours ago").

```typescript
import { getRelativeTime } from '@/hooks/useDashboard';

const relative = getRelativeTime('2024-01-15T08:00:00Z'); // "2 hours ago"
```

### Status Management

#### getStatusColorClass(status)

Returns Tailwind CSS classes for status indicators.

```typescript
import { getStatusColorClass } from '@/hooks/useDashboard';

const colorClass = getStatusColorClass('completed'); // "bg-green-100 text-green-800"
```

#### getStatusIcon(status)

Returns appropriate icon for analysis status.

```typescript
import { getStatusIcon } from '@/hooks/useDashboard';

const icon = getStatusIcon('processing'); // "⏳"
```

### Analytics Utilities

#### calculateSuccessRate(completed, total)

Calculates success rate percentage.

```typescript
import { calculateSuccessRate } from '@/hooks/useDashboard';

const rate = calculateSuccessRate(85, 100); // 85
```

#### calculateTrendPercentage(current, previous)

Calculates trend percentage with direction indicator.

```typescript
import { calculateTrendPercentage } from '@/hooks/useDashboard';

const trend = calculateTrendPercentage(120, 100); 
// { value: 20, isPositive: true }
```

#### formatResponseTime(ms)

Formats milliseconds to human-readable time.

```typescript
import { formatResponseTime } from '@/hooks/useDashboard';

const formatted = formatResponseTime(2500); // "2.5s"
```

## Advanced Usage Patterns

### Custom Hook with Filtering

```typescript
import { useAnalysesList } from '@/hooks/useDashboard';
import { useMemo, useState } from 'react';

export function useFilteredAnalyses() {
  const [filters, setFilters] = useState({
    status: 'all',
    dateRange: 'all',
    search: ''
  });

  const { data, loading, error, refetch } = useAnalysesList({
    page: 1,
    limit: 50,
    status: filters.status !== 'all' ? filters.status : undefined
  });

  const filteredAnalyses = useMemo(() => {
    if (!data?.analyses) return [];
    
    return data.analyses.filter(analysis => {
      const matchesSearch = !filters.search || 
        analysis.summary?.toLowerCase().includes(filters.search.toLowerCase());
      
      const matchesDate = filters.dateRange === 'all' || 
        isInDateRange(analysis.created_at, filters.dateRange);
      
      return matchesSearch && matchesDate;
    });
  }, [data?.analyses, filters]);

  return {
    analyses: filteredAnalyses,
    loading,
    error,
    filters,
    setFilters,
    refetch
  };
}
```

### Combining Multiple Hooks

```typescript
export default function CompleteDashboard() {
  const dashboard = useDashboard();
  const analyses = useAnalysesList({ limit: 5 });
  const statistics = useDashboardStatistics();

  const isLoading = dashboard.loading || analyses.loading || statistics.loading;
  const hasError = dashboard.error || analyses.error || statistics.error;

  if (isLoading) return <CompleteDashboardSkeleton />;
  if (hasError) return <DashboardError />;

  return (
    <div>
      <DashboardOverview data={dashboard.data} />
      <RecentAnalyses analyses={analyses.data?.analyses} />
      <StatisticsPanel data={statistics.data} />
    </div>
  );
}
```

### Error Recovery Pattern

```typescript
export default function ResilientDashboard() {
  const { data, loading, error, refetch } = useDashboard();
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  const handleRetry = useCallback(async () => {
    if (retryCount < maxRetries) {
      setRetryCount(prev => prev + 1);
      await refetch();
    }
  }, [refetch, retryCount]);

  if (error && retryCount >= maxRetries) {
    return <FatalErrorState />;
  }

  if (error) {
    return (
      <ErrorStateWithRetry 
        error={error} 
        onRetry={handleRetry}
        retryCount={retryCount}
        maxRetries={maxRetries}
      />
    );
  }

  return <DashboardContent data={data} loading={loading} />;
}
```

## Performance Considerations

### Memoization

All hooks use `useCallback` for stable function references:

```typescript
const fetchDashboard = useCallback(async () => {
  // Fetch logic
}, []); // Empty dependency array ensures stable reference
```

### Avoiding Unnecessary Rerenders

Hooks return stable object references when data hasn't changed:

```typescript
const { data } = useDashboard();
// `data` reference only changes when actual data changes
```

### Memory Management

Hooks properly clean up async operations:

```typescript
useEffect(() => {
  let cancelled = false;
  
  const fetchData = async () => {
    try {
      const result = await apiCall();
      if (!cancelled) {
        setData(result);
      }
    } catch (error) {
      if (!cancelled) {
        setError(error);
      }
    }
  };

  fetchData();

  return () => {
    cancelled = true;
  };
}, []);
```

## Testing

### Unit Testing Hook Behavior

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useDashboard } from '@/hooks/useDashboard';

describe('useDashboard', () => {
  it('should fetch dashboard data on mount', async () => {
    const { result } = renderHook(() => useDashboard());

    expect(result.current.loading).toBe(true);
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeDefined();
    });
  });

  it('should handle errors gracefully', async () => {
    // Mock API error
    jest.mocked(dashboardApi.getDashboard).mockRejectedValue(
      new Error('API Error')
    );

    const { result } = renderHook(() => useDashboard());

    await waitFor(() => {
      expect(result.current.error).toBe('API Error');
      expect(result.current.data).toBeNull();
    });
  });
});
```

### Integration Testing

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import DashboardPage from './DashboardPage';

describe('Dashboard Integration', () => {
  it('should display dashboard data after loading', async () => {
    render(<DashboardPage />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Total Analyses')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument(); // Mock data value
    });
  });
});
```

## Migration Guide

### From Static Data

**Before:**
```typescript
const mockData = {
  total_analyses: 42,
  completed_analyses: 38,
  // ...
};

return <StatsCard data={mockData} />;
```

**After:**
```typescript
const { data, loading, error } = useDashboard();

if (loading) return <LoadingState />;
if (error) return <ErrorState />;

return <StatsCard data={data?.overview} />;
```

### Adding Error Boundaries

Wrap dashboard components in error boundaries:

```typescript
<ErrorBoundary fallback={<DashboardErrorFallback />}>
  <DashboardPage />
</ErrorBoundary>
```

## Best Practices

1. **Always handle loading and error states**
2. **Use memoization for expensive computations**
3. **Implement proper error boundaries**
4. **Cache API responses when appropriate**
5. **Provide manual refresh capabilities**
6. **Use TypeScript for type safety**
7. **Test hook behavior in isolation**
8. **Follow React hooks rules consistently**