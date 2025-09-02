import React from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, clearCSRFTokenCache } from './api';
import type { User, LoginRequest, RegisterRequest } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: LoginRequest) => {
        try {
          set({ isLoading: true, error: null });
          
          const response = await authApi.login(credentials);
          
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null 
          });
        } catch (error: any) {
          // The error is already processed by the API client
          const errorMessage = error.message || 'Login failed';
          set({ 
            isLoading: false, 
            error: errorMessage,
            isAuthenticated: false,
            user: null 
          });
          throw error;
        }
      },

      register: async (data: RegisterRequest) => {
        try {
          set({ isLoading: true, error: null });
          
          const response = await authApi.register(data);
          
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null 
          });
        } catch (error: any) {
          // The error is already processed by the API client
          const errorMessage = error.message || 'Registration failed';
          set({ 
            isLoading: false, 
            error: errorMessage,
            isAuthenticated: false,
            user: null 
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          set({ isLoading: true, error: null });
          
          await authApi.logout();
          
          // Clear CSRF token cache on logout
          clearCSRFTokenCache();
          
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: null 
          });
        } catch (error: any) {
          // Even if logout fails on server, clear local state and CSRF cache
          clearCSRFTokenCache();
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: null 
          });
        }
      },

      checkAuth: async () => {
        try {
          set({ isLoading: true });
          
          const user = await authApi.getCurrentUser();
          
          if (user) {
            set({ 
              user, 
              isAuthenticated: true, 
              isLoading: false,
              error: null 
            });
          } else {
            // User is not authenticated (401 response handled in api.ts)
            set({ 
              user: null, 
              isAuthenticated: false, 
              isLoading: false,
              error: null 
            });
          }
        } catch (error: any) {
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: null 
          });
        }
      },

      clearError: () => set({ error: null }),
      
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Auth utility functions
export const getAuthState = () => useAuthStore.getState();

export const isAuthenticated = () => getAuthState().isAuthenticated;

export const requireAuth = () => {
  const { isAuthenticated, user } = getAuthState();
  if (!isAuthenticated || !user) {
    throw new Error('Authentication required');
  }
  return user;
};

// Higher-order component for protected routes
export const withAuth = function <P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  const AuthenticatedComponent: React.ComponentType<P> = (props: P) => {
    const { isAuthenticated, checkAuth, isLoading } = useAuthStore();
    
    // DISABLE automatic auth checking to prevent infinite loops
    // Protected components should manually call checkAuth() when needed

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="cultural-spinner w-8 h-8" />
        </div>
      );
    }

    if (!isAuthenticated) {
      // This will be handled by the auth interceptor
      return null;
    }

    return <Component {...props} />;
  };
  
  return AuthenticatedComponent;
};

// Hook for auth state with enhanced session management
export const useAuth = () => {
  const store = useAuthStore();
  
  // Add session management methods
  const extendedStore = {
    ...store,
    
    // Get list of active sessions
    getSessions: async () => {
      try {
        const response = await authApi.getSessions();
        return response.sessions || [];
      } catch (error: any) {
        console.error('Failed to get sessions:', error);
        throw error;
      }
    },
    
    // Invalidate all other sessions
    invalidateAllSessions: async () => {
      try {
        const response = await authApi.invalidateAllSessions();
        return response;
      } catch (error: any) {
        console.error('Failed to invalidate sessions:', error);
        throw error;
      }
    },
    
    // Rotate current session for enhanced security
    rotateSession: async () => {
      try {
        const response = await authApi.rotateSession();
        return response;
      } catch (error: any) {
        console.error('Failed to rotate session:', error);
        throw error;
      }
    },
    
    // Enhanced auth checking with better error handling
    checkAuthWithRetry: async (retries = 2): Promise<boolean> => {
      for (let i = 0; i < retries; i++) {
        try {
          await store.checkAuth();
          return store.isAuthenticated;
        } catch (error: any) {
          console.error(`Auth check attempt ${i + 1} failed:`, error);
          if (i === retries - 1) {
            // Final attempt failed, clear state
            store.setLoading(false);
            useAuthStore.setState({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null
            });
            return false;
          }
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
      }
      return false;
    }
  };
  
  return extendedStore;
};