# useOffline Hook

A React hook that provides offline detection and background sync functionality for the Indian Palmistry AI PWA, ensuring seamless user experience during network interruptions.

## Overview

The `useOffline` hook manages network connectivity detection and maintains a sync queue for actions performed while offline, automatically syncing them when the connection is restored.

## Features

- **Network Status Detection**: Real-time online/offline status monitoring
- **Background Sync Queue**: Queues actions performed while offline
- **Automatic Sync**: Processes queued actions when connection is restored
- **Persistent Storage**: Maintains sync queue in localStorage across sessions
- **Error Handling**: Graceful handling of sync failures with retry logic
- **TypeScript Support**: Full type safety for all operations

## Usage

### Basic Network Detection

```tsx
import { useOffline } from '@/hooks/useOffline';

function NetworkStatus() {
  const { isOnline, isOffline } = useOffline();

  return (
    <div>
      {isOffline && (
        <div className="bg-amber-500 text-white p-2">
          You are currently offline
        </div>
      )}
      <p>Status: {isOnline ? 'Online' : 'Offline'}</p>
    </div>
  );
}
```

### Adding Actions to Sync Queue

```tsx
import { useOffline } from '@/hooks/useOffline';

function FormComponent() {
  const { addToSyncQueue, isOffline } = useOffline();

  const handleSubmit = async (formData: FormData) => {
    if (isOffline) {
      // Queue the action for later sync
      addToSyncQueue({
        type: 'CREATE',
        endpoint: '/api/analysis',
        data: Object.fromEntries(formData),
        method: 'POST',
      });
      
      // Show user feedback
      alert('Changes saved offline. Will sync when you reconnect.');
    } else {
      // Perform action immediately
      await fetch('/api/analysis', {
        method: 'POST',
        body: formData,
      });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit">
        {isOffline ? 'Save Offline' : 'Submit'}
      </button>
    </form>
  );
}
```

### Manual Sync Processing

```tsx
import { useOffline } from '@/hooks/useOffline';

function SyncStatus() {
  const { syncQueue, processSync, isOnline } = useOffline();

  const handleManualSync = async () => {
    if (isOnline) {
      await processSync();
    }
  };

  return (
    <div>
      <p>{syncQueue.length} actions pending sync</p>
      {isOnline && syncQueue.length > 0 && (
        <button onClick={handleManualSync}>
          Sync Now
        </button>
      )}
    </div>
  );
}
```

### Complete Integration Example

```tsx
import { useOffline } from '@/hooks/useOffline';
import { useState } from 'react';

function DataManager() {
  const { isOnline, isOffline, syncQueue, addToSyncQueue, processSync } = useOffline();
  const [data, setData] = useState([]);

  const createItem = async (item: any) => {
    if (isOffline) {
      // Add to local state immediately
      setData(prev => [...prev, { ...item, id: Date.now(), pending: true }]);
      
      // Queue for sync
      addToSyncQueue({
        type: 'CREATE',
        endpoint: '/api/items',
        data: item,
        method: 'POST',
      });
    } else {
      // Create online
      const response = await fetch('/api/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item),
      });
      
      const newItem = await response.json();
      setData(prev => [...prev, newItem]);
    }
  };

  const updateItem = async (id: string, updates: any) => {
    if (isOffline) {
      // Update local state
      setData(prev => prev.map(item => 
        item.id === id ? { ...item, ...updates, pending: true } : item
      ));
      
      // Queue for sync
      addToSyncQueue({
        type: 'UPDATE',
        endpoint: `/api/items/${id}`,
        data: updates,
        method: 'PUT',
      });
    } else {
      // Update online
      await fetch(`/api/items/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      
      setData(prev => prev.map(item => 
        item.id === id ? { ...item, ...updates } : item
      ));
    }
  };

  return (
    <div>
      <div className="mb-4">
        Status: {isOnline ? 'Online' : 'Offline'}
        {syncQueue.length > 0 && (
          <span className="ml-2 text-amber-600">
            ({syncQueue.length} pending sync)
          </span>
        )}
      </div>
      
      {data.map(item => (
        <div key={item.id} className={item.pending ? 'opacity-50' : ''}>
          {/* Item display */}
        </div>
      ))}
    </div>
  );
}
```

## Return Values

| Property | Type | Description |
|----------|------|-------------|
| `isOnline` | `boolean` | Whether the device is currently online |
| `isOffline` | `boolean` | Whether the device is currently offline |
| `syncQueue` | `SyncAction[]` | Array of actions waiting to be synced |
| `addToSyncQueue` | `(action: SyncAction) => void` | Add an action to the sync queue |
| `processSync` | `() => Promise<void>` | Process all queued sync actions |

## SyncAction Type

```typescript
interface SyncAction {
  id: string;                    // Unique identifier for the action
  type: 'CREATE' | 'UPDATE' | 'DELETE'; // Type of operation
  endpoint: string;              // API endpoint to call
  data?: any;                    // Data to send with the request
  method?: 'POST' | 'PUT' | 'DELETE'; // HTTP method (defaults based on type)
  timestamp: number;             // When the action was queued
}
```

## Sync Process

### Automatic Sync on Reconnect

1. **Detection**: Hook detects network connection restored
2. **Processing**: Automatically calls `processSync()`
3. **Sequential Execution**: Processes sync actions one by one
4. **Error Handling**: Failed actions remain in queue for retry
5. **Cleanup**: Successfully synced actions are removed from queue

### Manual Sync

```tsx
const { processSync, syncQueue } = useOffline();

