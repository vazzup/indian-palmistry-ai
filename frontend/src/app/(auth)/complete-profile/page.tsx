'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import type { ProfileCompleteRequest } from '@/types';

const profileSchema = z.object({
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
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function CompleteProfilePage() {
  const router = useRouter();
  const { user, setUser } = useAuth();
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
  });

  // Redirect if user is not logged in or profile is already complete
  React.useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    // Check if profile is already complete
    if (user.age && user.gender) {
      // Check for pending analysis association
      const analysisId = sessionStorage.getItem('returnToAnalysis');
      if (analysisId) {
        router.push(`/analyses/${analysisId}`);
      } else {
        router.push('/dashboard');
      }
    }
  }, [user, router]);

  const onSubmit = async (data: ProfileFormData) => {
    if (!user) return;

    setIsSubmitting(true);
    setError('');

    try {
      const profileData: ProfileCompleteRequest = {
        age: data.age,
        gender: data.gender,
      };

      const response = await api.post('/api/v1/auth/complete-profile', profileData);
      const updatedUser = response.data;

      // Update user in auth store
      setUser(updatedUser);

      console.log('Profile completed successfully');

      // Check for pending analysis association and redirect accordingly
      const analysisId = sessionStorage.getItem('returnToAnalysis');
      if (analysisId) {
        console.log(`Redirecting to analysis ${analysisId} after profile completion`);
        router.push(`/analyses/${analysisId}`);
      } else {
        console.log('Redirecting to dashboard after profile completion');
        router.push('/dashboard');
      }
    } catch (error: any) {
      console.error('Profile completion failed:', error);
      const errorMessage = error?.response?.data?.detail || 'Failed to complete profile';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) {
    return null; // Will redirect to login
  }

  // Don't show the form if profile is already complete
  if (user.age && user.gender) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-saffron-50 to-turmeric-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-lg">
          <CardHeader className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-saffron-100 rounded-full flex items-center justify-center">
              <User className="w-8 h-8 text-saffron-600" />
            </div>
            <div>
              <CardTitle className="text-2xl font-bold text-gray-900">
                Complete Your Profile
              </CardTitle>
              <CardDescription className="text-gray-600 mt-2">
                We need a few more details to personalize your experience
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Display user info from OAuth */}
            <div className="bg-saffron-50 rounded-lg p-4 border border-saffron-200">
              <div className="flex items-center space-x-3">
                {user.picture && (
                  <img
                    src={user.picture}
                    alt={user.name || 'Profile'}
                    className="w-12 h-12 rounded-full border-2 border-white shadow-sm"
                  />
                )}
                <div>
                  <p className="font-medium text-gray-900">{user.name}</p>
                  <p className="text-sm text-gray-600">{user.email}</p>
                  {user.oauth_provider && (
                    <p className="text-xs text-saffron-600 capitalize">
                      Connected via {user.oauth_provider}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              {/* Age and Gender fields */}
              <div className="space-y-4">
                <Input
                  {...register('age', { valueAsNumber: true })}
                  type="number"
                  label="Age"
                  placeholder="Enter your age"
                  error={errors.age?.message}
                  disabled={isSubmitting}
                  min={13}
                  max={120}
                  required
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender *
                  </label>
                  <select
                    {...register('gender')}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500 disabled:bg-gray-50 disabled:text-gray-500 ${
                      errors.gender ? 'border-red-300' : 'border-gray-300'
                    }`}
                    disabled={isSubmitting}
                    required
                  >
                    <option value="">Select your gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                  {errors.gender && (
                    <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>
                  )}
                </div>
              </div>

              {/* Privacy notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                <div className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="text-blue-800 font-medium">Privacy Protected</p>
                    <p className="text-blue-700 mt-1">
                      This information is used to personalize your palmistry readings and is kept secure according to our Privacy Policy.
                    </p>
                  </div>
                </div>
              </div>

              {/* Age requirement notice */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <p className="text-xs text-yellow-800">
                  <strong>Age Requirement:</strong> You must be at least 13 years old to use this service in compliance with COPPA regulations.
                </p>
              </div>

              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-saffron-600 hover:bg-saffron-700"
                size="lg"
              >
                {isSubmitting ? 'Completing Profile...' : 'Complete Profile'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}