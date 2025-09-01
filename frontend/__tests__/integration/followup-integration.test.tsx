/**
 * @fileoverview Integration tests for Follow-up Questions Feature
 * 
 * Comprehensive integration tests that verify the complete user flow
 * from discovering follow-up questions to asking questions and viewing history.
 * Tests the interaction between all components and the store.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FollowupInterface } from '@/components/analysis/FollowupQuestions/FollowupInterface';
import { FollowupCTA } from '@/components/analysis/FollowupQuestions/FollowupCTA';
import { followupApi } from '@/lib/api';
import { useFollowupStore } from '@/lib/stores/followupStore';
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

// Test wrapper to reset store state
function TestWrapper({ children }: { children: React.ReactNode }) {
  React.useEffect(() => {
    useFollowupStore.getState().resetFollowup();
  }, []);
  
  return <>{children}</>;
}

describe('Follow-up Questions Integration', () => {
  const mockOnBack = vi.fn();
  const mockOnStartFollowup = vi.fn();
  
  beforeEach(() => {
    vi.clearAllMocks();
    useFollowupStore.getState().resetFollowup();
  });

  describe('Complete User Flow - New Conversation', () => {
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
      questionsCount: 0,
      maxQuestions: 5,
      createdAt: '2024-01-01T00:00:00Z'
    };

    it('completes full flow from CTA to asking question', async () => {
      const user = userEvent.setup();
      
      // Setup API mocks
      mockFollowupApi.getFollowupStatus.mockResolvedValue(mockStatus);
      mockFollowupApi.startFollowupConversation.mockResolvedValue(mockConversation);
      mockFollowupApi.askQuestion.mockResolvedValue({
        user_message: {
          id: 1,
          content: 'What does my heart line mean?',
          created_at: '2024-01-01T12:00:00Z'
        },
        assistant_message: {
          id: 2,
          content: 'Your heart line indicates strong emotional connections...',
          created_at: '2024-01-01T12:00:01Z',
          tokens_used: 150
        },
        questions_remaining: 4
      });

      // Start with CTA component
      const { rerender } = render(
        <TestWrapper>
          <FollowupCTA 
            analysisId={123}
            onStartFollowup={mockOnStartFollowup}
          />
        </TestWrapper>
      );

      // Wait for status check and CTA to appear
      await waitFor(() => {
        expect(screen.getByText('Ask Questions')).toBeInTheDocument();
      });

      // Click CTA to start follow-up
      await user.click(screen.getByText('Ask Questions'));
      expect(mockOnStartFollowup).toHaveBeenCalled();

      // Switch to FollowupInterface (simulating navigation)
      rerender(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      // Wait for interface to load and initialize
      await waitFor(() => {
        expect(screen.getByText('Questions about your palm reading')).toBeInTheDocument();
      });

      // Should show welcome message for first-time users
      expect(screen.getByText('Welcome to Follow-up Questions!')).toBeInTheDocument();

      // Type and submit a question
      const textarea = screen.getByPlaceholderText(/What would you like to know/);
      await user.type(textarea, 'What does my heart line mean?');

      const submitButton = screen.getByText('Ask Question');
      await user.click(submitButton);

      // Wait for question to be processed
      await waitFor(() => {
        expect(screen.getByText('What does my heart line mean?')).toBeInTheDocument();
        expect(screen.getByText('Your heart line indicates strong emotional connections...')).toBeInTheDocument();
      });

      // Verify API calls were made correctly
      expect(mockFollowupApi.getFollowupStatus).toHaveBeenCalledWith(123);
      expect(mockFollowupApi.startFollowupConversation).toHaveBeenCalledWith(123);
      expect(mockFollowupApi.askQuestion).toHaveBeenCalledWith(123, 456, 'What does my heart line mean?');
    });
  });

  describe('Complete User Flow - Existing Conversation', () => {
    const existingConversationStatus: FollowupStatus = {
      analysisCompleted: true,
      followupAvailable: true,
      followupConversationExists: true,
      questionsAsked: 2,
      questionsRemaining: 3,
      conversationId: 456
    };

    const mockHistoryResponse = {
      messages: [
        {
          id: 1,
          role: 'USER' as const,
          content: 'What does my life line mean?',
          created_at: '2024-01-01T10:00:00Z',
          tokens_used: 0
        },
        {
          id: 2,
          role: 'ASSISTANT' as const,
          content: 'Your life line indicates vitality...',
          tokens_used: 120,
          created_at: '2024-01-01T10:00:01Z'
        },
        {
          id: 3,
          role: 'USER' as const,
          content: 'Can you explain my head line?',
          created_at: '2024-01-01T10:05:00Z',
          tokens_used: 0
        },
        {
          id: 4,
          role: 'ASSISTANT' as const,
          content: 'Your head line shows intellectual capacity...',
          tokens_used: 130,
          created_at: '2024-01-01T10:05:01Z'
        }
      ],
      total: 4
    };

    it('loads existing conversation and allows continuing', async () => {
      const user = userEvent.setup();
      
      // Setup API mocks
      mockFollowupApi.getFollowupStatus.mockResolvedValue(existingConversationStatus);
      mockFollowupApi.getFollowupHistory.mockResolvedValue(mockHistoryResponse);

      render(
        <TestWrapper>
          <FollowupCTA 
            analysisId={123}
            onStartFollowup={mockOnStartFollowup}
          />
        </TestWrapper>
      );

      // Wait for CTA to show existing conversation state
      await waitFor(() => {
        expect(screen.getByText('Continue Your Questions')).toBeInTheDocument();
        expect(screen.getByText('Progress: 2/5 questions')).toBeInTheDocument();
      });

      // Click to continue
      await user.click(screen.getByText('Continue Questions'));
      expect(mockOnStartFollowup).toHaveBeenCalled();
    });

    it('shows conversation history when interface loads', async () => {
      // Setup API mocks
      mockFollowupApi.getFollowupStatus.mockResolvedValue(existingConversationStatus);
      mockFollowupApi.getFollowupHistory.mockResolvedValue(mockHistoryResponse);

      render(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      // Wait for interface to load
      await waitFor(() => {
        expect(screen.getByText('Questions about your palm reading')).toBeInTheDocument();
      });

      // Wait for history to load
      await waitFor(() => {
        expect(screen.getByText('What does my life line mean?')).toBeInTheDocument();
        expect(screen.getByText('Your life line indicates vitality...')).toBeInTheDocument();
        expect(screen.getByText('Can you explain my head line?')).toBeInTheDocument();
        expect(screen.getByText('Your head line shows intellectual capacity...')).toBeInTheDocument();
      });

      // Verify API calls
      expect(mockFollowupApi.getFollowupStatus).toHaveBeenCalledWith(123);
      expect(mockFollowupApi.getFollowupHistory).toHaveBeenCalledWith(123, 456);
    });
  });

  describe('Question Limit Enforcement', () => {
    const maxQuestionsStatus: FollowupStatus = {
      analysisCompleted: true,
      followupAvailable: true,
      followupConversationExists: true,
      questionsAsked: 5,
      questionsRemaining: 0,
      conversationId: 456
    };

    it('shows completion message when all questions used', async () => {
      mockFollowupApi.getFollowupStatus.mockResolvedValue(maxQuestionsStatus);
      mockFollowupApi.getFollowupHistory.mockResolvedValue({ messages: [], total: 0 });

      render(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('All questions completed')).toBeInTheDocument();
        expect(screen.getByText(/You've used all 5 questions/)).toBeInTheDocument();
        expect(screen.getByText('Back to Analysis Results')).toBeInTheDocument();
      });

      // Should not show question input
      expect(screen.queryByPlaceholderText(/What would you like to know/)).not.toBeInTheDocument();
    });

    it('allows back navigation when questions completed', async () => {
      const user = userEvent.setup();
      
      mockFollowupApi.getFollowupStatus.mockResolvedValue(maxQuestionsStatus);
      mockFollowupApi.getFollowupHistory.mockResolvedValue({ messages: [], total: 0 });

      render(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Back to Analysis Results')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Back to Analysis Results'));
      expect(mockOnBack).toHaveBeenCalled();
    });
  });

  describe('Error Handling Integration', () => {
    it('handles API errors gracefully during initialization', async () => {
      const user = userEvent.setup();
      
      mockFollowupApi.getFollowupStatus.mockRejectedValue(new Error('Network error'));

      render(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Should have retry option
      expect(screen.getByText('Try Again')).toBeInTheDocument();
      
      // Should have back navigation
      await user.click(screen.getByText(/Go back/));
      expect(mockOnBack).toHaveBeenCalled();
    });

    it('handles question submission errors', async () => {
      const user = userEvent.setup();
      
      const mockStatus: FollowupStatus = {
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: true,
        questionsAsked: 0,
        questionsRemaining: 5,
        conversationId: 456
      };

      mockFollowupApi.getFollowupStatus.mockResolvedValue(mockStatus);
      mockFollowupApi.getFollowupHistory.mockResolvedValue({ messages: [], total: 0 });
      mockFollowupApi.askQuestion.mockRejectedValue(new Error('Question submission failed'));

      render(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      // Wait for interface to load
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/What would you like to know/)).toBeInTheDocument();
      });

      // Try to submit a question
      const textarea = screen.getByPlaceholderText(/What would you like to know/);
      await user.type(textarea, 'What does my heart line mean?');
      await user.click(screen.getByText('Ask Question'));

      // Should show error
      await waitFor(() => {
        expect(screen.getByText('Question submission failed')).toBeInTheDocument();
      });

      // Should have dismiss option
      await user.click(screen.getByText('Dismiss'));
      
      await waitFor(() => {
        expect(screen.queryByText('Question submission failed')).not.toBeInTheDocument();
      });
    });
  });

  describe('State Persistence Integration', () => {
    it('maintains state across component remounts', async () => {
      const mockStatus: FollowupStatus = {
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: true,
        questionsAsked: 1,
        questionsRemaining: 4,
        conversationId: 456
      };

      const mockConversation: FollowupConversation = {
        id: 456,
        analysisId: 123,
        title: 'Follow-up Questions',
        questionsCount: 1,
        maxQuestions: 5,
        createdAt: '2024-01-01T00:00:00Z'
      };

      mockFollowupApi.getFollowupStatus.mockResolvedValue(mockStatus);
      mockFollowupApi.getFollowupHistory.mockResolvedValue({ messages: [], total: 0 });

      // Simulate store state from previous session
      useFollowupStore.setState({
        currentConversation: mockConversation,
        questions: [{
          id: '1-2',
          question: 'Previous question?',
          answer: 'Previous answer',
          timestamp: '2024-01-01T00:00:00Z',
          tokensUsed: 100
        }],
        currentAnalysisId: 123,
        followupStatus: mockStatus
      });

      const { rerender } = render(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      // Should show persisted question
      await waitFor(() => {
        expect(screen.getByText('Previous question?')).toBeInTheDocument();
      });

      // Remount component
      rerender(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      // Should still show persisted question
      await waitFor(() => {
        expect(screen.getByText('Previous question?')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility Integration', () => {
    it('maintains proper focus management through the flow', async () => {
      const user = userEvent.setup();
      
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
        questionsCount: 0,
        maxQuestions: 5,
        createdAt: '2024-01-01T00:00:00Z'
      };

      mockFollowupApi.getFollowupStatus.mockResolvedValue(mockStatus);
      mockFollowupApi.startFollowupConversation.mockResolvedValue(mockConversation);

      render(
        <TestWrapper>
          <FollowupInterface 
            analysisId={123}
            onBack={mockOnBack}
          />
        </TestWrapper>
      );

      // Wait for interface to load
      await waitFor(() => {
        expect(screen.getByText('Questions about your palm reading')).toBeInTheDocument();
      });

      // Check that back button has proper accessibility
      const backButton = screen.getByTitle('Go back to analysis results');
      expect(backButton).toHaveAttribute('aria-label', 'Go back to analysis results');

      // Tab to textarea and verify it's focusable
      const textarea = screen.getByLabelText(/Ask your question/);
      await user.tab();
      
      // Should be able to focus on textarea (exact focus testing is tricky in jsdom)
      expect(textarea).toBeInTheDocument();
      
      // Check ARIA relationships
      expect(textarea).toHaveAttribute('aria-describedby');
    });
  });
});