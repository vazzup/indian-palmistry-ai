'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, Hand, Brain, Heart } from 'lucide-react';
import { MobileImageUpload } from '@/components/analysis/MobileImageUpload';
import { BackgroundJobProgress } from '@/components/analysis/BackgroundJobProgress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { analysisApi, handleApiError } from '@/lib/api';
import { getRandomMessage } from '@/lib/cultural-theme';
import { LegalNotice } from '@/components/legal/LegalNotice';
import { LegalLinks } from '@/components/legal/LegalLinks';
import type { Analysis } from '@/types';

export default function HomePage() {
  const router = useRouter();
  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [welcomeMessage, setWelcomeMessage] = React.useState('Discover the ancient wisdom of your palms');
  
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
      <div className="min-h-screen bg-background py-8 px-4 md:px-6 lg:px-8">
        <div className="max-w-md md:max-w-2xl lg:max-w-4xl mx-auto space-y-6">
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
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="py-12 px-4 md:px-6 lg:px-8">
        <div className="max-w-md md:max-w-4xl lg:max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Content Column */}
            <div className="text-center lg:text-left space-y-6">
          {/* Logo/Icon */}
          <div className="mx-auto lg:mx-0 w-20 h-20 bg-gradient-to-br from-saffron-400 to-saffron-600 rounded-full flex items-center justify-center">
            <Hand className="w-10 h-10 text-white" />
          </div>

          {/* Title */}
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-foreground">
              PalmistTalk
            </h1>
            <p className="text-lg text-muted-foreground">
              {welcomeMessage}
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-3 gap-4 text-center lg:justify-start">
            <div className="space-y-2">
              <div className="mx-auto lg:mx-0 w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center">
                <Brain className="w-6 h-6 text-saffron-600" />
              </div>
              <p className="text-xs font-medium">AI Powered</p>
            </div>
            
            <div className="space-y-2">
              <div className="mx-auto lg:mx-0 w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-saffron-600" />
              </div>
              <p className="text-xs font-medium">Traditional</p>
            </div>
            
            <div className="space-y-2">
              <div className="mx-auto lg:mx-0 w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center">
                <Heart className="w-6 h-6 text-saffron-600" />
              </div>
              <p className="text-xs font-medium">Personal</p>
            </div>
          </div>
            </div>
            
            {/* Visual Column - Desktop Only */}
            <div className="hidden lg:flex items-center justify-center">
              <div className="relative">
                {/* Decorative palm illustration placeholder */}
                <div className="w-80 h-80 bg-gradient-to-br from-saffron-100 to-orange-100 rounded-full flex items-center justify-center border-4 border-saffron-200">
                  <div className="text-center space-y-4">
                    <Hand className="w-24 h-24 text-saffron-500 mx-auto" />
                    <div className="text-saffron-700">
                      <p className="text-lg font-semibold">Ancient Wisdom</p>
                      <p className="text-sm">Modern Technology</p>
                    </div>
                  </div>
                </div>
                {/* Floating elements */}
                <div className="absolute -top-4 -right-4 w-12 h-12 bg-saffron-200 rounded-full flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-saffron-600" />
                </div>
                <div className="absolute -bottom-4 -left-4 w-12 h-12 bg-orange-200 rounded-full flex items-center justify-center">
                  <Brain className="w-6 h-6 text-orange-600" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="px-4 md:px-6 lg:px-8 pb-8">
        <div className="max-w-md md:max-w-4xl lg:max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-start">
            {/* Instructions Column */}
            <div className="space-y-6">
          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Get Your Reading</CardTitle>
              <CardDescription>
                Upload clear photos of your palm(s) for an AI-powered reading at PalmistTalk.com based on ancient Indian palmistry
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div className="flex items-start gap-2">
                  <span className="text-saffron-500 font-bold">1.</span>
                  <span>Take clear photos of your palm in good lighting</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-saffron-500 font-bold">2.</span>
                  <span>Upload up to 2 images (left and right palms)</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-saffron-500 font-bold">3.</span>
                  <span>Get an instant summary, full reading requires sign-up</span>
                </div>
              </div>
            </CardContent>
          </Card>

            </div>
            
            {/* Upload Column */}
            <div className="space-y-6">
              {/* Upload Component */}
              <MobileImageUpload 
                onUpload={handleUpload}
                isUploading={isUploading}
              />

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

              {/* Legal Notice */}
              <LegalNotice variant="upload" />
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-muted/30 py-8 px-4 md:px-6 lg:px-8">
        <div className="max-w-md md:max-w-4xl lg:max-w-6xl mx-auto">
          <h2 className="text-xl md:text-2xl font-semibold text-center mb-6 md:mb-8">
            What You'll Discover
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
            <div className="flex md:flex-col md:text-center items-start md:items-center gap-3 md:gap-4">
              <div className="w-8 h-8 md:w-12 md:h-12 bg-saffron-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-4 h-4 md:w-6 md:h-6 text-white" />
              </div>
              <div>
                <h3 className="font-medium md:text-lg">Life Insights</h3>
                <p className="text-sm md:text-base text-muted-foreground">
                  Learn about your personality, strengths, and life path
                </p>
              </div>
            </div>
            
            <div className="flex md:flex-col md:text-center items-start md:items-center gap-3 md:gap-4">
              <div className="w-8 h-8 md:w-12 md:h-12 bg-saffron-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Heart className="w-4 h-4 md:w-6 md:h-6 text-white" />
              </div>
              <div>
                <h3 className="font-medium md:text-lg">Relationships</h3>
                <p className="text-sm md:text-base text-muted-foreground">
                  Understand your approach to love and relationships
                </p>
              </div>
            </div>
            
            <div className="flex md:flex-col md:text-center items-start md:items-center gap-3 md:gap-4">
              <div className="w-8 h-8 md:w-12 md:h-12 bg-saffron-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 md:w-6 md:h-6 text-white" />
              </div>
              <div>
                <h3 className="font-medium md:text-lg">Career & Health</h3>
                <p className="text-sm md:text-base text-muted-foreground">
                  Discover insights about your career path and wellbeing
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="py-8 px-4 text-center space-y-4">
        <LegalLinks variant="footer" />
        <p className="text-xs text-muted-foreground">
          PalmistTalk.com - Based on traditional Indian palmistry (Hast Rekha Shastra) enhanced with AI
        </p>
      </div>
    </div>
  );
}