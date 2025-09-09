'use client';

import React from 'react';
import { useAuthStore } from '@/lib/auth';

/**
 * AuthProvider component that handles automatic session checking
 * and provides authentication context to the entire application
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const checkAuth = useAuthStore(state => state.checkAuth);
  const isLoading = useAuthStore(state => state.isLoading);
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const user = useAuthStore(state => state.user);
  const [hasInitialized, setHasInitialized] = React.useState(false);

  React.useEffect(() => {
    const initializeAuth = async () => {
      console.log('AuthProvider: Starting authentication check...');
      console.log('AuthProvider: Current auth state before check:', { isAuthenticated, user: user?.email });
      
      try {
        // Check if user has a valid session with the server
        const authUser = await checkAuth();
        
        if (authUser) {
          console.log('AuthProvider: Valid session found for user:', authUser.email);
        } else {
          console.log('AuthProvider: No valid session - user needs to log in');
        }
        
        // Auth check completed successfully - set initialized
        console.log('AuthProvider: Auth check completed successfully, setting hasInitialized to true');
        setHasInitialized(true);
      } catch (error) {
        // Auth check failed, user is not authenticated
        console.error('AuthProvider: Auth check failed with error:', error);
        
        // Even on error, we consider auth initialized (just failed)
        console.log('AuthProvider: Auth check failed but initialization completed, setting hasInitialized to true');
        setHasInitialized(true);
      }
    };

    // Only initialize once when the app loads
    if (!hasInitialized) {
      console.log('AuthProvider: Initializing authentication for the first time');
      initializeAuth();
    }
  }, [checkAuth, hasInitialized, isAuthenticated, user]);

  // Show loading spinner only during initial authentication check
  if (!hasInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-amber-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
          {process.env.NODE_ENV === 'development' && (
            <p className="text-xs text-gray-500 mt-2">
              Loading: {isLoading ? 'true' : 'false'}, 
              Auth: {isAuthenticated ? 'true' : 'false'}, 
              User: {user?.email || 'none'}
            </p>
          )}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}