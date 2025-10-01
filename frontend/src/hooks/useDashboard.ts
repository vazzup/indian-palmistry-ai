/**
 * @fileoverview Dashboard data hook for fetching and managing dashboard data
 * Provides loading states, error handling, and data caching for dashboard components
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardApi, cacheApi, conversationsApi } from '@/lib/api';

/**
 * Dashboard overview data structure
 */
export interface DashboardOverview {
  total_analyses: number;
  completed_analyses: number;
  total_conversations: number;
  success_rate: number;
}

/**
 * Recent activity item structure
 */
export interface RecentActivity {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  analysis_id?: string;
}

/**
 * Dashboard analytics data structure
 */
export interface DashboardAnalytics {
  analyses_by_month: Array<{ month: string; count: number }>;
  success_rate_trend: Array<{ date: string; rate: number }>;
  avg_response_time: string;
  popular_features: Array<{ feature: string; usage: number }>;
}

/**
 * Complete dashboard data structure
 */
export interface DashboardData {
  overview: DashboardOverview;
  recent_activity: RecentActivity[];
  analytics: DashboardAnalytics;
}

/**
 * Analysis data structure for listings
 */
export interface AnalysisListItem {
  id: string;
  created_at: string;
  status: 'completed' | 'processing' | 'failed';
  summary?: string;
  conversation_count: number;
  left_image_url?: string;
  right_image_url?: string;
  cost?: number;
}

/**
 * Paginated analyses response structure
 */
export interface AnalysesListResponse {
  analyses: AnalysisListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

/**
 * Data consistency validation result
 */
export interface ConsistencyValidation {
  isConsistent: boolean;
  issues: Array<{
    type: 'count_mismatch' | 'status_mismatch' | 'data_missing' | 'stale_data';
    description: string;
    severity: 'low' | 'medium' | 'high';
    recommendation: string;
  }>;
  lastChecked: string;
  confidence: number; // 0-100
}

/**
 * Enhanced hook for managing dashboard data with cache management
 */
export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [consistencyValidation, setConsistencyValidation] = useState<ConsistencyValidation | null>(null);
  const [staleness, setStaleness] = useState<'fresh' | 'stale' | 'very_stale'>('fresh');
  
  const lastFetchTime = useRef<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate data staleness based on last fetch time
  const updateStaleness = useCallback(() => {
    if (!lastFetchTime.current) return;
    
    const now = new Date();
    const timeDiff = now.getTime() - lastFetchTime.current.getTime();
    const minutesDiff = timeDiff / (1000 * 60);
    
    if (minutesDiff > 30) {
      setStaleness('very_stale');
    } else if (minutesDiff > 10) {
      setStaleness('stale');
    } else {
      setStaleness('fresh');
    }
  }, []);

