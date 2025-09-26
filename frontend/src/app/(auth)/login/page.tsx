'use client';

import React, { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Hand } from 'lucide-react';
import { LoginForm } from '@/components/auth/LoginForm';
import { Spinner } from '@/components/ui/Spinner';
import { getRandomMessage } from '@/lib/cultural-theme';
import { LegalNotice } from '@/components/legal/LegalNotice';

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [welcomeMessage, setWelcomeMessage] = React.useState('Discover the ancient wisdom of your palms');
  
  React.useEffect(() => {
    setWelcomeMessage(getRandomMessage('welcome'));
  }, []);
  
  // Get redirect URL from query params
  const redirectTo = searchParams.get('redirect') || '/reading';
  const analysisId = searchParams.get('analysis');
  
  const handleLoginSuccess = async () => {
    // Check if user is coming from reading-summary page and has a guest analysis to claim
    const { getGuestAnalysisId, clearGuestAnalysisId, migrateFromReturnToAnalysis } = await import('@/lib/guest-analysis');
    const { analysisApi } = await import('@/lib/api');

    // Migrate from old returnToAnalysis key if needed (backward compatibility)
    migrateFromReturnToAnalysis();

    const guestAnalysisId = getGuestAnalysisId();

    if (guestAnalysisId && (redirectTo === 'reading-summary' || searchParams.get('redirect') === 'reading-summary')) {
      try {
        console.log(`Claiming guest reading ${guestAnalysisId} after login`);
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
    <div className="h-screen bg-background flex flex-col justify-center py-4 overflow-hidden">
      {/* Header */}
      <div className="px-4 mb-6">
        <div className="max-w-md mx-auto text-center space-y-3">
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

      {/* Login Form */}
      <div className="px-4">
        <LoginForm 
          redirectTo={redirectTo}
          onSuccess={handleLoginSuccess}
        />
      </div>

      {/* Footer */}
      <div className="px-4 mt-6">
        <p className="text-xs text-muted-foreground text-center">
          Your privacy is protected. We use secure authentication.
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner message="Loading..." />
      </div>
    }>
      <LoginPageContent />
    </Suspense>
  );
}
