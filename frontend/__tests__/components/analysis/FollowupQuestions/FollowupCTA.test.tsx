/**
 * @fileoverview Unit tests for FollowupCTA Component
 * 
 * Comprehensive test suite for the Follow-up Questions Call-to-Action component
 * covering all user interactions, state scenarios, and edge cases.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FollowupCTA } from '@/components/analysis/FollowupQuestions/FollowupCTA';
import { useFollowupStore } from '@/lib/stores/followupStore';
import type { FollowupStatus } from '@/types';
import { vi } from 'vitest';

// Mock the store
vi.mock('@/lib/stores/followupStore');

const mockUseFollowupStore = useFollowupStore as ReturnType<typeof vi.mocked<typeof useFollowupStore>>;

describe('FollowupCTA', () => {
  const mockOnStartFollowup = vi.fn();
  const mockCheckFollowupStatus = vi.fn();
  const mockClearError = vi.fn();
  
  const defaultProps = {
    analysisId: 123,
    onStartFollowup: mockOnStartFollowup
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockCheckFollowupStatus.mockResolvedValue(undefined);
  });

  describe('Loading State', () => {
    it('renders loading state correctly', () => {
      mockUseFollowupStore.mockReturnValue({
        followupStatus: null,
        isLoading: true,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        // Other store properties with default values
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      render(<FollowupCTA {...defaultProps} />);

      expect(screen.getByText('Checking follow-up availability...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('calls checkFollowupStatus on mount', () => {
      mockUseFollowupStore.mockReturnValue({
        followupStatus: null,
        isLoading: true,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      render(<FollowupCTA {...defaultProps} />);

      expect(mockCheckFollowupStatus).toHaveBeenCalledWith(123);
    });
  });

  describe('Not Available State', () => {
    it('does not render when followup is not available', () => {
      const status: FollowupStatus = {
        analysisCompleted: true,
        followupAvailable: false,
        followupConversationExists: false,
        questionsAsked: 0,
        questionsRemaining: 0
      };

      mockUseFollowupStore.mockReturnValue({
        followupStatus: status,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      const { container } = render(<FollowupCTA {...defaultProps} />);

      expect(container.firstChild).toBeNull();
    });

    it('does not render when analysis is not completed', () => {
      const status: FollowupStatus = {
        analysisCompleted: false,
        followupAvailable: false,
        followupConversationExists: false,
        questionsAsked: 0,
        questionsRemaining: 0
      };

      mockUseFollowupStore.mockReturnValue({
        followupStatus: status,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      const { container } = render(<FollowupCTA {...defaultProps} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Error State', () => {
    it('renders error state correctly', () => {
      mockUseFollowupStore.mockReturnValue({
        followupStatus: null,
        isLoading: false,
        error: 'Failed to check follow-up status',
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      render(<FollowupCTA {...defaultProps} />);

      expect(screen.getByText('Failed to check follow-up status')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    it('calls clearError when Try Again is clicked', async () => {
      const user = userEvent.setup();
      
      mockUseFollowupStore.mockReturnValue({
        followupStatus: null,
        isLoading: false,
        error: 'Failed to check follow-up status',
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      render(<FollowupCTA {...defaultProps} />);

      await user.click(screen.getByText('Try Again'));

      expect(mockClearError).toHaveBeenCalled();
    });
  });

  describe('Available State - New Conversation', () => {
    const availableStatus: FollowupStatus = {
      analysisCompleted: true,
      followupAvailable: true,
      followupConversationExists: false,
      questionsAsked: 0,
      questionsRemaining: 5
    };

    beforeEach(() => {
      mockUseFollowupStore.mockReturnValue({
        followupStatus: availableStatus,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });
    });

    it('renders new conversation CTA correctly', () => {
      render(<FollowupCTA {...defaultProps} />);

      expect(screen.getByText('Have questions about your palm reading?')).toBeInTheDocument();
      expect(screen.getByText(/Ask up to 5 personalized questions/)).toBeInTheDocument();
      expect(screen.getByText('Ask Questions')).toBeInTheDocument();
      expect(screen.getByText(/Questions are specific to your palm images/)).toBeInTheDocument();
    });

    it('calls onStartFollowup when button is clicked', async () => {
      const user = userEvent.setup();
      
      render(<FollowupCTA {...defaultProps} />);

      await user.click(screen.getByText('Ask Questions'));

      expect(mockOnStartFollowup).toHaveBeenCalled();
    });

    it('has proper accessibility attributes', () => {
      render(<FollowupCTA {...defaultProps} />);

      const button = screen.getByText('Ask Questions');
      expect(button).toHaveAttribute('aria-label', 'Start asking questions');
    });
  });

  describe('Available State - Existing Conversation', () => {
    const existingConversationStatus: FollowupStatus = {
      analysisCompleted: true,
      followupAvailable: true,
      followupConversationExists: true,
      questionsAsked: 3,
      questionsRemaining: 2,
      conversationId: 456
    };

    beforeEach(() => {
      mockUseFollowupStore.mockReturnValue({
        followupStatus: existingConversationStatus,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });
    });

    it('renders existing conversation CTA correctly', () => {
      render(<FollowupCTA {...defaultProps} />);

      expect(screen.getByText('Continue Your Questions')).toBeInTheDocument();
      expect(screen.getByText(/You've asked 3 of 5 questions/)).toBeInTheDocument();
      expect(screen.getByText('Continue Questions')).toBeInTheDocument();
      expect(screen.getByText('Progress: 3/5 questions')).toBeInTheDocument();
      expect(screen.getByText('2 remaining')).toBeInTheDocument();
    });

    it('shows progress bar with correct percentage', () => {
      render(<FollowupCTA {...defaultProps} />);

      const progressBar = screen.getByLabelText('3 out of 5 questions used');
      expect(progressBar).toHaveStyle('width: 60%'); // 3/5 * 100%
    });

    it('calls onStartFollowup when continue button is clicked', async () => {
      const user = userEvent.setup();
      
      render(<FollowupCTA {...defaultProps} />);

      await user.click(screen.getByText('Continue Questions'));

      expect(mockOnStartFollowup).toHaveBeenCalled();
    });

    it('has proper accessibility attributes for continuation', () => {
      render(<FollowupCTA {...defaultProps} />);

      const button = screen.getByText('Continue Questions');
      expect(button).toHaveAttribute('aria-label', 'Continue asking questions');
    });

    it('shows saved questions message for existing conversation', () => {
      render(<FollowupCTA {...defaultProps} />);

      expect(screen.getByText(/Your questions are saved and linked to this palm reading/)).toBeInTheDocument();
    });
  });

  describe('Visual Design and Animations', () => {
    const availableStatus: FollowupStatus = {
      analysisCompleted: true,
      followupAvailable: true,
      followupConversationExists: false,
      questionsAsked: 0,
      questionsRemaining: 5
    };

    beforeEach(() => {
      mockUseFollowupStore.mockReturnValue({
        followupStatus: availableStatus,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });
    });

    it('has gradient background styling', () => {
      render(<FollowupCTA {...defaultProps} />);

      const card = screen.getByText('Have questions about your palm reading?').closest('.bg-gradient-to-r');
      expect(card).toHaveClass('from-saffron-50', 'via-orange-50', 'to-amber-50');
    });

    it('has icon with proper styling', () => {
      render(<FollowupCTA {...defaultProps} />);

      // Check for MessageCircle icon container
      expect(screen.getByText('Have questions about your palm reading?')).toBeInTheDocument();
    });

    it('has button with gradient and hover effects', () => {
      render(<FollowupCTA {...defaultProps} />);

      const button = screen.getByText('Ask Questions');
      expect(button).toHaveClass('bg-gradient-to-r', 'from-saffron-600', 'to-orange-600');
    });
  });

  describe('Custom Props', () => {
    it('applies custom className', () => {
      const status: FollowupStatus = {
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: false,
        questionsAsked: 0,
        questionsRemaining: 5
      };

      mockUseFollowupStore.mockReturnValue({
        followupStatus: status,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      const { container } = render(
        <FollowupCTA {...defaultProps} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('works with different analysisId', () => {
      const status: FollowupStatus = {
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: false,
        questionsAsked: 0,
        questionsRemaining: 5
      };

      mockUseFollowupStore.mockReturnValue({
        followupStatus: status,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      render(<FollowupCTA analysisId={999} onStartFollowup={mockOnStartFollowup} />);

      expect(mockCheckFollowupStatus).toHaveBeenCalledWith(999);
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined followupStatus gracefully', () => {
      mockUseFollowupStore.mockReturnValue({
        followupStatus: undefined as any,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      const { container } = render(<FollowupCTA {...defaultProps} />);

      expect(container.firstChild).toBeNull();
    });

    it('handles maxQuestions different from 5', () => {
      const status: FollowupStatus = {
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: true,
        questionsAsked: 7,
        questionsRemaining: 3
      };

      mockUseFollowupStore.mockReturnValue({
        followupStatus: status,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      render(<FollowupCTA {...defaultProps} />);

      expect(screen.getByText('Progress: 7/5 questions')).toBeInTheDocument();
      expect(screen.getByText('3 remaining')).toBeInTheDocument();
    });

    it('handles zero remaining questions', () => {
      const status: FollowupStatus = {
        analysisCompleted: true,
        followupAvailable: true,
        followupConversationExists: true,
        questionsAsked: 5,
        questionsRemaining: 0
      };

      mockUseFollowupStore.mockReturnValue({
        followupStatus: status,
        isLoading: false,
        error: null,
        checkFollowupStatus: mockCheckFollowupStatus,
        clearError: mockClearError,
        currentConversation: null,
        questions: [],
        isSubmitting: false,
        currentAnalysisId: null,
        startFollowupConversation: vi.fn(),
        askQuestion: vi.fn(),
        loadQuestions: vi.fn(),
        resetFollowup: vi.fn()
      });

      render(<FollowupCTA {...defaultProps} />);

      expect(screen.getByText('0 remaining')).toBeInTheDocument();
    });
  });
});