const handleSync = async () => {
  if (syncQueue.length > 0) {
    try {
      await processSync();
      console.log('Sync completed successfully');
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }
};
```

## Storage Persistence

The hook persists sync queue data across browser sessions:

```typescript
// Automatic save to localStorage
const SYNC_QUEUE_KEY = 'palmistry-sync-queue';

// Queue is saved whenever actions are added/removed
localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(syncQueue));

// Queue is restored on hook initialization
const savedQueue = localStorage.getItem(SYNC_QUEUE_KEY);
```

## Error Handling

### Sync Failures

```typescript
// Failed actions remain in queue
const processSync = async () => {
  const failedActions = [];
  
  for (const action of syncQueue) {
    try {
      await syncAction(action);
      // Success - action is removed from queue
    } catch (error) {
      console.warn('Sync failed for action:', action.id, error);
      failedActions.push(action);
    }
  }
  
  // Update queue with only failed actions
  setSyncQueue(failedActions);
};
```

### Network Detection Issues

```typescript
// Fallback detection if navigator.onLine is unreliable
const checkRealNetworkStatus = async () => {
  try {
    await fetch('/api/health', { method: 'HEAD' });
    return true;
  } catch {
    return false;
  }
};
```

## Performance Considerations

- **Debounced Network Checks**: Network status changes are debounced to prevent excessive re-renders
- **Lazy Sync Processing**: Sync only runs when necessary (on reconnect or manual trigger)
- **Storage Optimization**: Large data objects are cleaned up after successful sync
- **Memory Management**: Event listeners are properly cleaned up on unmount

## PWA Integration

The hook integrates seamlessly with service workers:

```typescript
// Register service worker for background sync
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(registration => {
    // Service worker can handle sync queue persistence
    registration.sync.register('palmistry-background-sync');
  });
}
```

## Testing

The hook is thoroughly tested with:

```typescript
// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
});

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Test offline detection
it('should detect when going offline', () => {
  const { result } = renderHook(() => useOffline());
  
  expect(result.current.isOnline).toBe(true);
  
  // Simulate going offline
  Object.defineProperty(navigator, 'onLine', { value: false });
  fireEvent(window, new Event('offline'));
  
  expect(result.current.isOffline).toBe(true);
});
```

## Best Practices

1. **Queue Important Actions**: Only queue actions that users expect to persist
2. **Provide User Feedback**: Always inform users when actions are queued
3. **Handle Conflicts**: Consider how to handle data conflicts during sync
4. **Limit Queue Size**: Implement queue size limits to prevent memory issues
5. **Validate Before Sync**: Ensure data is still valid before syncing

## Related Components

- **[OfflineIndicator](../components/ui/OfflineIndicator.md)** - Uses this hook to display status
- **[SecurityProvider](../components/providers/SecurityProvider.md)** - May integrate for secure offline actions

## Browser Support

Compatible with browsers supporting:
- Navigator Online API (`navigator.onLine`)
- localStorage API
- Service Workers (for enhanced PWA features)
- Fetch API for sync operations

## Service Worker Integration

```javascript
// sw.js - Service worker background sync
self.addEventListener('sync', event => {
  if (event.tag === 'palmistry-background-sync') {
    event.waitUntil(processSyncQueue());
  }
});

async function processSyncQueue() {
  const queue = await getStoredSyncQueue();
  // Process queue items
}