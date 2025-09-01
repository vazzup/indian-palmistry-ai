/**
 * @fileoverview Follow-up Questions Call-to-Action Component
 * 
 * This component displays a prominent call-to-action on analysis results pages,
 * inviting users to ask follow-up questions about their palm reading. It shows
 * the current status of follow-up questions and provides a clear entry point
 * to the follow-up questions interface.
 * 
 * Features:
 * - Checks follow-up availability automatically
 * - Shows progress indicator if questions already asked
 * - Beautiful gradient card design with cultural theme
 * - Mobile-responsive layout
 * - Loading states and error handling
 * - Accessibility support
 * 
 * @example
 * ```tsx
 * <FollowupCTA 
 *   analysisId={123}
 *   onStartFollowup={() => setShowFollowupInterface(true)}
 * />
 * ```
 */

'use client';

import React from 'react';
import { MessageCircle, ArrowRight, CheckCircle } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useFollowupStore } from '@/lib/stores/followupStore';

/**
 * Props for the FollowupCTA component
 */
interface FollowupCTAProps {
  /** ID of the analysis to show follow-up CTA for */
  analysisId: number;
  /** Callback function when user clicks to start follow-up questions */
  onStartFollowup: () => void;
  /** Optional className for custom styling */
  className?: string;
}

/**
 * Follow-up Questions Call-to-Action Component
 * 
 * Displays an attractive CTA card that invites users to ask follow-up questions
 * about their palm reading. Shows status information and progress if questions
 * have already been asked.
 * 
 * The component automatically checks follow-up availability when mounted and
 * hides itself if follow-up questions are not available for the analysis.
 * 
 * @param props - Component props
 * @returns JSX element or null if follow-up not available
 */
export function FollowupCTA({ analysisId, onStartFollowup, className = '' }: FollowupCTAProps) {
  const { 
    followupStatus, 
    isLoading, 
    error,
    checkFollowupStatus,
    clearError
  } = useFollowupStore();

  // Check follow-up status on component mount
  React.useEffect(() => {
    checkFollowupStatus(analysisId).catch(console.error);
  }, [analysisId, checkFollowupStatus]);

  // Don't render if still loading or not available
  if (isLoading) {
    return (
      <Card className={`mt-8 p-6 bg-gradient-to-r from-saffron-50 to-orange-50 border-saffron-200 ${className}`}>
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-saffron-600"></div>
          <span className="ml-3 text-saffron-700 text-sm">Checking follow-up availability...</span>
        </div>
      </Card>
    );
  }

  // Hide if follow-up is not available
  if (!followupStatus?.followupAvailable) {
    return null;
  }

  // Show error state if there's an error
  if (error) {
    return (
      <Card className={`mt-8 p-6 bg-red-50 border-red-200 ${className}`}>
        <div className="text-center">
          <p className="text-red-700 text-sm mb-3">{error}</p>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={clearError}
            className="border-red-300 text-red-700 hover:bg-red-100"
          >
            Try Again
          </Button>
        </div>
      </Card>
    );
  }

  const hasExistingConversation = followupStatus.followupConversationExists;
  const questionsUsed = followupStatus.questionsAsked;
  const questionsRemaining = followupStatus.questionsRemaining;
  const maxQuestions = 5; // Default maximum questions

  return (
    <Card 
      className={`mt-8 p-6 bg-gradient-to-r from-saffron-50 via-orange-50 to-amber-50 border-saffron-200 shadow-sm hover:shadow-md transition-shadow duration-300 ${className}`}
    >
      <div className="space-y-4">
        {/* Header Section */}
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-saffron-500 to-orange-500 rounded-full shadow-md">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {hasExistingConversation 
                ? 'Continue Your Questions' 
                : 'Have questions about your palm reading?'
              }
            </h3>
            <p className="text-gray-600 text-sm">
              {hasExistingConversation
                ? `You've asked ${questionsUsed} of ${maxQuestions} questions. Continue exploring your palm insights.`
                : 'Ask up to 5 personalized questions about your specific palm features and get detailed answers.'
              }
            </p>
          </div>
        </div>

        {/* Progress Section (if conversation exists) */}
        {hasExistingConversation && (
          <div className="space-y-3 pt-2 border-t border-saffron-200">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-saffron-800 font-medium">
                  Progress: {questionsUsed}/{maxQuestions} questions
                </span>
              </div>
              <span className="text-saffron-600 font-medium">
                {questionsRemaining} remaining
              </span>
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-saffron-200 rounded-full h-3 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-saffron-500 to-orange-500 h-3 rounded-full transition-all duration-500 ease-out shadow-sm"
                style={{ width: `${(questionsUsed / maxQuestions) * 100}%` }}
                aria-label={`${questionsUsed} out of ${maxQuestions} questions used`}
              />
            </div>
          </div>
        )}

        {/* Action Section */}
        <div className="pt-2">
          <Button 
            onClick={onStartFollowup}
            className="w-full sm:w-auto bg-gradient-to-r from-saffron-600 to-orange-600 hover:from-saffron-700 hover:to-orange-700 text-white font-medium px-6 py-3 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-[1.02] active:scale-[0.98]"
            icon={<ArrowRight className="w-4 h-4" />}
            aria-label={hasExistingConversation ? 'Continue asking questions' : 'Start asking questions'}
          >
            {hasExistingConversation ? 'Continue Questions' : 'Ask Questions'}
          </Button>
        </div>

        {/* Additional Info */}
        <div className="pt-2 border-t border-saffron-200">
          <div className="flex items-center gap-2 text-xs text-saffron-700">
            <div className="w-2 h-2 bg-saffron-500 rounded-full"></div>
            <span>
              {hasExistingConversation 
                ? 'Your questions are saved and linked to this palm reading'
                : 'Questions are specific to your palm images and reading context'
              }
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}

/**
 * Default export for convenient importing
 */
export default FollowupCTA;