  // Set up staleness monitoring
  useEffect(() => {
    intervalRef.current = setInterval(updateStaleness, 60000); // Check every minute
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [updateStaleness]);

  const fetchDashboard = useCallback(async (options?: { skipCache?: boolean }) => {
    try {
      setLoading(true);
      setError(null);
      
      // If skipCache is true, refresh cache first
      if (options?.skipCache) {
        setIsRefreshing(true);
        try {
          await cacheApi.refreshCachePattern('dashboard:*');
        } catch (cacheError) {
          console.warn('Cache refresh failed, continuing with regular fetch:', cacheError);
        }
      }
      
      const dashboardData = await dashboardApi.getDashboard();
      setData(dashboardData);
      lastFetchTime.current = new Date();
      setLastRefresh(new Date());
      setStaleness('fresh');
      
      // Clear any previous consistency validation when data is refreshed
      if (options?.skipCache) {
        setConsistencyValidation(null);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard data';
      setError(errorMessage);
      
      // For authentication errors, don't set fallback data - let the layout handle redirect
      if (errorMessage.includes('log in')) {
        setData(null);
      } else {
        // For other errors, provide fallback empty data to prevent crashes
        setData(createEmptyDashboardData());
      }
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Validate data consistency with analyses endpoint
  const validateConsistency = useCallback(async (): Promise<ConsistencyValidation> => {
    try {
      // Get both dashboard and analyses data for comparison
      const [dashboardData, analysesData, cacheValidation] = await Promise.allSettled([
        dashboardApi.getDashboard(),
        dashboardApi.getAnalyses({ limit: 1 }), // Just get count
        cacheApi.validateCacheConsistency()
      ]);
      
      const issues: ConsistencyValidation['issues'] = [];
      let confidence = 100;
      
      // Check if dashboard total matches analyses total
      if (dashboardData.status === 'fulfilled' && analysesData.status === 'fulfilled') {
        const dashboardTotal = dashboardData.value.overview.total_analyses;
        const analysesTotal = analysesData.value.total;
        
        if (dashboardTotal !== analysesTotal) {
          issues.push({
            type: 'count_mismatch',
            description: `Dashboard shows ${dashboardTotal} analyses, but analyses page shows ${analysesTotal}`,
            severity: 'high',
            recommendation: 'Refresh the dashboard cache to sync data'
          });
          confidence -= 30;
        }
        
        // Check for completed analyses consistency
        const dashboardCompleted = dashboardData.value.overview.completed_analyses;
        const analysesCompleted = analysesData.value.analyses.filter((a: any) => a.status === 'completed').length;
        
        if (Math.abs(dashboardCompleted - analysesCompleted) > 1 && analysesData.value.total > 0) {
          issues.push({
            type: 'status_mismatch',
            description: `Completed analyses count mismatch detected`,
            severity: 'medium',
            recommendation: 'Check for recently updated analyses status'
          });
          confidence -= 15;
        }
      } else {
        issues.push({
          type: 'data_missing',
          description: 'Unable to fetch data for consistency check',
          severity: 'high',
          recommendation: 'Check network connection and try again'
        });
        confidence -= 50;
      }
      
      // Include cache validation results
      if (cacheValidation.status === 'fulfilled' && !cacheValidation.value.consistent) {
        cacheValidation.value.inconsistencies.forEach(inconsistency => {
          issues.push({
            type: 'stale_data',
            description: `Cache inconsistency: ${inconsistency.issue}`,
            severity: 'medium',
            recommendation: 'Refresh cache to resolve inconsistency'
          });
        });
        confidence -= 20;
      }
      
      // Check data staleness
      if (staleness === 'very_stale') {
        issues.push({
          type: 'stale_data',
          description: 'Dashboard data is over 30 minutes old',
          severity: 'low',
          recommendation: 'Refresh to get the latest data'
        });
        confidence -= 10;
      }
      
      const validation: ConsistencyValidation = {
        isConsistent: issues.length === 0,
        issues,
        lastChecked: new Date().toISOString(),
        confidence: Math.max(0, confidence)
      };
      
      setConsistencyValidation(validation);
      return validation;
    } catch (error) {
      console.error('Consistency validation failed:', error);
      const validation: ConsistencyValidation = {
        isConsistent: false,
        issues: [{
          type: 'data_missing',
          description: 'Consistency validation failed due to network or server error',
          severity: 'high',
          recommendation: 'Check connection and try refreshing the page'
        }],
        lastChecked: new Date().toISOString(),
        confidence: 0
      };
      setConsistencyValidation(validation);
      return validation;
    }
  }, [staleness]);

  // Force refresh cache and reload data
  const forceRefresh = useCallback(async () => {
    await fetchDashboard({ skipCache: true });
  }, [fetchDashboard]);

  // Auto-refresh data periodically (every 5 minutes)
  useEffect(() => {
    const autoRefreshInterval = setInterval(() => {
      if (!loading && !isRefreshing) {
        fetchDashboard();
      }
    }, 5 * 60 * 1000);
    
    return () => clearInterval(autoRefreshInterval);
  }, [fetchDashboard, loading, isRefreshing]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    data,
    loading,
    error,
    isRefreshing,
    lastRefresh,
    staleness,
    consistencyValidation,
    refetch: fetchDashboard,
    forceRefresh,
    validateConsistency,
  };
}

/**
 * Enhanced hook for managing analyses list with cache management
 */
export function useAnalysesList(options?: {
  page?: number;
  limit?: number;
  status?: string;
  sort?: string;
}) {
  const [data, setData] = useState<AnalysesListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchAnalyses = useCallback(async (skipCache?: boolean) => {
    try {
      setLoading(true);
      setError(null);
      
      // If skipCache is true, refresh cache first
      if (skipCache) {
        setIsRefreshing(true);
        try {
          await cacheApi.refreshCachePattern('analyses:*');
        } catch (cacheError) {
          console.warn('Cache refresh failed, continuing with regular fetch:', cacheError);
        }
      }
      
      const analysesData = await dashboardApi.getAnalyses(options);
      setData(analysesData);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to fetch analyses data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analyses');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [options]);

  // Force refresh with cache invalidation
  const forceRefresh = useCallback(async () => {
    await fetchAnalyses(true);
  }, [fetchAnalyses]);

  useEffect(() => {
    fetchAnalyses();
  }, [fetchAnalyses]);

  return {
    data,
    loading,
    error,
    isRefreshing,
    lastRefresh,
    refetch: fetchAnalyses,
    forceRefresh,
  };
}

/**
 * Enhanced hook for fetching dashboard statistics with cache management
 */
export function useDashboardStatistics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStatistics = useCallback(async (skipCache?: boolean) => {
    try {
      setLoading(true);
      setError(null);
      
      if (skipCache) {
        setIsRefreshing(true);
        try {
          await cacheApi.refreshCachePattern('statistics:*');
        } catch (cacheError) {
          console.warn('Statistics cache refresh failed:', cacheError);
        }
      }
      
      const statisticsData = await dashboardApi.getDashboardStatistics();
      setData(statisticsData);
    } catch (err) {
      console.error('Failed to fetch dashboard statistics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  const forceRefresh = useCallback(async () => {
    await fetchStatistics(true);
  }, [fetchStatistics]);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return {
    data,
    loading,
    error,
    isRefreshing,
    refetch: fetchStatistics,
    forceRefresh,
  };
}

/**
 * Utility function to transform backend analysis data to frontend format
 */
export function transformAnalysisData(backendAnalysis: any): AnalysisListItem {
  return {
    id: backendAnalysis.id,
    created_at: backendAnalysis.created_at,
    status: backendAnalysis.status,
    summary: backendAnalysis.summary,
    conversation_count: backendAnalysis.conversation_count || 0,
    left_image_url: backendAnalysis.left_image_url,
    right_image_url: backendAnalysis.right_image_url,
    cost: backendAnalysis.cost,
  };
}

/**
 * Utility function to format dates consistently
 */
export function formatAnalysisDate(dateString: string, includeTime = false): string {
  const date = new Date(dateString);
  const options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  };

  if (includeTime) {
    options.hour = '2-digit';
    options.minute = '2-digit';
  }

  return date.toLocaleDateString('en-US', options);
}

/**
 * Utility function to get status color classes
 */
export function getStatusColorClass(status: string): string {
  const normalizedStatus = status.toLowerCase();
  switch (normalizedStatus) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'processing':
      return 'bg-yellow-100 text-yellow-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Utility function to calculate success rate percentage
 */
export function calculateSuccessRate(completed: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
}

/**
 * Transform backend recent activity to frontend format
 */
export function transformRecentActivity(activity: any[]): RecentActivity[] {
  return activity.map((item: any) => ({
    id: item.id,
    type: item.type || 'unknown',
    message: item.message || item.description || 'Activity occurred',
    timestamp: item.timestamp || item.created_at,
    analysis_id: item.analysis_id,
  }));
}

/**
 * Transform backend analytics data to frontend format
 */
export function transformAnalyticsData(analytics: any): DashboardAnalytics {
  return {
    analyses_by_month: analytics.analyses_by_month || [],
    success_rate_trend: analytics.success_rate_trend || [],
    avg_response_time: analytics.avg_response_time || '--',
    popular_features: analytics.popular_features || [],
  };
}

/**
 * Get status icon component for different analysis statuses
 */
export function getStatusIcon(status: string) {
  const normalizedStatus = status.toLowerCase();
  switch (normalizedStatus) {
    case 'completed':
      return '✓';
    case 'processing':
      return '⏳';
    case 'failed':
      return '✗';
    default:
      return '◯';
  }
}

/**
 * Calculate trend percentage from current and previous values
 */
export function calculateTrendPercentage(current: number, previous: number): { value: number; isPositive: boolean } | undefined {
  if (previous === 0 || !previous) return undefined;
  
  const change = ((current - previous) / previous) * 100;
  return {
    value: Math.abs(Math.round(change)),
    isPositive: change >= 0,
  };
}

/**
 * Format response time from milliseconds to human readable format
 */
export function formatResponseTime(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

/**
 * Get relative time string (e.g., "2 hours ago")
 */
export function getRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 30) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  
  return formatAnalysisDate(timestamp);
}

/**
 * Validate and sanitize analysis data from backend
 */
export function sanitizeAnalysisData(analysis: any): AnalysisListItem {
  // Normalize status to lowercase for frontend consistency
  const normalizedStatus = analysis.status?.toLowerCase() || 'processing';
  const validStatuses = ['completed', 'processing', 'failed'];
  
  return {
    id: analysis.id?.toString() || 'unknown',
    created_at: analysis.created_at || analysis.createdAt || new Date().toISOString(),
    status: validStatuses.includes(normalizedStatus) 
      ? normalizedStatus as 'completed' | 'processing' | 'failed'
      : 'processing',
    summary: analysis.summary || analysis.description || undefined,
    conversation_count: Math.max(0, parseInt(analysis.conversation_count) || 0),
    left_image_url: analysis.left_image_url || analysis.leftImagePath,
    right_image_url: analysis.right_image_url || analysis.rightImagePath,
    cost: analysis.cost ? parseFloat(analysis.cost) : undefined,
  };
}

/**
 * Hook for cache debugging and management (development only)
 */
export function useCacheDebug() {
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCacheInfo = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const info = await cacheApi.getCacheDebug();
      setDebugInfo(info);
    } catch (err) {
      console.error('Failed to fetch cache debug info:', err);
      setError(err instanceof Error ? err.message : 'Failed to load cache info');
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshCache = useCallback(async (pattern?: string) => {
    try {
      setLoading(true);
      if (pattern) {
        await cacheApi.refreshCachePattern(pattern);
      } else {
        await cacheApi.refreshCache();
      }
      // Refresh debug info after cache refresh
      await fetchCacheInfo();
    } catch (err) {
      console.error('Failed to refresh cache:', err);
      setError(err instanceof Error ? err.message : 'Failed to refresh cache');
    } finally {
      setLoading(false);
    }
  }, [fetchCacheInfo]);

  const validateConsistency = useCallback(async () => {
    try {
      setLoading(true);
      const validation = await cacheApi.validateCacheConsistency();
      return validation;
    } catch (err) {
      console.error('Failed to validate cache consistency:', err);
      setError(err instanceof Error ? err.message : 'Failed to validate consistency');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    debugInfo,
    loading,
    error,
    fetchCacheInfo,
    refreshCache,
    validateConsistency,
  };
}

/**
 * Generate empty dashboard data for loading states
 */
export function createEmptyDashboardData(): DashboardData {
  return {
    overview: {
      total_analyses: 0,
      completed_analyses: 0,
      total_conversations: 0,
      success_rate: 0,
    },
    recent_activity: [],
    analytics: {
      analyses_by_month: [],
      success_rate_trend: [],
      avg_response_time: '--',
      popular_features: [],
    },
  };
}

/**
 * Conversation list item structure
 */
export interface ConversationListItem {
  id: string;
  analysis_id: string;
  title: string;
  message_count: number;
  last_message: {
    content: string;
    role: 'USER' | 'ASSISTANT';
    created_at: string;
  } | null;
  created_at: string;
  updated_at: string;
  analysis: {
    id: string;
    status: string;
    summary?: string;
  } | null;
}

/**
 * Paginated conversations response structure
 */
export interface ConversationsListResponse {
  conversations: ConversationListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

/**
 * Enhanced hook for managing user conversations list
 */
export function useConversationsList(options?: {
  page?: number;
  limit?: number;
  analysis_id?: string;
  sort?: string;
}) {
  const [data, setData] = useState<ConversationsListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchConversations = useCallback(async (skipCache?: boolean) => {
    try {
      setLoading(true);
      setError(null);

      // If skipCache is true, refresh cache first
      if (skipCache) {
        setIsRefreshing(true);
        try {
          await cacheApi.refreshCachePattern('conversations:*');
        } catch (cacheError) {
          console.warn('Cache refresh failed, continuing with regular fetch:', cacheError);
        }
      }

      console.log('[DEBUG] useConversationsList: Fetching conversations with options:', options);
      const conversationsData = await conversationsApi.getUserConversations(options);
      console.log('[DEBUG] useConversationsList: Received data:', {
        total: conversationsData.total,
        count: conversationsData.conversations?.length,
        conversations: conversationsData.conversations?.map(c => ({
          id: c.id,
          analysis_id: c.analysis_id,
          title: c.title,
          created_at: c.created_at
        }))
      });
      setData(conversationsData);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to fetch conversations data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [options]);

  // Force refresh with cache invalidation
  const forceRefresh = useCallback(async () => {
    await fetchConversations(true);
  }, [fetchConversations]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return {
    data,
    loading,
    error,
    isRefreshing,
    lastRefresh,
    refetch: fetchConversations,
    forceRefresh,
  };
}

/**
 * Hook for managing conversation messages
 */
export function useConversationMessages(analysisId: string, conversationId: string, options?: {
  page?: number;
  limit?: number;
}) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchMessages = useCallback(async (skipCache?: boolean) => {
    if (!conversationId || !analysisId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      if (skipCache) {
        setIsRefreshing(true);
        try {
          await cacheApi.refreshCachePattern(`conversation:${conversationId}:*`);
        } catch (cacheError) {
          console.warn('Messages cache refresh failed:', cacheError);
        }
      }
      
      const messagesData = await conversationsApi.getConversationMessages(analysisId, conversationId, options);
      setData(messagesData);
    } catch (err) {
      console.error('Failed to fetch conversation messages:', err);
      setError(err instanceof Error ? err.message : 'Failed to load messages');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [analysisId, conversationId, options]);

  const forceRefresh = useCallback(async () => {
    await fetchMessages(true);
  }, [fetchMessages]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  return {
    data,
    loading,
    error,
    isRefreshing,
    refetch: fetchMessages,
    forceRefresh,
  };
}

/**
 * Get data staleness indicator color and text
 */
export function getStalenessInfo(staleness: 'fresh' | 'stale' | 'very_stale') {
  switch (staleness) {
    case 'fresh':
      return { color: 'text-green-600', text: 'Up to date', icon: '✓' };
    case 'stale':
      return { color: 'text-yellow-600', text: 'May be outdated', icon: '⚠️' };
    case 'very_stale':
      return { color: 'text-red-600', text: 'Outdated data', icon: '⚠️' };
  }
}

/**
 * Format consistency validation for display
 */
export function formatConsistencyIssues(validation: ConsistencyValidation | null) {
  if (!validation) return null;
  
  const highIssues = validation.issues.filter(i => i.severity === 'high');
  const mediumIssues = validation.issues.filter(i => i.severity === 'medium');
  const lowIssues = validation.issues.filter(i => i.severity === 'low');
  
  return {
    hasIssues: validation.issues.length > 0,
    severity: highIssues.length > 0 ? 'high' : mediumIssues.length > 0 ? 'medium' : 'low',
    summary: `${highIssues.length} critical, ${mediumIssues.length} moderate, ${lowIssues.length} minor issues`,
    confidence: validation.confidence,
    recommendations: [...new Set(validation.issues.map(i => i.recommendation))],
  };
}