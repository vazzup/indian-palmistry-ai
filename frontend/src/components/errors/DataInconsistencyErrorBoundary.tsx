'use client';

import React, { Component, ReactNode } from 'react';
import { 
  AlertTriangle, 
  RefreshCw, 
  Shield, 
  Database,
  CheckCircle,
  Info
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cacheApi } from '@/lib/api';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  isRecovering: boolean;
  cacheCleared: boolean;
  retryCount: number;
}

/**
 * Error boundary specifically designed for handling data inconsistency errors
 * Provides recovery options including cache clearing and data refresh
 */
export class DataInconsistencyErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      isRecovering: false,
      cacheCleared: false,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Data inconsistency error caught:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error details for debugging
    this.logErrorDetails(error, errorInfo);
  }

  private logErrorDetails = (error: Error, errorInfo: React.ErrorInfo) => {
    const errorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // In development, log to console
    if (process.env.NODE_ENV === 'development') {
      console.group('🔍 Data Inconsistency Error Details');
      console.error('Error:', error);
      console.info('Component Stack:', errorInfo.componentStack);
      console.info('Full Details:', errorDetails);
      console.groupEnd();
    }

    // You could send this to a logging service in production
    // logToService(errorDetails);
  };

  private handleRetry = async () => {
    if (this.state.retryCount >= this.maxRetries) {
      return;
    }

    this.setState({ 
      isRecovering: true,
      retryCount: this.state.retryCount + 1
    });

    try {
      // Simple retry - just reset the error boundary
      setTimeout(() => {
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          isRecovering: false
        });
      }, 1000);
    } catch (error) {
      console.error('Retry failed:', error);
      this.setState({ isRecovering: false });
    }
  };

  private handleClearCacheAndRetry = async () => {
    this.setState({ isRecovering: true });

    try {
      // Clear all cache
      await cacheApi.refreshCache();
      
      this.setState({ cacheCleared: true });
      
      // Wait a moment for cache to clear, then retry
      setTimeout(() => {
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          isRecovering: false,
          retryCount: 0
        });
      }, 2000);
    } catch (error) {
      console.error('Cache clear failed:', error);
      this.setState({ isRecovering: false });
    }
  };

  private handleForceRefresh = () => {
    // Force a hard refresh of the page
    window.location.reload();
  };

  private getErrorCategory = (error: Error): 'data_mismatch' | 'cache_stale' | 'network_error' | 'unknown' => {
    const message = error.message.toLowerCase();
    
    if (message.includes('mismatch') || message.includes('inconsistent') || message.includes('count')) {
      return 'data_mismatch';
    }
    if (message.includes('cache') || message.includes('stale') || message.includes('outdated')) {
      return 'cache_stale';
    }
    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return 'network_error';
    }
    
    return 'unknown';
  };

  private getErrorRecommendations = (category: string): string[] => {
    switch (category) {
      case 'data_mismatch':
        return [
          'Clear cache to sync data between dashboard and analyses',
          'Check if recent actions are still processing',
          'Verify network connection is stable'
        ];
      case 'cache_stale':
        return [
          'Clear browser cache and refresh the page',
          'Use the "Clear Cache" button to invalidate stale data',
          'Check if the server cache needs updating'
        ];
      case 'network_error':
        return [
          'Check your internet connection',
          'Try refreshing the page',
          'Verify the server is accessible'
        ];
      default:
        return [
          'Try refreshing the page',
          'Clear cache if the problem persists',
          'Contact support if errors continue'
        ];
    }
  };

  render() {
    if (this.state.hasError) {
      const errorCategory = this.getErrorCategory(this.state.error!);
      const recommendations = this.getErrorRecommendations(errorCategory);
      const canRetry = this.state.retryCount < this.maxRetries;

      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-4">
          <Card className="max-w-lg w-full">
            <CardHeader>
              <CardTitle className="flex items-center text-red-600">
                <AlertTriangle className="w-5 h-5 mr-2" />
                Data Inconsistency Detected
              </CardTitle>
              <CardDescription>
                There appears to be a mismatch in your dashboard data. Don't worry - this is usually fixable.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Error Details */}
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800 font-medium">
                  Error Type: {errorCategory.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
                <p className="text-xs text-red-600 mt-1">
                  {this.state.error?.message}
                </p>
              </div>

              {/* Recommendations */}
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900 flex items-center">
                  <Info className="w-4 h-4 mr-1" />
                  Recommended Actions:
                </h4>
                <ul className="space-y-1">
                  {recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start">
                      <span className="inline-block w-1 h-1 bg-gray-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recovery Actions */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {canRetry && (
                  <Button
                    onClick={this.handleRetry}
                    disabled={this.state.isRecovering}
                    variant="outline"
                  >
                    {this.state.isRecovering ? (
                      <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4 mr-1" />
                    )}
                    Retry ({this.maxRetries - this.state.retryCount} left)
                  </Button>
                )}

                <Button
                  onClick={this.handleClearCacheAndRetry}
                  disabled={this.state.isRecovering}
                  variant="outline"
                  className="text-orange-600 border-orange-300 hover:bg-orange-50"
                >
                  {this.state.isRecovering ? (
                    <Database className="w-4 h-4 mr-1" />
                  ) : (
                    <Shield className="w-4 h-4 mr-1" />
                  )}
                  Clear Cache & Retry
                </Button>

                <Button
                  onClick={this.handleForceRefresh}
                  disabled={this.state.isRecovering}
                  className="sm:col-span-2"
                >
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Force Page Refresh
                </Button>
              </div>

              {/* Recovery Status */}
              {this.state.isRecovering && (
                <div className="flex items-center justify-center p-3 bg-blue-50 rounded-lg">
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin text-blue-600" />
                  <span className="text-sm text-blue-800">
                    {this.state.cacheCleared ? 'Cache cleared, retrying...' : 'Attempting recovery...'}
                  </span>
                </div>
              )}

              {!canRetry && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    Maximum retry attempts reached. Try clearing cache or refreshing the page.
                  </p>
                </div>
              )}

              {/* Debug Info (Development Only) */}
              {process.env.NODE_ENV === 'development' && (
                <details className="mt-4">
                  <summary className="text-xs text-gray-500 cursor-pointer">
                    Debug Information (Dev Only)
                  </summary>
                  <div className="mt-2 p-2 bg-gray-100 rounded text-xs font-mono">
                    <div>Error: {this.state.error?.message}</div>
                    <div>Stack: {this.state.error?.stack?.split('\n')[0]}</div>
                    <div>Retry Count: {this.state.retryCount}/{this.maxRetries}</div>
                    <div>Timestamp: {new Date().toISOString()}</div>
                  </div>
                </details>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component for wrapping components with data inconsistency error handling
 */
export function withDataInconsistencyErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundaryComponent(props: P) {
    return (
      <DataInconsistencyErrorBoundary fallback={fallback}>
        <WrappedComponent {...props} />
      </DataInconsistencyErrorBoundary>
    );
  };
}

/**
 * Hook for manually triggering error boundary (for testing or error simulation)
 */
export function useErrorBoundary() {
  const [, setState] = React.useState();
  
  return React.useCallback((error: Error) => {
    setState(() => {
      throw error;
    });
  }, []);
}