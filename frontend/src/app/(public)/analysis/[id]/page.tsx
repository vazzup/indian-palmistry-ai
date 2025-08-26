'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { BackgroundJobProgress } from '@/components/analysis/BackgroundJobProgress';
import { analysisApi, handleApiError } from '@/lib/api';

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = parseInt(params.id as string);
  
  const [initialCheck, setInitialCheck] = React.useState(true);

  // Check if analysis is already completed on mount
  React.useEffect(() => {
    const checkInitialStatus = async () => {
      if (!analysisId || isNaN(analysisId)) {
        router.push('/');
        return;
      }

      try {
        // First, try to get the analysis status
        const status = await analysisApi.getAnalysisStatus(analysisId.toString());
        
        if (status.status === 'completed') {
          // If already completed, redirect immediately to summary
          router.push(`/analysis/${analysisId}/summary`);
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
    // Navigate to the summary page
    router.push(`/analysis/${analysisId}/summary`);
  };

  const handleAnalysisError = (error: string) => {
    console.error('Analysis failed:', error);
    // Could redirect to error page or back to upload
    router.push('/?error=' + encodeURIComponent(error));
  };

  // Show loading state during initial check
  if (initialCheck) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-saffron-600 mx-auto mb-2"></div>
          <p className="text-muted-foreground">Checking analysis status...</p>
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
            Analyzing Your Palm
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