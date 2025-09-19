/**
 * @fileoverview New Reading Modal Component for Dashboard
 * Allows authenticated users to start a new palm reading without leaving the dashboard
 * Mobile-friendly modal design with proper spacing and touch targets
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { X, Hand, Sparkles } from 'lucide-react';
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
}

export function NewReadingModal({ isOpen, onClose }: NewReadingModalProps) {
  const router = useRouter();
  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [welcomeMessage, setWelcomeMessage] = React.useState('Start your next palm reading');

  // Set random message for variety
  React.useEffect(() => {
    if (isOpen) {
      setWelcomeMessage(getRandomMessage('welcome'));
      // Reset state when modal opens
      setAnalysis(null);
      setUploadError(null);
      setIsUploading(false);
    }
  }, [isOpen]);

  const handleUpload = async (files: File[]) => {
    try {
      setIsUploading(true);
      setUploadError(null);

      console.log('Authenticated user upload started with files:', files.map(f => ({ name: f.name, size: f.size })));

      // Create analysis for authenticated user
      const analysisData = await analysisApi.uploadImages(files);
      console.log('Authenticated analysis created:', analysisData);

      setAnalysis(analysisData);
      setIsUploading(false); // Upload successful, now showing progress

    } catch (error) {
      console.error('Upload failed:', error);
      const errorMessage = handleApiError(error);
      setUploadError(errorMessage);
      setIsUploading(false);
    }
  };

  const handleAnalysisComplete = (completedAnalysis: Analysis) => {
    console.log('Analysis completed in modal, redirecting to dashboard analysis page');
    onClose();
    // Navigate to the dashboard analysis page (authenticated route)
    router.push(`/analyses/${completedAnalysis.id}`);
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

  // If analysis is created and processing, show progress
  if (analysis && (analysis.status === 'processing' || analysis.status === 'pending')) {
    return (
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={handleBackdropClick}
      >
        <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
          <div className="p-6">
            <BackgroundJobProgress
              analysisId={analysis.id}
              onComplete={handleAnalysisComplete}
            />
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
                disabled={isUploading}
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