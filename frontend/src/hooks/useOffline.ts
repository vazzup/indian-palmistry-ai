import { useState, useEffect } from 'react';

interface PendingAction {
  id: string;
  action: string;
  data: any;
  timestamp: number;
}

export const useOffline = () => {
  const [isOnline, setIsOnline] = useState(true);
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);

  useEffect(() => {
    // Initialize online status
    setIsOnline(navigator.onLine);

    // Load pending actions from localStorage
    const saved = localStorage.getItem('pendingActions');
    if (saved) {
      try {
        setPendingActions(JSON.parse(saved));
      } catch (error) {
        console.error('Failed to load pending actions:', error);
      }
    }

    const handleOnline = () => {
      setIsOnline(true);
      processPendingActions();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    // Save pending actions to localStorage whenever they change
    localStorage.setItem('pendingActions', JSON.stringify(pendingActions));
  }, [pendingActions]);

  const addPendingAction = (action: string, data: any) => {
    const newAction: PendingAction = {
      id: Date.now().toString(),
      action,
      data,
      timestamp: Date.now(),
    };

    setPendingActions(prev => [...prev, newAction]);
  };

  const processPendingActions = async () => {
    if (pendingActions.length === 0) return;

    console.log(`Processing ${pendingActions.length} pending actions...`);

    // Process actions one by one
    for (const action of pendingActions) {
      try {
        await processAction(action);
        // Remove successful action
        setPendingActions(prev => prev.filter(a => a.id !== action.id));
      } catch (error) {
        console.error('Failed to process pending action:', action, error);
        // Keep failed actions for retry
      }
    }
  };

  const processAction = async (action: PendingAction): Promise<void> => {
    // TODO: Implement actual action processing based on action type
    // This would integrate with your API layer
    console.log('Processing action:', action);

    switch (action.action) {
      case 'upload_analysis':
        // Re-attempt file upload
        break;
      case 'send_message':
        // Re-attempt message sending
        break;
      case 'create_conversation':
        // Re-attempt conversation creation
        break;
      default:
        console.warn('Unknown action type:', action.action);
    }
  };

  const clearPendingActions = () => {
    setPendingActions([]);
    localStorage.removeItem('pendingActions');
  };

  return {
    isOnline,
    pendingActions,
    addPendingAction,
    processPendingActions,
    clearPendingActions,
  };
};