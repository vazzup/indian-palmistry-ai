import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useOffline } from '@/hooks/useOffline';

describe('useOffline Hook', () => {
  beforeEach(() => {
    // Mock navigator.onLine as true by default
    Object.defineProperty(navigator, 'onLine', {
      value: true,
      writable: true,
    });

    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });

    // Clear any existing event listeners
    vi.clearAllMocks();
  });

  it('should initialize with current online status', () => {
    const { result } = renderHook(() => useOffline());

    expect(result.current.isOnline).toBe(true);
    expect(result.current.pendingActions).toEqual([]);
    expect(typeof result.current.addPendingAction).toBe('function');
    expect(typeof result.current.processPendingActions).toBe('function');
    expect(typeof result.current.clearPendingActions).toBe('function');
  });

  it('should initialize as offline when navigator is offline', () => {
    Object.defineProperty(navigator, 'onLine', {
      value: false,
    });

    const { result } = renderHook(() => useOffline());

    expect(result.current.isOnline).toBe(false);
  });

  it('should add pending action', () => {
    const { result } = renderHook(() => useOffline());

    act(() => {
      result.current.addPendingAction('test_action', { data: 'test' });
    });

    expect(result.current.pendingActions).toHaveLength(1);
    expect(result.current.pendingActions[0].action).toBe('test_action');
    expect(result.current.pendingActions[0].data).toEqual({ data: 'test' });
  });

  it('should clear pending actions', () => {
    const { result } = renderHook(() => useOffline());

    act(() => {
      result.current.addPendingAction('test_action', { data: 'test' });
    });

    expect(result.current.pendingActions).toHaveLength(1);

    act(() => {
      result.current.clearPendingActions();
    });

    expect(result.current.pendingActions).toHaveLength(0);
  });
});