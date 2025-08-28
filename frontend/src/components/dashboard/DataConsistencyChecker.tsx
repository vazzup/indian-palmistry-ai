'use client';

import React, { useState, useCallback } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw, 
  Info,
  TrendingDown,
  TrendingUp,
  Loader2
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { dashboardApi, cacheApi } from '@/lib/api';
import { formatAnalysisDate } from '@/hooks/useDashboard';

interface ConsistencyIssue {
  type: 'count_mismatch' | 'status_mismatch' | 'timing_mismatch' | 'cache_stale';
  severity: 'low' | 'medium' | 'high';
  description: string;
  recommendation: string;
  details?: {
    expected?: any;
    actual?: any;
    difference?: number;
  };
}

interface ConsistencyCheckResult {
  isConsistent: boolean;
  issues: ConsistencyIssue[];
  checkedAt: string;
  confidence: number;
  metrics: {
    dashboardTotal: number;
    analysesTotal: number;
    dashboardCompleted: number;
    analysesCompleted: number;
    cacheInconsistencies: number;
  };
}

/**
 * Component for validating data consistency between dashboard and analyses
 * Provides detailed reporting and recommendations for resolving issues
 */
export function DataConsistencyChecker() {
  const [isChecking, setIsChecking] = useState(false);
  const [result, setResult] = useState<ConsistencyCheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoCheck, setAutoCheck] = useState(false);

  const performConsistencyCheck = useCallback(async (): Promise<ConsistencyCheckResult> => {
    const issues: ConsistencyIssue[] = [];
    let confidence = 100;

    try {
      // Fetch data from both endpoints simultaneously
      const [dashboardResponse, analysesResponse, cacheValidation] = await Promise.allSettled([
        dashboardApi.getDashboard(),
        dashboardApi.getAnalyses({ limit: 50 }), // Get more analyses for better validation
        cacheApi.validateCacheConsistency()
      ]);

      // Initialize metrics
      const metrics = {
        dashboardTotal: 0,
        analysesTotal: 0,
        dashboardCompleted: 0,
        analysesCompleted: 0,
        cacheInconsistencies: 0
      };

      // Validate dashboard data
      if (dashboardResponse.status === 'fulfilled') {
        metrics.dashboardTotal = dashboardResponse.value.overview.total_analyses;
        metrics.dashboardCompleted = dashboardResponse.value.overview.completed_analyses;
      } else {
        issues.push({
          type: 'cache_stale',
          severity: 'high',
          description: 'Failed to fetch dashboard data',
          recommendation: 'Check network connection and refresh dashboard'
        });
        confidence -= 40;
      }

      // Validate analyses data
      if (analysesResponse.status === 'fulfilled') {
        metrics.analysesTotal = analysesResponse.value.total;
        metrics.analysesCompleted = analysesResponse.value.analyses
          .filter((a: any) => a.status === 'completed').length;
      } else {
        issues.push({
          type: 'cache_stale',
          severity: 'high',
          description: 'Failed to fetch analyses data',
          recommendation: 'Check network connection and refresh analyses list'
        });
        confidence -= 40;
      }

      // Check total analyses count consistency
      if (dashboardResponse.status === 'fulfilled' && analysesResponse.status === 'fulfilled') {
        const totalDiff = Math.abs(metrics.dashboardTotal - metrics.analysesTotal);
        
        if (totalDiff > 0) {
          issues.push({
            type: 'count_mismatch',
            severity: totalDiff > 5 ? 'high' : totalDiff > 2 ? 'medium' : 'low',
            description: `Total analyses count mismatch: Dashboard shows ${metrics.dashboardTotal}, Analyses page shows ${metrics.analysesTotal}`,
            recommendation: 'Clear cache and refresh both dashboard and analyses to sync data',
            details: {
              expected: metrics.analysesTotal,
              actual: metrics.dashboardTotal,
              difference: totalDiff
            }
          });
          confidence -= (totalDiff > 5 ? 30 : totalDiff > 2 ? 20 : 10);
        }

        // Check completed analyses consistency
        const completedDiff = Math.abs(metrics.dashboardCompleted - metrics.analysesCompleted);
        
        if (completedDiff > 1) { // Allow for 1 difference due to timing
          issues.push({
            type: 'status_mismatch',
            severity: completedDiff > 3 ? 'high' : 'medium',
            description: `Completed analyses mismatch: Dashboard shows ${metrics.dashboardCompleted}, Analyses shows ${metrics.analysesCompleted}`,
            recommendation: 'This usually indicates cache staleness. Try refreshing the dashboard.',
            details: {
              expected: metrics.analysesCompleted,
              actual: metrics.dashboardCompleted,
              difference: completedDiff
            }
          });
          confidence -= (completedDiff > 3 ? 25 : 15);
        }

        // Check for logical inconsistencies
        if (metrics.dashboardCompleted > metrics.dashboardTotal) {
          issues.push({
            type: 'count_mismatch',
            severity: 'high',
            description: 'Dashboard shows more completed analyses than total analyses',
            recommendation: 'This indicates a serious data integrity issue. Contact support.'
          });
          confidence -= 40;
        }
      }

      // Validate cache consistency
      if (cacheValidation.status === 'fulfilled') {
        const cacheResult = cacheValidation.value;
        if (!cacheResult.consistent) {
          metrics.cacheInconsistencies = cacheResult.inconsistencies?.length || 0;
          
          cacheResult.inconsistencies?.forEach((inconsistency: any) => {
            issues.push({
              type: 'cache_stale',
              severity: 'medium',
              description: `Cache inconsistency in ${inconsistency.key}: ${inconsistency.issue}`,
              recommendation: 'Refresh cache to resolve this inconsistency'
            });
          });
          
          confidence -= Math.min(30, metrics.cacheInconsistencies * 5);
        }
      } else {
        issues.push({
          type: 'cache_stale',
          severity: 'low',
          description: 'Could not validate cache consistency',
          recommendation: 'Cache validation service may be temporarily unavailable'
        });
        confidence -= 5;
      }

      // Check for timing issues (data that seems too fresh or too stale)
      const now = new Date();
      if (dashboardResponse.status === 'fulfilled') {
        const recentActivity = dashboardResponse.value.recent_activity || [];
        const latestActivity = recentActivity[0];
        
        if (latestActivity && metrics.analysesTotal > 0) {
          const activityTime = new Date(latestActivity.timestamp);
          const timeDiff = now.getTime() - activityTime.getTime();
          const hoursDiff = timeDiff / (1000 * 60 * 60);
          
          if (hoursDiff > 24 && metrics.analysesCompleted > 0) {
            issues.push({
              type: 'timing_mismatch',
              severity: 'low',
              description: `Latest activity is over 24 hours old, but there are completed analyses`,
              recommendation: 'Check if recent analyses are being properly recorded in activity log'
            });
            confidence -= 5;
          }
        }
      }

      return {
        isConsistent: issues.length === 0,
        issues,
        checkedAt: now.toISOString(),
        confidence: Math.max(0, confidence),
        metrics
      };

    } catch (error) {
      console.error('Consistency check failed:', error);
      
      return {
        isConsistent: false,
        issues: [{
          type: 'cache_stale',
          severity: 'high',
          description: 'Consistency check failed due to network or server error',
          recommendation: 'Check your connection and try again'
        }],
        checkedAt: new Date().toISOString(),
        confidence: 0,
        metrics: {
          dashboardTotal: 0,
          analysesTotal: 0,
          dashboardCompleted: 0,
          analysesCompleted: 0,
          cacheInconsistencies: 0
        }
      };
    }
  }, []);

  const handleCheck = useCallback(async () => {
    setIsChecking(true);
    setError(null);
    
    try {
      const checkResult = await performConsistencyCheck();
      setResult(checkResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Consistency check failed');
    } finally {
      setIsChecking(false);
    }
  }, [performConsistencyCheck]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle className="w-4 h-4" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4" />;
      case 'low':
        return <Info className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  // Auto-check on mount if enabled
  React.useEffect(() => {
    if (autoCheck) {
      handleCheck();
    }
  }, [autoCheck, handleCheck]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            {result?.isConsistent ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            ) : result ? (
              <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            ) : (
              <RefreshCw className="w-5 h-5 text-gray-600 mr-2" />
            )}
            Data Consistency Check
          </div>
          <Button
            onClick={handleCheck}
            disabled={isChecking}
            variant="outline"
            size="sm"
          >
            {isChecking ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-1" />
            )}
            {isChecking ? 'Checking...' : 'Check Now'}
          </Button>
        </CardTitle>
        <CardDescription>
          Validates data consistency between dashboard and analyses
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-bold text-blue-600">{result.metrics.dashboardTotal}</div>
                <div className="text-xs text-blue-700">Dashboard Total</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-bold text-blue-600">{result.metrics.analysesTotal}</div>
                <div className="text-xs text-blue-700">Analyses Total</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-lg font-bold text-green-600">{result.confidence}%</div>
                <div className="text-xs text-green-700">Confidence</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-600">{result.issues.length}</div>
                <div className="text-xs text-gray-700">Issues</div>
              </div>
            </div>

            {/* Issues */}
            {result.issues.length > 0 ? (
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Issues Found:</h4>
                {result.issues.map((issue, index) => (
                  <div key={index} className={`p-3 rounded-lg border ${getSeverityColor(issue.severity)}`}>
                    <div className="flex items-start space-x-2">
                      {getSeverityIcon(issue.severity)}
                      <div className="flex-1">
                        <p className="font-medium text-sm">{issue.description}</p>
                        <p className="text-xs mt-1 opacity-80">{issue.recommendation}</p>
                        {issue.details && (
                          <div className="text-xs mt-2 space-y-1">
                            {issue.details.expected && (
                              <div>Expected: {issue.details.expected}</div>
                            )}
                            {issue.details.actual && (
                              <div>Actual: {issue.details.actual}</div>
                            )}
                            {issue.details.difference && (
                              <div>Difference: {issue.details.difference}</div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
                <p className="text-green-700 font-medium">All data is consistent!</p>
              </div>
            )}

            {/* Last Check */}
            <div className="text-xs text-gray-500 text-center">
              Last checked: {formatAnalysisDate(result.checkedAt, true)}
            </div>
          </div>
        )}

        {!result && !isChecking && (
          <div className="text-center py-6">
            <RefreshCw className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">Click "Check Now" to validate data consistency</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}