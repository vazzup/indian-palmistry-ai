/**
 * @fileoverview Question Input Component
 * 
 * This component provides a sophisticated input interface for users to ask
 * follow-up questions about their palm reading. It includes real-time validation,
 * character counting, helpful suggestions, and accessibility features.
 * 
 * Features:
 * - Real-time question validation (length, content relevance)
 * - Character counter with visual feedback
 * - Helpful placeholder suggestions
 * - Loading state during submission
 * - Error handling and display
 * - Mobile-responsive design
 * - Accessibility support (ARIA labels, keyboard navigation)
 * - Prevents spam/injection with content filtering
 * 
 * @example
 * ```tsx
 * <QuestionInput
 *   onSubmit={handleQuestionSubmit}
 *   isSubmitting={isSubmitting}
 *   remainingQuestions={2}
 * />
 * ```
 */

'use client';

import React, { useState, useCallback } from 'react';
import { Send, AlertCircle, CheckCircle, Lightbulb } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FollowupLoading } from './FollowupLoading';

/**
 * Props for the QuestionInput component
 */
interface QuestionInputProps {
  /** Callback function when user submits a question */
  onSubmit: (question: string) => Promise<void>;
  /** Whether the form is currently submitting */
  isSubmitting: boolean;
  /** Number of questions remaining */
  remainingQuestions: number;
  /** Optional className for custom styling */
  className?: string;
  /** Whether to show helpful tips */
  showTips?: boolean;
  /** Placeholder text for the textarea */
  placeholder?: string;
}

/**
 * Validation rules for questions
 */
const VALIDATION_RULES = {
  minLength: 10,
  maxLength: 500,
  palmistryKeywords: [
    'palm', 'hand', 'finger', 'thumb', 'line', 'mount', 'reading',
    'palmistry', 'life line', 'heart line', 'head line', 'fate line',
    'marriage line', 'money line', 'health line', 'travel line'
  ],
  forbiddenPatterns: [
    /medical\s+advice/i,
    /health\s+diagnosis/i,
    /future\s+prediction/i,
    /ignore\s+previous/i,
    /system\s+instructions/i,
    /roleplay\s+as/i
  ]
} as const;

/**
 * Sample question suggestions
 */
const QUESTION_SUGGESTIONS = [
  "What does my heart line mean for my love life?",
  "Why is my life line curved in this way?",
  "Can you explain the meaning of the lines on my mount of Venus?",
  "What do the crosses on my palm indicate?",
  "How does my thumb shape relate to my personality?",
  "What do the small lines near my fingers mean?",
  "Can you tell me about the mounts on my palm?",
  "What does the length of my fingers indicate?"
];

/**
 * Question Input Component
 * 
 * Provides a comprehensive input interface for follow-up questions with
 * validation, suggestions, and user guidance.
 * 
 * @param props - Component props
 * @returns JSX element with question input form
 */
