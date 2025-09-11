import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useCSRF } from '@/hooks/useCSRF';
import { authApi } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  authApi: {
    getCSRFToken: vi.fn(),
  },
}));

const mockAuthApi = vi.mocked(authApi);

describe('useCSRF', () => {
  beforeEach(() => {
    // Clear DOM and mocks
    document.head.innerHTML = '';
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up DOM
    document.head.innerHTML = '';
  });

  it('should initialize with null token and loading state', () => {
    const { result } = renderHook(() => useCSRF());

    expect(result.current.csrfToken).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(typeof result.current.refreshCSRFToken).toBe('function');
  });

  it('should use existing meta tag token if available', async () => {
    // Create existing meta tag
    const metaTag = document.createElement('meta');
    metaTag.name = 'csrf-token';
    metaTag.content = 'existing-token';
    document.head.appendChild(metaTag);

    const { result } = renderHook(() => useCSRF());

    await waitFor(() => {
      expect(result.current.csrfToken).toBe('existing-token');
    });

    expect(mockAuthApi.getCSRFToken).not.toHaveBeenCalled();
  });

  it('should fetch token from API when no meta tag exists', async () => {
    mockAuthApi.getCSRFToken.mockResolvedValue('api-token');

    const { result } = renderHook(() => useCSRF());

    await waitFor(() => {
      expect(result.current.csrfToken).toBe('api-token');
    });

    expect(mockAuthApi.getCSRFToken).toHaveBeenCalledTimes(1);

    // Should create new meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    expect(metaTag?.getAttribute('content')).toBe('api-token');
  });

  it('should update existing meta tag when fetching from API', async () => {
    // Create existing empty meta tag
    const metaTag = document.createElement('meta');
    metaTag.name = 'csrf-token';
    metaTag.content = '';
    document.head.appendChild(metaTag);

    mockAuthApi.getCSRFToken.mockResolvedValue('new-api-token');

    const { result } = renderHook(() => useCSRF());

    await waitFor(() => {
      expect(result.current.csrfToken).toBe('new-api-token');
    });

    expect(metaTag.getAttribute('content')).toBe('new-api-token');
  });

  it('should handle API errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockAuthApi.getCSRFToken.mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useCSRF());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.csrfToken).toBeNull();
    expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch CSRF token:', expect.any(Error));

    consoleSpy.mockRestore();
  });

  it('should refresh CSRF token manually', async () => {
    mockAuthApi.getCSRFToken
      .mockResolvedValueOnce('initial-token')
      .mockResolvedValueOnce('refreshed-token');

    const { result } = renderHook(() => useCSRF());

    await waitFor(() => {
      expect(result.current.csrfToken).toBe('initial-token');
    });

    // Refresh token
    await result.current.refreshCSRFToken();

    await waitFor(() => {
      expect(result.current.csrfToken).toBe('refreshed-token');
    });

    expect(mockAuthApi.getCSRFToken).toHaveBeenCalledTimes(2);
  });

  it('should handle refresh errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockAuthApi.getCSRFToken
      .mockResolvedValueOnce('initial-token')
      .mockRejectedValueOnce(new Error('Refresh Error'));

    const { result } = renderHook(() => useCSRF());

    await waitFor(() => {
      expect(result.current.csrfToken).toBe('initial-token');
    });

    await result.current.refreshCSRFToken();

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.csrfToken).toBe('initial-token'); // Should remain unchanged
    expect(consoleSpy).toHaveBeenCalledWith('Failed to refresh CSRF token:', expect.any(Error));

    consoleSpy.mockRestore();
  });

  it('should show loading state during initial fetch', async () => {
    let resolvePromise: (value: string) => void;
    const promise = new Promise<string>((resolve) => {
      resolvePromise = resolve;
    });
    mockAuthApi.getCSRFToken.mockReturnValue(promise);

    const { result } = renderHook(() => useCSRF());

    // Initially not loading
    expect(result.current.isLoading).toBe(false);

    // Should eventually show loading state
    await waitFor(() => {
      expect(result.current.isLoading).toBe(true);
    });

    // Resolve the promise
    resolvePromise!('test-token');

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.csrfToken).toBe('test-token');
    });
  });
});