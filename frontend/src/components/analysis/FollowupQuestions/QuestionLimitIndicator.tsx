/**
 * @fileoverview Question Limit Indicator Component
 * 
 * This component displays the current progress of questions asked versus the
 * maximum allowed questions for a follow-up conversation. It provides a visual
 * progress indicator and helpful messaging about remaining questions.
 * 
 * Features:
 * - Visual progress bar with gradient animation
 * - Clear numerical display of progress
 * - Contextual messages based on usage
 * - Mobile-responsive design
 * - Color-coded progress (green for available, amber for running low, red for used up)
 * - Accessibility support
 * 
 * @example
 * ```tsx
 * <QuestionLimitIndicator used={3} total={5} />
 * <QuestionLimitIndicator 
 *   used={5} 
 *   total={5} 
 *   showDetails={true}
 *   size="lg"
 * />
 * ```
 */

'use client';

import React from 'react';
import { CheckCircle, AlertCircle, XCircle, HelpCircle } from 'lucide-react';

/**
 * Props for the QuestionLimitIndicator component
 */
interface QuestionLimitIndicatorProps {
  /** Number of questions used */
  used: number;
  /** Total number of questions allowed */
  total: number;
  /** Show detailed information and tips */
  showDetails?: boolean;
  /** Size of the indicator */
  size?: 'sm' | 'md' | 'lg';
  /** Optional className for custom styling */
  className?: string;
  /** Whether to show as compact inline version */
  compact?: boolean;
}

/**
 * Question Limit Indicator Component
 * 
 * Displays a progress indicator showing how many questions have been used
 * out of the total allowed. Provides visual feedback with colors and icons
 * to help users understand their remaining question allowance.
 * 
 * @param props - Component props
 * @returns JSX element with question limit indicator
 */
export function QuestionLimitIndicator({ 
  used, 
  total, 
  showDetails = false,
  size = 'md',
  className = '',
  compact = false
}: QuestionLimitIndicatorProps) {
  
  const remaining = Math.max(0, total - used);
  const percentage = Math.min(100, (used / total) * 100);
  const isComplete = used >= total;
  const isRunningLow = remaining <= 1 && !isComplete;
  
  // Size configurations
  const sizeConfig = {
    sm: {
      text: 'text-sm',
      icon: 'w-4 h-4',
      bar: 'h-2',
      padding: 'p-2'
    },
    md: {
      text: 'text-base',
      icon: 'w-5 h-5',
      bar: 'h-3',
      padding: 'p-3'
    },
    lg: {
      text: 'text-lg',
      icon: 'w-6 h-6',
      bar: 'h-4',
      padding: 'p-4'
    }
  };
  
  const config = sizeConfig[size];
  
  // Color and icon based on status
  const getStatusInfo = () => {
    if (isComplete) {
      return {
        color: 'red',
        icon: <XCircle className={`${config.icon} text-red-600`} />,
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        textColor: 'text-red-800',
        barColor: 'from-red-500 to-red-600',
        message: 'All questions used'
      };
    } else if (isRunningLow) {
      return {
        color: 'amber',
        icon: <AlertCircle className={`${config.icon} text-amber-600`} />,
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-200',
        textColor: 'text-amber-800',
        barColor: 'from-amber-500 to-orange-500',
        message: `Only ${remaining} question${remaining === 1 ? '' : 's'} left`
      };
    } else {
      return {
        color: 'green',
        icon: <CheckCircle className={`${config.icon} text-green-600`} />,
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        textColor: 'text-green-800',
        barColor: 'from-saffron-500 to-orange-500',
        message: `${remaining} question${remaining === 1 ? '' : 's'} remaining`
      };
    }
  };
  
  const statusInfo = getStatusInfo();
  
  // Compact version for inline display
  if (compact) {
    return (
      <div className={`inline-flex items-center gap-2 ${className}`}>
        <div className={`${statusInfo.textColor} ${config.text} font-medium`}>
          {used}/{total}
        </div>
        <div className={`w-12 ${statusInfo.bgColor} rounded-full ${config.bar} overflow-hidden`}>
          <div 
            className={`bg-gradient-to-r ${statusInfo.barColor} ${config.bar} transition-all duration-500 ease-out`}
            style={{ width: `${percentage}%` }}
            aria-label={`${used} out of ${total} questions used`}
          />
        </div>
      </div>
    );
  }
  
  return (
    <div 
      className={`${statusInfo.bgColor} ${statusInfo.borderColor} border rounded-lg ${config.padding} ${className}`}
      role="region"
      aria-label="Question usage indicator"
    >
      <div className="space-y-3">
        {/* Header with icon and status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {statusInfo.icon}
            <span className={`${statusInfo.textColor} font-medium ${config.text}`}>
              Questions: {used}/{total}
            </span>
          </div>
          
          {!isComplete && (
            <span className={`${statusInfo.textColor} ${config.text}`}>
              {remaining} left
            </span>
          )}
        </div>
        
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="w-full bg-gray-200 rounded-full overflow-hidden">
            <div 
              className={`bg-gradient-to-r ${statusInfo.barColor} transition-all duration-700 ease-out shadow-sm ${config.bar}`}
              style={{ width: `${percentage}%` }}
              aria-label={`${used} out of ${total} questions used`}
            />
          </div>
          
          {/* Progress labels */}
          <div className="flex justify-between items-center text-xs text-gray-500">
            <span>0</span>
            <span className={`${statusInfo.textColor} font-medium`}>
              {statusInfo.message}
            </span>
            <span>{total}</span>
          </div>
        </div>
        
        {/* Detailed information */}
        {showDetails && (
          <div className={`pt-2 border-t ${statusInfo.borderColor} space-y-2`}>
            {!isComplete && (
              <div className="flex items-start gap-2">
                <HelpCircle className="w-4 h-4 text-saffron-600 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-saffron-700 space-y-1">
                  <p>
                    <strong>Tip:</strong> Ask specific questions about features you can see in your palm images for the most accurate answers.
                  </p>
                  {remaining > 1 && (
                    <p>
                      Make each question count! Focus on different aspects like lines, mounts, or finger characteristics.
                    </p>
                  )}
                </div>
              </div>
            )}
            
            {isComplete && (
              <div className="text-xs text-red-700">
                <p>
                  You've used all your questions for this palm reading. You can review your answers above.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Specialized component for header display (compact version)
 */
export function HeaderQuestionLimitIndicator({ used, total, className = '' }: {
  used: number;
  total: number;
  className?: string;
}) {
  return (
    <QuestionLimitIndicator
      used={used}
      total={total}
      size="sm"
      compact={true}
      className={className}
    />
  );
}

/**
 * Specialized component for detailed progress display
 */
export function DetailedQuestionLimitIndicator({ used, total, className = '' }: {
  used: number;
  total: number;
  className?: string;
}) {
  return (
    <QuestionLimitIndicator
      used={used}
      total={total}
      size="md"
      showDetails={true}
      className={className}
    />
  );
}

/**
 * Default export for convenient importing
 */
export default QuestionLimitIndicator;