import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { SecureForm } from '@/components/ui/SecureForm';
import { useCSRF } from '@/hooks/useCSRF';
import { sanitizeObject, rateLimiter } from '@/lib/security';

// Mock dependencies
vi.mock('@/hooks/useCSRF');
vi.mock('@/lib/security', () => ({
  sanitizeObject: vi.fn(),
  rateLimiter: {
    isAllowed: vi.fn(),
  },
}));

const mockUseCSRF = vi.mocked(useCSRF);
const mockSanitizeObject = vi.mocked(sanitizeObject);
const mockRateLimiter = vi.mocked(rateLimiter);

describe('SecureForm', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    mockUseCSRF.mockReturnValue({
      csrfToken: 'test-csrf-token',
      isLoading: false,
      refreshCSRFToken: vi.fn(),
    });

    mockSanitizeObject.mockImplementation((obj: any) => obj);
    mockRateLimiter.isAllowed.mockReturnValue(true);
  });

  it('should render form with children', () => {
    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <input name="test" placeholder="Test input" />
        <button type="submit">Submit</button>
      </SecureForm>
    );

    expect(screen.getByPlaceholderText('Test input')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
  });

  it('should include CSRF token as hidden field', () => {
    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const hiddenInput = screen.getByDisplayValue('test-csrf-token');
    expect(hiddenInput).toBeInTheDocument();
    expect(hiddenInput).toHaveAttribute('type', 'hidden');
    expect(hiddenInput).toHaveAttribute('name', 'csrf_token');
  });

  it('should not include CSRF token field when token is null', () => {
    mockUseCSRF.mockReturnValue({
      csrfToken: null,
      isLoading: false,
      refreshCSRFToken: vi.fn(),
    });

    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <button type="submit">Submit</button>
      </SecureForm>
    );

    expect(screen.queryByDisplayValue('test-csrf-token')).not.toBeInTheDocument();
  });

  it('should call onSubmit with form data and sanitized data', async () => {
    const user = userEvent.setup();

    mockSanitizeObject.mockReturnValue({
      test: 'sanitized-value',
      csrf_token: 'test-csrf-token',
    });

    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <input name="test" />
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const input = screen.getByRole('textbox');
    const submitButton = screen.getByRole('button', { name: 'Submit' });

    await user.type(input, 'test-value');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    const [formData, sanitizedData] = mockOnSubmit.mock.calls[0];
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get('test')).toBe('test-value');
    expect(formData.get('csrf_token')).toBe('test-csrf-token');
    expect(sanitizedData).toEqual({
      test: 'sanitized-value',
      csrf_token: 'test-csrf-token',
    });
  });

  it('should sanitize inputs by default', async () => {
    const user = userEvent.setup();

    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <input name="test" />
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const input = screen.getByRole('textbox');
    const submitButton = screen.getByRole('button', { name: 'Submit' });

    await user.type(input, 'test-value');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockSanitizeObject).toHaveBeenCalledWith({
        test: 'test-value',
      });
    });
  });

  it('should skip sanitization when disabled', async () => {
    const user = userEvent.setup();

    render(
      <SecureForm onSubmit={mockOnSubmit} sanitizeInputs={false}>
        <input name="test" />
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const input = screen.getByRole('textbox');
    const submitButton = screen.getByRole('button', { name: 'Submit' });

    await user.type(input, 'test-value');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    expect(mockSanitizeObject).not.toHaveBeenCalled();

    const [, sanitizedData] = mockOnSubmit.mock.calls[0];
    expect(sanitizedData).toEqual({
      test: 'test-value',
      csrf_token: 'test-csrf-token',
    });
  });

  it('should enforce rate limiting', async () => {
    const user = userEvent.setup();
    mockRateLimiter.isAllowed.mockReturnValue(false);

    render(
      <SecureForm onSubmit={mockOnSubmit} rateLimitKey="test-form" maxAttempts={3}>
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const submitButton = screen.getByRole('button', { name: 'Submit' });
    await user.click(submitButton);

    expect(screen.getByText('Too many attempts. Please wait before trying again.')).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
    expect(mockRateLimiter.isAllowed).toHaveBeenCalledWith('test-form', 3);
  });

  it('should disable form during submission', async () => {
    const user = userEvent.setup();
    let resolveSubmit: () => void;
    const submitPromise = new Promise<void>((resolve) => {
      resolveSubmit = resolve;
    });

    mockOnSubmit.mockReturnValue(submitPromise);

    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <input name="test" />
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const input = screen.getByRole('textbox');
    const submitButton = screen.getByRole('button', { name: 'Submit' });

    await user.click(submitButton);

    // Form should be disabled during submission
    expect(input).toBeDisabled();
    expect(submitButton).toBeDisabled();

    // Resolve the submission
    resolveSubmit!();

    await waitFor(() => {
      expect(input).not.toBeDisabled();
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('should display error messages', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockRejectedValue(new Error('Submission failed'));

    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const submitButton = screen.getByRole('button', { name: 'Submit' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Submission failed')).toBeInTheDocument();
    });

    // Error should have proper styling
    const errorElement = screen.getByText('Submission failed');
    expect(errorElement).toHaveClass('text-sm', 'text-red-600');
  });

  it('should clear error on new submission', async () => {
    const user = userEvent.setup();
    mockOnSubmit
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce(undefined);

    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const submitButton = screen.getByRole('button', { name: 'Submit' });

    // First submission fails
    await user.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText('First error')).toBeInTheDocument();
    });

    // Second submission succeeds and clears error
    await user.click(submitButton);
    await waitFor(() => {
      expect(screen.queryByText('First error')).not.toBeInTheDocument();
    });
  });

  it('should pass through form props', () => {
    render(
      <SecureForm 
        onSubmit={mockOnSubmit} 
        className="custom-form" 
        id="test-form"
        data-testid="secure-form"
      >
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const form = screen.getByTestId('secure-form');
    expect(form).toHaveClass('custom-form');
    expect(form).toHaveAttribute('id', 'test-form');
  });

  it('should handle generic error message for errors without message', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockRejectedValue(new Error(''));

    render(
      <SecureForm onSubmit={mockOnSubmit}>
        <button type="submit">Submit</button>
      </SecureForm>
    );

    const submitButton = screen.getByRole('button', { name: 'Submit' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('An error occurred while submitting the form')).toBeInTheDocument();
    });
  });
});