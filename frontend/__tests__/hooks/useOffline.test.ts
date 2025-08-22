/**
 * @jest-environment jsdom
 */
import { renderHook, act } from '@testing-library/react';
import { useOffline } from '@/hooks/useOffline';

describe('useOffline', () => {
  beforeEach(() => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });

    // Clear any existing event listeners
    jest.clearAllMocks();
  });

  it('should initialize with current online status', () => {
    const { result } = renderHook(() => useOffline());

    expect(result.current.isOnline).toBe(true);
    expect(result.current.isOffline).toBe(false);
    expect(result.current.syncQueue).toEqual([]);
    expect(typeof result.current.addToSyncQueue).toBe('function');
    expect(typeof result.current.processSync).toBe('function');
  });

  it('should initialize as offline when navigator is offline', () => {
    Object.defineProperty(navigator, 'onLine', {
      value: false,
    });

    const { result } = renderHook(() => useOffline());

    expect(result.current.isOnline).toBe(false);
    expect(result.current.isOffline).toBe(true);
  });

  it('should update status when online event fires', () => {
    Object.defineProperty(navigator, 'onLine', {
      value: false,
    });

    const { result } = renderHook(() => useOffline());

    expect(result.current.isOnline).toBe(false);

    // Simulate going online
    Object.defineProperty(navigator, 'onLine', {
      value: true,
    });

    act(() => {
      window.dispatchEvent(new Event('online'));
    });

    expect(result.current.isOnline).toBe(true);
    expect(result.current.isOffline).toBe(false);
  });

  it('should update status when offline event fires', () => {
    const { result } = renderHook(() => useOffline());

    expect(result.current.isOnline).toBe(true);

    // Simulate going offline
    Object.defineProperty(navigator, 'onLine', {
      value: false,
    });

    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    expect(result.current.isOnline).toBe(false);
    expect(result.current.isOffline).toBe(true);
  });

  it('should add actions to sync queue', () => {
    const { result } = renderHook(() => useOffline());

    const action1 = {
      id: '1',
      type: 'CREATE' as const,
      endpoint: '/api/test',
      data: { name: 'test' },
      timestamp: Date.now(),
    };

    const action2 = {
      id: '2',
      type: 'UPDATE' as const,
      endpoint: '/api/test/2',
      data: { name: 'updated' },
      timestamp: Date.now(),
    };

    act(() => {
      result.current.addToSyncQueue(action1);
      result.current.addToSyncQueue(action2);
    });

    expect(result.current.syncQueue).toHaveLength(2);
    expect(result.current.syncQueue[0]).toEqual(action1);
    expect(result.current.syncQueue[1]).toEqual(action2);
  });

  it('should process sync queue when going online', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });
    global.fetch = mockFetch;

    Object.defineProperty(navigator, 'onLine', {
      value: false,
    });

    const { result } = renderHook(() => useOffline());

    const action = {
      id: '1',
      type: 'CREATE' as const,
      endpoint: '/api/test',
      data: { name: 'test' },
      timestamp: Date.now(),
    };

    // Add action while offline
    act(() => {
      result.current.addToSyncQueue(action);
    });

    expect(result.current.syncQueue).toHaveLength(1);

    // Go online (this should trigger sync processing)
    Object.defineProperty(navigator, 'onLine', {
      value: true,
    });

    act(() => {
      window.dispatchEvent(new Event('online'));
    });

    // Wait for sync processing
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'test' }),
    });

    expect(result.current.syncQueue).toHaveLength(0);
  });

  it('should handle different action types in sync queue', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useOffline());

    const createAction = {
      id: '1',
      type: 'CREATE' as const,
      endpoint: '/api/test',
      data: { name: 'test' },
      timestamp: Date.now(),
    };

    const updateAction = {
      id: '2',
      type: 'UPDATE' as const,
      endpoint: '/api/test/2',
      data: { name: 'updated' },
      timestamp: Date.now(),
    };

    const deleteAction = {
      id: '3',
      type: 'DELETE' as const,
      endpoint: '/api/test/3',
      data: undefined,
      timestamp: Date.now(),
    };

    act(() => {
      result.current.addToSyncQueue(createAction);
      result.current.addToSyncQueue(updateAction);
      result.current.addToSyncQueue(deleteAction);
    });

    await act(async () => {
      await result.current.processSync();
    });

    expect(mockFetch).toHaveBeenCalledTimes(3);
    expect(mockFetch).toHaveBeenNthCalledWith(1, '/api/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'test' }),
    });
    expect(mockFetch).toHaveBeenNthCalledWith(2, '/api/test/2', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'updated' }),
    });
    expect(mockFetch).toHaveBeenNthCalledWith(3, '/api/test/3', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
  });

  it('should handle sync errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    const mockFetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      })
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Server error' }),
      });
    
    global.fetch = mockFetch;

    const { result } = renderHook(() => useOffline());

    const actions = [
      {
        id: '1',
        type: 'CREATE' as const,
        endpoint: '/api/success',
        data: { name: 'success' },
        timestamp: Date.now(),
      },
      {
        id: '2',
        type: 'CREATE' as const,
        endpoint: '/api/network-error',
        data: { name: 'network-error' },
        timestamp: Date.now(),
      },
      {
        id: '3',
        type: 'CREATE' as const,
        endpoint: '/api/server-error',
        data: { name: 'server-error' },
        timestamp: Date.now(),
      },
    ];

    act(() => {
      actions.forEach(action => result.current.addToSyncQueue(action));
    });

    await act(async () => {
      await result.current.processSync();
    });

    expect(mockFetch).toHaveBeenCalledTimes(3);
    expect(consoleSpy).toHaveBeenCalledTimes(2); // Two errors logged
    expect(result.current.syncQueue).toHaveLength(0); // All items processed regardless of errors

    consoleSpy.mockRestore();
  });

  it('should clean up event listeners on unmount', () => {
    const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
    
    const { unmount } = renderHook(() => useOffline());

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));

    removeEventListenerSpy.mockRestore();
  });

  it('should persist sync queue to localStorage', () => {
    const { result } = renderHook(() => useOffline());

    const action = {
      id: '1',
      type: 'CREATE' as const,
      endpoint: '/api/test',
      data: { name: 'test' },
      timestamp: Date.now(),
    };

    act(() => {
      result.current.addToSyncQueue(action);
    });

    const stored = localStorage.getItem('palmistry-sync-queue');
    expect(stored).toBeTruthy();
    expect(JSON.parse(stored!)).toEqual([action]);
  });

  it('should restore sync queue from localStorage on mount', () => {
    const persistedAction = {
      id: 'persisted',
      type: 'CREATE' as const,
      endpoint: '/api/persisted',
      data: { name: 'persisted' },
      timestamp: Date.now(),
    };

    localStorage.setItem('palmistry-sync-queue', JSON.stringify([persistedAction]));

    const { result } = renderHook(() => useOffline());

    expect(result.current.syncQueue).toEqual([persistedAction]);
  });

  it('should handle localStorage errors gracefully', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    const originalSetItem = localStorage.setItem;
    
    localStorage.setItem = jest.fn(() => {
      throw new Error('Storage full');
    });

    const { result } = renderHook(() => useOffline());

    const action = {
      id: '1',
      type: 'CREATE' as const,
      endpoint: '/api/test',
      data: { name: 'test' },
      timestamp: Date.now(),
    };

    act(() => {
      result.current.addToSyncQueue(action);
    });

    expect(result.current.syncQueue).toEqual([action]); // Still works in memory
    expect(consoleSpy).toHaveBeenCalledWith('Failed to save sync queue:', expect.any(Error));

    localStorage.setItem = originalSetItem;
    consoleSpy.mockRestore();
  });
});