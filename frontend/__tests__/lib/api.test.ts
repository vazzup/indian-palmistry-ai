import { describe, it, expect, vi, beforeEach } from 'vitest';
import { handleApiError } from '@/lib/api';

describe('API utilities', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('handleApiError', () => {
    it('should extract message from response data', () => {
      const error = {
        response: {
          data: {
            message: 'Validation error'
          }
        }
      };
      
      const result = handleApiError(error);
      expect(result).toBe('Validation error');
    });

    it('should extract detail from response data', () => {
      const error = {
        response: {
          data: {
            detail: 'Not found'
          }
        }
      };
      
      const result = handleApiError(error);
      expect(result).toBe('Not found');
    });

    it('should handle array of error details', () => {
      const error = {
        response: {
          data: {
            detail: [
              { msg: 'Field is required' },
              { msg: 'Invalid format' }
            ]
          }
        }
      };
      
      const result = handleApiError(error);
      expect(result).toBe('Field is required, Invalid format');
    });

    it('should use error message as fallback', () => {
      const error = {
        message: 'Network error'
      };
      
      const result = handleApiError(error);
      expect(result).toBe('Network error');
    });

    it('should handle unknown errors', () => {
      const error = {};
      
      const result = handleApiError(error);
      expect(result).toBe('An unexpected error occurred');
    });

    it('should handle status-specific errors', () => {
      const error = {
        response: {
          status: 401,
          data: {}
        }
      };
      
      const result = handleApiError(error);
      expect(result).toBe('Authentication required');
    });

    it('should handle rate limiting', () => {
      const error = {
        response: {
          status: 429,
          data: {}
        }
      };
      
      const result = handleApiError(error);
      expect(result).toBe('Too many requests. Please wait and try again.');
    });

    it('should handle server errors', () => {
      const error = {
        response: {
          status: 500,
          data: {}
        }
      };
      
      const result = handleApiError(error);
      expect(result).toBe('Server error. Please try again later.');
    });
  });
});