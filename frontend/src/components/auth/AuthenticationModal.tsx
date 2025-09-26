/**
 * @fileoverview Authentication Modal Component
 * Modal dialog for converting users from guest summary to authenticated full reading
 * Mobile-friendly design with proper spacing and touch targets
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { X, Lock, Sparkles, Eye, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';

interface AuthenticationModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisId: number;
  onLoginSuccess?: () => void;
}

export function AuthenticationModal({
  isOpen,
  onClose,
  analysisId,
  onLoginSuccess
}: AuthenticationModalProps) {
  const router = useRouter();

  const handleLogin = () => {
    // The analysis ID is already stored in sessionStorage as 'guestAnalysisId'
    // Just redirect to login with a parameter indicating we're coming from reading-summary
    router.push('/login?redirect=reading-summary');
  };

  const handleRegister = () => {
    // The analysis ID is already stored in sessionStorage as 'guestAnalysisId'
    // Just redirect to register with a parameter indicating we're coming from reading-summary
    router.push('/register?redirect=reading-summary');
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-saffron-100 flex items-center justify-center">
              <Lock className="w-5 h-5 text-saffron-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Unlock Full Reading</h2>
              <p className="text-sm text-gray-500">Access your complete palm analysis</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full w-8 h-8 p-0 flex items-center justify-center hover:bg-gray-100 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6">
          <Card className="border-2 border-saffron-200 bg-gradient-to-br from-saffron-50 to-orange-50">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-saffron-500 rounded-full flex items-center justify-center mb-4">
                <Lock className="w-8 h-8 text-white" />
              </div>

              <CardTitle className="text-xl text-saffron-800">
                Complete Your Palm Reading Journey
              </CardTitle>

              <CardDescription className="text-saffron-700">
                You've seen the summary - now discover the complete insights hidden in your palms
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium text-saffron-800 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  What you'll unlock:
                </h4>

                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <Eye className="w-5 h-5 text-saffron-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-sm text-gray-900">Complete Analysis</p>
                      <p className="text-xs text-gray-600">
                        Detailed insights about your life, love, career, and health lines
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <MessageCircle className="w-5 h-5 text-saffron-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-sm text-gray-900">AI Conversations</p>
                      <p className="text-xs text-gray-600">
                        Ask follow-up questions and dive deeper into your reading
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-saffron-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-sm text-gray-900">Personal Dashboard</p>
                      <p className="text-xs text-gray-600">
                        Save and compare multiple readings over time
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white/70 rounded-lg p-4 border border-saffron-200">
                <p className="text-xs text-center text-saffron-700 mb-3">
                  Free account • No payment required • Instant access
                </p>

                <div className="space-y-3">
                  <Button
                    size="lg"
                    onClick={handleLogin}
                    className="w-full"
                  >
                    Sign In to Continue
                  </Button>

                  <Button
                    variant="outline"
                    size="lg"
                    onClick={handleRegister}
                    className="w-full border-saffron-300 text-saffron-700 hover:bg-saffron-50"
                  >
                    Create Free Account
                  </Button>
                </div>
              </div>

              <div className="text-center">
                <p className="text-xs text-gray-500">
                  Your palm reading will be waiting for you after sign in
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}