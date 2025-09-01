/**
 * @fileoverview Unit tests for QuestionInput Component
 * 
 * Comprehensive test suite covering validation, user interactions,
 * suggestions, error handling, and accessibility features.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuestionInput } from '@/components/analysis/FollowupQuestions/QuestionInput';

describe('QuestionInput', () => {
  const mockOnSubmit = vi.fn();
  
  const defaultProps = {
    onSubmit: mockOnSubmit,
    isSubmitting: false,
    remainingQuestions: 3
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering and Initial State', () => {
    it('renders correctly with default props', () => {
      render(<QuestionInput {...defaultProps} />);

      expect(screen.getByLabelText(/Ask your question \(3 remaining\)/)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/What would you like to know/)).toBeInTheDocument();
      expect(screen.getByText('0/500 characters')).toBeInTheDocument();
      expect(screen.getByText('Min: 10 characters')).toBeInTheDocument();
      expect(screen.getByText('Ask Question')).toBeInTheDocument();
      expect(screen.getByText('Show Examples')).toBeInTheDocument();
    });

    it('shows custom placeholder when provided', () => {
      render(
        <QuestionInput 
          {...defaultProps} 
          placeholder="Custom placeholder text"
        />
      );

      expect(screen.getByPlaceholderText('Custom placeholder text')).toBeInTheDocument();
    });

    it('shows tips by default', () => {
      render(<QuestionInput {...defaultProps} />);

      expect(screen.getByText('💡 Pro Tips:')).toBeInTheDocument();
    });

    it('can hide tips when showTips is false', () => {
      render(<QuestionInput {...defaultProps} showTips={false} />);

      expect(screen.queryByText('💡 Pro Tips:')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading component when submitting', () => {
      render(<QuestionInput {...defaultProps} isSubmitting={true} />);

      expect(screen.getByText(/Our AI is analyzing your question/)).toBeInTheDocument();
      expect(screen.queryByText('Ask Question')).not.toBeInTheDocument();
    });
  });

  describe('Question Suggestions', () => {
    it('shows examples when Show Examples is clicked', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      await user.click(screen.getByText('Show Examples'));

      expect(screen.getByText('Example Questions:')).toBeInTheDocument();
      expect(screen.getByText('Hide Examples')).toBeInTheDocument();
      
      // Should show at least 4 example questions
      const suggestions = screen.getAllByText(/What does/);
      expect(suggestions.length).toBeGreaterThanOrEqual(4);
    });

    it('hides examples when Hide Examples is clicked', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      // First show examples
      await user.click(screen.getByText('Show Examples'));
      expect(screen.getByText('Example Questions:')).toBeInTheDocument();

      // Then hide them
      await user.click(screen.getByText('Hide Examples'));
      expect(screen.queryByText('Example Questions:')).not.toBeInTheDocument();
      expect(screen.getByText('Show Examples')).toBeInTheDocument();
    });

    it('populates textarea when suggestion is clicked', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      await user.click(screen.getByText('Show Examples'));
      
      // Click on a suggestion
      const suggestion = screen.getByText(/What does my heart line mean for my love life?/);
      await user.click(suggestion);

      const textarea = screen.getByDisplayValue('What does my heart line mean for my love life?');
      expect(textarea).toBeInTheDocument();
      expect(screen.queryByText('Example Questions:')).not.toBeInTheDocument();
    });
  });

  describe('Input Validation', () => {
    it('shows character count as user types', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      await user.type(textarea, 'Hello');

      expect(screen.getByText('5/500 characters')).toBeInTheDocument();
    });

    it('shows ready to submit indicator for valid questions', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      await user.type(textarea, 'What does my palm reading mean?');

      await waitFor(() => {
        expect(screen.getByText('✓ Ready to submit')).toBeInTheDocument();
      });
    });

    it('shows validation error for too short questions', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'short');
      await user.click(submitButton);

      expect(screen.getByText('Question must be at least 10 characters long')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows validation error for too long questions', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      const longText = 'a'.repeat(501);
      await user.type(textarea, longText);
      await user.click(submitButton);

      expect(screen.getByText('Question must be less than 500 characters')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows validation error for non-palmistry questions', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'What is the weather like today?');
      await user.click(submitButton);

      expect(screen.getByText('Please ask questions related to palm reading or palmistry features visible in your images')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('accepts valid palmistry questions', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'What does my heart line mean for relationships?');
      await user.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalledWith('What does my heart line mean for relationships?');
    });

    it('clears validation error when user starts typing', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      // First, trigger a validation error
      await user.type(textarea, 'short');
      await user.click(submitButton);
      
      expect(screen.getByText('Question must be at least 10 characters long')).toBeInTheDocument();

      // Then start typing to clear the error
      await user.type(textarea, ' question about palm');
      
      await waitFor(() => {
        expect(screen.queryByText('Question must be at least 10 characters long')).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('calls onSubmit with trimmed question text', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, '  What does my heart line indicate?  ');
      await user.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalledWith('What does my heart line indicate?');
    });

    it('clears textarea after successful submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/) as HTMLTextAreaElement;
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'What does my palm reading mean?');
      await user.click(submitButton);

      await waitFor(() => {
        expect(textarea.value).toBe('');
      });
    });

    it('shows error when onSubmit throws', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Submission failed';
      mockOnSubmit.mockRejectedValue(new Error(errorMessage));
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'What does my heart line mean?');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it('prevents submission when no questions remaining', () => {
      render(<QuestionInput {...defaultProps} remainingQuestions={0} />);

      const submitButton = screen.getByText('Ask Question');
      expect(submitButton).toBeDisabled();
    });

    it('can be submitted with Enter key (form submission)', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);

      await user.type(textarea, 'What does my heart line indicate?');
      await user.type(textarea, '{enter}');

      // Note: This might need adjustment based on how the form handles Enter
      // The current implementation doesn't prevent default, so Enter should submit
      expect(mockOnSubmit).toHaveBeenCalledWith('What does my heart line indicate?');
    });
  });

  describe('Button States', () => {
    it('disables button for invalid questions', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'short');

      expect(submitButton).toBeDisabled();
    });

    it('enables button for valid questions', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'What does my heart line mean?');

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });

    it('disables button when submitting', () => {
      render(<QuestionInput {...defaultProps} isSubmitting={true} />);

      // When submitting, the loading component is shown instead of the form
      expect(screen.queryByText('Ask Question')).not.toBeInTheDocument();
    });
  });

  describe('Warning Messages', () => {
    it('shows warning when one question remaining', () => {
      render(<QuestionInput {...defaultProps} remainingQuestions={1} />);

      expect(screen.getByText(/This is your last question. Make it count!/)).toBeInTheDocument();
    });

    it('shows warning when two questions remaining', () => {
      render(<QuestionInput {...defaultProps} remainingQuestions={2} />);

      expect(screen.getByText(/This is your second-to-last question. Make it count!/)).toBeInTheDocument();
    });

    it('does not show warning when more than 2 questions remaining', () => {
      render(<QuestionInput {...defaultProps} remainingQuestions={3} />);

      expect(screen.queryByText(/Make it count!/)).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and relationships', () => {
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      expect(textarea).toHaveAttribute('aria-describedby');
      
      const describedBy = textarea.getAttribute('aria-describedby');
      expect(describedBy).toContain('character-count');
      expect(describedBy).toContain('question-help');
    });

    it('has proper role for validation errors', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'short');
      await user.click(submitButton);

      const errorElement = screen.getByText('Question must be at least 10 characters long');
      expect(errorElement.closest('[role="alert"]')).toBeInTheDocument();
    });

    it('has live region for validation feedback', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const submitButton = screen.getByText('Ask Question');

      await user.type(textarea, 'short');
      await user.click(submitButton);

      const liveRegion = screen.getByText('Question must be at least 10 characters long').closest('[aria-live="polite"]');
      expect(liveRegion).toBeInTheDocument();
    });
  });

  describe('Character Limit Enforcement', () => {
    it('enforces maxLength on textarea', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/) as HTMLTextAreaElement;
      expect(textarea.maxLength).toBe(500);
    });

    it('shows red character count at limit', async () => {
      const user = userEvent.setup();
      
      render(<QuestionInput {...defaultProps} />);

      const textarea = screen.getByLabelText(/Ask your question/);
      const longText = 'a'.repeat(500);
      
      await user.type(textarea, longText);

      const charCount = screen.getByText('500/500 characters');
      expect(charCount).toHaveClass('text-red-600');
    });
  });

  describe('Custom Props', () => {
    it('applies custom className', () => {
      const { container } = render(
        <QuestionInput {...defaultProps} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('updates remaining questions display', () => {
      render(<QuestionInput {...defaultProps} remainingQuestions={1} />);

      expect(screen.getByLabelText(/Ask your question \(1 remaining\)/)).toBeInTheDocument();
    });
  });
});