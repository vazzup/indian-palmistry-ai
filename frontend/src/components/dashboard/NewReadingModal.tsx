/**
 * @fileoverview New Reading Modal Component for Dashboard
 * Allows authenticated users to start a new palm reading without leaving the dashboard
 * Mobile-friendly modal design with proper spacing and touch targets
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { X, Hand, Sparkles, AlertTriangle, MessageCircle } from 'lucide-react';
import { MobileImageUpload } from '@/components/analysis/MobileImageUpload';
import { BackgroundJobProgress } from '@/components/analysis/BackgroundJobProgress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { analysisApi, handleApiError } from '@/lib/api';
import { getRandomMessage } from '@/lib/cultural-theme';
import type { Analysis } from '@/types';

interface NewReadingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

export function NewReadingModal({ isOpen, onClose, onComplete }: NewReadingModalProps) {
  const router = useRouter();
  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [welcomeMessage, setWelcomeMessage] = React.useState('Start your next palm reading');

  // Warning state
  const [currentReading, setCurrentReading] = React.useState<Analysis | null>(null);
  const [showWarning, setShowWarning] = React.useState(false);
  const [warningConfirmed, setWarningConfirmed] = React.useState(false);
  const [loadingCurrentReading, setLoadingCurrentReading] = React.useState(false);

  // Fetch current reading and show warning if needed
  React.useEffect(() => {
    if (isOpen) {
      setWelcomeMessage(getRandomMessage('welcome'));
      // Reset state when modal opens
      setAnalysis(null);
      setUploadError(null);
      setIsUploading(false);
      setShowWarning(false);
      setWarningConfirmed(false);

      // Check if user has a current reading
      fetchCurrentReading();
    }
  }, [isOpen]);

  const fetchCurrentReading = async () => {
    try {
      setLoadingCurrentReading(true);
      const reading = await analysisApi.getCurrentReading();
      setCurrentReading(reading);

      // In the single reading model, show warning if they have an existing reading
      if (reading) {
        setShowWarning(true);
      }
    } catch (error) {
      // No current reading or error - no warning needed
      setCurrentReading(null);
    } finally {
      setLoadingCurrentReading(false);
    }
  };

  const handleUpload = async (files: File[]) => {
    // If we need to show a warning and it hasn't been confirmed, don't proceed
    if (showWarning && !warningConfirmed) {
      return;
    }

    try {
      setIsUploading(true);
      setUploadError(null);

      console.log('Authenticated user upload started with files:', files.map(f => ({ name: f.name, size: f.size })));

      // Create analysis for authenticated user (this will replace the current reading)
      const uploadedAnalysis = await analysisApi.uploadImages(files);
      console.log('Authenticated analysis created:', uploadedAnalysis);

      setAnalysis(uploadedAnalysis);
      // Keep isUploading true until we transition to progress view
      // The progress view will handle the analysis state

    } catch (error) {
      console.error('Upload failed:', error);
      const errorMessage = handleApiError(error);
      setUploadError(errorMessage);
      setAnalysis(null);
      setIsUploading(false);
    }
  };

  const handleAnalysisComplete = React.useCallback((result: any) => {
    console.log('handleAnalysisComplete called with:', result, 'analysis:', analysis);

    // For authenticated users, use onComplete callback if provided, otherwise redirect to /reading
    if (onComplete) {
      console.log('Analysis complete - calling onComplete callback');
      onComplete();
    } else {
      console.log('Analysis complete - redirecting to /reading page');
      onClose();
      router.push('/reading');
    }
  }, [analysis, router, onClose, onComplete]);

  const handleAnalysisError = (error: string) => {
    setUploadError(`Analysis failed: ${error}`);
    setAnalysis(null);
    setIsUploading(false);
  };

  const handleClose = () => {
    if (!isUploading) {
      onClose();
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isUploading) {
      onClose();
    }
  };

  if (!isOpen) return null;

  // If analysis is created and no upload error, show progress
  if (analysis && !uploadError) {
    return (
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={handleBackdropClick}
      >
        <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
          <div className="p-6 space-y-6">
            {/* Header */}
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-gray-900">
                Analyzing Your Palm
              </h2>
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
                  setIsUploading(false);
                }}
              >
                Upload Different Images
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-saffron-100 flex items-center justify-center">
              <Hand className="w-5 h-5 text-saffron-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">New Palm Reading</h2>
              <p className="text-sm text-gray-500">Upload your palm images to get started</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="rounded-full w-8 h-8 p-0 flex items-center justify-center hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Close modal"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6">
          {/* Warning Dialog */}
          {showWarning && currentReading && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-amber-900 mb-2">
                    Warning: You'll lose your conversations
                  </h3>
                  <p className="text-amber-800 mb-4">
                    Creating a new reading will replace your current reading and delete all associated conversations.
                    Your current reading and all associated conversations will be permanently lost.
                  </p>
                  <div className="flex items-center gap-4 text-sm text-amber-700 mb-4">
                    <div className="flex items-center gap-2">
                      <MessageCircle className="w-4 h-4" />
                      <span>All conversations will be deleted</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mb-4">
                    <input
                      type="checkbox"
                      id="confirm-warning"
                      checked={warningConfirmed}
                      onChange={(e) => setWarningConfirmed(e.target.checked)}
                      className="w-4 h-4 text-amber-600 bg-white border-amber-300 rounded focus:ring-amber-500"
                    />
                    <label htmlFor="confirm-warning" className="text-sm text-amber-800">
                      I understand I will lose all my conversations and want to proceed
                    </label>
                  </div>
                  {!warningConfirmed && (
                    <p className="text-sm text-amber-700 italic">
                      Please confirm you understand the consequences before uploading new images.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Welcome Message */}
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-saffron-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {welcomeMessage}
            </h3>
            <p className="text-gray-600">
              Upload clear photos of your palm(s) for a detailed AI-powered reading
            </p>
          </div>

          {/* Error Display */}
          {uploadError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{uploadError}</p>
            </div>
          )}

          {/* Upload Component */}
          <Card className="border-saffron-200">
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-lg">Upload Palm Images</CardTitle>
              <CardDescription>
                For best results, ensure good lighting and clear visibility of palm lines
              </CardDescription>
            </CardHeader>

            <CardContent>
              <MobileImageUpload
                onUpload={handleUpload}
                isUploading={isUploading}
                disabled={isUploading || (showWarning && !warningConfirmed)}
              />
            </CardContent>
          </Card>

          {/* Benefits Section */}
          <div className="bg-saffron-50 rounded-lg p-4">
            <h4 className="font-medium text-saffron-900 mb-2">What you'll get:</h4>
            <ul className="text-sm text-saffron-800 space-y-1">
              <li>• Complete palm line analysis based on traditional Hast Rekha Shastra</li>
              <li>• Personalized insights about your personality and life path</li>
              <li>• Interactive chat to ask questions about your reading</li>
              <li>• Detailed interpretations saved to your dashboard</li>
            </ul>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 rounded-b-xl border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Your readings are private and secure</span>
            <span>Analysis typically takes 30-60 seconds</span>
          </div>
        </div>
      </div>
    </div>
  );
}