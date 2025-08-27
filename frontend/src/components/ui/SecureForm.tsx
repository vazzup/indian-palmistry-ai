'use client';

import React from 'react';
import { useCSRF } from '@/hooks/useCSRF';
import { sanitizeObject, rateLimiter } from '@/lib/security';

interface SecureFormProps extends Omit<React.FormHTMLAttributes<HTMLFormElement>, 'onSubmit'> {
  onSubmit: (data: FormData, sanitizedData: Record<string, any>) => void | Promise<void>;
  rateLimitKey?: string;
  maxAttempts?: number;
  children: React.ReactNode;
  sanitizeInputs?: boolean;
}

export const SecureForm: React.FC<SecureFormProps> = ({
  onSubmit,
  rateLimitKey,
  maxAttempts = 5,
  children,
  sanitizeInputs = true,
  ...formProps
}) => {
  const { csrfToken } = useCSRF();
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    // Rate limiting check
    if (rateLimitKey && !rateLimiter.isAllowed(rateLimitKey, maxAttempts)) {
      setError('Too many attempts. Please wait before trying again.');
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData(event.currentTarget);
      
      // Convert FormData to regular object for sanitization
      const data: Record<string, any> = {};
      formData.forEach((value, key) => {
        data[key] = value;
      });

      // Sanitize inputs if enabled
      const sanitizedData = sanitizeInputs ? sanitizeObject(data) : data;

      // Add CSRF token if available
      if (csrfToken) {
        formData.append('csrf_token', csrfToken);
        sanitizedData.csrf_token = csrfToken;
      }

      await onSubmit(formData, sanitizedData);
    } catch (error: any) {
      setError(error.message || 'An error occurred while submitting the form');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form {...formProps} onSubmit={handleSubmit}>
      {/* CSRF Token Hidden Field */}
      {csrfToken && (
        <input type="hidden" name="csrf_token" value={csrfToken} />
      )}
      
      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Form Content */}
      <fieldset disabled={isSubmitting}>
        {children}
      </fieldset>
    </form>
  );
};