'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { BackgroundJobProgress } from '@/components/analysis/BackgroundJobProgress';
import { readingApi, handleApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function ReadingPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const analysisId = parseInt(params.id as string);
  
  const [initialCheck, setInitialCheck] = React.useState(true);

  // Check if reading is already completed on mount
  React.useEffect(() => {
    const checkInitialStatus = async () => {
      if (!analysisId || isNaN(analysisId)) {
        router.push('/');
        return;
      }

      try {
        // First, try to get the reading status
        const status = await readingApi.getReadingStatus(analysisId.toString());
        
        if (status.status === 'completed') {
          // Smart routing based on authentication status
          if (isAuthenticated) {
            // Logged-in users go directly to dashboard full reading
            router.push(`/readings/${analysisId}`);
          } else {
            // Anonymous users see summary page to encourage signup
            router.push(`/reading/${analysisId}/summary`);
          }
          return;
        }
        
        setInitialCheck(false);
      } catch (error: any) {
        console.error('Error checking initial status:', error);
        // If there's an error, let the polling component handle it
        setInitialCheck(false);
      }
    };

    checkInitialStatus();
  }, [analysisId, router]);

  const handleAnalysisComplete = (result: any) => {
    // Smart routing based on authentication status
    if (isAuthenticated) {
      // Logged-in users go directly to dashboard full reading
      router.push(`/readings/${analysisId}`);
    } else {
      // Anonymous users see summary page to encourage signup
      router.push(`/reading/${analysisId}/summary`);
    }
  };

  const handleAnalysisError = (error: string) => {
    console.error('Reading failed:', error);
    // Could redirect to error page or back to upload
    router.push('/?error=' + encodeURIComponent(error));
  };

  // Show loading state during initial check
  if (initialCheck) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-saffron-600 mx-auto mb-2"></div>
          <p className="text-muted-foreground">Checking reading status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-md mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold text-foreground">
            Reading Your Palm
          </h1>
          <p className="text-muted-foreground">
            Please wait while our AI reads your palm
          </p>
        </div>

        {/* Progress Component */}
        <BackgroundJobProgress 
          analysisId={analysisId}
          onComplete={handleAnalysisComplete}
          onError={handleAnalysisError}
        />

        {/* Back option */}
        <div className="text-center">
          <button 
            onClick={() => router.push('/')}
            className="text-saffron-600 hover:text-saffron-700 underline text-sm"
          >
            ← Back to Upload
          </button>
        </div>
      </div>
    </div>
  );
}