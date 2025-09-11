import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { OfflineIndicator } from '@/components/ui/OfflineIndicator';
import { useOffline } from '@/hooks/useOffline';

// Mock the useOffline hook
vi.mock('@/hooks/useOffline');

const mockUseOffline = vi.mocked(useOffline);

describe('OfflineIndicator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when online with no pending actions', () => {
    mockUseOffline.mockReturnValue({
      isOnline: true,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    const { container } = render(<OfflineIndicator />);
    expect(container).toBeEmptyDOMElement();
  });

  it('should render offline indicator when offline', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    expect(screen.getByText('You\'re Offline')).toBeInTheDocument();
    expect(screen.getByText('Some features may not work. Changes will sync when back online.')).toBeInTheDocument();
  });

  it('should show pending actions count when back online', () => {
    mockUseOffline.mockReturnValue({
      isOnline: true,
      pendingActions: [
        {
          id: '1',
          action: 'upload_analysis',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
        {
          id: '2',
          action: 'send_message',
          data: { name: 'test2' },
          timestamp: Date.now(),
        },
      ],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    expect(screen.getByText('Back Online')).toBeInTheDocument();
    expect(screen.getByText('2 pending actions to sync')).toBeInTheDocument();
  });

  it('should show singular text for single pending action', () => {
    mockUseOffline.mockReturnValue({
      isOnline: true,
      pendingActions: [
        {
          id: '1',
          action: 'upload_analysis',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
      ],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    expect(screen.getByText('1 pending action to sync')).toBeInTheDocument();
  });

  it('should have proper positioning classes', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    const indicator = screen.getByText('You\'re Offline').closest('div')?.closest('div')?.closest('div');
    
    expect(indicator).toHaveClass(
      'fixed',
      'bottom-4',
      'left-4',
      'right-4',
      'z-50'
    );
  });

  it('should show wifi off icon when offline', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    // Check for WiFi off icon (Lucide icon)
    const container = screen.getByText('You\'re Offline').closest('div')?.closest('div');
    expect(container?.querySelector('svg')).toBeInTheDocument();
  });

  it('should show sync button when online with pending actions', () => {
    const mockProcessPendingActions = vi.fn();
    mockUseOffline.mockReturnValue({
      isOnline: true,
      pendingActions: [
        {
          id: '1',
          action: 'upload_analysis',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
      ],
      addPendingAction: vi.fn(),
      processPendingActions: mockProcessPendingActions,
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    const syncButton = screen.getByRole('button', { name: /sync now/i });
    expect(syncButton).toBeInTheDocument();
    
    fireEvent.click(syncButton);
    expect(mockProcessPendingActions).toHaveBeenCalled();
  });

  it('should show cached content message when offline', () => {
    mockUseOffline.mockReturnValue({
      isOnline: false,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    expect(screen.getByText('Cached content available')).toBeInTheDocument();
  });

  it('should update when connection status changes', () => {
    const { rerender } = render(<OfflineIndicator />);

    // Initially offline
    mockUseOffline.mockReturnValue({
      isOnline: false,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    rerender(<OfflineIndicator />);
    expect(screen.getByText('You\'re Offline')).toBeInTheDocument();

    // Go back online with no pending actions (should not render)
    mockUseOffline.mockReturnValue({
      isOnline: true,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    rerender(<OfflineIndicator />);
    expect(screen.queryByText('You\'re Offline')).not.toBeInTheDocument();
    expect(screen.queryByText('Back Online')).not.toBeInTheDocument();
  });

  it('should show success message when all actions synced', () => {
    mockUseOffline.mockReturnValue({
      isOnline: true,
      pendingActions: [],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    const { container } = render(<OfflineIndicator />);
    
    // Should not render when online with no pending actions
    expect(container).toBeEmptyDOMElement();
  });

  it('should show wifi icon when online', () => {
    mockUseOffline.mockReturnValue({
      isOnline: true,
      pendingActions: [
        {
          id: '1',
          action: 'upload_analysis',
          data: { name: 'test1' },
          timestamp: Date.now(),
        },
      ],
      addPendingAction: vi.fn(),
      processPendingActions: vi.fn(),
      clearPendingActions: vi.fn(),
    });

    render(<OfflineIndicator />);
    
    // Should show wifi icon when online
    const container = screen.getByText('Back Online').closest('div')?.closest('div');
    expect(container?.querySelector('svg')).toBeInTheDocument();
  });
});