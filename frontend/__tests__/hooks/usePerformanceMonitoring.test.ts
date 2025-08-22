/**
 * @jest-environment jsdom
 */
import { renderHook, act } from '@testing-library/react';
import { usePerformanceMonitoring } from '@/hooks/usePerformanceMonitoring';

// Mock web-vitals
const mockGetFCP = jest.fn();
const mockGetLCP = jest.fn();
const mockGetCLS = jest.fn();
const mockGetFID = jest.fn();
const mockGetTTFB = jest.fn();

jest.mock('web-vitals', () => ({
  getFCP: mockGetFCP,
  getLCP: mockGetLCP,
  getCLS: mockGetCLS,
  getFID: mockGetFID,
  getTTFB: mockGetTTFB,
}));

// Mock Performance API
const mockPerformance = {
  now: jest.fn(() => Date.now()),
  mark: jest.fn(),
  measure: jest.fn(),
  getEntriesByType: jest.fn(),
  getEntriesByName: jest.fn(),
};

Object.defineProperty(window, 'performance', {
  value: mockPerformance,
  writable: true,
});

describe('usePerformanceMonitoring', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPerformance.now.mockReturnValue(Date.now());
    mockPerformance.getEntriesByType.mockReturnValue([]);
    mockPerformance.getEntriesByName.mockReturnValue([]);
  });

  it('should initialize with empty metrics and provide utility functions', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    expect(result.current.metrics).toEqual({});
    expect(result.current.isEnabled).toBe(true);
    expect(typeof result.current.startTiming).toBe('function');
    expect(typeof result.current.endTiming).toBe('function');
    expect(typeof result.current.recordMetric).toBe('function');
    expect(typeof result.current.getMetrics).toBe('function');
    expect(typeof result.current.clearMetrics).toBe('function');
  });

  it('should initialize web vitals monitoring', () => {
    renderHook(() => usePerformanceMonitoring());

    expect(mockGetFCP).toHaveBeenCalledWith(expect.any(Function));
    expect(mockGetLCP).toHaveBeenCalledWith(expect.any(Function));
    expect(mockGetCLS).toHaveBeenCalledWith(expect.any(Function));
    expect(mockGetFID).toHaveBeenCalledWith(expect.any(Function));
    expect(mockGetTTFB).toHaveBeenCalledWith(expect.any(Function));
  });

  it('should handle web vitals callbacks', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    // Simulate FCP metric callback
    const fcpCallback = mockGetFCP.mock.calls[0][0];
    act(() => {
      fcpCallback({
        name: 'FCP',
        value: 1500,
        delta: 1500,
        id: 'test-fcp-id',
      });
    });

    expect(result.current.metrics.FCP).toEqual({
      name: 'FCP',
      value: 1500,
      delta: 1500,
      id: 'test-fcp-id',
    });

    // Simulate LCP metric callback
    const lcpCallback = mockGetLCP.mock.calls[0][0];
    act(() => {
      lcpCallback({
        name: 'LCP',
        value: 2500,
        delta: 2500,
        id: 'test-lcp-id',
      });
    });

    expect(result.current.metrics.LCP).toEqual({
      name: 'LCP',
      value: 2500,
      delta: 2500,
      id: 'test-lcp-id',
    });
  });

  it('should start and end timing measurements', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    const startTime = Date.now();
    mockPerformance.now.mockReturnValue(startTime);

    act(() => {
      result.current.startTiming('api-call');
    });

    expect(mockPerformance.mark).toHaveBeenCalledWith('api-call-start');

    // Simulate time passing
    const endTime = startTime + 500;
    mockPerformance.now.mockReturnValue(endTime);
    mockPerformance.getEntriesByName.mockReturnValue([
      { startTime }
    ]);

    act(() => {
      result.current.endTiming('api-call');
    });

    expect(mockPerformance.mark).toHaveBeenCalledWith('api-call-end');
    expect(mockPerformance.measure).toHaveBeenCalledWith(
      'api-call',
      'api-call-start',
      'api-call-end'
    );

    expect(result.current.metrics['api-call']).toEqual({
      name: 'api-call',
      value: 500,
      startTime,
      endTime,
    });
  });

  it('should handle timing errors gracefully', () => {
    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
    const { result } = renderHook(() => usePerformanceMonitoring());

    // Try to end timing without starting
    act(() => {
      result.current.endTiming('non-existent-timing');
    });

    expect(consoleSpy).toHaveBeenCalledWith('No start mark found for: non-existent-timing');

    // Mock performance API to throw errors
    mockPerformance.mark.mockImplementation(() => {
      throw new Error('Performance API error');
    });

    act(() => {
      result.current.startTiming('error-test');
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to start timing for error-test:',
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });

  it('should record custom metrics', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    act(() => {
      result.current.recordMetric('custom-metric', 100);
    });

    expect(result.current.metrics['custom-metric']).toEqual({
      name: 'custom-metric',
      value: 100,
      timestamp: expect.any(Number),
    });
  });

  it('should record metrics with additional data', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    const additionalData = {
      type: 'navigation',
      url: '/test',
      userAgent: 'test-agent',
    };

    act(() => {
      result.current.recordMetric('navigation-time', 200, additionalData);
    });

    expect(result.current.metrics['navigation-time']).toEqual({
      name: 'navigation-time',
      value: 200,
      timestamp: expect.any(Number),
      ...additionalData,
    });
  });

  it('should get all metrics', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    act(() => {
      result.current.recordMetric('metric1', 100);
      result.current.recordMetric('metric2', 200);
    });

    const allMetrics = result.current.getMetrics();

    expect(allMetrics).toEqual({
      metric1: expect.objectContaining({ name: 'metric1', value: 100 }),
      metric2: expect.objectContaining({ name: 'metric2', value: 200 }),
    });
  });

  it('should clear all metrics', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    act(() => {
      result.current.recordMetric('metric1', 100);
      result.current.recordMetric('metric2', 200);
    });

    expect(Object.keys(result.current.metrics)).toHaveLength(2);

    act(() => {
      result.current.clearMetrics();
    });

    expect(result.current.metrics).toEqual({});
  });

  it('should be disabled when performance API is not available', () => {
    const originalPerformance = window.performance;
    
    // Remove performance API
    Object.defineProperty(window, 'performance', {
      value: undefined,
      writable: true,
    });

    const { result } = renderHook(() => usePerformanceMonitoring());

    expect(result.current.isEnabled).toBe(false);
    expect(result.current.metrics).toEqual({});

    // Functions should still work but do nothing
    act(() => {
      result.current.startTiming('test');
      result.current.endTiming('test');
      result.current.recordMetric('test', 100);
    });

    expect(result.current.metrics).toEqual({});

    // Restore performance API
    Object.defineProperty(window, 'performance', {
      value: originalPerformance,
      writable: true,
    });
  });

  it('should handle navigation timing', () => {
    const navigationEntries = [
      {
        name: 'navigation',
        entryType: 'navigation',
        startTime: 0,
        domContentLoadedEventStart: 500,
        domContentLoadedEventEnd: 600,
        loadEventStart: 800,
        loadEventEnd: 900,
        duration: 1000,
      }
    ];

    mockPerformance.getEntriesByType.mockImplementation((type) => {
      if (type === 'navigation') return navigationEntries;
      return [];
    });

    const { result } = renderHook(() => usePerformanceMonitoring());

    // Should automatically record navigation metrics
    expect(result.current.metrics).toEqual(
      expect.objectContaining({
        'dom-content-loaded': expect.objectContaining({
          name: 'dom-content-loaded',
          value: 500,
        }),
        'load-complete': expect.objectContaining({
          name: 'load-complete',
          value: 900,
        }),
      })
    );
  });

  it('should track resource loading performance', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    act(() => {
      result.current.startTiming('image-load');
    });

    const startTime = Date.now();
    mockPerformance.now.mockReturnValue(startTime + 200);
    mockPerformance.getEntriesByName.mockReturnValue([{ startTime }]);

    act(() => {
      result.current.endTiming('image-load');
    });

    expect(result.current.metrics['image-load']).toEqual({
      name: 'image-load',
      value: 200,
      startTime,
      endTime: startTime + 200,
    });
  });

  it('should handle CLS metric specifically', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    const clsCallback = mockGetCLS.mock.calls[0][0];
    act(() => {
      clsCallback({
        name: 'CLS',
        value: 0.05,
        delta: 0.02,
        id: 'test-cls-id',
      });
    });

    expect(result.current.metrics.CLS).toEqual({
      name: 'CLS',
      value: 0.05,
      delta: 0.02,
      id: 'test-cls-id',
    });
  });

  it('should batch metric updates for performance', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());

    act(() => {
      // Record multiple metrics quickly
      for (let i = 0; i < 10; i++) {
        result.current.recordMetric(`metric-${i}`, i * 100);
      }
    });

    expect(Object.keys(result.current.metrics)).toHaveLength(10);
    expect(result.current.metrics['metric-5']).toEqual({
      name: 'metric-5',
      value: 500,
      timestamp: expect.any(Number),
    });
  });
});