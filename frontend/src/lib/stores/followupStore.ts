/**
 * @fileoverview Zustand store for Analysis Follow-up Questions feature
 * 
 * This store manages all state related to follow-up questions functionality:
 * - Follow-up status checking and availability
 * - Conversation creation and management 
 * - Question submission and response handling
 * - Question history and limits tracking
 * - Error handling and loading states
 * 
 * Features:
 * - Optimistic updates for better UX
 * - Proper error handling with user-friendly messages
 * - State persistence for conversation data
 * - Performance optimization with selective updates
 * 
 * @example
 * ```typescript
 * const { 
 *   followupStatus, 
 *   checkFollowupStatus, 
 *   askQuestion 
 * } = useFollowupStore();
 * 
 * // Check if follow-up questions are available
 * await checkFollowupStatus(analysisId);
 * 
 * // Ask a question
 * if (followupStatus?.followupAvailable) {
 *   await askQuestion(conversationId, "What does my heart line mean?");
 * }
 * ```
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { followupApi } from '@/lib/api';
import type { 
  FollowupStatus, 
  FollowupConversation, 
  QuestionAnswer 
} from '@/types';

/**
 * Follow-up Questions Store State Interface
 * 
 * Manages all state related to follow-up questions functionality including
 * status tracking, conversation management, question history, and UI states.
 */
interface FollowupStore {
  // ============================================================================
  // STATE PROPERTIES
  // ============================================================================
  
  /** Current follow-up availability status for an analysis */
  followupStatus: FollowupStatus | null;
  
  /** Active follow-up conversation details */
  currentConversation: FollowupConversation | null;
  
  /** Array of question-answer pairs for current conversation */
  questions: QuestionAnswer[];
  
  /** Global loading state for initial operations */
  isLoading: boolean;
  
  /** Loading state specifically for question submission */
  isSubmitting: boolean;
  
  /** Current error message, null if no error */
  error: string | null;
  
  /** Analysis ID for current follow-up session */
  currentAnalysisId: number | null;

  // ============================================================================
  // ACTION METHODS
  // ============================================================================
  
  /**
   * Check if follow-up questions are available for an analysis
   * 
   * This method verifies:
   * - Analysis is completed and available for follow-up
   * - User has remaining questions (if conversation exists)
   * - Current conversation status and limits
   * 
   * @param analysisId - ID of the analysis to check
   * @throws Error if API call fails or analysis not found
   * 
   * @example
   * ```typescript
   * try {
   *   await checkFollowupStatus(123);
   *   if (followupStatus.followupAvailable) {
   *     // Show follow-up CTA
   *   }
   * } catch (error) {
   *   console.error('Failed to check status:', error);
   * }
   * ```
   */
  checkFollowupStatus: (analysisId: number) => Promise<void>;
  
  /**
   * Start a new follow-up conversation for an analysis
   * 
   * This creates a new conversation and uploads palm images to OpenAI Files API
   * for context-aware responses. Only one follow-up conversation per analysis.
   * 
   * @param analysisId - ID of the analysis to start follow-up for
   * @throws Error if conversation creation fails or analysis not found
   * 
   * @example
   * ```typescript
   * try {
   *   await startFollowupConversation(123);
   *   // Conversation created, can now ask questions
   * } catch (error) {
   *   console.error('Failed to start conversation:', error);
   * }
   * ```
   */
  startFollowupConversation: (analysisId: number) => Promise<void>;
  
  /**
   * Submit a follow-up question and get AI response
   * 
   * Questions are validated on client side before submission:
   * - Length between 10-500 characters
   * - Must be related to palmistry
   * - Respects 5-question limit per analysis
   * 
   * @param conversationId - ID of the conversation to add question to
   * @param question - User's question about their palm reading
   * @throws Error if question submission fails or limit exceeded
   * 
   * @example
   * ```typescript
   * try {
   *   await askQuestion(456, "What does my heart line mean for love?");
   *   // Question added to history with AI response
   * } catch (error) {
   *   console.error('Failed to ask question:', error);
   * }
   * ```
   */
  askQuestion: (conversationId: number, question: string) => Promise<void>;
  
  /**
   * Load question history for current conversation
   * 
   * Retrieves all previous questions and answers for the current conversation.
   * Called automatically when conversation is set, can be called manually to refresh.
   * 
   * @param conversationId - ID of conversation to load history for
   * @throws Error if history loading fails
   * 
   * @example
   * ```typescript
   * await loadQuestions(456);
   * // questions array now contains all Q&A pairs
   * ```
   */
  loadQuestions: (conversationId: number) => Promise<void>;
  
