/**
 * @fileoverview Authentication store using Zustand
 * Provides centralized authentication state management with session persistence
 */

'use client';

import React from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, analysisApi, handleApiError } from './api';

export interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  age?: number;
  gender?: string;
  oauth_provider?: string;
  oauth_email_verified?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CurrentAnalysis {
  id: number;
  user_id?: number;  // Optional because guest users don't have user_id
  status: string;
  created_at: string;
  updated_at: string;
  summary?: string;
  full_report?: string;
  key_features?: string[];
  strengths?: string[];
  guidance?: string[];
  left_image_url?: string;
  right_image_url?: string;
}

interface AuthState {
  // State
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  error: string | null;
  currentAnalysis: CurrentAnalysis | null;
  analysisLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string, name: string, age: number, gender: string) => Promise<User>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<User | null>;
  clearError: () => void;
  setUser: (user: User | null) => void;
  associateAnalysisIfNeeded: () => Promise<string | null>;
  fetchCurrentAnalysis: () => Promise<CurrentAnalysis | null>;
  setCurrentAnalysis: (analysis: CurrentAnalysis | null) => void;
  clearCurrentAnalysis: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null,
      currentAnalysis: null,
      analysisLoading: false,

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
      register: async (email: string, password: string, name: string, age: number, gender: string) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.register({ email, password, name, age, gender });
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
            error: null,
            currentAnalysis: null,
            analysisLoading: false
          });
        }
      },

      // Check authentication status
      checkAuth: async () => {
        // Don't set loading to true for background auth checks
        // This prevents loading states during app initialization
        const currentState = get();
        
        try {
          const user = await authApi.getCurrentUser();
          
          if (user) {
            // Valid user returned - set authenticated state
            set({ 
              isAuthenticated: true, 
              user,
              error: null 
            });
            return user;
          } else {
            // Null user returned (401 error) - clear auth state
            set({ 
              isAuthenticated: false, 
              user: null,
              error: null 
            });
            return null;
          }
        } catch (error: any) {
          // Network or other errors - clear authentication state
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

      // Associate analysis if returnToAnalysis exists in sessionStorage
      associateAnalysisIfNeeded: async () => {
        if (typeof window === 'undefined') return null;

        const analysisId = sessionStorage.getItem('returnToAnalysis');
        if (!analysisId) {
          console.log('No returnToAnalysis found in sessionStorage');
          return null;
        }

        try {
          console.log(`Attempting to associate analysis ${analysisId} with current user`);
          await analysisApi.associateAnalysis(analysisId);

          // Clear the sessionStorage after successful association
          sessionStorage.removeItem('returnToAnalysis');
          console.log(`Successfully associated analysis ${analysisId} and cleared sessionStorage`);

          return analysisId;
        } catch (error: any) {
          console.error(`Failed to associate analysis ${analysisId}:`, error);

          // Clear sessionStorage even on failure to prevent retry loops
          sessionStorage.removeItem('returnToAnalysis');

          // Don't throw error - we want login/register to succeed even if association fails
          return null;
        }
      },

      // Fetch current analysis for authenticated user
      fetchCurrentAnalysis: async () => {
        const { isAuthenticated } = get();

        if (!isAuthenticated) {
          console.log('[DEBUG] fetchCurrentAnalysis: Not authenticated, skipping');
          return null;
        }

        set({ analysisLoading: true });
        try {
          console.log('[DEBUG] fetchCurrentAnalysis: Fetching current analysis');
          const analysis = await analysisApi.getCurrentReading();
          console.log('[DEBUG] fetchCurrentAnalysis: Got analysis:', analysis?.id);
          set({ currentAnalysis: analysis, analysisLoading: false });
          return analysis;
        } catch (error: any) {
          console.log('[DEBUG] fetchCurrentAnalysis: Error:', error);
          // 404 means no current reading - this is normal
          const is404 = error?.response?.status === 404 ||
                        error?.status === 404 ||
                        error?.message?.includes('404') ||
                        error?.message?.includes('not found');

          if (is404) {
            console.log('[DEBUG] fetchCurrentAnalysis: No current reading found (404)');
            set({ currentAnalysis: null, analysisLoading: false });
            return null;
          }

          // Other errors - log but don't throw
          console.error('Failed to fetch current analysis:', error);
          set({ currentAnalysis: null, analysisLoading: false });
          return null;
        }
      },

      // Set current analysis directly
      setCurrentAnalysis: (analysis: CurrentAnalysis | null) => {
        console.log('[DEBUG] setCurrentAnalysis:', analysis?.id);
        set({ currentAnalysis: analysis });
      },

      // Clear current analysis
      clearCurrentAnalysis: () => {
        console.log('[DEBUG] clearCurrentAnalysis');
        set({ currentAnalysis: null });
      },
    }),
    {
      name: 'auth-storage', // unique name for localStorage
      partialize: (state) => ({
        // Only persist user data and current analysis, not loading states or errors
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        currentAnalysis: state.currentAnalysis
      }),
    }
  )
);

// Convenience hook that matches the expected interface
export const useAuth = () => {
  const storedIsAuthenticated = useAuthStore(state => state.isAuthenticated);
  const isLoading = useAuthStore(state => state.isLoading);
  const user = useAuthStore(state => state.user);
  const error = useAuthStore(state => state.error);
  const currentAnalysis = useAuthStore(state => state.currentAnalysis);
  const analysisLoading = useAuthStore(state => state.analysisLoading);
  const login = useAuthStore(state => state.login);
  const register = useAuthStore(state => state.register);
  const logout = useAuthStore(state => state.logout);

  // Fix invalid state: cannot be authenticated without user data
  const isAuthenticated = storedIsAuthenticated && user !== null;


  // If we detect invalid state, clear it
  React.useEffect(() => {
    if (storedIsAuthenticated && !user) {
      useAuthStore.setState({
        isAuthenticated: false,
        user: null
      });
    }
  }, [storedIsAuthenticated, user]);
  const checkAuth = useAuthStore(state => state.checkAuth);
  const clearError = useAuthStore(state => state.clearError);
  const setUser = useAuthStore(state => state.setUser);
  const associateAnalysisIfNeeded = useAuthStore(state => state.associateAnalysisIfNeeded);
  const fetchCurrentAnalysis = useAuthStore(state => state.fetchCurrentAnalysis);
  const setCurrentAnalysis = useAuthStore(state => state.setCurrentAnalysis);
  const clearCurrentAnalysis = useAuthStore(state => state.clearCurrentAnalysis);

  return {
    isAuthenticated,
    isLoading,
    user,
    error,
    currentAnalysis,
    analysisLoading,
    login,
    register,
    logout,
    checkAuth,
    clearError,
    setUser,
    associateAnalysisIfNeeded,
    fetchCurrentAnalysis,
    setCurrentAnalysis,
    clearCurrentAnalysis,
  };
};

export default useAuth;