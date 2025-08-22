/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { OfflineIndicator } from '@/components/ui/OfflineIndicator';
import { useOffline } from '@/hooks/useOffline';

// Mock the useOffline hook
jest.mock('@/hooks/useOffline');

const mockUseOffline = useOffline as jest.MockedFunction<typeof useOffline>;

describe('OfflineIndicator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not render when online', () => {
    mockUseOffline.mockReturnValue({
      isOnline: true,
      isOffline: false,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    const { container } = render(<OfflineIndicator />);
    expect(container).toBeEmptyDOMElement();
  });

  it('should render offline indicator when offline', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    render(<OfflineIndicator />);
    
    expect(screen.getByText('You are currently offline')).toBeInTheDocument();
    expect(screen.getByText('Some features may be limited')).toBeInTheDocument();
  });

  it('should show sync queue count when items are pending', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [
        {
          id: '1',
          type: 'CREATE',
          endpoint: '/api/test1',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
        {
          id: '2',
          type: 'UPDATE',
          endpoint: '/api/test2',
          data: { name: 'test2' },
          timestamp: Date.now(),
        },
      ],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    render(<OfflineIndicator />);
    
    expect(screen.getByText('You are currently offline')).toBeInTheDocument();
    expect(screen.getByText('2 changes will sync when you reconnect')).toBeInTheDocument();
  });

  it('should show singular text for single sync item', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [
        {
          id: '1',
          type: 'CREATE',
          endpoint: '/api/test1',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
      ],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    render(<OfflineIndicator />);
    
    expect(screen.getByText('1 change will sync when you reconnect')).toBeInTheDocument();
  });

  it('should have proper styling classes', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    render(<OfflineIndicator />);
    
    const indicator = screen.getByText('You are currently offline').closest('div');
    
    expect(indicator).toHaveClass(
      'fixed',
      'top-0',
      'left-0',
      'right-0',
      'bg-amber-500',
      'text-white',
      'px-4',
      'py-2',
      'text-center',
      'text-sm',
      'z-50'
    );
  });

  it('should include wifi off icon', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    render(<OfflineIndicator />);
    
    // Check for WiFi off icon (should be an SVG or icon element)
    const iconElement = screen.getByText('You are currently offline').previousSibling;
    expect(iconElement).toBeInTheDocument();
  });

  it('should be accessible', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [
        {
          id: '1',
          type: 'CREATE',
          endpoint: '/api/test1',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
      ],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    render(<OfflineIndicator />);
    
    const indicator = screen.getByRole('status', { name: /offline/i });
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveAttribute('aria-label', 'Offline status with 1 pending change');
  });

  it('should handle empty sync queue accessibility', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    render(<OfflineIndicator />);
    
    const indicator = screen.getByRole('status', { name: /offline/i });
    expect(indicator).toHaveAttribute('aria-label', 'Currently offline');
  });

  it('should update when connection status changes', () => {
    const { rerender } = render(<OfflineIndicator />);

    // Initially offline
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    rerender(<OfflineIndicator />);
    expect(screen.getByText('You are currently offline')).toBeInTheDocument();

    // Go back online
    mockUseOffline.mockReturnValue({
      isOnline: true,
      isOffline: false,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    rerender(<OfflineIndicator />);
    expect(screen.queryByText('You are currently offline')).not.toBeInTheDocument();
  });

  it('should update sync count dynamically', () => {
    const { rerender } = render(<OfflineIndicator />);

    // Start with no pending items
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    rerender(<OfflineIndicator />);
    expect(screen.getByText('Some features may be limited')).toBeInTheDocument();

    // Add pending items
    mockUseOffline.mockReturnValue({
      isOnline: false,
      isOffline: true,
      syncQueue: [
        {
          id: '1',
          type: 'CREATE',
          endpoint: '/api/test1',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
        {
          id: '2',
          type: 'UPDATE',
          endpoint: '/api/test2',
          data: { name: 'test2' },
          timestamp: Date.now(),
        },
        {
          id: '3',
          type: 'DELETE',
          endpoint: '/api/test3',
          data: undefined,
          timestamp: Date.now(),
        },
      ],
      addToSyncQueue: jest.fn(),
      processSync: jest.fn(),
    });

    rerender(<OfflineIndicator />);
    expect(screen.getByText('3 changes will sync when you reconnect')).toBeInTheDocument();
  });
});