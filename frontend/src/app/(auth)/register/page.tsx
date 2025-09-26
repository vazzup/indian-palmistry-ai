'use client';

import React, { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Hand } from 'lucide-react';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { Spinner } from '@/components/ui/Spinner';
import { getRandomMessage } from '@/lib/cultural-theme';

function RegisterPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [welcomeMessage, setWelcomeMessage] = React.useState('Discover the ancient wisdom of your palms');
  
  // Set random message after mount to avoid hydration mismatch
  React.useEffect(() => {
    setWelcomeMessage(getRandomMessage('welcome'));
  }, []);
  
  // Get redirect URL from query params
  const redirectTo = searchParams.get('redirect') || '/reading';
  const analysisId = searchParams.get('analysis');
  
  const handleRegisterSuccess = async () => {
    // Check if user is coming from reading-summary page and has a guest analysis to claim
    const { getGuestAnalysisId, clearGuestAnalysisId, migrateFromReturnToAnalysis } = await import('@/lib/guest-analysis');
    const { analysisApi } = await import('@/lib/api');

    // Migrate from old returnToAnalysis key if needed (backward compatibility)
    migrateFromReturnToAnalysis();

    const guestAnalysisId = getGuestAnalysisId();

    if (guestAnalysisId && (redirectTo === 'reading-summary' || searchParams.get('redirect') === 'reading-summary')) {
      try {
        console.log(`Claiming guest reading ${guestAnalysisId} after registration`);
        await analysisApi.claimReading(guestAnalysisId);
        clearGuestAnalysisId();
        console.log('Guest reading claimed successfully, redirecting to /reading');
        router.push('/reading');
        return;
      } catch (error) {
        console.error('Failed to claim guest reading:', error);
        // If claiming fails, clear the ID and continue with normal flow
        clearGuestAnalysisId();
      }
    }

    // Legacy support for old analysis association flow
    if (analysisId) {
      // Redirect to specific analysis if coming from login gate (URL parameter)
      // In the new model, this should redirect to /reading instead
      router.push('/reading');
    } else {
      // Default redirect
      router.push(redirectTo);
    }
  };

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
              Indian Palmistry AI
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {welcomeMessage}
            </p>
          </div>
        </div>
      </div>

      {/* Register Form */}
      <div className="flex-1 px-4 pb-8">
        <RegisterForm 
          redirectTo={redirectTo}
          onSuccess={handleRegisterSuccess}
        />
      </div>

      {/* Footer */}
      <div className="py-6 px-4 text-center">
        <p className="text-xs text-muted-foreground">
          Your data is secure and will never be shared
        </p>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner message="Loading..." />
      </div>
    }>
      <RegisterPageContent />
    </Suspense>
  );
}