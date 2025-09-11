'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Lock, Sparkles, Eye, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';

interface LoginGateProps {
  analysisId: number;
  onLoginSuccess?: () => void;
  showFullFeatures?: boolean;
}

export const LoginGate: React.FC<LoginGateProps> = ({ 
  analysisId,
  onLoginSuccess,
  showFullFeatures = true,
}) => {
  const router = useRouter();
  
  const handleLogin = () => {
    // Store the current analysis ID to return after login
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('returnToAnalysis', analysisId.toString());
    }
    // Also pass via URL parameter for the login page
    router.push(`/login?analysis=${analysisId}`);
  };
  
  const handleRegister = () => {
    // Store the current analysis ID to return after registration
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('returnToAnalysis', analysisId.toString());
    }
    // Also pass via URL parameter for the register page
    router.push(`/register?analysis=${analysisId}`);
  };
  
  return (
    <Card className="w-full max-w-md mx-auto border-2 border-saffron-200 bg-gradient-to-br from-saffron-50 to-orange-50">
      <CardHeader className="text-center">
        <div className="mx-auto w-16 h-16 bg-saffron-500 rounded-full flex items-center justify-center mb-4">
          <Lock className="w-8 h-8 text-white" />
        </div>
        
        <CardTitle className="text-xl text-saffron-800">
          Unlock Your Full Palm Reading
        </CardTitle>
        
        <CardDescription className="text-saffron-700">
          You've seen the summary - now discover the complete insights hidden in your palms
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {showFullFeatures && (
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
        )}
        
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
  );
};