'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, ArrowLeft, Hand } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { getRandomMessage } from '@/lib/cultural-theme';

const resetSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
});

type ResetFormData = z.infer<typeof resetSchema>;

export default function ResetPasswordPage() {
  const router = useRouter();
  const [isSubmitted, setIsSubmitted] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);
  const [welcomeMessage] = React.useState(() => getRandomMessage('healing'));
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    getValues,
  } = useForm<ResetFormData>({
    resolver: zodResolver(resetSchema),
  });
  
  const onSubmit = async (data: ResetFormData) => {
    try {
      setIsLoading(true);
      
      // TODO: Implement actual password reset API call
      // For now, simulate a delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setIsSubmitted(true);
    } catch (error: any) {
      console.error('Password reset failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        {/* Header */}
        <div className="py-8 px-4">
          <div className="max-w-md mx-auto text-center space-y-4">
            {/* Logo */}
            <div 
              className="mx-auto w-16 h-16 bg-gradient-to-br from-saffron-400 to-saffron-600 rounded-full flex items-center justify-center cursor-pointer"
              onClick={() => router.push('/')}
            >
              <Hand className="w-8 h-8 text-white" />
            </div>
            
            {/* App Title */}
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                Check Your Email
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                {welcomeMessage}
              </p>
            </div>
          </div>
        </div>

        {/* Success Message */}
        <div className="flex-1 px-4 pb-8">
          <Card className="w-full max-w-md mx-auto">
            <CardHeader className="text-center space-y-2">
              <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-xl">✉️</span>
              </div>
              <CardTitle className="text-xl">Email Sent!</CardTitle>
              <CardDescription>
                We've sent password reset instructions to <strong>{getValues('email')}</strong>
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div className="text-sm text-muted-foreground text-center">
                <p>Check your inbox and click the reset link to create a new password.</p>
                <p className="mt-2">If you don't see the email, check your spam folder.</p>
              </div>
              
              <div className="space-y-2">
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => {
                    setIsSubmitted(false);
                    setIsLoading(false);
                  }}
                  className="w-full"
                >
                  Try Different Email
                </Button>
                
                <Button
                  size="lg"
                  onClick={() => router.push('/login')}
                  className="w-full"
                >
                  Back to Sign In
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="py-6 px-4 text-center">
          <p className="text-xs text-muted-foreground">
            🔒 For security, reset links expire in 15 minutes
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="py-8 px-4">
        <div className="max-w-md mx-auto text-center space-y-4">
          {/* Logo */}
          <div 
            className="mx-auto w-16 h-16 bg-gradient-to-br from-saffron-400 to-saffron-600 rounded-full flex items-center justify-center cursor-pointer"
            onClick={() => router.push('/')}
          >
            <Hand className="w-8 h-8 text-white" />
          </div>
          
          {/* App Title */}
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Reset Password
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {welcomeMessage}
            </p>
          </div>
        </div>
      </div>

      {/* Reset Form */}
      <div className="flex-1 px-4 pb-8">
        <Card className="w-full max-w-md mx-auto">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center">
              <span className="text-saffron-600 text-xl">🔑</span>
            </div>
            <CardTitle className="text-2xl">Forgot Password?</CardTitle>
            <CardDescription>
              Enter your email address and we'll send you a link to reset your password
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Email field */}
              <Input
                {...register('email')}
                type="email"
                label="Email Address"
                placeholder="Enter your email"
                icon={<Mail className="w-4 h-4" />}
                error={errors.email?.message}
                disabled={isLoading}
                autoComplete="email"
                autoFocus
              />
              
              {/* Submit button */}
              <Button
                type="submit"
                size="lg"
                loading={isLoading}
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? 'Sending Reset Link...' : 'Send Reset Link'}
              </Button>
              
              {/* Back to login */}
              <div className="text-center">
                <button
                  type="button"
                  className="text-sm text-saffron-600 hover:text-saffron-700 inline-flex items-center gap-1"
                  onClick={() => router.push('/login')}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Sign In
                </button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <div className="py-6 px-4 text-center">
        <p className="text-xs text-muted-foreground">
          🔒 Reset links are secure and expire for your protection
        </p>
      </div>
    </div>
  );
}