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
import { OAuthButtons } from '@/components/auth/OAuthButtons';
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
  age: z
    .number()
    .min(13, 'You must be at least 13 years old')
    .max(120, 'Please enter a valid age'),
  gender: z
    .string()
    .min(1, 'Please select your gender')
    .refine(val => ['Male', 'Female'].includes(val), {
      message: 'Please select a valid gender option'
    }),
  acceptTerms: z
    .boolean()
    .refine(val => val === true, {
      message: 'You must agree to the Terms of Service and Privacy Policy'
    }),
  acceptDisclaimer: z
    .boolean()
    .refine(val => val === true, {
      message: 'You must acknowledge this is for entertainment only'
    }),
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
    console.log('Form submitted with data:', { 
      name: data.name, 
      email: data.email, 
      acceptTerms: data.acceptTerms,
      acceptDisclaimer: data.acceptDisclaimer,
      password: '[REDACTED]' 
    });
    try {
      clearError();
      
      const registerData: RegisterRequest = {
        name: data.name,
        email: data.email,
        password: data.password,
        age: data.age,
        gender: data.gender,
      };

      console.log('Calling registerUser...');
      await registerUser(data.email, data.password, data.name, data.age, data.gender);
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
        <CardTitle className="text-2xl">Create Account</CardTitle>
        <CardDescription>
          Join us to unlock your full palm reading experience and save your conversations
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {/* OAuth Buttons */}
        <OAuthButtons className="mb-6" />

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

          {/* Age and Gender fields side by side */}
          <div className="grid grid-cols-2 gap-4">
            <Input
              {...register('age', { valueAsNumber: true })}
              type="number"
              label="Age"
              placeholder="Age"
              error={errors.age?.message}
              disabled={isLoading || isSubmitting}
              min={13}
              max={120}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gender
              </label>
              <select
                {...register('gender')}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500 disabled:bg-gray-50 disabled:text-gray-500 ${
                  errors.gender ? 'border-red-300' : 'border-gray-300'
                }`}
                disabled={isLoading || isSubmitting}
              >
                <option value="">Select gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
              {errors.gender && (
                <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>
              )}
            </div>
          </div>

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
          
          {/* Legal Agreement Checkboxes */}
          <div className="space-y-3">
            {/* Terms and Privacy Policy Agreement */}
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                {...register('acceptTerms')}
                type="checkbox"
                disabled={isLoading || isSubmitting}
                className="mt-1 w-4 h-4 text-saffron-600 bg-white border-gray-300 rounded focus:ring-saffron-500 focus:ring-2"
              />
              <div className="text-xs text-gray-700">
                I agree to the{' '}
                <button
                  type="button"
                  className="text-saffron-600 hover:text-saffron-700 underline font-medium"
                  onClick={() => window.open('/terms', '_blank')}
                >
                  Terms of Service
                </button>{' '}
                and{' '}
                <button
                  type="button"
                  className="text-saffron-600 hover:text-saffron-700 underline font-medium"
                  onClick={() => window.open('/privacy', '_blank')}
                >
                  Privacy Policy
                </button>
                {errors.acceptTerms && (
                  <div className="text-red-500 text-xs mt-1">{errors.acceptTerms.message}</div>
                )}
              </div>
            </label>

            {/* Entertainment Disclaimer Agreement */}
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                {...register('acceptDisclaimer')}
                type="checkbox"
                disabled={isLoading || isSubmitting}
                className="mt-1 w-4 h-4 text-saffron-600 bg-white border-gray-300 rounded focus:ring-saffron-500 focus:ring-2"
              />
              <div className="text-xs text-gray-700">
                <strong>I understand this is for entertainment purposes only</strong> and agree to the{' '}
                <button
                  type="button"
                  className="text-saffron-600 hover:text-saffron-700 underline font-medium"
                  onClick={() => window.open('/disclaimer', '_blank')}
                >
                  disclaimer
                </button>
                {errors.acceptDisclaimer && (
                  <div className="text-red-500 text-xs mt-1">{errors.acceptDisclaimer.message}</div>
                )}
              </div>
            </label>
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