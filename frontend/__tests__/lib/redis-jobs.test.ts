/**
 * @fileoverview Tests for background job polling system
 * Tests React hooks for real-time analysis status updates
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAnalysisJobPolling } from '@/lib/redis-jobs';
import { analysisApi } from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api', () => ({
  analysisApi: {
    getAnalysisStatus: vi.fn(),
  },
}));

const mockedAnalysisApi = vi.mocked(analysisApi);

describe('useAnalysisJobPolling', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should start with queued status and polling enabled', () => {
    mockedAnalysisApi.getAnalysisStatus.mockResolvedValue({
      status: 'queued',
    });

    const { result } = renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
      })
    );

    expect(result.current.status.status).toBe('queued');
    expect(result.current.isPolling).toBe(true);
  });

  it('should call API and update status', async () => {
    mockedAnalysisApi.getAnalysisStatus
      .mockResolvedValueOnce({ status: 'queued' })
      .mockResolvedValueOnce({ status: 'processing' });

    const { result } = renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        pollInterval: 100,
      })
    );

    // Initial call should happen immediately
    await waitFor(() => {
      expect(mockedAnalysisApi.getAnalysisStatus).toHaveBeenCalledWith('1');
    });

    // Advance timer to trigger next poll
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(result.current.status.status).toBe('processing');
    });
  });

  it('should stop polling and call onComplete when job completes', async () => {
    const onComplete = vi.fn();
    const mockResult = { palmReading: 'Your life line is strong...' };

    mockedAnalysisApi.getAnalysisStatus
      .mockResolvedValueOnce({ status: 'processing' })
      .mockResolvedValueOnce({ 
        status: 'completed', 
        result: mockResult 
      });

    const { result } = renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        onComplete,
        pollInterval: 100,
      })
    );

    // Advance timer to trigger polling
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(result.current.status.status).toBe('completed');
      expect(result.current.isPolling).toBe(false);
      expect(onComplete).toHaveBeenCalledWith(mockResult);
    });
  });

  it('should stop polling and call onError when job fails', async () => {
    const onError = vi.fn();
    const errorMessage = 'Analysis failed: Invalid image format';

    mockedAnalysisApi.getAnalysisStatus
      .mockResolvedValueOnce({ status: 'processing' })
      .mockResolvedValueOnce({ 
        status: 'failed', 
        error_message: errorMessage 
      });

    const { result } = renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        onError,
        pollInterval: 100,
      })
    );

    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(result.current.status.status).toBe('failed');
      expect(result.current.isPolling).toBe(false);
      expect(onError).toHaveBeenCalledWith(errorMessage);
    });
  });

  it('should handle API errors gracefully', async () => {
    const onError = vi.fn();
    const apiError = new Error('Network error');

    mockedAnalysisApi.getAnalysisStatus.mockRejectedValue(apiError);

    const { result } = renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        onError,
        pollInterval: 100,
      })
    );

    await waitFor(() => {
      expect(result.current.isPolling).toBe(false);
      expect(onError).toHaveBeenCalledWith('Failed to check analysis status');
    });
  });

  it('should allow manual stop of polling', async () => {
    mockedAnalysisApi.getAnalysisStatus.mockResolvedValue({
      status: 'processing',
    });

    const { result } = renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        pollInterval: 100,
      })
    );

    expect(result.current.isPolling).toBe(true);

    // Stop polling manually
    result.current.stopPolling();

    expect(result.current.isPolling).toBe(false);
  });

  it('should clean up interval on unmount', () => {
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval');
    
    mockedAnalysisApi.getAnalysisStatus.mockResolvedValue({
      status: 'processing',
    });

    const { unmount } = renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        pollInterval: 100,
      })
    );

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
  });

  it('should use custom poll interval', async () => {
    mockedAnalysisApi.getAnalysisStatus.mockResolvedValue({
      status: 'processing',
    });

    renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        pollInterval: 5000, // 5 seconds
      })
    );

    // Should not call again after 1 second with 5 second interval
    vi.advanceTimersByTime(1000);
    expect(mockedAnalysisApi.getAnalysisStatus).toHaveBeenCalledTimes(1);

    // Should call again after 5 seconds
    vi.advanceTimersByTime(4000);
    await waitFor(() => {
      expect(mockedAnalysisApi.getAnalysisStatus).toHaveBeenCalledTimes(2);
    });
  });

  it('should handle missing error message in failed job', async () => {
    const onError = vi.fn();

    mockedAnalysisApi.getAnalysisStatus.mockResolvedValue({ 
      status: 'failed' 
      // No error message provided
    });

    renderHook(() =>
      useAnalysisJobPolling({
        analysisId: 1,
        onError,
        pollInterval: 100,
      })
    );

    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Analysis failed');
    });
  });
});