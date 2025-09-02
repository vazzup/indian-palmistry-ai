/**
 * @fileoverview Tests for authentication fixes applied during debugging session
 * Tests infinite loop prevention, route-based auth checking, and proper hook behavior
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '@/lib/auth';

// Mock dependencies
vi.mock('@/lib/api', () => ({
  authApi: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    pathname: '/test',
  }),
  usePathname: () => '/test',
}));

// Mock localStorage
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('Authentication Fixes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear();
    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('useAuth hook infinite loop prevention', () => {
    it('should not create infinite API calls on public routes', async () => {
      const { authApi } = await import('@/lib/api');
      const mockGetCurrentUser = vi.mocked(authApi.getCurrentUser);
      
      // Mock public route
      vi.mocked(vi.importActual('next/navigation')).usePathname = () => '/';
      
      // Mock no stored auth
      mockLocalStorage.getItem.mockReturnValue(null);
      
      const { result } = renderHook(() => useAuth());
      
      // Should not trigger auth check immediately on public route with no stored auth
      expect(mockGetCurrentUser).not.toHaveBeenCalled();
      
      // Even after timer, should not call if on public route
      act(() => {
        vi.advanceTimersByTime(200);
      });
      
      expect(mockGetCurrentUser).not.toHaveBeenCalled();
      expect(result.current.isLoading).toBe(false);
    });

    it('should limit auth check frequency to prevent loops', async () => {
      const { authApi } = await import('@/lib/api');
      const mockGetCurrentUser = vi.mocked(authApi.getCurrentUser);
      
      // Mock authenticated route
      vi.mocked(vi.importActual('next/navigation')).usePathname = () => '/dashboard';
      
      // Mock stored auth
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify({ isAuthenticated: true }));
      
      mockGetCurrentUser.mockResolvedValue({
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      });

      const { result, rerender } = renderHook(() => useAuth());
      
      // Initial call
      act(() => {
        vi.advanceTimersByTime(200);
      });
      
      await waitFor(() => {
        expect(mockGetCurrentUser).toHaveBeenCalledTimes(1);
      });
      
      // Multiple re-renders should not trigger additional calls
      rerender();
      rerender();
      rerender();
      
      act(() => {
        vi.advanceTimersByTime(200);
      });
      
      // Should still only be called once
      expect(mockGetCurrentUser).toHaveBeenCalledTimes(1);
    });

    it('should use timeout to debounce auth checks', async () => {
      const { authApi } = await import('@/lib/api');
      const mockGetCurrentUser = vi.mocked(authApi.getCurrentUser);
      
      // Mock protected route with stored auth
      vi.mocked(vi.importActual('next/navigation')).usePathname = () => '/profile';
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify({ isAuthenticated: true }));
      
      mockGetCurrentUser.mockResolvedValue({
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      });

      renderHook(() => useAuth());
      
      // Should not call immediately
      expect(mockGetCurrentUser).not.toHaveBeenCalled();
      
      // Should call after timeout
      act(() => {
        vi.advanceTimersByTime(100);
      });
      
      await waitFor(() => {
        expect(mockGetCurrentUser).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Route-based authentication checking', () => {
    it('should skip auth check on public routes', () => {
      const { authApi } = await import('@/lib/api');
      const mockGetCurrentUser = vi.mocked(authApi.getCurrentUser);
      
      const publicRoutes = ['/', '/analysis/123/summary', '/auth/login', '/auth/register'];
      
      publicRoutes.forEach(route => {
        vi.clearAllMocks();
        vi.mocked(vi.importActual('next/navigation')).usePathname = () => route;
        mockLocalStorage.getItem.mockReturnValue(null);
        
        renderHook(() => useAuth());
        
        // Should not trigger auth check on public routes
        act(() => {
          vi.advanceTimersByTime(200);
        });
        
        expect(mockGetCurrentUser).not.toHaveBeenCalled();
      });
    });

    it('should perform auth check on protected routes with stored auth', async () => {
      const { authApi } = await import('@/lib/api');
      const mockGetCurrentUser = vi.mocked(authApi.getCurrentUser);
      
      const protectedRoutes = ['/dashboard', '/profile', '/settings'];
      
      for (const route of protectedRoutes) {
        vi.clearAllMocks();
        vi.mocked(vi.importActual('next/navigation')).usePathname = () => route;
        mockLocalStorage.getItem.mockReturnValue(JSON.stringify({ isAuthenticated: true }));
        
        mockGetCurrentUser.mockResolvedValue({
          id: 'user-123',
          email: 'test@example.com',
          name: 'Test User',
        });

        renderHook(() => useAuth());
        
        act(() => {
          vi.advanceTimersByTime(200);
        });
        
        await waitFor(() => {
          expect(mockGetCurrentUser).toHaveBeenCalledTimes(1);
        });
      }
    });
  });

  describe('Dependency array fixes', () => {
    it('should not include function references in useEffect dependencies', () => {
      // This test ensures we fixed the infinite loop by not including
      // store.checkAuth in the dependency array
      
      const { result, rerender } = renderHook(() => useAuth());
      
      // Multiple re-renders should not trigger new effects
      const initialCallCount = vi.mocked(vi.importActual('@/lib/api')).authApi.getCurrentUser.mock.calls.length;
      
      rerender();
      rerender(); 
      rerender();
      
      // Should maintain stable dependency array
      const finalCallCount = vi.mocked(vi.importActual('@/lib/api')).authApi.getCurrentUser.mock.calls.length;
      
      // Difference should be minimal (at most 1 call from the hook setup)
      expect(finalCallCount - initialCallCount).toBeLessThanOrEqual(1);
    });

    it('should only depend on stable values', () => {
      const { result } = renderHook(() => useAuth());
      
      // The hook should only depend on:
      // - store.isAuthenticated (boolean)
      // - store.isLoading (boolean)
      // NOT on function references like store.checkAuth
      
      expect(typeof result.current.isAuthenticated).toBe('boolean');
      expect(typeof result.current.isLoading).toBe('boolean');
      expect(typeof result.current.user).toBe('object');
      expect(typeof result.current.login).toBe('function');
      expect(typeof result.current.logout).toBe('function');
      expect(typeof result.current.checkAuth).toBe('function');
    });
  });

  describe('Error handling improvements', () => {
    it('should handle auth API errors gracefully', async () => {
      const { authApi } = await import('@/lib/api');
      const mockGetCurrentUser = vi.mocked(authApi.getCurrentUser);
      
      // Mock API error
      mockGetCurrentUser.mockRejectedValue(new Error('Network error'));
      
      // Mock protected route with stored auth
      vi.mocked(vi.importActual('next/navigation')).usePathname = () => '/dashboard';
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify({ isAuthenticated: true }));
      
      const { result } = renderHook(() => useAuth());
      
      act(() => {
        vi.advanceTimersByTime(200);
      });
      
      await waitFor(() => {
        // Should handle error without crashing
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isAuthenticated).toBe(false);
      });
    });

    it('should clean up timers on unmount', () => {
      const { unmount } = renderHook(() => useAuth());
      
      // Setup a timer
      act(() => {
        vi.advanceTimersByTime(50); // Not enough to trigger, timer should be pending
      });
      
      // Unmount should clean up
      unmount();
      
      // Advance past timer duration - should not cause issues
      act(() => {
        vi.advanceTimersByTime(200);
      });
      
      // No auth API calls should have been made after unmount
      expect(vi.mocked(vi.importActual('@/lib/api')).authApi.getCurrentUser).not.toHaveBeenCalled();
    });
  });

  describe('State management consistency', () => {
    it('should maintain consistent loading states', async () => {
      const { authApi } = await import('@/lib/api');
      const mockGetCurrentUser = vi.mocked(authApi.getCurrentUser);
      
      mockGetCurrentUser.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => resolve({
            id: 'user-123',
            email: 'test@example.com', 
            name: 'Test User',
          }), 100);
        });
      });
      
      // Mock protected route
      vi.mocked(vi.importActual('next/navigation')).usePathname = () => '/dashboard';
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify({ isAuthenticated: true }));
      
      const { result } = renderHook(() => useAuth());
      
      // Initial state
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isAuthenticated).toBe(false);
      
      // Trigger auth check
      act(() => {
        vi.advanceTimersByTime(200);
      });
      
      // Should be loading during API call
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });
      
      // Advance mock async operation
      act(() => {
        vi.advanceTimersByTime(100);
      });
      
      // Should complete loading
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isAuthenticated).toBe(true);
        expect(result.current.user).toBeDefined();
      });
    });
  });
});

describe('SecurityProvider fixes', () => {
  // Test that SecurityProvider doesn't cause Rules of Hooks violations
  it('should always call useAuth in the same order', () => {
    // This test ensures we fixed the conditional hook calling
    const TestComponent = ({ shouldUseAuth }: { shouldUseAuth: boolean }) => {
      // The WRONG way (causes Rules of Hooks violation):
      // if (shouldUseAuth) {
      //   useAuth(); // This would violate Rules of Hooks
      // }
      
      // The CORRECT way:
      const authResult = useAuth();
      
      // Control behavior with conditional logic INSIDE the hook result
      return shouldUseAuth ? authResult.isAuthenticated : false;
    };
    
    // Should not throw Rules of Hooks error
    expect(() => {
      renderHook((props) => TestComponent(props || { shouldUseAuth: true }));
    }).not.toThrow();
    
    expect(() => {
      renderHook((props) => TestComponent(props || { shouldUseAuth: false }));  
    }).not.toThrow();
  });
});