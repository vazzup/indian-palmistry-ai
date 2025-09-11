import { renderHook } from '@testing-library/react';
import { vi } from 'vitest';
import { usePerformanceMonitoring } from '@/hooks/usePerformanceMonitoring';

// Mock web-vitals
vi.mock('web-vitals', () => ({
  onCLS: vi.fn(),
  onFCP: vi.fn(),
  onLCP: vi.fn(),
  onTTFB: vi.fn(),
}));

// Mock performance
Object.defineProperty(global, 'performance', {
  value: {
    now: vi.fn(() => 1000),
  },
  writable: true,
});

describe('usePerformanceMonitoring Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(performance.now).mockReturnValue(1000);
  });

  it('should return measurement functions', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());
    
    expect(typeof result.current.measureCustomMetric).toBe('function');
    expect(typeof result.current.measureApiCall).toBe('function');
  });

  it('should measure custom metrics', () => {
    const { result } = renderHook(() => usePerformanceMonitoring());
    
    const startTime = 100;
    const endTime = 200;
    
    const duration = result.current.measureCustomMetric('test-metric', startTime, endTime);
    
    expect(duration).toBe(100);
  });

  it('should measure custom metrics without end time', () => {
    vi.mocked(performance.now).mockReturnValue(1100);
    
    const { result } = renderHook(() => usePerformanceMonitoring());
    
    const startTime = 100;
    
    const duration = result.current.measureCustomMetric('test-metric', startTime);
    
    expect(duration).toBe(1000); // 1100 - 100
  });

  it('should measure API calls successfully', async () => {
    const { result } = renderHook(() => usePerformanceMonitoring());
    
    const mockApiCall = vi.fn().mockResolvedValue('success');
    
    const response = await result.current.measureApiCall('test-api', mockApiCall);
    
    expect(response).toBe('success');
    expect(mockApiCall).toHaveBeenCalled();
  });

  it('should measure API calls that fail', async () => {
    const { result } = renderHook(() => usePerformanceMonitoring());
    
    const mockApiCall = vi.fn().mockRejectedValue(new Error('API Error'));
    
    await expect(result.current.measureApiCall('test-api', mockApiCall)).rejects.toThrow('API Error');
    expect(mockApiCall).toHaveBeenCalled();
  });
});