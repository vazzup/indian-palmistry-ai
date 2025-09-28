'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import {
  Hand,
  MessageCircle,
  Plus,
  Calendar,
  Loader2,
  AlertCircle,
  RefreshCw,
  Send
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { NewReadingModal } from '@/components/dashboard/NewReadingModal';
import { useAuth } from '@/lib/auth';
import { analysisApi, conversationsApi, handleApiError } from '@/lib/api';
import { LoadingPage } from '@/components/ui/Spinner';
import type { Analysis } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ReadingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();

  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showNewReadingModal, setShowNewReadingModal] = React.useState(false);

  // Floating input state
  const [question, setQuestion] = React.useState('');
  const [isAsking, setIsAsking] = React.useState(false);

  // Transition state for analysis-to-chat mode
  const [isTransitioning, setIsTransitioning] = React.useState(false);
  const [transitionMessage, setTransitionMessage] = React.useState('');

  // Fetch current reading
  const fetchCurrentReading = React.useCallback(async () => {
    console.log('[DEBUG] ReadingPage: fetchCurrentReading called, isAuthenticated:', isAuthenticated, 'authLoading:', authLoading);
    if (!isAuthenticated || authLoading) {
      console.log('[DEBUG] ReadingPage: Skipping fetch - not authenticated or loading');
      return;
    }

    try {
      console.log('[DEBUG] ReadingPage: Starting fetch current reading');
      setLoading(true);
      setError(null);

      console.log('[DEBUG] ReadingPage: Calling analysisApi.getCurrentReading()');
      const response = await analysisApi.getCurrentReading();
      console.log('[DEBUG] ReadingPage: Got response:', response);
      setAnalysis(response);

    } catch (err: any) {
      console.error('[DEBUG] ReadingPage: Error caught:', err);

      // Check if this is a 404 error (no current reading found)
      const is404Error = err?.response?.status === 404 ||
                        err?.status === 404 ||
                        err?.code === 'ERR_BAD_REQUEST' && err?.response?.status === 404;

      const errorMessage = handleApiError(err);
      console.log('[DEBUG] ReadingPage: Error message:', errorMessage);
      console.log('[DEBUG] ReadingPage: Is 404 error:', is404Error);

      if (is404Error ||
          errorMessage.includes('No current reading found') ||
          errorMessage.includes('404') ||
          errorMessage.includes('not found') ||
          errorMessage.includes('No reading found')) {
        // No current reading - this is normal for new users
        console.log('[DEBUG] ReadingPage: No current reading found - setting analysis to null');
        setAnalysis(null);
      } else {
        console.log('[DEBUG] ReadingPage: Setting error:', errorMessage);
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, authLoading]);

  // Check for guest analysis to claim on page load (after OAuth redirects)
  React.useEffect(() => {
    const handleGuestAnalysisClaim = async () => {
      if (!isAuthenticated || authLoading) return;

      try {
        const { getGuestAnalysisId, clearGuestAnalysisId, migrateFromReturnToAnalysis } = await import('@/lib/guest-analysis');
        const { analysisApi } = await import('@/lib/api');

        // Migrate from old returnToAnalysis key if needed
        migrateFromReturnToAnalysis();

        const guestAnalysisId = getGuestAnalysisId();

        if (guestAnalysisId) {
          console.log(`Found guest analysis ${guestAnalysisId} on reading page load, attempting to claim`);
          try {
            await analysisApi.claimReading(guestAnalysisId);
            clearGuestAnalysisId();
            console.log('Guest analysis claimed successfully on reading page load');

            // Refetch current reading after claiming
            fetchCurrentReading();
          } catch (error) {
            console.error('Failed to claim guest analysis on reading page load:', error);
            clearGuestAnalysisId();

            // Still fetch current reading in case user has another analysis
            fetchCurrentReading();
          }
        } else {
          // No guest analysis, fetch normally
          fetchCurrentReading();
        }
      } catch (error) {
        console.error('Error in guest analysis claim logic:', error);
        fetchCurrentReading();
      }
    };

    handleGuestAnalysisClaim();
  }, [isAuthenticated, authLoading, fetchCurrentReading]);

  // Handle asking a question
  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim() || !analysis || isAsking || isTransitioning) return;

    setIsAsking(true);
    setQuestion(''); // Clear input immediately
    let messageInterval: NodeJS.Timeout | null = null;

    try {
      // Show interstitial loading screen for engaging UX
      setIsTransitioning(true);

      // Animate through different mystical messages to enhance UX
      const messages = [
        'Preparing your question...',
        'Reading your palms again...',
        'Connecting with ancient wisdom...',
        'Thinking about your question...',
        'Crafting your personalized response...'
      ];

      let messageIndex = 0;
      setTransitionMessage(messages[0]);

      // Cycle through messages every 1.2 seconds for visual engagement
      messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % messages.length;
        setTransitionMessage(messages[messageIndex]);
      }, 1200);

      // Start conversation with the question
      const response = await conversationsApi.startConversation(analysis.id.toString(), question.trim());

      // Navigate to the conversation page
      router.push(`/conversation/${response.conversation.id}`);

    } catch (err) {
      console.error('Error starting conversation:', err);
      setQuestion(question); // Restore question on error
      // Handle error - maybe show a toast
    } finally {
      // Clean up transition interval
      if (messageInterval) {
        clearInterval(messageInterval);
      }
      setIsAsking(false);
      setIsTransitioning(false);
    }
  };

  // Handle redo reading
  const handleRedoReading = () => {
    setShowNewReadingModal(true);
  };

  // Handle reading completion
  const handleReadingComplete = React.useCallback(() => {
    setShowNewReadingModal(false);
    // Refresh the current reading data
    fetchCurrentReading();
  }, [fetchCurrentReading]);

  // Loading state
  if (authLoading || loading) {
    return <LoadingPage message="Loading your reading..." />;
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout
        title="Your Reading"
        description="Your personalized palm reading analysis"
      >
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Unable to Load Reading
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex gap-2 justify-center">
              <Button onClick={fetchCurrentReading}>Try Again</Button>
            </div>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  // No reading state
  if (!analysis) {
    return (
      <DashboardLayout
        title="Your Reading"
        description="Your personalized palm reading analysis"
      >
        <Card className="border-saffron-200 shadow-lg">
          <CardContent className="py-16 text-center">
            <div className="w-20 h-20 bg-gradient-to-br from-saffron-100 to-turmeric-100 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm">
              <Hand className="w-10 h-10 text-saffron-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Your Palm Reading Awaits
            </h3>
            <p className="text-gray-600 mb-2 max-w-md mx-auto">
              Discover the ancient wisdom hidden in your palms through our AI-powered palmistry analysis.
            </p>
            <p className="text-sm text-saffron-600 mb-6">
              ✨ Unlock insights about your personality, relationships, and life path
            </p>
            <Button
              onClick={handleRedoReading}
              className="bg-saffron-600 hover:bg-saffron-700 text-white px-8 py-3 text-lg shadow-lg hover:shadow-xl transition-all duration-200"
              size="lg"
            >
              Get Your Palm Reading
            </Button>
          </CardContent>
        </Card>

        <NewReadingModal
          isOpen={showNewReadingModal}
          onClose={() => setShowNewReadingModal(false)}
          onComplete={handleReadingComplete}
        />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title="Your Reading"
      description="Your personalized palm reading analysis"
    >
      {/* Interstitial Loading Screen */}
      {isTransitioning && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md mx-4 text-center">
            <div className="relative mb-6">
              <div className="w-16 h-16 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin mx-auto"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <Hand className="w-6 h-6 text-saffron-600" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Pondering your question...
            </h3>
            <p className="text-gray-600 mb-4 min-h-[1.5rem]">
              {transitionMessage}
            </p>
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-6 pb-24"> {/* Extra padding for floating input */}
        {/* Reading Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Your Palm Reading</h1>
            <p className="text-gray-600 mt-1">
              Created {new Date(analysis.created_at).toLocaleDateString()}
            </p>
          </div>
          <Button variant="outline" onClick={handleRedoReading}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Redo Reading
          </Button>
        </div>

        {/* Reading Content */}
        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary */}
            {analysis.summary && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Summary</h3>
                <div className="prose prose-gray max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {analysis.summary}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* Full Report */}
            {analysis.full_report && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Detailed Analysis</h3>
                <div className="prose prose-gray max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {analysis.full_report}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* Key Features */}
            {analysis.key_features && analysis.key_features.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Key Features</h3>
                <ul className="space-y-2">
                  {analysis.key_features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <div className="w-2 h-2 bg-saffron-500 rounded-full mt-2 mr-3 flex-shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Strengths */}
            {analysis.strengths && analysis.strengths.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Your Strengths</h3>
                <ul className="space-y-2">
                  {analysis.strengths.map((strength, index) => (
                    <li key={index} className="flex items-start">
                      <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0" />
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Guidance */}
            {analysis.guidance && analysis.guidance.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Life Guidance</h3>
                <ul className="space-y-2">
                  {analysis.guidance.map((guide, index) => (
                    <li key={index} className="flex items-start">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0" />
                      <span>{guide}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Conversation History */}
        {/* TODO: Add conversation topics list here */}
      </div>

      {/* Liquid Glass Floating Chat Input */}
      <div className="fixed bottom-6 left-4 right-4 z-50">
        <div className="max-w-2xl mx-auto">
          <form onSubmit={handleAskQuestion}>
            <div className="bg-white/80 backdrop-blur-xl border border-white/20 shadow-2xl shadow-black/10 rounded-2xl ring-1 ring-black/5 p-3">
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  placeholder="Ask about your palm reading..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={isAsking || isTransitioning}
                  className="flex-1 rounded-full bg-gray-50/50 border-0 px-6 py-3 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-saffron-500/20 focus:bg-white/80 transition-all duration-200"
                />
                <button
                  type="submit"
                  disabled={!question.trim() || isAsking || isTransitioning}
                  className="rounded-full w-10 h-10 p-0 bg-gradient-to-r from-saffron-500 to-saffron-600 text-white shadow-lg hover:shadow-xl hover:scale-105 focus:scale-105 disabled:opacity-50 disabled:hover:scale-100 transition-all duration-200 flex items-center justify-center"
                >
                  {isAsking || isTransitioning ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Modals */}
      <NewReadingModal
        isOpen={showNewReadingModal}
        onClose={() => setShowNewReadingModal(false)}
        onComplete={handleReadingComplete}
      />
    </DashboardLayout>
  );
}