'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Eye, Lock, Sparkles, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AuthenticationModal } from '@/components/auth/AuthenticationModal';
import { LoadingPage } from '@/components/ui/Spinner';
import { analysisApi, handleApiError } from '@/lib/api';
import { getRandomMessage } from '@/lib/cultural-theme';
import { useAuth } from '@/lib/auth';
import { getGuestAnalysisId } from '@/lib/guest-analysis';
import type { Analysis } from '@/types';

export default function ReadingSummaryPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();

  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = React.useState(false);
  const [successMessage] = React.useState(() => getRandomMessage('completion'));

  React.useEffect(() => {
    const fetchAnalysis = async () => {
      // Get analysis ID from session storage instead of URL
      const analysisId = getGuestAnalysisId();

      if (!analysisId) {
        setError('No reading found. Please start a new reading from the homepage.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const analysisData = await analysisApi.getAnalysisSummary(analysisId);
        setAnalysis(analysisData);
      } catch (err: any) {
        const errorMessage = handleApiError(err);
        setError(errorMessage);

        // If analysis not found, it might have been deleted or expired
        if (errorMessage.includes('not found') || errorMessage.includes('404')) {
          setError('This reading is no longer available. Please start a new reading.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, []);

  // If user becomes authenticated while on this page, redirect appropriately
  React.useEffect(() => {
    if (isAuthenticated && analysis) {
      // User authenticated while viewing summary - redirect to their reading page
      router.push('/reading');
    }
  }, [isAuthenticated, analysis, router]);

  if (loading) {
    return <LoadingPage message="Loading your palm reading..." />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4 md:px-6 lg:px-8">
        <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto border-red-200">
          <CardContent className="p-6 text-center">
            <div className="text-red-600 mb-4">
              <Eye className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold text-red-700 mb-2">
              Reading Not Available
            </h2>
            <p className="text-red-600 text-sm mb-4">
              {error}
            </p>
            <Button
              onClick={() => router.push('/')}
              className="bg-saffron-600 hover:bg-saffron-700 text-white"
            >
              Start New Reading
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4 md:px-6 lg:px-8">
        <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto">
          <CardContent className="p-6 text-center">
            <div className="text-saffron-600 mb-4">
              <Eye className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold mb-2">
              No Reading Found
            </h2>
            <p className="text-muted-foreground text-sm mb-4">
              We couldn't find your palm reading. Please start a new one.
            </p>
            <Button
              onClick={() => router.push('/')}
              className="bg-saffron-600 hover:bg-saffron-700 text-white"
            >
              Start New Reading
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (analysis.status?.toLowerCase() === 'failed') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4 md:px-6 lg:px-8">
        <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto border-red-200">
          <CardContent className="p-6 text-center">
            <div className="text-red-600 mb-4">
              <Eye className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold text-red-700 mb-2">
              Analysis Failed
            </h2>
            <p className="text-red-600 text-sm mb-4">
              {analysis.error_message || 'The palm reading could not be completed.'}
            </p>
            <Button
              onClick={() => router.push('/')}
              className="bg-saffron-600 hover:bg-saffron-700 text-white"
            >
              Try With Different Images
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (analysis.status?.toLowerCase() !== 'completed' || !analysis.summary) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4 md:px-6 lg:px-8">
        <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto">
          <CardContent className="p-6 text-center">
            <div className="text-saffron-600 mb-4">
              <Sparkles className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold mb-2">
              Analysis In Progress
            </h2>
            <p className="text-muted-foreground text-sm">
              Your palm reading is still being prepared. Please wait a moment and refresh the page.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8 px-4 md:px-6 lg:px-8">
      <div className="max-w-md md:max-w-2xl lg:max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-saffron-400 to-saffron-600 rounded-full flex items-center justify-center">
            <Eye className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">
            {successMessage}
          </h1>
          <p className="text-muted-foreground">
            Here's a glimpse of your palm reading
          </p>
        </div>

        {/* Summary Card */}
        <Card className="border-saffron-200 bg-gradient-to-br from-saffron-50 to-orange-50">
          <CardHeader>
            <CardTitle className="text-saffron-800 flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              Your Palm Reading Summary
            </CardTitle>
            <CardDescription className="text-saffron-700">
              Based on traditional Indian palmistry (Hast Rekha Shastra)
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Summary Text */}
            <div className="bg-white/70 rounded-lg p-4 border border-saffron-200">
              <p className="text-gray-800 leading-relaxed">
                {analysis.summary}
              </p>
            </div>

            {/* Full Reading CTA */}
            <button
              onClick={() => setShowAuthModal(true)}
              className="bg-white/50 rounded-lg p-3 border border-saffron-200 hover:bg-white/80 hover:border-saffron-300 transition-all duration-200 w-full text-left cursor-pointer active:bg-white/90"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-saffron-600" />
                  <span className="text-sm font-medium text-saffron-800">
                    Unlock your complete reading
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-saffron-600" />
              </div>
              <p className="text-xs text-saffron-700 mt-1">
                Sign up or log in to save this reading and get complete insights about your life, relationships, and future
              </p>
            </button>

            {/* Analysis metadata */}
            <div className="text-center text-xs text-saffron-600 space-y-1">
              <p>Analysis completed in {
                analysis.processing_completed_at && analysis.processing_started_at
                  ? Math.round((new Date(analysis.processing_completed_at).getTime() -
                               new Date(analysis.processing_started_at).getTime()) / 1000)
                  : 'Unknown'
              } seconds</p>
              <p>Based on {analysis.tokens_used || 'many'} AI insights</p>
            </div>
          </CardContent>
        </Card>

        {/* Authentication Modal */}
        <AuthenticationModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          analysisId={analysis.id}
        />

        {/* Primary CTA */}
        {!showAuthModal && (
          <Card
            className="border-dashed border-saffron-300 bg-saffron-50/50 hover:bg-saffron-100/50 transition-colors cursor-pointer"
            onClick={() => setShowAuthModal(true)}
          >
            <CardContent className="p-4 text-center">
              <Lock className="w-8 h-8 text-saffron-500 mx-auto mb-2" />
              <p className="text-sm font-medium text-saffron-800 mb-1">
                Ready to unlock your complete reading?
              </p>
              <p className="text-xs text-saffron-600">
                Create an account to save this reading and ask questions about it
              </p>
            </CardContent>
          </Card>
        )}

        {/* Disclaimer */}
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            For entertainment purposes only. Not professional advice.
          </p>
        </div>
      </div>
    </div>
  );
}