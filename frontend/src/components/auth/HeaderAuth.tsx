'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { User } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/lib/auth';

interface HeaderAuthProps {
  variant?: 'minimal' | 'full';
  className?: string;
}

/**
 * HeaderAuth - Subtle authentication header for the homepage
 * Features:
 * - Minimal design that doesn't overwhelm the main content
 * - Shows login/register buttons for unauthenticated users
 * - Shows user menu for authenticated users
 * - Cultural design elements with saffron theme
 * - Mobile-first responsive design
 */
export const HeaderAuth: React.FC<HeaderAuthProps> = ({ 
  variant = 'minimal',
  className = ''
}) => {
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuth();
  
  const handleLogin = () => {
    router.push('/login');
  };
  
  const handleRegister = () => {
    router.push('/register');
  };
  
  const handleLogout = async () => {
    try {
      await logout();
      router.push('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };
  
  const handleProfile = () => {
    router.push('/dashboard');
  };

  if (isAuthenticated && user) {
    return (
      <div className={`flex items-center justify-between p-4 ${className}`}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-saffron-100 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-saffron-600" />
          </div>
          <span className="text-sm font-medium text-gray-700">
            Welcome, {user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'Guest'}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={handleProfile}
            className="text-saffron-600 hover:text-saffron-700"
          >
            Dashboard
          </Button>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={handleLogout}
            className="text-gray-600 hover:text-gray-700"
          >
            Sign Out
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-end p-4 ${className}`}>
      <div className="flex items-center gap-3">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={handleLogin}
          className="text-gray-600 hover:text-saffron-600 hover:bg-saffron-50 transition-colors"
        >
          Sign In
        </Button>
        <Button 
          size="sm"
          onClick={handleRegister}
          className="bg-saffron-500 hover:bg-saffron-600 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
        >
          Sign Up
        </Button>
      </div>
    </div>
  );
};