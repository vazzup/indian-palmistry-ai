/**
 * @fileoverview Follow-up Questions Components Export Index
 * 
 * This file provides a centralized export point for all follow-up questions
 * components, making them easy to import and use throughout the application.
 * 
 * @example
 * ```typescript
 * import { 
 *   FollowupCTA, 
 *   FollowupInterface, 
 *   QuestionInput 
 * } from '@/components/analysis/FollowupQuestions';
 * ```
 */

// Main components
export { FollowupCTA } from './FollowupCTA';
export { FollowupInterface } from './FollowupInterface';
export { QuestionInput } from './QuestionInput';
export { QuestionHistory } from './QuestionHistory';

// UI components
export { 
  QuestionLimitIndicator,
  HeaderQuestionLimitIndicator,
  DetailedQuestionLimitIndicator 
} from './QuestionLimitIndicator';

export { 
  FollowupLoading,
  ConversationSetupLoading,
  QuestionProcessingLoading,
  HistoryLoading,
  StatusCheckLoading
} from './FollowupLoading';

// Default exports for convenience
export { default as FollowupCTADefault } from './FollowupCTA';
export { default as FollowupInterfaceDefault } from './FollowupInterface';
export { default as QuestionInputDefault } from './QuestionInput';
export { default as QuestionHistoryDefault } from './QuestionHistory';
export { default as QuestionLimitIndicatorDefault } from './QuestionLimitIndicator';
export { default as FollowupLoadingDefault } from './FollowupLoading';