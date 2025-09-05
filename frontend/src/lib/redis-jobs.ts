/**
 * @fileoverview Background job polling system for AI analysis
 * Provides React hooks for real-time job status updates
 */

import { useEffect, useState } from 'react';
import { analysisApi } from './api';
import type { JobStatus } from '@/types';

/**
 * Props for the analysis job polling hook
 */
interface UseAnalysisJobPollingProps {
  /** Analysis ID to poll for status updates */
  analysisId: number;
  /** Callback fired when job completes successfully */
  onComplete?: (result: any) => void;
  /** Callback fired when job fails */
  onError?: (error: string) => void;
  /** Polling interval in milliseconds (default: 2000) */
  pollInterval?: number;
}

/**
 * React hook for polling analysis job status with automatic cleanup
 * Handles the background AI analysis workflow with real-time updates
 * 
 * @param props - Polling configuration and callbacks
 * @returns Object with current status, polling state, and control functions
 * 
 * @example
 * ```tsx
 * const { status, isPolling, stopPolling } = useAnalysisJobPolling({
 *   analysisId: analysis.id,
 *   onComplete: (result) => navigateToResults(result),
 *   onError: (error) => showErrorMessage(error),
 *   pollInterval: 3000
 * });
 * ```
 */
export function useAnalysisJobPolling({
  analysisId,
  onComplete,
  onError,
  pollInterval = 2000,
}: UseAnalysisJobPollingProps) {
  const [status, setStatus] = useState<JobStatus>({ status: 'queued' });
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    if (!analysisId || !isPolling) return;

    const pollStatus = async () => {
      try {
        const response = await analysisApi.getAnalysisStatus(analysisId.toString());
        console.log('Polling status for analysis', analysisId, ':', response);
        
        setStatus({
          status: response.status as 'queued' | 'processing' | 'completed' | 'failed',
          result: response.result,
          // Fix: Use correct field name from backend API response
          error: response.error_message
        });

        if (response.status === 'completed') {
          console.log('Analysis completed! Calling onComplete with:', response.result);
          setIsPolling(false);
          onComplete?.(response.result);
        } else if (response.status === 'failed') {
          console.log('Analysis failed! Calling onError with:', response.error_message);
          setIsPolling(false);
          // Fix: Use correct field name from backend API response
          onError?.(response.error_message || 'Analysis failed');
        }
      } catch (error) {
        console.error('Error polling job status:', error);
        setIsPolling(false);
        onError?.('Failed to check analysis status');
      }
    };

    // Initial poll
    pollStatus();

    // Set up polling interval
    const interval = setInterval(pollStatus, pollInterval);

    return () => {
      clearInterval(interval);
    };
  }, [analysisId, isPolling, pollInterval, onComplete, onError]);

  const stopPolling = () => {
    setIsPolling(false);
  };

  return {
    status,
    isPolling,
    stopPolling,
  };
}