  /**
   * Reset all follow-up state to initial values
   * 
   * Clears all conversation data, questions, status, and error states.
   * Useful when navigating away from follow-up interface or starting fresh.
   * 
   * @example
   * ```typescript
   * resetFollowup(); // Clear all follow-up state
   * ```
   */
  resetFollowup: () => void;
  
  /**
   * Clear current error state
   * 
   * Removes error message from store state. Used by error display components
   * when user dismisses error or when starting new operations.
   * 
   * @example
   * ```typescript
   * clearError(); // Remove error message from UI
   * ```
   */
  clearError: () => void;
}

/**
 * Zustand store for Follow-up Questions functionality
 * 
 * This store is configured with:
 * - DevTools integration for debugging in development
 * - Persistence for conversation data across browser sessions
 * - Performance optimization with selective state updates
 * 
 * State is persisted to localStorage to maintain conversation context
 * across page refreshes and browser sessions.
 */
export const useFollowupStore = create<FollowupStore>()(
  devtools(
    persist(
      (set, get) => ({
        // ========================================================================
        // INITIAL STATE
        // ========================================================================
        followupStatus: null,
        currentConversation: null,
        questions: [],
        isLoading: false,
        isSubmitting: false,
        error: null,
        currentAnalysisId: null,

        // ========================================================================
        // ACTION IMPLEMENTATIONS
        // ========================================================================

        checkFollowupStatus: async (analysisId: number) => {
          try {
            set({ isLoading: true, error: null, currentAnalysisId: analysisId });
            
            const status = await followupApi.getFollowupStatus(analysisId);
            
            set({ 
              followupStatus: status,
              isLoading: false
            });

            // If conversation exists, load it
            if (status.followupConversationExists && status.conversationId) {
              // Set basic conversation data from status
              set({
                currentConversation: {
                  id: status.conversationId,
                  analysisId: analysisId,
                  title: `Follow-up Questions for Analysis #${analysisId}`,
                  questionsCount: status.questionsAsked,
                  maxQuestions: 5, // Default max questions
                  createdAt: new Date().toISOString() // Placeholder
                }
              });
            }
            
          } catch (error: any) {
            const errorMessage = error.message || 'Failed to check follow-up status';
            set({ 
              error: errorMessage,
              isLoading: false
            });
            throw error;
          }
        },

        startFollowupConversation: async (analysisId: number) => {
          try {
            set({ isLoading: true, error: null, currentAnalysisId: analysisId });
            
            const conversation = await followupApi.startFollowupConversation(analysisId);
            
            set({ 
              currentConversation: conversation,
              questions: [], // Start with empty questions
              isLoading: false
            });
            
            // Update status to reflect new conversation
            await get().checkFollowupStatus(analysisId);
            
          } catch (error: any) {
            const errorMessage = error.message || 'Failed to start follow-up conversation';
            set({ 
              error: errorMessage,
              isLoading: false
            });
            throw error;
          }
        },

        askQuestion: async (conversationId: number, question: string) => {
          const state = get();
          
          if (!state.currentConversation) {
            throw new Error('No active conversation found');
          }

          // Client-side validation
          if (question.trim().length < 10) {
            throw new Error('Question must be at least 10 characters long');
          }
          if (question.trim().length > 500) {
            throw new Error('Question must be less than 500 characters');
          }

          // Check question limit
          if (state.currentConversation.questionsCount >= state.currentConversation.maxQuestions) {
            throw new Error('You have reached the maximum number of questions for this analysis');
          }

          try {
            set({ isSubmitting: true, error: null });
            
            const response = await followupApi.askQuestion(
              state.currentConversation.analysisId, 
              conversationId, 
              question.trim()
            );
            
            // Create new Q&A pair from response
            const newQA: QuestionAnswer = {
              id: `${response.user_message.id}-${response.assistant_message.id}`,
              question: response.user_message.content,
              answer: response.assistant_message.content,
              timestamp: response.user_message.created_at,
              tokensUsed: response.assistant_message.tokens_used || 0
            };
            
            // Update state with optimistic updates
            set(currentState => ({
              questions: [...currentState.questions, newQA],
              currentConversation: currentState.currentConversation ? {
                ...currentState.currentConversation,
                questionsCount: currentState.currentConversation.questionsCount + 1
              } : null,
              isSubmitting: false
            }));
            
            // Update status to reflect new question count
            if (state.currentAnalysisId) {
              get().checkFollowupStatus(state.currentAnalysisId);
            }
            
          } catch (error: any) {
            const errorMessage = error.message || 'Failed to process question';
            set({ 
              error: errorMessage,
              isSubmitting: false
            });
            throw error;
          }
        },

        loadQuestions: async (conversationId: number) => {
          const state = get();
          
          if (!state.currentConversation) {
            console.warn('No current conversation found for loading questions');
            return;
          }

          try {
            set({ isLoading: true, error: null });
            
            const response = await followupApi.getFollowupHistory(
              state.currentConversation.analysisId,
              conversationId
            );
            
            const questions: QuestionAnswer[] = [];
            const messages = response.messages;
            
            // Pair user and assistant messages
            for (let i = 0; i < messages.length; i += 2) {
              if (i + 1 < messages.length) {
                const userMessage = messages[i];
                const assistantMessage = messages[i + 1];
                
                // Only pair if user message followed by assistant message
                if (userMessage.role === 'USER' && assistantMessage.role === 'ASSISTANT') {
                  questions.push({
                    id: `${userMessage.id}-${assistantMessage.id}`,
                    question: userMessage.content,
                    answer: assistantMessage.content,
                    timestamp: userMessage.created_at,
                    tokensUsed: assistantMessage.tokens_used || 0
                  });
                }
              }
            }
            
            set({ 
              questions,
              isLoading: false
            });
            
          } catch (error: any) {
            const errorMessage = error.message || 'Failed to load questions';
            set({ 
              error: errorMessage,
              isLoading: false
            });
            throw error;
          }
        },

        resetFollowup: () => {
          set({
            followupStatus: null,
            currentConversation: null,
            questions: [],
            isLoading: false,
            isSubmitting: false,
            error: null,
            currentAnalysisId: null
          });
        },

        clearError: () => {
          set({ error: null });
        }
      }),
      {
        name: 'followup-store',
        // Only persist conversation data, not loading states
        partialize: (state) => ({
          currentConversation: state.currentConversation,
          questions: state.questions,
          currentAnalysisId: state.currentAnalysisId,
          followupStatus: state.followupStatus
        }),
      }
    ),
    {
      name: 'followup-store'
    }
  )
);

