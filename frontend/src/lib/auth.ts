/**
 * @fileoverview Authentication store using Zustand
 * Provides centralized authentication state management with session persistence
 */

'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from './api';

export interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthState {
  // State
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string, name: string) => Promise<User>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<User | null>;
  clearError: () => void;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null,

      // Login action
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.login({ email, password });
          set({ 
            isAuthenticated: true, 
            user, 
            isLoading: false,
            error: null 
          });
          return user;
        } catch (error: any) {
          const errorMessage = error?.response?.data?.detail || 'Login failed';
          set({ 
            isLoading: false, 
            error: errorMessage,
            isAuthenticated: false,
            user: null 
          });
          throw error;
        }
      },

      // Register action
      register: async (email: string, password: string, name: string) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.register({ email, password, name });
          set({ 
            isAuthenticated: true, 
            user, 
            isLoading: false,
            error: null 
          });
          return user;
        } catch (error: any) {
          const errorMessage = error?.response?.data?.detail || 'Registration failed';
          set({ 
            isLoading: false, 
            error: errorMessage,
            isAuthenticated: false,
            user: null 
          });
          throw error;
        }
      },

      // Logout action
      logout: async () => {
        set({ isLoading: true });
        try {
          await authApi.logout();
        } catch (error) {
          // Even if logout fails on server, clear local state
          console.warn('Logout API call failed, clearing local state anyway');
        } finally {
          set({ 
            isAuthenticated: false, 
            user: null, 
            isLoading: false,
            error: null 
          });
        }
      },

      // Check authentication status
      checkAuth: async () => {
        // Don't set loading to true for background auth checks
        // This prevents loading states during app initialization
        try {
          const user = await authApi.getCurrentUser();
          set({ 
            isAuthenticated: true, 
            user,
            error: null 
          });
          return user;
        } catch (error: any) {
          // Clear authentication state if check fails
          set({ 
            isAuthenticated: false, 
            user: null,
            error: null // Don't show error for failed auth checks
          });
          return null;
        }
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },

      // Set user directly (for external updates)
      setUser: (user: User | null) => {
        set({ 
          user, 
          isAuthenticated: !!user,
          error: null 
        });
      },
    }),
    {
      name: 'auth-storage', // unique name for localStorage
      partialize: (state) => ({ 
        // Only persist user data, not loading states or errors
        isAuthenticated: state.isAuthenticated,
        user: state.user
      }),
    }
  )
);

// Convenience hook that matches the expected interface
export const useAuth = () => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const isLoading = useAuthStore(state => state.isLoading);
  const user = useAuthStore(state => state.user);
  const error = useAuthStore(state => state.error);
  const login = useAuthStore(state => state.login);
  const register = useAuthStore(state => state.register);
  const logout = useAuthStore(state => state.logout);
  const checkAuth = useAuthStore(state => state.checkAuth);
  const clearError = useAuthStore(state => state.clearError);

  return {
    isAuthenticated,
    isLoading,
    user,
    error,
    login,
    register,
    logout,
    checkAuth,
    clearError,
  };
};

export default useAuth;