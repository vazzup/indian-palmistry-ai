/**
 * @fileoverview Main landing page for Indian Palmistry AI application
 * Features mobile-first design with cultural authenticity
 * Handles palm image upload and real-time analysis progress
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, Hand, Brain, Heart } from 'lucide-react';
import { MobileImageUpload } from '@/components/analysis/MobileImageUpload';
import { BackgroundJobProgress } from '@/components/analysis/BackgroundJobProgress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { HeaderAuth } from '@/components/auth/HeaderAuth';
import { ValuePropCard } from '@/components/auth/ValuePropCard';
import { ExperienceChoice } from '@/components/auth/ExperienceChoice';
import { useAuth } from '@/lib/auth';
import { analysisApi, handleApiError } from '@/lib/api';
import { getRandomMessage } from '@/lib/cultural-theme';
import type { Analysis } from '@/types';

/**
 * Main landing page component for Indian Palmistry AI
 * 
 * Features:
 * - Cultural saffron-based design theme
 * - Mobile-optimized palm image upload
 * - Real-time analysis progress tracking
 * - Respectful messaging based on Hast Rekha Shastra
 * - Seamless flow from upload to analysis to results
 * 
 * The page adapts its UI based on analysis state:
 * - Initial state: Shows welcome message and upload interface
 * - Processing state: Shows progress indicator with cultural messaging
 * - Complete state: Navigates to analysis results
 */
