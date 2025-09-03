'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, Lock } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuth } from '@/lib/auth';
import type { LoginRequest } from '@/types';

const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  redirectTo?: string;
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ 
  redirectTo = '/dashboard', 
  onSuccess 
}) => {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuth();
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });
  
  React.useEffect(() => {
    clearError();
  }, [clearError]);
  
  const onSubmit = async (data: LoginFormData) => {
    try {
      clearError();
      await login(data.email, data.password);
      
      if (onSuccess) {
        onSuccess();
      } else {
        router.push(redirectTo);
      }
    } catch (error: any) {
      // Error is handled by the auth store
      console.error('Login failed:', error);
    }
  };
  
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center space-y-2">
        <div className="mx-auto w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center">
          <span className="text-saffron-600 text-xl">🪬</span>
        </div>
        <CardTitle className="text-2xl">Welcome Back</CardTitle>
        <CardDescription>
          Sign in to access your palm readings and conversations
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Global error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
          
          {/* Email field */}
          <Input
            {...register('email')}
            type="email"
            label="Email Address"
            placeholder="Enter your email"
            icon={<Mail className="w-4 h-4" />}
            error={errors.email?.message}
            disabled={isLoading || isSubmitting}
            autoComplete="email"
            autoFocus
          />
          
          {/* Password field */}
          <Input
            {...register('password')}
            type="password"
            label="Password"
            placeholder="Enter your password"
            icon={<Lock className="w-4 h-4" />}
            error={errors.password?.message}
            disabled={isLoading || isSubmitting}
            showPasswordToggle
            autoComplete="current-password"
          />
          
          {/* Submit button */}
          <Button
            type="submit"
            size="lg"
            loading={isLoading || isSubmitting}
            disabled={isLoading || isSubmitting}
            className="w-full"
          >
            {isLoading || isSubmitting ? 'Signing In...' : 'Sign In'}
          </Button>
          
          {/* Links */}
          <div className="text-center space-y-2">
            <button
              type="button"
              className="text-sm text-saffron-600 hover:text-saffron-700 underline"
              onClick={() => router.push('/reset')}
            >
              Forgot your password?
            </button>
            
            <div className="text-sm text-gray-600">
              Don't have an account?{' '}
              <button
                type="button"
                className="text-saffron-600 hover:text-saffron-700 font-medium underline"
                onClick={() => router.push('/register')}
              >
                Sign up
              </button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};