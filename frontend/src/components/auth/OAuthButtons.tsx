'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';

interface OAuthProvider {
  name: string;
  display_name: string;
  login_url: string;
}

interface OAuthButtonsProps {
  className?: string;
  showDivider?: boolean;
}

const providerConfig = {
  google: {
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path
          fill="#4285f4"
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
          fill="#34a853"
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
          fill="#fbbc05"
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
          fill="#ea4335"
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
      </svg>
    ),
    bgColor: 'bg-white hover:bg-gray-50',
    textColor: 'text-gray-900',
    borderColor: 'border-gray-300'
  }
};

export const OAuthButtons: React.FC<OAuthButtonsProps> = ({
  className = '',
  showDivider = true
}) => {
  const [providers, setProviders] = React.useState<OAuthProvider[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    // Fetch available OAuth providers
    const fetchProviders = async () => {
      try {
        const response = await api.get('/api/v1/auth/oauth/providers');
        setProviders(response.data.providers || []);
      } catch (error) {
        console.error('Failed to fetch OAuth providers:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProviders();
  }, []);

  const handleOAuthLogin = (provider: OAuthProvider) => {
    // Redirect to backend OAuth endpoint
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.location.href = `${backendUrl}/api/v1${provider.login_url}`;
  };

  if (loading) {
    return (
      <div className={`space-y-3 ${className}`}>
        <div className="animate-pulse bg-gray-200 h-10 rounded-md"></div>
      </div>
    );
  }

  if (providers.length === 0) {
    return null;
  }

  return (
    <div className={className}>
      {showDivider && (
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or continue with</span>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {providers.map((provider) => {
          const config = providerConfig[provider.name as keyof typeof providerConfig];
          if (!config) return null;

          return (
            <Button
              key={provider.name}
              type="button"
              variant="outline"
              size="lg"
              onClick={() => handleOAuthLogin(provider)}
              className={`w-full ${config.bgColor} ${config.textColor} border ${config.borderColor} font-medium`}
            >
              <div className="flex items-center justify-center space-x-3">
                {config.icon}
                <span>Continue with {provider.display_name}</span>
              </div>
            </Button>
          );
        })}
      </div>
    </div>
  );
};