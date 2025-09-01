/**
 * @fileoverview Question History Component
 * 
 * This component displays the conversation history of questions and answers
 * between the user and AI in a beautiful, easy-to-read format. Each Q&A pair
 * is presented with clear visual separation and metadata.
 * 
 * Features:
 * - Beautiful timeline-style layout with numbering
 * - Distinct styling for questions vs answers
 * - Metadata display (timestamps, tokens used)
 * - Mobile-responsive design
 * - Copy-to-clipboard functionality
 * - Smooth animations and transitions
 * - Accessibility support
 * - Empty state handling
 * 
 * @example
 * ```tsx
 * <QuestionHistory questions={questionsArray} />
 * <QuestionHistory 
 *   questions={questionsArray}
 *   showMetadata={true}
 *   allowCopy={true}
 * />
 * ```
 */

'use client';

import React, { useState } from 'react';
import { 
  MessageCircle, 
  Clock, 
  Zap, 
  Copy, 
  Check, 
  User, 
  Bot,
  Calendar
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { QuestionAnswer } from '@/types';

/**
 * Props for the QuestionHistory component
 */
interface QuestionHistoryProps {
  /** Array of question-answer pairs to display */
  questions: QuestionAnswer[];
  /** Whether to show metadata (timestamps, tokens) */
  showMetadata?: boolean;
  /** Whether to allow copying of answers */
  allowCopy?: boolean;
  /** Optional className for custom styling */
  className?: string;
  /** Maximum number of questions to show initially */
  initialLimit?: number;
}

/**
 * Individual Question-Answer Pair Component
 */
interface QuestionAnswerPairProps {
  qa: QuestionAnswer;
  index: number;
  showMetadata: boolean;
  allowCopy: boolean;
}

function QuestionAnswerPair({ qa, index, showMetadata, allowCopy }: QuestionAnswerPairProps) {
  const [copiedAnswer, setCopiedAnswer] = useState(false);
  
  /**
   * Copies answer text to clipboard
   */
  const handleCopyAnswer = async () => {
    try {
      await navigator.clipboard.writeText(qa.answer);
      setCopiedAnswer(true);
      setTimeout(() => setCopiedAnswer(false), 2000);
    } catch (error) {
      console.error('Failed to copy answer:', error);
    }
  };
  
  /**
   * Formats timestamp for display
   */
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch (error) {
      return 'Unknown time';
    }
  };
  
  return (
    <div className="relative pl-8 pb-8 last:pb-0">
      {/* Timeline Line */}
      <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-gradient-to-b from-saffron-300 to-orange-300 last:hidden"></div>
      
      {/* Question Number Badge */}
      <div className="absolute left-0 top-0 w-6 h-6 bg-gradient-to-br from-saffron-600 to-orange-600 text-white rounded-full flex items-center justify-center text-sm font-semibold shadow-md">
        {index + 1}
      </div>
      
      <div className="space-y-4">
        {/* Question Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <User className="w-4 h-4 text-saffron-600" />
            <span className="font-medium text-saffron-700">Your Question</span>
            {showMetadata && (
              <>
                <Clock className="w-3 h-3 text-gray-400 ml-2" />
                <span className="text-xs text-gray-500">
                  {formatTimestamp(qa.timestamp)}
                </span>
              </>
            )}
          </div>
          
          <Card className="bg-gradient-to-r from-saffron-50 to-orange-50 border-saffron-200 p-4">
            <p className="text-gray-900 leading-relaxed">
              {qa.question}
            </p>
          </Card>
        </div>
        
        {/* Answer Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <Bot className="w-4 h-4 text-green-600" />
              <span className="font-medium text-green-700">AI Response</span>
              {showMetadata && qa.tokensUsed > 0 && (
                <>
                  <Zap className="w-3 h-3 text-gray-400 ml-2" />
                  <span className="text-xs text-gray-500">
                    {qa.tokensUsed} tokens
                  </span>
                </>
              )}
            </div>
            
            {allowCopy && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopyAnswer}
                className="text-gray-500 hover:text-gray-700 p-1"
                title="Copy answer to clipboard"
              >
                {copiedAnswer ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            )}
          </div>
          
          <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 p-4">
            <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {qa.answer}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

/**
 * Empty State Component
 */
function EmptyState() {
  return (
    <Card className="p-8 text-center bg-gray-50 border-gray-200">
      <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        No questions yet
      </h3>
      <p className="text-gray-600 max-w-sm mx-auto">
        Your questions and answers will appear here as you ask them. Start by asking your first question below!
      </p>
    </Card>
  );
}

/**
 * Question History Component
 * 
 * Displays a timeline of questions and answers with beautiful formatting
 * and helpful metadata. Supports various display options and user interactions.
 * 
 * @param props - Component props
 * @returns JSX element with question history
 */
export function QuestionHistory({ 
  questions, 
  showMetadata = true,
  allowCopy = true,
  className = '',
  initialLimit
}: QuestionHistoryProps) {
  
  const [showAll, setShowAll] = useState(false);
  
  // Handle empty state
  if (!questions || questions.length === 0) {
    return <EmptyState />;
  }
  
  // Determine which questions to show
  const shouldLimitDisplay = initialLimit && initialLimit > 0 && questions.length > initialLimit;
  const questionsToShow = shouldLimitDisplay && !showAll 
    ? questions.slice(0, initialLimit)
    : questions;
  
  const hiddenCount = questions.length - (questionsToShow.length);
  
  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <MessageCircle className="w-5 h-5 text-saffron-600" />
        <h2 className="text-lg font-semibold text-gray-900">
          Your Questions & Answers
        </h2>
        <span className="bg-saffron-100 text-saffron-700 px-2 py-1 rounded-full text-xs font-medium">
          {questions.length} question{questions.length === 1 ? '' : 's'}
        </span>
      </div>
      
      {/* Questions Timeline */}
      <div className="space-y-6">
        {questionsToShow.map((qa, index) => (
          <QuestionAnswerPair
            key={qa.id}
            qa={qa}
            index={index}
            showMetadata={showMetadata}
            allowCopy={allowCopy}
          />
        ))}
        
        {/* Show More Button */}
        {shouldLimitDisplay && (
          <div className="text-center pt-4 border-t border-gray-200">
            <Button
              variant="outline"
              onClick={() => setShowAll(!showAll)}
              className="text-saffron-600 border-saffron-300 hover:bg-saffron-50"
            >
              {showAll ? 'Show Less' : `Show ${hiddenCount} More Question${hiddenCount === 1 ? '' : 's'}`}
            </Button>
          </div>
        )}
      </div>
      
      {/* Summary Stats */}
      {showMetadata && questions.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-sm text-gray-500">Total Questions</div>
              <div className="text-lg font-semibold text-saffron-600">
                {questions.length}
              </div>
            </div>
            
            <div>
              <div className="text-sm text-gray-500">Total Tokens</div>
              <div className="text-lg font-semibold text-green-600">
                {questions.reduce((sum, q) => sum + q.tokensUsed, 0).toLocaleString()}
              </div>
            </div>
            
            <div className="col-span-2 sm:col-span-1">
              <div className="text-sm text-gray-500">Latest Question</div>
              <div className="text-sm font-medium text-gray-700 flex items-center justify-center gap-1">
                <Calendar className="w-3 h-3" />
                {questions.length > 0 && formatTimestamp(questions[questions.length - 1]?.timestamp)}
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

/**
 * Helper function to format timestamps consistently
 */
function formatTimestamp(timestamp: string) {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } else {
      return date.toLocaleDateString();
    }
  } catch (error) {
    return 'Unknown time';
  }
}

/**
 * Default export for convenient importing
 */
export default QuestionHistory;