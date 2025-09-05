'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, Lock, User } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuth } from '@/lib/auth';
import type { RegisterRequest } from '@/types';

const registerSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .min(2, 'Name must be at least 2 characters')
    .max(50, 'Name cannot exceed 50 characters'),
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      'Password must include uppercase, lowercase, and number'
    ),
  confirmPassword: z
    .string()
    .min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

interface RegisterFormProps {
  redirectTo?: string;
  onSuccess?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ 
  redirectTo = '/dashboard', 
  onSuccess 
}) => {
  const router = useRouter();
  const { register: registerUser, isLoading, error, clearError, associateAnalysisIfNeeded } = useAuth();
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });
  
  React.useEffect(() => {
    clearError();
  }, []); // Remove clearError from dependency array to prevent infinite calls
  
  const onSubmit = async (data: RegisterFormData) => {
    console.log('Form submitted with data:', data);
    try {
      clearError();
      
      const registerData: RegisterRequest = {
        name: data.name,
        email: data.email,
        password: data.password,
      };
      
      console.log('Calling registerUser...');
      await registerUser(data.email, data.password, data.name);
      console.log('Registration successful');
      
      // Try to associate any pending anonymous analysis
      const associatedAnalysisId = await associateAnalysisIfNeeded();
      
      if (onSuccess) {
        onSuccess();
      } else {
        // If we associated an analysis, redirect to it instead of default redirect
        if (associatedAnalysisId) {
          console.log(`Registration successful - redirecting to associated analysis ${associatedAnalysisId}`);
          router.push(`/analyses/${associatedAnalysisId}`);
        } else {
          console.log('Registration successful - using default redirect:', redirectTo);
          router.push(redirectTo);
        }
      }
    } catch (error: any) {
      // Error is handled by the auth store
      console.error('Registration failed:', error);
    }
  };
  
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center space-y-2">
        <div className="mx-auto w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center">
          <span className="text-saffron-600 text-xl">🌸</span>
        </div>
        <CardTitle className="text-2xl">Create Account</CardTitle>
        <CardDescription>
          Join us to unlock your full palm reading experience and save your conversations
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
          
          {/* Name field */}
          <Input
            {...register('name')}
            type="text"
            label="Full Name"
            placeholder="Enter your full name"
            icon={<User className="w-4 h-4" />}
            error={errors.name?.message}
            disabled={isLoading || isSubmitting}
            autoComplete="name"
            autoFocus
          />
          
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
          />
          
          {/* Password field */}
          <Input
            {...register('password')}
            type="password"
            label="Password"
            placeholder="Create a strong password"
            icon={<Lock className="w-4 h-4" />}
            error={errors.password?.message}
            disabled={isLoading || isSubmitting}
            showPasswordToggle
            autoComplete="new-password"
            helpText="Must include uppercase, lowercase, and number"
          />
          
          {/* Confirm Password field */}
          <Input
            {...register('confirmPassword')}
            type="password"
            label="Confirm Password"
            placeholder="Confirm your password"
            icon={<Lock className="w-4 h-4" />}
            error={errors.confirmPassword?.message}
            disabled={isLoading || isSubmitting}
            showPasswordToggle
            autoComplete="new-password"
          />
          
          {/* Terms notice */}
          <div className="text-xs text-muted-foreground">
            By creating an account, you agree to our{' '}
            <button
              type="button"
              className="text-saffron-600 hover:text-saffron-700 underline"
              onClick={() => window.open('/terms', '_blank')}
            >
              Terms of Service
            </button>{' '}
            and{' '}
            <button
              type="button"
              className="text-saffron-600 hover:text-saffron-700 underline"
              onClick={() => window.open('/privacy', '_blank')}
            >
              Privacy Policy
            </button>
          </div>
          
          {/* Submit button */}
          <Button
            type="submit"
            size="lg"
            loading={isLoading || isSubmitting}
            disabled={isLoading || isSubmitting}
            className="w-full"
          >
            {isLoading || isSubmitting ? 'Creating Account...' : 'Create Account'}
          </Button>
          
          {/* Links */}
          <div className="text-center">
            <div className="text-sm text-gray-600">
              Already have an account?{' '}
              <button
                type="button"
                className="text-saffron-600 hover:text-saffron-700 font-medium underline"
                onClick={() => router.push('/login')}
              >
                Sign in
              </button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};