/**
 * @fileoverview Background job polling and real-time streaming system for AI analysis
 * Provides React hooks for real-time job status updates via polling and SSE
 */

import { useEffect, useState, useRef, useCallback } from 'react';
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

        setStatus({
          status: response.status as 'queued' | 'processing' | 'completed' | 'failed',
          result: response.result,
          error: response.error_message
        });

        if (response.status === 'completed') {
          setIsPolling(false);
          onComplete?.(response.result);
        } else if (response.status === 'failed') {
          setIsPolling(false);
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

/**
 * Props for the analysis job streaming hook
 */
interface UseAnalysisEventStreamProps {
  /** Analysis ID to stream status updates for */
  analysisId: number;
  /** Callback fired when job completes successfully */
  onComplete?: (result: any) => void;
  /** Callback fired when job fails */
  onError?: (error: string) => void;
  /** Whether to enable automatic fallback to polling if SSE fails (default: true) */
  enableFallback?: boolean;
  /** Maximum number of reconnection attempts before falling back (default: 3) */
  maxReconnectAttempts?: number;
  /** Delay between reconnection attempts in milliseconds (default: 2000) */
  reconnectDelay?: number;
}

/**
 * React hook for streaming analysis job status via Server-Sent Events with automatic fallback
 * Provides real-time updates for analysis progress using SSE, falling back to polling if needed
 *
 * @param props - Streaming configuration and callbacks
 * @returns Object with current status, streaming state, and control functions
 *
 * @example
 * ```tsx
 * const { status, isStreaming, disconnect } = useAnalysisEventStream({
 *   analysisId: analysis.id,
 *   onComplete: (result) => navigateToResults(result),
 *   onError: (error) => showErrorMessage(error),
 * });
 * ```
 */
export function useAnalysisEventStream({
  analysisId,
  onComplete,
  onError,
  enableFallback = true,
  maxReconnectAttempts = 3,
  reconnectDelay = 2000,
}: UseAnalysisEventStreamProps) {
  const [status, setStatus] = useState<JobStatus>({ status: 'queued' });
  const [isStreaming, setIsStreaming] = useState(true);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'fallback' | 'reconnecting'>('connecting');

  const eventSourceRef = useRef<EventSource | null>(null);
  const fallbackHookRef = useRef<any>(null);
  const isCleaningUpRef = useRef(false);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isStreamingRef = useRef(true);

  const disconnect = useCallback(() => {
    isCleaningUpRef.current = true;
    isStreamingRef.current = false;
    setIsStreaming(false);

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (fallbackHookRef.current?.stopPolling) {
      fallbackHookRef.current.stopPolling();
    }

    setConnectionState('disconnected');
  }, []);

  // Fallback to polling hook when SSE fails - only initialize when needed
  const fallbackHook = useAnalysisJobPolling({
    analysisId: connectionState === 'fallback' ? analysisId : 0, // Only poll when in fallback mode
    onComplete,
    onError,
    pollInterval: 3000,
  });

  useEffect(() => {
    if (!analysisId) {
      return;
    }

    // Reset streaming state on new analysis
    isStreamingRef.current = true;
    setIsStreaming(true);

    // Prevent duplicate connections - only clean up if we're actually creating a new one
    if (eventSourceRef.current) {
      return;
    }

    isCleaningUpRef.current = false;

    // Store fallback hook reference for cleanup
    fallbackHookRef.current = fallbackHook;

    const connectSSE = () => {
      if (isCleaningUpRef.current) return;

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const streamUrl = `${apiBaseUrl}/api/v1/analyses/${analysisId}/stream`;
      setConnectionState('connecting');

      // Add small delay to ensure component is stable
      setTimeout(() => {
        if (isCleaningUpRef.current || eventSourceRef.current) return;

        const eventSource = new EventSource(streamUrl);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          if (isCleaningUpRef.current) return;
          setConnectionState('connected');

          // Reset reconnection attempts on successful connection
          reconnectAttemptsRef.current = 0;
        };

      eventSource.onmessage = (event) => {
        if (isCleaningUpRef.current) return;

        try {
          const data = JSON.parse(event.data);

          // Update status from SSE data
          setStatus({
            status: data.status as 'queued' | 'processing' | 'completed' | 'failed',
            progress: data.progress,
            error: data.error_message,
            result: data.result
          });
        } catch (error) {
          console.error('Error parsing SSE data:', error);
        }
      };

      // Handle specific event types
      eventSource.addEventListener('status_update', (event) => {
        if (isCleaningUpRef.current) return;

        try {
          const data = JSON.parse(event.data);

          setStatus({
            status: data.status as 'queued' | 'processing' | 'completed' | 'failed',
            progress: data.progress,
            error: data.error_message,
            result: data.result
          });
        } catch (error) {
          console.error('Error parsing status update:', error);
        }
      });

      eventSource.addEventListener('analysis_complete', (event) => {
        if (isCleaningUpRef.current) return;

        try {
          const data = JSON.parse(event.data);

          setStatus({
            status: 'completed',
            progress: 100,
            result: data.result
          });

          setIsStreaming(false);
          onComplete?.(data.result);
        } catch (error) {
          console.error('Error parsing completion event:', error);
        }
      });

      eventSource.addEventListener('analysis_failed', (event) => {
        if (isCleaningUpRef.current) return;

        try {
          const data = JSON.parse(event.data);

          setStatus({
            status: 'failed',
            progress: 0,
            error: data.error_message
          });

          setIsStreaming(false);
          onError?.(data.error_message || 'Analysis failed');
        } catch (error) {
          console.error('Error parsing failure event:', error);
        }
      });

      eventSource.addEventListener('close', () => {
        if (isCleaningUpRef.current) return;
        setIsStreaming(false);
      });

      eventSource.addEventListener('error', (event) => {
        if (isCleaningUpRef.current) return;
        setConnectionState('disconnected');
      });

      eventSource.onerror = (error) => {
        if (isCleaningUpRef.current) return;

        eventSource.close();
        eventSourceRef.current = null;

        // Try to reconnect if we haven't exceeded max attempts
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          setConnectionState('reconnecting');

          reconnectTimeoutRef.current = setTimeout(() => {
            if (!isCleaningUpRef.current) {
              connectSSE();
            }
          }, reconnectDelay * reconnectAttemptsRef.current); // Exponential backoff
        } else if (enableFallback && !isCleaningUpRef.current) {
          setConnectionState('fallback');

          // Stop our own streaming and let the fallback hook take over
          setIsStreaming(false);
        } else {
          setConnectionState('disconnected');
          onError?.('Connection failed after all retry attempts');
        }
      };
      }, 100); // 100ms delay for setTimeout
    };

    connectSSE();

    return () => {
      disconnect();
    };
  }, [analysisId]);

  // Return the fallback hook's state when in fallback mode
  if (connectionState === 'fallback' && enableFallback) {
    return {
      status: fallbackHook.status,
      isStreaming: fallbackHook.isPolling,
      connectionState,
      disconnect: () => {
        disconnect();
        fallbackHook.stopPolling();
      }
    };
  }

  return {
    status,
    isStreaming,
    connectionState,
    disconnect,
  };
}