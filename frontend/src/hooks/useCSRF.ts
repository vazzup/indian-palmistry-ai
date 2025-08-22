import { useState, useEffect } from 'react';
import { authApi } from '@/lib/api';

export const useCSRF = () => {
  const [csrfToken, setCSRFToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchCSRFToken = async () => {
      try {
        setIsLoading(true);
        
        // Try to get from meta tag first
        const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (metaToken) {
          setCSRFToken(metaToken);
          return;
        }

        // Fetch from API
        const token = await authApi.getCSRFToken();
        setCSRFToken(token);

        // Update meta tag for axios interceptor
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
          metaTag.setAttribute('content', token);
        } else {
          const newMetaTag = document.createElement('meta');
          newMetaTag.name = 'csrf-token';
          newMetaTag.content = token;
          document.head.appendChild(newMetaTag);
        }
      } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCSRFToken();
  }, []);

  const refreshCSRFToken = async () => {
    setIsLoading(true);
    try {
      const token = await authApi.getCSRFToken();
      setCSRFToken(token);
      
      // Update meta tag
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) {
        metaTag.setAttribute('content', token);
      }
    } catch (error) {
      console.error('Failed to refresh CSRF token:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    csrfToken,
    isLoading,
    refreshCSRFToken,
  };
};