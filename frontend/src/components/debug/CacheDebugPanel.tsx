'use client';

import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Database, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  TrendingDown,
  Info,
  BarChart3,
  Trash2,
  Eye,
  EyeOff
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useCacheDebug } from '@/hooks/useDashboard';

/**
 * Cache Debug Panel - Development only component for cache inspection and management
 * Only renders in development mode
 */
export function CacheDebugPanel() {
  const [isVisible, setIsVisible] = useState(false);
  const [consistencyResult, setConsistencyResult] = useState<any>(null);
  const { debugInfo, loading, error, fetchCacheInfo, refreshCache, validateConsistency } = useCacheDebug();

  // Only show in development
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') {
      return;
    }
    
    // Auto-fetch cache info on mount
    fetchCacheInfo();
  }, [fetchCacheInfo]);

  // Don't render in production
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const handleConsistencyCheck = async () => {
    const result = await validateConsistency();
    setConsistencyResult(result);
  };

  const handleRefreshCache = async (pattern?: string) => {
    await refreshCache(pattern);
    // Re-fetch cache info after refresh
    setTimeout(fetchCacheInfo, 1000);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

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

  return (
    <>
      {/* Debug Toggle Button - Fixed position */}
      <div className="fixed bottom-4 left-4 z-50">
        <Button
          onClick={() => setIsVisible(!isVisible)}
          variant="outline"
          size="sm"
          className="bg-orange-600 text-white hover:bg-orange-700 border-orange-600 shadow-lg"
        >
          <Database className="w-4 h-4 mr-1" />
          Cache Debug
          {isVisible ? <EyeOff className="w-4 h-4 ml-1" /> : <Eye className="w-4 h-4 ml-1" />}
        </Button>
      </div>

      {/* Debug Panel */}
      {isVisible && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Cache Debug Panel</h2>
                  <p className="text-sm text-gray-600">Development mode only - Cache inspection and management</p>
                </div>
                <Button
                  onClick={() => setIsVisible(false)}
                  variant="outline"
                  size="sm"
                >
                  Close
                </Button>
              </div>

              {/* Error State */}
              {error && (
                <Card className="mb-6">
                  <CardContent className="py-4">
                    <div className="flex items-center space-x-3 text-red-600">
                      <AlertTriangle className="w-5 h-5" />
                      <span>{error}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Quick Actions */}
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <RefreshCw className="w-5 h-5 mr-2" />
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <Button
                      onClick={() => fetchCacheInfo()}
                      disabled={loading}
                      variant="outline"
                      size="sm"
                    >
                      <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                      Refresh Info
                    </Button>
                    
                    <Button
                      onClick={() => handleRefreshCache()}
                      disabled={loading}
                      variant="outline"
                      size="sm"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Clear All Cache
                    </Button>
                    
                    <Button
                      onClick={() => handleRefreshCache('dashboard:*')}
                      disabled={loading}
                      variant="outline"
                      size="sm"
                    >
                      <RefreshCw className="w-4 h-4 mr-1" />
                      Refresh Dashboard
                    </Button>
                    
                    <Button
                      onClick={handleConsistencyCheck}
                      disabled={loading}
                      variant="outline"
                      size="sm"
                    >
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Check Consistency
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Cache Statistics */}
                {debugInfo && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <BarChart3 className="w-5 h-5 mr-2" />
                        Cache Statistics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-blue-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">{debugInfo.total_keys}</div>
                          <div className="text-sm text-blue-700">Total Keys</div>
                        </div>
                        
                        {debugInfo.cache_stats && (
                          <div className="text-center p-3 bg-green-50 rounded-lg">
                            <div className="text-2xl font-bold text-green-600">
                              {Math.round(debugInfo.cache_stats.hit_ratio * 100)}%
                            </div>
                            <div className="text-sm text-green-700">Hit Ratio</div>
                          </div>
                        )}
                      </div>
                      
                      {debugInfo.cache_stats && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Cache Hits:</span>
                            <span className="font-medium text-green-600">{debugInfo.cache_stats.hits}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Cache Misses:</span>
                            <span className="font-medium text-red-600">{debugInfo.cache_stats.misses}</span>
                          </div>
                          {debugInfo.memory_usage && (
                            <div className="flex justify-between text-sm">
                              <span>Memory Usage:</span>
                              <span className="font-medium">{debugInfo.memory_usage}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Cache Breakdown */}
                {debugInfo?.pattern_breakdown && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <Database className="w-5 h-5 mr-2" />
                        Cache Pattern Breakdown
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Object.entries(debugInfo.pattern_breakdown).map(([pattern, count]) => (
                          <div key={pattern} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span className="text-sm font-mono">{pattern}</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium">{count as number}</span>
                              <Button
                                onClick={() => handleRefreshCache(pattern)}
                                disabled={loading}
                                variant="outline"
                                size="sm"
                              >
                                <RefreshCw className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Consistency Check Results */}
              {consistencyResult && (
                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      {consistencyResult.consistent ? (
                        <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 mr-2 text-red-600" />
                      )}
                      Consistency Check Results
                    </CardTitle>
                    <CardDescription>
                      Checked {consistencyResult.total_checked} cache entries
                      {consistencyResult.consistent ? ' - All consistent!' : ` - Found ${consistencyResult.inconsistencies?.length} issues`}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {consistencyResult.consistent ? (
                      <div className="text-center py-8">
                        <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
                        <p className="text-green-700 font-medium">All cache data is consistent!</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {consistencyResult.inconsistencies?.map((issue: any, index: number) => (
                          <div key={index} className={`p-3 rounded-lg border ${getSeverityColor('medium')}`}>
                            <div className="font-medium">{issue.key}</div>
                            <div className="text-sm">{issue.issue}</div>
                          </div>
                        ))}
                        
                        {consistencyResult.recommendations?.length > 0 && (
                          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                            <h4 className="font-medium text-blue-900 mb-2">Recommendations:</h4>
                            <ul className="text-sm text-blue-800 space-y-1">
                              {consistencyResult.recommendations.map((rec: string, index: number) => (
                                <li key={index}>• {rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* User Cache Breakdown */}
              {debugInfo?.user_keys && Object.keys(debugInfo.user_keys).length > 0 && (
                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle>User Cache Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(debugInfo.user_keys).map(([userId, count]) => (
                        <div key={userId} className="flex justify-between text-sm">
                          <span className="font-mono">{userId}</span>
                          <span className="font-medium">{count as number} keys</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}