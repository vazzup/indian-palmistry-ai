/**
 * @fileoverview Follow-up Questions Interface Component
 * 
 * This is the main interface component for the follow-up questions feature.
 * It orchestrates the entire follow-up questions experience, managing the
 * conversation flow, state updates, and user interactions.
 * 
 * Features:
 * - Automatic conversation initialization
 * - Question history loading and display
 * - Question input with validation
 * - Progress tracking and limits
 * - Error handling and recovery
 * - Mobile-responsive design
 * - Accessibility support
 * - Smooth animations and transitions
 * 
 * @example
 * ```tsx
 * <FollowupInterface 
 *   analysisId={123}
 *   onBack={() => setShowInterface(false)}
 * />
 * ```
 */

'use client';

import React from 'react';
import { ArrowLeft, MessageCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { QuestionInput } from './QuestionInput';
import { QuestionHistory } from './QuestionHistory';
import { QuestionLimitIndicator, HeaderQuestionLimitIndicator } from './QuestionLimitIndicator';
import { FollowupLoading, ConversationSetupLoading } from './FollowupLoading';
import { useFollowupStore } from '@/lib/stores/followupStore';

/**
 * Props for the FollowupInterface component
 */
interface FollowupInterfaceProps {
  /** ID of the analysis to show follow-up interface for */
  analysisId: number;
  /** Callback function when user clicks back button */
  onBack: () => void;
  /** Optional className for custom styling */
  className?: string;
}

/**
 * Error Boundary Component for Follow-up Interface
 */
interface ErrorDisplayProps {
  error: string;
  onRetry: () => void;
  onClear: () => void;
}

function ErrorDisplay({ error, onRetry, onClear }: ErrorDisplayProps) {
  return (
    <Card className="p-6 bg-red-50 border-red-200">
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <AlertTriangle className="w-12 h-12 text-red-600" />
        </div>
        
        <div>
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            Something went wrong
          </h3>
          <p className="text-red-700 text-sm mb-4">
            {error}
          </p>
        </div>
        
        <div className="flex gap-3 justify-center">
          <Button
            variant="outline"
            onClick={onRetry}
            className="border-red-300 text-red-700 hover:bg-red-100"
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Try Again
          </Button>
          <Button
            variant="ghost"
            onClick={onClear}
            className="text-red-600 hover:bg-red-100"
          >
            Dismiss
          </Button>
        </div>
      </div>
    </Card>
  );
}

/**
 * Follow-up Questions Interface Component
 * 
 * Main interface that manages the complete follow-up questions experience.
 * Handles conversation initialization, question submission, and history display.
 * 
 * @param props - Component props
 * @returns JSX element with complete follow-up interface
 */
export function FollowupInterface({ analysisId, onBack, className = '' }: FollowupInterfaceProps) {
  const {
    currentConversation,
    questions,
    isLoading,
    isSubmitting,
    error,
    followupStatus,
    startFollowupConversation,
    askQuestion,
    loadQuestions,
    clearError,
    checkFollowupStatus
  } = useFollowupStore();

  // Initialize follow-up on mount
  React.useEffect(() => {
    const initializeFollowup = async () => {
      try {
        // First check status
        await checkFollowupStatus(analysisId);
        
        // If no conversation exists, create one
        if (!currentConversation) {
          await startFollowupConversation(analysisId);
        }
      } catch (error) {
        console.error('Failed to initialize follow-up:', error);
      }
    };
    
    initializeFollowup();
  }, [analysisId, currentConversation, checkFollowupStatus, startFollowupConversation]);

  // Load questions when conversation is available
  React.useEffect(() => {
    if (currentConversation?.id && questions.length === 0) {
      loadQuestions(currentConversation.id).catch(console.error);
    }
  }, [currentConversation?.id, questions.length, loadQuestions]);

  /**
   * Handles question submission
   */
  const handleQuestionSubmit = async (question: string) => {
    if (!currentConversation?.id) {
      throw new Error('No active conversation found');
    }
    
    await askQuestion(currentConversation.id, question);
  };

  /**
   * Handles retry for failed operations
   */
  const handleRetry = async () => {
    clearError();
    try {
      if (!currentConversation) {
        await startFollowupConversation(analysisId);
      } else {
        await loadQuestions(currentConversation.id);
      }
    } catch (error) {
      console.error('Retry failed:', error);
    }
  };

  // Check if user can ask more questions
  const canAskMoreQuestions = currentConversation 
    ? currentConversation.questionsCount < currentConversation.maxQuestions
    : false;

  // Show loading state during initialization
  if (isLoading && !currentConversation) {
    return (
      <div className={`max-w-4xl mx-auto ${className}`}>
        <ConversationSetupLoading />
      </div>
    );
  }

  // Show error state
  if (error && !currentConversation) {
    return (
      <div className={`max-w-4xl mx-auto space-y-6 ${className}`}>
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            onClick={onBack}
            className="p-2"
            title="Go back to reading"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <h1 className="text-2xl font-bold text-gray-900">
            Follow-up Questions
          </h1>
        </div>
        
        <ErrorDisplay
          error={error}
          onRetry={handleRetry}
          onClear={clearError}
        />
      </div>
    );
  }

  return (
    <div className={`max-w-4xl mx-auto space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex items-center gap-4 flex-1">
          <Button 
            variant="outline" 
            onClick={onBack}
            className="p-2 hover:bg-saffron-50"
            title="Go back to reading results"
            aria-label="Go back to reading results"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <MessageCircle className="w-6 h-6 text-saffron-600" />
              Questions about your palm reading
            </h1>
            <p className="text-gray-600 mt-1">
              Ask specific questions about your palm features and get personalized answers
            </p>
          </div>
        </div>
        
        {/* Question Limit Indicator in Header */}
        {currentConversation && (
          <div className="w-full sm:w-auto">
            <HeaderQuestionLimitIndicator 
              used={currentConversation.questionsCount}
              total={currentConversation.maxQuestions}
            />
          </div>
        )}
      </div>

      {/* Error Display (for non-critical errors) */}
      {error && currentConversation && (
        <Card className="p-4 bg-red-50 border-red-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <span className="text-red-800 text-sm">{error}</span>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={clearError}
              className="text-red-600 hover:bg-red-100"
            >
              Dismiss
            </Button>
          </div>
        </Card>
      )}

      {/* Question History */}
      {questions.length > 0 && (
        <QuestionHistory 
          questions={questions} 
          showMetadata={true}
          allowCopy={true}
        />
      )}

      {/* Question Input or Completion Message */}
      {canAskMoreQuestions && currentConversation ? (
        <div className="space-y-4">
          {/* Progress Indicator (detailed version) */}
          <QuestionLimitIndicator 
            used={currentConversation.questionsCount}
            total={currentConversation.maxQuestions}
            showDetails={true}
          />
          
          {/* Question Input */}
          <QuestionInput 
            onSubmit={handleQuestionSubmit}
            isSubmitting={isSubmitting}
            remainingQuestions={currentConversation.maxQuestions - currentConversation.questionsCount}
            showTips={questions.length === 0} // Show tips for first question
          />
        </div>
      ) : (
        /* All Questions Used */
        <Card className="p-8 text-center bg-gradient-to-r from-gray-50 to-slate-50 border-gray-200">
          <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-3">
            All questions completed
          </h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            You've used all 5 questions for this palm reading. You can review your questions 
            and answers above, or return to your analysis results.
          </p>
          
          <div className="space-y-3">
            <Button
              onClick={onBack}
              className="bg-gradient-to-r from-saffron-600 to-orange-600 hover:from-saffron-700 hover:to-orange-700 text-white"
              icon={<ArrowLeft className="w-4 h-4" />}
            >
              Back to Analysis Results
            </Button>
            
            <div className="text-xs text-gray-500">
              Your questions and answers are saved and linked to this palm reading
            </div>
          </div>
        </Card>
      )}

      {/* Welcome Message for First-Time Users */}
      {questions.length === 0 && currentConversation && !isLoading && (
        <Card className="p-6 bg-gradient-to-r from-saffron-50 to-orange-50 border-saffron-200">
          <div className="text-center space-y-3">
            <MessageCircle className="w-12 h-12 text-saffron-600 mx-auto" />
            <h3 className="text-lg font-semibold text-saffron-800">
              Welcome to Follow-up Questions!
            </h3>
            <p className="text-saffron-700 text-sm max-w-2xl mx-auto">
              Ask specific questions about your palm reading and get detailed, personalized answers 
              based on your actual palm images. You have {currentConversation.maxQuestions} questions 
              to explore different aspects of your palmistry reading.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}

/**
 * Default export for convenient importing
 */
export default FollowupInterface;