export function QuestionInput({ 
  onSubmit, 
  isSubmitting, 
  remainingQuestions,
  className = '',
  showTips = true,
  placeholder
}: QuestionInputProps) {
  
  const [question, setQuestion] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  /**
   * Validates a question against our rules
   */
  const validateQuestion = useCallback((text: string): string | null => {
    const trimmed = text.trim();
    
    // Length validation
    if (trimmed.length < VALIDATION_RULES.minLength) {
      return `Question must be at least ${VALIDATION_RULES.minLength} characters long`;
    }
    
    if (trimmed.length > VALIDATION_RULES.maxLength) {
      return `Question must be less than ${VALIDATION_RULES.maxLength} characters`;
    }
    
    // Check for forbidden patterns (security)
    for (const pattern of VALIDATION_RULES.forbiddenPatterns) {
      if (pattern.test(trimmed)) {
        return 'Please ask questions specifically about your palm reading';
      }
    }
    
    // Check for palmistry relevance
    const hasRelevantTerm = VALIDATION_RULES.palmistryKeywords.some(keyword => 
      trimmed.toLowerCase().includes(keyword.toLowerCase())
    );
    
    if (!hasRelevantTerm) {
      return 'Please ask questions related to palm reading or palmistry features visible in your images';
    }
    
    return null;
  }, []);
  
  /**
   * Handles form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedQuestion = question.trim();
    const validation = validateQuestion(trimmedQuestion);
    
    if (validation) {
      setValidationError(validation);
      return;
    }
    
    try {
      setValidationError(null);
      await onSubmit(trimmedQuestion);
      setQuestion(''); // Clear input on success
    } catch (error: any) {
      setValidationError(error.message || 'Failed to submit question');
    }
  };
  
  /**
   * Handles input changes with real-time validation
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setQuestion(value);
    
    // Clear validation error when user starts typing
    if (validationError) {
      setValidationError(null);
    }
  };
  
  /**
   * Handles suggestion click
   */
  const handleSuggestionClick = (suggestion: string) => {
    setQuestion(suggestion);
    setShowSuggestions(false);
    setValidationError(null);
  };
  
  // Calculate validation status
  const isValid = question.trim().length >= VALIDATION_RULES.minLength && !validateQuestion(question);
  const characterCount = question.length;
  const isAtLimit = characterCount >= VALIDATION_RULES.maxLength;
  
  // Get placeholder text
  const placeholderText = placeholder || 
    "What would you like to know about your palm reading? For example: 'What does the curve in my life line mean?' or 'Can you explain the lines on my mount of Venus?'";
  
  // Show loading state during submission
  if (isSubmitting) {
    return (
      <Card className={`p-6 ${className}`}>
        <FollowupLoading 
          type="question-processing" 
          message="Our AI is analyzing your question with your palm images..."
        />
      </Card>
    );
  }
  
  return (
    <Card className={`p-6 ${className}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <label 
            htmlFor="question-input" 
            className="block text-sm font-medium text-gray-700"
          >
            Ask your question ({remainingQuestions} remaining)
          </label>
          
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="text-saffron-600 hover:text-saffron-700"
            icon={<Lightbulb className="w-4 h-4" />}
          >
            {showSuggestions ? 'Hide' : 'Show'} Examples
          </Button>
        </div>
        
        {/* Question Suggestions */}
        {showSuggestions && (
          <div className="bg-saffron-50 border border-saffron-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-saffron-800 mb-2">
              Example Questions:
            </h4>
            <div className="space-y-1">
              {QUESTION_SUGGESTIONS.slice(0, 4).map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="block w-full text-left text-sm text-saffron-700 hover:text-saffron-900 hover:bg-saffron-100 rounded px-2 py-1 transition-colors"
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Textarea Input */}
        <div className="space-y-2">
          <textarea
            id="question-input"
            value={question}
            onChange={handleInputChange}
            placeholder={placeholderText}
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-saffron-500 focus:border-transparent resize-none transition-colors"
            rows={4}
            maxLength={VALIDATION_RULES.maxLength}
            disabled={isSubmitting}
            aria-describedby="character-count validation-error question-help"
          />
          
          {/* Character Counter */}
          <div className="flex items-center justify-between text-sm">
            <div id="character-count" className="flex items-center gap-2">
              <span className={`${isAtLimit ? 'text-red-600' : 'text-gray-500'}`}>
                {characterCount}/{VALIDATION_RULES.maxLength} characters
              </span>
              
              {isValid && (
                <div className="flex items-center gap-1 text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span>Ready to submit</span>
                </div>
              )}
            </div>
            
            <div className="text-gray-500">
              Min: {VALIDATION_RULES.minLength} characters
            </div>
          </div>
        </div>
        
        {/* Validation Error */}
        {validationError && (
          <div 
            id="validation-error"
            className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg"
            role="alert"
            aria-live="polite"
          >
            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
            <span className="text-red-800 text-sm">{validationError}</span>
          </div>
        )}
        
        {/* Submit Button */}
        <Button
          type="submit"
          disabled={!isValid || isSubmitting || remainingQuestions <= 0}
          className="w-full bg-gradient-to-r from-saffron-600 to-orange-600 hover:from-saffron-700 hover:to-orange-700 text-white py-3 rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md"
          icon={<Send className="w-4 h-4" />}
          loading={isSubmitting}
        >
          {isSubmitting ? 'Submitting Question...' : 'Ask Question'}
        </Button>
        
        {/* Helpful Tips */}
        {showTips && (
          <div 
            id="question-help"
            className="p-4 bg-gradient-to-r from-saffron-50 to-orange-50 border border-saffron-200 rounded-lg"
          >
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-saffron-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-saffron-800 space-y-1">
                <p>
                  <strong>💡 Pro Tips:</strong>
                </p>
                <ul className="list-disc list-inside space-y-1 text-saffron-700">
                  <li>Ask about specific features you can see in your palm images</li>
                  <li>Mention specific lines, mounts, or markings for detailed answers</li>
                  <li>Be specific - "What does my heart line shape mean?" is better than "Tell me about love"</li>
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {/* Warning when running low */}
        {remainingQuestions <= 1 && remainingQuestions > 0 && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-center gap-2 text-amber-800">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">
                This is your {remainingQuestions === 1 ? 'last' : 'second-to-last'} question. Make it count!
              </span>
            </div>
          </div>
        )}
      </form>
    </Card>
  );
}

/**
 * Default export for convenient importing
 */
export default QuestionInput;