export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [welcomeMessage, setWelcomeMessage] = React.useState('Experience the timeless wisdom of Indian palm reading');
  const [showExperienceChoice, setShowExperienceChoice] = React.useState(false);

  // Set random message on client side to avoid hydration mismatch
  React.useEffect(() => {
    setWelcomeMessage(getRandomMessage('welcome'));
  }, []);

  const handleUpload = async (files: File[]) => {
    try {
      setIsUploading(true);
      setUploadError(null);
      
      const uploadedAnalysis = await analysisApi.uploadImages(files);
      setAnalysis(uploadedAnalysis);
      
      // Optional: Auto-navigate to analysis page
      // router.push(`/analysis/${uploadedAnalysis.id}/summary`);
    } catch (error: any) {
      const errorMessage = handleApiError(error);
      setUploadError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };
  
  const handleGetStarted = () => {
    if (isAuthenticated) {
      // Skip experience choice for authenticated users
      setShowExperienceChoice(false);
    } else {
      // Show experience choice for guests
      setShowExperienceChoice(true);
    }
  };
  
  const handleGuestChoice = () => {
    setShowExperienceChoice(false);
    // Continue with existing guest upload flow
  };
  
  const handleAuthChoice = () => {
    router.push('/register');
  };

  const handleAnalysisComplete = (result: any) => {
    if (analysis) {
      // Navigate to the summary page
      router.push(`/analysis/${analysis.id}/summary`);
    }
  };

  const handleAnalysisError = (error: string) => {
    setUploadError(`Analysis failed: ${error}`);
    setAnalysis(null);
  };

  if (analysis && !uploadError) {
    return (
      <div className="min-h-screen bg-background py-8 px-4">
        <div className="max-w-md mx-auto space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold text-gray-900">
              Analyzing Your Palm
            </h1>
            <p className="text-gray-600">
              Please wait while our AI reads your palm
            </p>
          </div>

          {/* Progress Component */}
          <BackgroundJobProgress 
            analysisId={analysis.id}
            onComplete={handleAnalysisComplete}
            onError={handleAnalysisError}
          />

          {/* Cancel option */}
          <div className="text-center">
            <Button 
              variant="ghost" 
              onClick={() => {
                setAnalysis(null);
                setUploadError(null);
              }}
            >
              Upload Different Images
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header Authentication */}
      <HeaderAuth className="bg-white/80 backdrop-blur-sm border-b border-amber-200/50" />
      
      {/* Hero Section */}
      <div className="py-8 px-4">
        <div className="max-w-md mx-auto text-center space-y-6">
          {/* Logo/Icon */}
          <div className="mx-auto w-20 h-20 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center">
            <Hand className="w-10 h-10 text-white" />
          </div>

          {/* Title */}
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-gray-900">
              Indian Palmistry AI
            </h1>
            <p className="text-lg text-gray-600">
              {welcomeMessage}
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="space-y-2">
              <div className="mx-auto w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                <Brain className="w-6 h-6 text-orange-600" />
              </div>
              <p className="text-xs font-medium">AI Powered</p>
            </div>
            
            <div className="space-y-2">
              <div className="mx-auto w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-orange-600" />
              </div>
              <p className="text-xs font-medium">Traditional</p>
            </div>
            
            <div className="space-y-2">
              <div className="mx-auto w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                <Heart className="w-6 h-6 text-orange-600" />
              </div>
              <p className="text-xs font-medium">Personal</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Action Section */}
      <div className="px-4 pb-8">
        <div className="max-w-md mx-auto space-y-6">
          {!showExperienceChoice ? (
            <>
              {/* Value Proposition for Non-Authenticated Users */}
              {!isAuthenticated && (
                <ValuePropCard className="mb-6" onSignUp={handleAuthChoice} />
              )}
              
              {/* Instructions */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">
                    {isAuthenticated ? 'Upload Your Palm Images' : 'Get Your Reading'}
                  </CardTitle>
                  <CardDescription>
                    {isAuthenticated 
                      ? 'Upload clear photos for a complete personalized reading'
                      : 'Upload clear photos of your palm(s) for an AI-powered reading based on ancient Indian palmistry'
                    }
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm text-gray-600">
                    <div className="flex items-start gap-2">
                      <span className="text-orange-500 font-bold">1.</span>
                      <span>Take clear photos of your palm in good lighting</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-orange-500 font-bold">2.</span>
                      <span>Upload up to 2 images (left and right palms)</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-orange-500 font-bold">3.</span>
                      <span>
                        {isAuthenticated 
                          ? 'Get your complete personalized reading and analysis'
                          : 'Get an instant summary, full reading requires sign-up'
                        }
                      </span>
                    </div>
                  </div>
                  
                  {/* Experience Choice Button for Guests */}
                  {!isAuthenticated && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <Button 
                        onClick={handleGetStarted}
                        size="lg"
                        className="w-full bg-saffron-500 hover:bg-saffron-600"
                      >
                        Choose Your Experience
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Upload Component - Show for authenticated users or when guest has chosen */}
              {(isAuthenticated || (!isAuthenticated && !showExperienceChoice)) && (
                <MobileImageUpload 
                  onUpload={handleUpload}
                  isUploading={isUploading}
                />
              )}

              {/* Error Display */}
              {uploadError && (
                <Card className="border-red-200 bg-red-50">
                  <CardContent className="p-4">
                    <div className="text-red-600 text-sm">
                      <p className="font-medium">Upload Failed</p>
                      <p>{uploadError}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Privacy Note */}
              <div className="text-center">
                <p className="text-xs text-gray-600">
                  🔒 Your images are processed securely and not stored permanently
                </p>
              </div>
            </>
          ) : (
            /* Experience Choice Component */
            <>
              <ExperienceChoice 
                onGuestChoice={handleGuestChoice}
                onAuthChoice={handleAuthChoice}
              />
              
              {/* Back Button */}
              <div className="text-center">
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setShowExperienceChoice(false)}
                  className="text-gray-600 hover:text-gray-800"
                >
                  ← Back to Reading
                </Button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-gray-50 py-8 px-4">
        <div className="max-w-md mx-auto">
          <h2 className="text-xl font-semibold text-center mb-6">
            What You'll Discover
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-medium">Life Insights</h3>
                <p className="text-sm text-gray-600">
                  Learn about your personality, strengths, and life path
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Heart className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-medium">Relationships</h3>
                <p className="text-sm text-gray-600">
                  Understand your approach to love and relationships
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-medium">Career & Health</h3>
                <p className="text-sm text-gray-600">
                  Discover insights about your career path and wellbeing
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="py-6 px-4 text-center">
        <p className="text-xs text-gray-600">
          Based on traditional Indian palmistry (Hast Rekha Shastra) enhanced with AI
        </p>
      </div>
    </div>
  );
}
