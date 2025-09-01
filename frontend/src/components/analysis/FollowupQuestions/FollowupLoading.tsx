/**
 * @fileoverview Follow-up Questions Loading Component
 * 
 * This component provides various loading states for the follow-up questions
 * feature with beautiful animations and cultural theming. It shows different
 * loading messages and animations based on the current operation being performed.
 * 
 * Features:
 * - Multiple loading states for different operations
 * - Beautiful saffron-themed spinner animations
 * - Contextual loading messages
 * - Mobile-responsive design
 * - Accessibility support with proper ARIA labels
 * 
 * @example
 * ```tsx
 * <FollowupLoading message="Getting your personalized answer..." />
 * <FollowupLoading type="conversation-setup" />
 * <FollowupLoading type="question-processing" />
 * ```
 */

'use client';

import React from 'react';
import { Loader2, MessageCircle, Brain, Sparkles } from 'lucide-react';

/**
 * Different types of loading states with specific styling and messaging
 */
type LoadingType = 
  | 'default'
  | 'conversation-setup'
  | 'question-processing'
  | 'history-loading'
  | 'status-check';

/**
 * Props for the FollowupLoading component
 */
interface FollowupLoadingProps {
  /** Custom loading message to display */
  message?: string;
  /** Type of loading state (affects icon and default message) */
  type?: LoadingType;
  /** Size of the loading indicator */
  size?: 'sm' | 'md' | 'lg';
  /** Optional className for custom styling */
  className?: string;
}

/**
 * Default loading messages for different types
 */
const DEFAULT_MESSAGES: Record<LoadingType, string> = {
  default: 'Loading...',
  'conversation-setup': 'Setting up your follow-up conversation...',
  'question-processing': 'Getting your personalized answer...',
  'history-loading': 'Loading your question history...',
  'status-check': 'Checking follow-up availability...'
};

/**
 * Icons for different loading types
 */
const LOADING_ICONS: Record<LoadingType, React.ReactNode> = {
  default: <Loader2 className="animate-spin" />,
  'conversation-setup': <MessageCircle className="animate-pulse" />,
  'question-processing': <Brain className="animate-pulse" />,
  'history-loading': <Sparkles className="animate-pulse" />,
  'status-check': <Loader2 className="animate-spin" />
};

/**
 * Follow-up Questions Loading Component
 * 
 * Displays loading states for various follow-up questions operations with
 * beautiful animations and contextual messaging. The component adapts its
 * appearance based on the type of loading operation.
 * 
 * @param props - Component props
 * @returns JSX element with loading indicator
 */
export function FollowupLoading({ 
  message, 
  type = 'default', 
  size = 'md',
  className = '' 
}: FollowupLoadingProps) {
  
  const displayMessage = message || DEFAULT_MESSAGES[type];
  const icon = LOADING_ICONS[type];
  
  // Size classes for different sizes
  const sizeClasses = {
    sm: {
      container: 'py-4',
      icon: 'w-4 h-4',
      text: 'text-sm'
    },
    md: {
      container: 'py-6',
      icon: 'w-6 h-6',
      text: 'text-base'
    },
    lg: {
      container: 'py-8',
      icon: 'w-8 h-8',
      text: 'text-lg'
    }
  };
  
  const currentSizeClasses = sizeClasses[size];

  return (
    <div 
      className={`flex flex-col items-center justify-center ${currentSizeClasses.container} ${className}`}
      role="status"
      aria-label={displayMessage}
      aria-live="polite"
    >
      {/* Loading Icon with Animation */}
      <div className="relative mb-4">
        {/* Background pulse effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-saffron-300 to-orange-300 rounded-full animate-ping opacity-20"></div>
        
        {/* Main icon */}
        <div className={`relative p-3 bg-gradient-to-br from-saffron-500 to-orange-500 rounded-full shadow-lg`}>
          <div className={`text-white ${currentSizeClasses.icon}`}>
            {React.isValidElement(icon) ? React.cloneElement(icon as React.ReactElement<any>, {
              className: `${currentSizeClasses.icon} text-white`
            }) : icon}
          </div>
        </div>
      </div>
      
      {/* Loading Message */}
      <div className="text-center space-y-2">
        <p className={`font-medium text-saffron-800 ${currentSizeClasses.text}`}>
          {displayMessage}
        </p>
        
        {/* Loading dots animation */}
        <div className="flex items-center justify-center space-x-1">
          <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
          <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
          <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce"></div>
        </div>
      </div>
      
      {/* Additional context for screen readers */}
      <span className="sr-only">
        Please wait while we process your request. This may take a few moments.
      </span>
    </div>
  );
}

/**
 * Specialized loading component for conversation setup
 */
export function ConversationSetupLoading({ className = '' }: { className?: string }) {
  return (
    <FollowupLoading
      type="conversation-setup"
      size="lg"
      className={className}
    />
  );
}

/**
 * Specialized loading component for question processing
 */
export function QuestionProcessingLoading({ className = '' }: { className?: string }) {
  return (
    <FollowupLoading
      type="question-processing"
      size="md"
      message="Our AI is analyzing your question with your palm images..."
      className={className}
    />
  );
}

/**
 * Specialized loading component for history loading
 */
export function HistoryLoading({ className = '' }: { className?: string }) {
  return (
    <FollowupLoading
      type="history-loading"
      size="sm"
      className={className}
    />
  );
}

/**
 * Specialized loading component for status checking
 */
export function StatusCheckLoading({ className = '' }: { className?: string }) {
  return (
    <FollowupLoading
      type="status-check"
      size="sm"
      className={className}
    />
  );
}

/**
 * Default export for convenient importing
 */
export default FollowupLoading;