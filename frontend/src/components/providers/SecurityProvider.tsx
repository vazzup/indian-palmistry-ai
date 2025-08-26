'use client';

import React from 'react';
import { setupCSPReporting, sessionManager } from '@/lib/security';
import { useAuth } from '@/lib/auth';

interface SecurityProviderProps {
  children: React.ReactNode;
}

export const SecurityProvider: React.FC<SecurityProviderProps> = ({ children }) => {
  // TEMPORARILY DISABLE ALL AUTH FUNCTIONALITY TO STOP INFINITE REQUESTS
  const isAuthenticated = false;
  const logout = undefined;
  
  // Commenting out useAuth call temporarily
  // const auth = useAuth();
  // const isAuthenticated = auth.isAuthenticated;
  // const logout = auth.logout;

  React.useEffect(() => {
    // Set up CSP violation reporting
    setupCSPReporting();

    // Set up session management for authenticated users
    if (isAuthenticated) {
      sessionManager.startSession();

      // Listen for session warning events
      const handleSessionWarning = () => {
        // You could show a modal or notification here
        console.warn('Session will expire soon');
      };

      const handleUserActivity = () => {
        // Extend session on user activity
        sessionManager.extendSession();
      };

      // Listen for user activity to extend session
      const activityEvents = ['click', 'keydown', 'scroll', 'mousemove'];
      
      activityEvents.forEach(event => {
        document.addEventListener(event, handleUserActivity, { passive: true });
      });

      window.addEventListener('sessionWarning', handleSessionWarning);

      return () => {
        sessionManager.clearTimeouts();
        activityEvents.forEach(event => {
          document.removeEventListener(event, handleUserActivity);
        });
        window.removeEventListener('sessionWarning', handleSessionWarning);
      };
    }
  }, [isAuthenticated, logout]);

  // Monitor for authentication state changes
  React.useEffect(() => {
    if (!isAuthenticated) {
      sessionManager.clearTimeouts();
    }
  }, [isAuthenticated]);

  return <>{children}</>;
};