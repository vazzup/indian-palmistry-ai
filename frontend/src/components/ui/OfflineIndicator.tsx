'use client';

import React from 'react';
import { WifiOff, Wifi, Clock, RefreshCw } from 'lucide-react';
import { useOffline } from '@/hooks/useOffline';
import { Button } from './Button';
import { Card, CardContent } from './Card';

export const OfflineIndicator: React.FC = () => {
  const { isOnline, pendingActions, processPendingActions } = useOffline();

  if (isOnline && pendingActions.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 sm:left-auto sm:max-w-sm">
      <Card className={`${isOnline ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'}`}>
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {isOnline ? (
                <Wifi className="w-5 h-5 text-green-600" />
              ) : (
                <WifiOff className="w-5 h-5 text-red-600" />
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <h3 className={`text-sm font-medium ${
                isOnline ? 'text-yellow-800' : 'text-red-800'
              }`}>
                {isOnline ? 'Back Online' : 'You\'re Offline'}
              </h3>
              
              <p className={`text-xs mt-1 ${
                isOnline ? 'text-yellow-700' : 'text-red-700'
              }`}>
                {isOnline ? (
                  pendingActions.length > 0 ? (
                    `${pendingActions.length} pending action${pendingActions.length !== 1 ? 's' : ''} to sync`
                  ) : (
                    'All data synced successfully'
                  )
                ) : (
                  'Some features may not work. Changes will sync when back online.'
                )}
              </p>

              {isOnline && pendingActions.length > 0 && (
                <div className="mt-2 flex items-center space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={processPendingActions}
                    className="text-xs h-7"
                  >
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Sync Now
                  </Button>
                </div>
              )}

              {!isOnline && (
                <div className="mt-2 flex items-center text-red-600">
                  <Clock className="w-3 h-3 mr-1" />
                  <span className="text-xs">
                    Cached content available
                  </span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};