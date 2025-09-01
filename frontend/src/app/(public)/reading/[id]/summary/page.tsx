'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Eye, Lock, Sparkles, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoginGate } from '@/components/auth/LoginGate';
import { LoadingPage } from '@/components/ui/Spinner';
import { FollowupCTA, FollowupInterface } from '@/components/analysis/FollowupQuestions';
import { readingApi, handleApiError } from '@/lib/api';
import { getRandomMessage } from '@/lib/cultural-theme';
import { useAuth } from '@/lib/auth';
import type { Reading } from '@/types';

export default function ReadingSummaryPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = params.id as string;
  const { isAuthenticated, user } = useAuth();
  
  const [analysis, setAnalysis] = React.useState<Reading | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showLoginGate, setShowLoginGate] = React.useState(false);
  const [showFollowup, setShowFollowup] = React.useState(false);
  const [successMessage] = React.useState(() => getRandomMessage('completion'));

  React.useEffect(() => {
    const fetchAnalysis = async () => {
      if (!analysisId) {
        setError('Invalid reading ID');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const analysisData = await readingApi.getReadingSummary(analysisId);
        setAnalysis(analysisData);
        
        // Don't auto-show login gate, let user click when ready
      } catch (err: any) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [analysisId]);

  // Redirect logged-in users directly to dashboard full reading
  React.useEffect(() => {
    if (isAuthenticated && !loading && !error) {
      router.push(`/readings/${analysisId}`);
    }
  }, [isAuthenticated, loading, error, analysisId, router]);

  if (loading) {
    return <LoadingPage message="Loading your palm reading..." />;
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4 md:px-6 lg:px-8">
        <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto border-red-200">
          <CardContent className="p-6 text-center">
            <div className="text-red-600 mb-4">
              <Eye className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold text-red-700 mb-2">
              Reading Not Found
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

  if (analysis.status?.toLowerCase() === 'failed') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4 md:px-6 lg:px-8">
        <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto border-red-200">
          <CardContent className="p-6 text-center">
            <div className="text-red-600 mb-4">
              <Eye className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold text-red-700 mb-2">
              Reading Failed
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

  if (analysis.status?.toLowerCase() !== 'completed' || !analysis.summary) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4 md:px-6 lg:px-8">
        <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto">
          <CardContent className="p-6 text-center">
            <div className="text-saffron-600 mb-4">
              <Sparkles className="w-12 h-12 mx-auto" />
            </div>
            <h2 className="text-lg font-semibold mb-2">
              Reading In Progress
            </h2>
            <p className="text-muted-foreground text-sm">
              Your palm reading is still being prepared. Please check back in a few moments.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show follow-up interface if requested
  if (showFollowup) {
    return (
      <div className="min-h-screen bg-background py-8 px-4 md:px-6 lg:px-8">
        <FollowupInterface 
          analysisId={parseInt(analysisId)}
          onBack={() => setShowFollowup(false)}
        />
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

            {/* Teaser for full reading */}
            <button 
              onClick={() => {
                console.log('Full reading button clicked!');
                if (isAuthenticated) {
                  // User is authenticated, redirect to full reading
                  router.push(`/readings/${analysisId}`);
                } else {
                  // User is not authenticated, show login gate
                  setShowLoginGate(true);
                }
              }}
              className="bg-white/50 rounded-lg p-3 border border-saffron-200 hover:bg-white/80 hover:border-saffron-300 transition-all duration-200 w-full text-left cursor-pointer active:bg-white/90"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isAuthenticated ? (
                    <Eye className="w-4 h-4 text-saffron-600" />
                  ) : (
                    <Lock className="w-4 h-4 text-saffron-600" />
                  )}
                  <span className="text-sm font-medium text-saffron-800">
                    {isAuthenticated ? 'View full detailed reading' : 'Full detailed reading available'}
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-saffron-600" />
              </div>
              <p className="text-xs text-saffron-700 mt-1">
                {isAuthenticated 
                  ? 'Click to view your complete reading with insights about your life, relationships, and future'
                  : 'Sign in to unlock complete insights about your life, relationships, and future'
                }
              </p>
            </button>

            {/* Analysis metadata */}
            <div className="text-center text-xs text-saffron-600 space-y-1">
              <p>✨ Reading completed in {
                analysis.processing_completed_at && analysis.processing_started_at 
                  ? Math.round((new Date(analysis.processing_completed_at).getTime() - 
                               new Date(analysis.processing_started_at).getTime()) / 1000)
                  : 'Unknown'
              } seconds</p>
              <p>🔮 Based on {analysis.tokens_used || 'many'} AI insights</p>
            </div>
          </CardContent>
        </Card>

        {/* Follow-up Questions CTA - Only show for authenticated users with completed reading */}
        {isAuthenticated && analysis.status?.toLowerCase() === 'completed' && (
          <FollowupCTA 
            analysisId={parseInt(analysisId)}
            onStartFollowup={() => setShowFollowup(true)}
          />
        )}

        {/* Login Gate */}
        {showLoginGate && (
          <div className="space-y-4">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                This is just a glimpse of what your palms reveal...
              </p>
            </div>
            
            <LoginGate 
              analysisId={parseInt(analysisId)}
              showFullFeatures={true}
            />
          </div>
        )}

        {/* If login gate hasn't appeared yet, show a call-to-action */}
        {!showLoginGate && (
          <button
            onClick={() => {
              if (isAuthenticated) {
                router.push(`/readings/${analysisId}`);
              } else {
                setShowLoginGate(true);
              }
            }}
            className="w-full"
          >
            <Card className="border-dashed border-saffron-300 bg-saffron-50/50 hover:bg-saffron-100/50 transition-colors cursor-pointer">
              <CardContent className="p-4 text-center">
                {isAuthenticated ? (
                  <Eye className="w-8 h-8 text-saffron-500 mx-auto mb-2" />
                ) : (
                  <Lock className="w-8 h-8 text-saffron-500 mx-auto mb-2" />
                )}
                <p className="text-sm font-medium text-saffron-800 mb-1">
                  {isAuthenticated ? 'Ready to view your full reading?' : 'Ready for the full reading?'}
                </p>
                <p className="text-xs text-saffron-600">
                  {isAuthenticated ? 'Click here to view complete insights' : 'Click here to unlock complete insights'}
                </p>
              </CardContent>
            </Card>
          </button>
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