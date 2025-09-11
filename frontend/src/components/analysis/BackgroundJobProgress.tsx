'use client';

import React from 'react';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { getRandomMessage } from '@/lib/cultural-theme';
import { useAnalysisJobPolling } from '@/lib/redis-jobs';
import type { JobStatus } from '@/types';

interface BackgroundJobProgressProps {
  analysisId: number;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

export const BackgroundJobProgress: React.FC<BackgroundJobProgressProps> = ({
  analysisId,
  onComplete,
  onError,
}) => {
  const { status, isPolling, stopPolling } = useAnalysisJobPolling({
    analysisId,
    onComplete,
    onError,
  });
  const [messages, setMessages] = React.useState({
    queued: 'Queuing your analysis...',
    processing: 'Analyzing your palm...',
    completed: 'Analysis complete!',
    failed: 'Analysis failed',
  });
  
  // Set random messages on client side to avoid hydration mismatch
  React.useEffect(() => {
    setMessages({
      queued: getRandomMessage('loading'),
      processing: getRandomMessage('loading'),
      completed: getRandomMessage('completion'),
      failed: 'Analysis failed', // No error messages in cultural-theme
    });
  }, []);
  
  // Completion and errors are handled by the polling hook
  // No need for duplicate logic here
  
  const getStatusIcon = () => {
    if (!status) return <Clock className="w-6 h-6 text-gray-400" />;
    
    switch (status.status) {
      case 'queued':
        return <Clock className="w-6 h-6 text-orange-500" />;
      case 'processing':
        return <Spinner size="md" type="minimal" />;
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Clock className="w-6 h-6 text-gray-400" />;
    }
  };
  
  const getStatusMessage = () => {
    if (!status) return 'Initializing...';
    return messages[status.status as keyof typeof messages] || 'Processing...';
  };
  
  const getProgressPercentage = () => {
    if (!status) return 0;
    
    switch (status.status) {
      case 'queued':
        return 10;
      case 'processing':
        return status.progress || 50;
      case 'completed':
        return 100;
      case 'failed':
        return 0;
      default:
        return 0;
    }
  };
  
  const isComplete = status?.status === 'completed';
  const isFailed = status?.status === 'failed';
  const isActive = isPolling && !isComplete && !isFailed;
  
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardContent className="p-6">
        <div className="text-center space-y-6">
          {/* Status icon */}
          <div className="flex justify-center">
            {getStatusIcon()}
          </div>
          
          {/* Title */}
          <div className="space-y-2">
            <h3 className="text-lg font-medium text-gray-900">
              {isComplete ? 'Analysis Complete!' : 
               isFailed ? 'Analysis Failed' : 
               'Reading Your Palm'}
            </h3>
            
            <p className="text-sm text-gray-600">
              {getStatusMessage()}
            </p>
          </div>
          
          {/* Progress bar */}
          {!isFailed && (
            <div className="space-y-2">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-500 ${
                    isComplete ? 'bg-green-500' : 'bg-orange-500'
                  }`}
                  style={{ width: `${getProgressPercentage()}%` }}
                />
              </div>
              
              <div className="text-xs text-gray-500">
                {getProgressPercentage()}% complete
              </div>
            </div>
          )}
          
          {/* Additional details */}
          {status && (
            <div className="text-xs text-gray-400 space-y-1">
              <div>Status: {status.status.toUpperCase()}</div>
              {isActive && (
                <div className="flex items-center justify-center gap-1">
                  <div className="w-1 h-1 bg-orange-400 rounded-full animate-bounce" />
                  <div className="w-1 h-1 bg-orange-400 rounded-full animate-bounce delay-75" />
                  <div className="w-1 h-1 bg-orange-400 rounded-full animate-bounce delay-150" />
                </div>
              )}
            </div>
          )}
          
          {/* Error details */}
          {status?.error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">
                {status.error}
              </p>
            </div>
          )}
          
          {/* Cultural encouragement */}
          {isActive && (
            <div className="bg-orange-50 border border-orange-200 rounded-md p-3">
              <p className="text-xs text-orange-700">
                Ancient wisdom meets modern technology
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};