/**
 * @fileoverview Dashboard data hook for fetching and managing dashboard data
 * Provides loading states, error handling, and data caching for dashboard components
 */

import { useState, useEffect, useCallback } from 'react';
import { dashboardApi } from '@/lib/api';

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
 * Hook for managing dashboard data
 */
export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const dashboardData = await dashboardApi.getDashboard();
      setData(dashboardData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    data,
    loading,
    error,
    refetch: fetchDashboard,
  };
}

/**
 * Hook for managing analyses list with pagination and filtering
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

  const fetchAnalyses = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const analysesData = await dashboardApi.getAnalyses(options);
      setData(analysesData);
    } catch (err) {
      console.error('Failed to fetch analyses data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analyses');
    } finally {
      setLoading(false);
    }
  }, [options]);

  useEffect(() => {
    fetchAnalyses();
  }, [fetchAnalyses]);

  return {
    data,
    loading,
    error,
    refetch: fetchAnalyses,
  };
}

/**
 * Hook for fetching dashboard statistics
 */
export function useDashboardStatistics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const statisticsData = await dashboardApi.getDashboardStatistics();
      setData(statisticsData);
    } catch (err) {
      console.error('Failed to fetch dashboard statistics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return {
    data,
    loading,
    error,
    refetch: fetchStatistics,
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