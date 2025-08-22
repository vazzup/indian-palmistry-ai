'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { Eye, Lock, Sparkles, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoginGate } from '@/components/auth/LoginGate';
import { LoadingPage } from '@/components/ui/Spinner';
import { analysisApi, handleApiError } from '@/lib/api';
import { getRandomMessage } from '@/lib/cultural-theme';
import type { Analysis } from '@/types';

export default function AnalysisSummaryPage() {
  const params = useParams();
  const analysisId = parseInt(params.id as string);
  
  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showLoginGate, setShowLoginGate] = React.useState(false);
  const [successMessage] = React.useState(() => getRandomMessage('success'));

  React.useEffect(() => {
    const fetchAnalysis = async () => {
      if (!analysisId || isNaN(analysisId)) {
        setError('Invalid analysis ID');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const analysisData = await analysisApi.getAnalysisSummary(analysisId);
        setAnalysis(analysisData);
        
        // Show login gate after a brief moment to let user read the summary
        setTimeout(() => setShowLoginGate(true), 3000);
      } catch (err: any) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [analysisId]);

  if (loading) {
    return <LoadingPage message="Loading your palm reading..." />;
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <Card className="w-full max-w-md mx-auto border-red-200">
          <CardContent className="p-6 text-center">
            <div className="text-red-600 mb-4">
              <Eye className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold text-red-700 mb-2">
              Analysis Not Found
            </h2>
            <p className="text-red-600 text-sm mb-4">
              {error || 'This palm reading could not be found.'}
            </p>
            <button
              onClick={() => window.location.href = '/'}
              className="text-saffron-600 hover:text-saffron-700 underline"
            >
              Start a new reading
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (analysis.status === 'FAILED') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <Card className="w-full max-w-md mx-auto border-red-200">
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
            <button
              onClick={() => window.location.href = '/'}
              className="text-saffron-600 hover:text-saffron-700 underline"
            >
              Try with different images
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (analysis.status !== 'COMPLETED' || !analysis.summary) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <Card className="w-full max-w-md mx-auto">
          <CardContent className="p-6 text-center">
            <div className="text-saffron-600 mb-4">
              <Sparkles className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold mb-2">
              Analysis In Progress
            </h2>
            <p className="text-muted-foreground text-sm">
              Your palm reading is still being prepared. Please check back in a few moments.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-md mx-auto space-y-6">
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

            {/* Teaser for full reading */}
            <div className="bg-white/50 rounded-lg p-3 border border-saffron-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-saffron-600" />
                  <span className="text-sm font-medium text-saffron-800">
                    Full detailed reading available
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-saffron-600" />
              </div>
              <p className="text-xs text-saffron-700 mt-1">
                Sign in to unlock complete insights about your life, relationships, and future
              </p>
            </div>

            {/* Analysis metadata */}
            <div className="text-center text-xs text-saffron-600 space-y-1">
              <p>✨ Analysis completed in {
                analysis.processing_completed_at && analysis.processing_started_at 
                  ? Math.round((new Date(analysis.processing_completed_at).getTime() - 
                               new Date(analysis.processing_started_at).getTime()) / 1000)
                  : 'Unknown'
              } seconds</p>
              <p>🔮 Based on {analysis.tokens_used || 'many'} AI insights</p>
            </div>
          </CardContent>
        </Card>

        {/* Login Gate */}
        {showLoginGate && (
          <div className="space-y-4">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                This is just a glimpse of what your palms reveal...
              </p>
            </div>
            
            <LoginGate 
              analysisId={analysisId}
              showFullFeatures={true}
            />
          </div>
        )}

        {/* If login gate hasn't appeared yet, show a preview */}
        {!showLoginGate && (
          <Card className="border-dashed border-saffron-300 bg-saffron-50/50">
            <CardContent className="p-4 text-center">
              <Lock className="w-8 h-8 text-saffron-500 mx-auto mb-2" />
              <p className="text-sm font-medium text-saffron-800 mb-1">
                Want to see more?
              </p>
              <p className="text-xs text-saffron-600">
                The complete reading is loading...
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