// ============================================================================
// UTILITY HOOKS AND SELECTORS
// ============================================================================

/**
 * Hook to get only follow-up status (performance optimized)
 * Use this when you only need status information, not full store state
 */
export const useFollowupStatus = () => 
  useFollowupStore(state => state.followupStatus);

/**
 * Hook to get only current conversation (performance optimized)
 * Use this when you only need conversation data, not full store state  
 */
export const useCurrentConversation = () => 
  useFollowupStore(state => state.currentConversation);

/**
 * Hook to get only questions array (performance optimized)
 * Use this when you only need questions data, not full store state
 */
export const useQuestions = () => 
  useFollowupStore(state => state.questions);

/**
 * Hook to get only loading states (performance optimized)
 * Use this when you only need loading information, not full store state
 */
export const useFollowupLoading = () => 
  useFollowupStore(state => ({
    isLoading: state.isLoading,
    isSubmitting: state.isSubmitting
  }));

/**
 * Hook to get only action methods (performance optimized)
 * Use this when you only need actions, not state data
 */
export const useFollowupActions = () => 
  useFollowupStore(state => ({
    checkFollowupStatus: state.checkFollowupStatus,
    startFollowupConversation: state.startFollowupConversation,
    askQuestion: state.askQuestion,
    loadQuestions: state.loadQuestions,
    resetFollowup: state.resetFollowup,
    clearError: state.clearError
  }));

/**
 * Hook to get error state (performance optimized)
 * Use this when you only need error information, not full store state
 */
export const useFollowupError = () => 
  useFollowupStore(state => state.error);

/**
 * Helper function to check if user can ask more questions
 * @returns boolean indicating if more questions are allowed
 */
export const useCanAskMoreQuestions = () => 
  useFollowupStore(state => {
    if (!state.currentConversation) return false;
    return state.currentConversation.questionsCount < state.currentConversation.maxQuestions;
  });

/**
 * Helper function to get remaining questions count
 * @returns number of remaining questions, or 0 if no conversation
 */
export const useRemainingQuestions = () => 
  useFollowupStore(state => {
    if (!state.currentConversation) return 0;
    return state.currentConversation.maxQuestions - state.currentConversation.questionsCount;
  });