/**
 * @fileoverview Unit tests for Follow-up Questions Store
 * 
 * Comprehensive test suite covering all aspects of the followup store including:
 * - Initial state validation
 * - API integration methods
 * - State updates and optimistic updates
 * - Error handling scenarios
 * - Persistence and selectors
 * - Edge cases and validation
 */

import { act, renderHook } from '@testing-library/react';
import { useFollowupStore } from '@/lib/stores/followupStore';
import { followupApi } from '@/lib/api';
import type { FollowupStatus, FollowupConversation, QuestionAnswer } from '@/types';
import { vi } from 'vitest';

// Mock the API
vi.mock('@/lib/api', () => ({
  followupApi: {
    getFollowupStatus: vi.fn(),
    startFollowupConversation: vi.fn(),
    askQuestion: vi.fn(),
    getFollowupHistory: vi.fn(),
  }
}));

const mockFollowupApi = followupApi as ReturnType<typeof vi.mocked<typeof followupApi>>;

describe('FollowupStore', () => {
  
  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();
    
    // Clear store state
    useFollowupStore.getState().resetFollowup();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useFollowupStore());
      
      expect(result.current.followupStatus).toBeNull();
      expect(result.current.currentConversation).toBeNull();
      expect(result.current.questions).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.currentAnalysisId).toBeNull();
    });
  });

  describe('checkFollowupStatus', () => {
    const mockStatus: FollowupStatus = {
      analysisCompleted: true,
      followupAvailable: true,
      followupConversationExists: false,
      questionsAsked: 0,
      questionsRemaining: 5,
    };

    it('should successfully check followup status', async () => {
      mockFollowupApi.getFollowupStatus.mockResolvedValue(mockStatus);
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        await result.current.checkFollowupStatus(123);
      });

      expect(mockFollowupApi.getFollowupStatus).toHaveBeenCalledWith(123);
      expect(result.current.followupStatus).toEqual(mockStatus);
      expect(result.current.currentAnalysisId).toBe(123);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should set conversation when status indicates existing conversation', async () => {
      const statusWithConversation: FollowupStatus = {
        ...mockStatus,
        followupConversationExists: true,
        conversationId: 456,
        questionsAsked: 2
      };
      
      mockFollowupApi.getFollowupStatus.mockResolvedValue(statusWithConversation);
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        await result.current.checkFollowupStatus(123);
      });

      expect(result.current.currentConversation).toEqual({
        id: 456,
        analysisId: 123,
        title: 'Follow-up Questions for Analysis #123',
        questionsCount: 2,
        maxQuestions: 5,
        createdAt: expect.any(String)
      });
    });

    it('should handle API error', async () => {
      const errorMessage = 'Failed to check status';
      mockFollowupApi.getFollowupStatus.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.checkFollowupStatus(123);
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isLoading).toBe(false);
    });

    it('should set loading state during API call', async () => {
      let resolvePromise: (value: FollowupStatus) => void;
      const promise = new Promise<FollowupStatus>((resolve) => {
        resolvePromise = resolve;
      });
      
      mockFollowupApi.getFollowupStatus.mockReturnValue(promise);
      
      const { result } = renderHook(() => useFollowupStore());
      
      act(() => {
        result.current.checkFollowupStatus(123);
      });
      
      // Should be loading
      expect(result.current.isLoading).toBe(true);
      
      await act(async () => {
        resolvePromise!(mockStatus);
      });
      
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('startFollowupConversation', () => {
    const mockConversation: FollowupConversation = {
      id: 456,
      analysisId: 123,
      title: 'Follow-up Questions',
      questionsCount: 0,
      maxQuestions: 5,
      createdAt: '2024-01-01T00:00:00Z'
    };

    it('should successfully start conversation', async () => {
      mockFollowupApi.startFollowupConversation.mockResolvedValue(mockConversation);
      mockFollowupApi.getFollowupStatus.mockResolvedValue({
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: true,
        questionsAsked: 0,
        questionsRemaining: 5,
        conversationId: 456
      });
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        await result.current.startFollowupConversation(123);
      });

      expect(mockFollowupApi.startFollowupConversation).toHaveBeenCalledWith(123);
      expect(result.current.currentConversation).toEqual(mockConversation);
      expect(result.current.questions).toEqual([]);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle conversation creation error', async () => {
      const errorMessage = 'Failed to create conversation';
      mockFollowupApi.startFollowupConversation.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.startFollowupConversation(123);
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('askQuestion', () => {
    const mockConversation: FollowupConversation = {
      id: 456,
      analysisId: 123,
      title: 'Follow-up Questions',
      questionsCount: 0,
      maxQuestions: 5,
      createdAt: '2024-01-01T00:00:00Z'
    };

    const mockQuestionResponse = {
      user_message: {
        id: 1,
        content: 'What does my heart line mean?',
        created_at: '2024-01-01T12:00:00Z'
      },
      assistant_message: {
        id: 2,
        content: 'Your heart line indicates...',
        created_at: '2024-01-01T12:00:01Z',
        tokens_used: 150
      },
      questions_remaining: 4
    };

    beforeEach(() => {
      // Set up conversation in store
      useFollowupStore.setState({
        currentConversation: mockConversation,
        currentAnalysisId: 123
      });
    });

    it('should successfully ask question', async () => {
      mockFollowupApi.askQuestion.mockResolvedValue(mockQuestionResponse);
      mockFollowupApi.getFollowupStatus.mockResolvedValue({
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: true,
        questionsAsked: 1,
        questionsRemaining: 4,
        conversationId: 456
      });
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        await result.current.askQuestion(456, 'What does my heart line mean?');
      });

      expect(mockFollowupApi.askQuestion).toHaveBeenCalledWith(123, 456, 'What does my heart line mean?');
      
      expect(result.current.questions).toHaveLength(1);
      expect(result.current.questions[0]).toEqual({
        id: '1-2',
        question: 'What does my heart line mean?',
        answer: 'Your heart line indicates...',
        timestamp: '2024-01-01T12:00:00Z',
        tokensUsed: 150
      });
      
      expect(result.current.currentConversation?.questionsCount).toBe(1);
      expect(result.current.isSubmitting).toBe(false);
    });

    it('should validate question length', async () => {
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.askQuestion(456, 'short');
        } catch (error: any) {
          expect(error.message).toBe('Question must be at least 10 characters long');
        }
      });

      expect(mockFollowupApi.askQuestion).not.toHaveBeenCalled();
    });

    it('should validate question maximum length', async () => {
      const longQuestion = 'a'.repeat(501);
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.askQuestion(456, longQuestion);
        } catch (error: any) {
          expect(error.message).toBe('Question must be less than 500 characters');
        }
      });

      expect(mockFollowupApi.askQuestion).not.toHaveBeenCalled();
    });

    it('should validate question limit', async () => {
      // Set conversation to max questions
      useFollowupStore.setState({
        currentConversation: {
          ...mockConversation,
          questionsCount: 5
        }
      });
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.askQuestion(456, 'This is a valid question length');
        } catch (error: any) {
          expect(error.message).toBe('You have reached the maximum number of questions for this analysis');
        }
      });

      expect(mockFollowupApi.askQuestion).not.toHaveBeenCalled();
    });

    it('should handle no active conversation', async () => {
      useFollowupStore.setState({ currentConversation: null });
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.askQuestion(456, 'This is a valid question');
        } catch (error: any) {
          expect(error.message).toBe('No active conversation found');
        }
      });

      expect(mockFollowupApi.askQuestion).not.toHaveBeenCalled();
    });

    it('should handle API error', async () => {
      const errorMessage = 'Failed to process question';
      mockFollowupApi.askQuestion.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.askQuestion(456, 'This is a valid question');
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isSubmitting).toBe(false);
    });
  });

  describe('loadQuestions', () => {
    const mockConversation: FollowupConversation = {
      id: 456,
      analysisId: 123,
      title: 'Follow-up Questions',
      questionsCount: 2,
      maxQuestions: 5,
      createdAt: '2024-01-01T00:00:00Z'
    };

    const mockHistoryResponse = {
      messages: [
        {
          id: 1,
          role: 'USER' as const,
          content: 'First question?',
          created_at: '2024-01-01T10:00:00Z',
          tokens_used: 0
        },
        {
          id: 2,
          role: 'ASSISTANT' as const,
          content: 'First answer.',
          tokens_used: 100,
          created_at: '2024-01-01T10:00:01Z'
        },
        {
          id: 3,
          role: 'USER' as const,
          content: 'Second question?',
          created_at: '2024-01-01T10:05:00Z',
          tokens_used: 0
        },
        {
          id: 4,
          role: 'ASSISTANT' as const,
          content: 'Second answer.',
          tokens_used: 120,
          created_at: '2024-01-01T10:05:01Z'
        }
      ],
      total: 4
    };

    beforeEach(() => {
      useFollowupStore.setState({ currentConversation: mockConversation });
    });

    it('should successfully load questions', async () => {
      mockFollowupApi.getFollowupHistory.mockResolvedValue(mockHistoryResponse);
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        await result.current.loadQuestions(456);
      });

      expect(mockFollowupApi.getFollowupHistory).toHaveBeenCalledWith(123, 456);
      expect(result.current.questions).toHaveLength(2);
      expect(result.current.questions[0]).toEqual({
        id: '1-2',
        question: 'First question?',
        answer: 'First answer.',
        timestamp: '2024-01-01T10:00:00Z',
        tokensUsed: 100
      });
      expect(result.current.questions[1]).toEqual({
        id: '3-4',
        question: 'Second question?',
        answer: 'Second answer.',
        timestamp: '2024-01-01T10:05:00Z',
        tokensUsed: 120
      });
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle missing conversation', async () => {
      useFollowupStore.setState({ currentConversation: null });
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        await result.current.loadQuestions(456);
      });

      expect(mockFollowupApi.getFollowupHistory).not.toHaveBeenCalled();
    });

    it('should handle API error', async () => {
      const errorMessage = 'Failed to load questions';
      mockFollowupApi.getFollowupHistory.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        try {
          await result.current.loadQuestions(456);
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle mismatched message pairs', async () => {
      const mismatchedMessages = {
        messages: [
          {
            id: 1,
            role: 'USER' as const,
            content: 'Question without answer',
            created_at: '2024-01-01T10:00:00Z',
            tokens_used: 0
          },
          // Missing assistant response
          {
            id: 3,
            role: 'USER' as const,
            content: 'Another question',
            created_at: '2024-01-01T10:05:00Z',
            tokens_used: 0
          }
        ],
        total: 2
      };
      
      mockFollowupApi.getFollowupHistory.mockResolvedValue(mismatchedMessages);
      
      const { result } = renderHook(() => useFollowupStore());
      
      await act(async () => {
        await result.current.loadQuestions(456);
      });

      expect(result.current.questions).toHaveLength(0);
    });
  });

  describe('resetFollowup', () => {
    it('should reset all state to initial values', () => {
      const { result } = renderHook(() => useFollowupStore());
      
      // Set some state first
      act(() => {
        useFollowupStore.setState({
          followupStatus: {
            analysisCompleted: true,
            followupAvailable: true,
            followupConversationExists: true,
            questionsAsked: 3,
            questionsRemaining: 2
          },
          currentConversation: {
            id: 456,
            analysisId: 123,
            title: 'Test',
            questionsCount: 3,
            maxQuestions: 5,
            createdAt: '2024-01-01T00:00:00Z'
          },
          questions: [{
            id: '1-2',
            question: 'Test?',
            answer: 'Answer',
            timestamp: '2024-01-01T00:00:00Z',
            tokensUsed: 100
          }],
          error: 'Some error',
          currentAnalysisId: 123
        });
      });
      
      act(() => {
        result.current.resetFollowup();
      });

      expect(result.current.followupStatus).toBeNull();
      expect(result.current.currentConversation).toBeNull();
      expect(result.current.questions).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.currentAnalysisId).toBeNull();
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      const { result } = renderHook(() => useFollowupStore());
      
      // Set error first
      act(() => {
        useFollowupStore.setState({ error: 'Some error' });
      });
      
      expect(result.current.error).toBe('Some error');
      
      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Selectors', () => {
    const mockStatus: FollowupStatus = {
      analysisCompleted: true,
      followupAvailable: true,
      followupConversationExists: false,
      questionsAsked: 0,
      questionsRemaining: 5
    };

    const mockConversation: FollowupConversation = {
      id: 456,
      analysisId: 123,
      title: 'Follow-up Questions',
      questionsCount: 2,
      maxQuestions: 5,
      createdAt: '2024-01-01T00:00:00Z'
    };

    const mockQuestions: QuestionAnswer[] = [{
      id: '1-2',
      question: 'Test question?',
      answer: 'Test answer',
      timestamp: '2024-01-01T00:00:00Z',
      tokensUsed: 100
    }];

    beforeEach(() => {
      useFollowupStore.setState({
        followupStatus: mockStatus,
        currentConversation: mockConversation,
        questions: mockQuestions,
        isLoading: true,
        isSubmitting: true,
        error: 'Test error'
      });
    });

    it('should provide performance-optimized selectors', () => {
      // Import selectors
      const { 
        useFollowupStatus, 
        useCurrentConversation, 
        useQuestions,
        useFollowupLoading,
        useFollowupActions,
        useFollowupError,
        useCanAskMoreQuestions,
        useRemainingQuestions
      } = require('@/lib/stores/followupStore');
      
      const statusResult = renderHook(() => useFollowupStatus());
      expect(statusResult.result.current).toEqual(mockStatus);
      
      const conversationResult = renderHook(() => useCurrentConversation());
      expect(conversationResult.result.current).toEqual(mockConversation);
      
      const questionsResult = renderHook(() => useQuestions());
      expect(questionsResult.result.current).toEqual(mockQuestions);
      
      const loadingResult = renderHook(() => useFollowupLoading());
      expect(loadingResult.result.current).toEqual({
        isLoading: true,
        isSubmitting: true
      });
      
      const errorResult = renderHook(() => useFollowupError());
      expect(errorResult.result.current).toBe('Test error');
      
      const canAskResult = renderHook(() => useCanAskMoreQuestions());
      expect(canAskResult.result.current).toBe(true); // 2 < 5
      
      const remainingResult = renderHook(() => useRemainingQuestions());
      expect(remainingResult.result.current).toBe(3); // 5 - 2
    });
  });
});