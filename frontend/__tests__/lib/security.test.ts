/**
 * @jest-environment jsdom
 */
import {
  sanitizeInput,
  sanitizeObject,
  validateFileUpload,
  rateLimiter,
} from '@/lib/security';

describe('security utilities', () => {
  describe('sanitizeInput', () => {
    it('should remove script tags', () => {
      const maliciousInput = '<script>alert("xss")</script>Hello World';
      const result = sanitizeInput(maliciousInput);
      expect(result).toBe('Hello World');
    });

    it('should remove javascript: protocols', () => {
      const maliciousInput = 'javascript:alert("xss")';
      const result = sanitizeInput(maliciousInput);
      expect(result).toBe('alert("xss")');
    });

    it('should remove event handlers', () => {
      const maliciousInput = '<div onclick="alert(1)">Click me</div>';
      const result = sanitizeInput(maliciousInput);
      expect(result).toBe('<div>Click me</div>');
    });

    it('should handle mixed case script tags', () => {
      const maliciousInput = '<ScRiPt>alert("xss")</ScRiPt>Safe content';
      const result = sanitizeInput(maliciousInput);
      expect(result).toBe('Safe content');
    });

    it('should preserve safe content', () => {
      const safeInput = 'This is a safe string with <em>emphasis</em>';
      const result = sanitizeInput(safeInput);
      expect(result).toBe('This is a safe string with <em>emphasis</em>');
    });

    it('should trim whitespace', () => {
      const inputWithWhitespace = '   Hello World   ';
      const result = sanitizeInput(inputWithWhitespace);
      expect(result).toBe('Hello World');
    });

    it('should handle empty strings', () => {
      const emptyInput = '';
      const result = sanitizeInput(emptyInput);
      expect(result).toBe('');
    });

    it('should handle null and undefined', () => {
      expect(sanitizeInput(null as any)).toBe('');
      expect(sanitizeInput(undefined as any)).toBe('');
    });
  });

  describe('sanitizeObject', () => {
    it('should sanitize string values in object', () => {
      const input = {
        name: '<script>alert("xss")</script>John',
        email: 'john@example.com',
        bio: 'Hello <script>world</script>!',
      };

      const result = sanitizeObject(input);

      expect(result).toEqual({
        name: 'John',
        email: 'john@example.com',
        bio: 'Hello !',
      });
    });

    it('should preserve non-string values', () => {
      const input = {
        name: 'John',
        age: 30,
        isActive: true,
        tags: ['tag1', 'tag2'],
        metadata: { role: 'admin' },
      };

      const result = sanitizeObject(input);

      expect(result).toEqual({
        name: 'John',
        age: 30,
        isActive: true,
        tags: ['tag1', 'tag2'],
        metadata: { role: 'admin' },
      });
    });

    it('should handle nested objects', () => {
      const input = {
        user: {
          name: '<script>alert("xss")</script>John',
          profile: {
            bio: 'Hello <script>world</script>!',
          },
        },
        count: 5,
      };

      // Note: sanitizeObject only sanitizes top-level strings
      const result = sanitizeObject(input);

      expect(result).toEqual({
        user: {
          name: '<script>alert("xss")</script>John',
          profile: {
            bio: 'Hello <script>world</script>!',
          },
        },
        count: 5,
      });
    });

    it('should handle empty objects', () => {
      const input = {};
      const result = sanitizeObject(input);
      expect(result).toEqual({});
    });
  });

  describe('validateFileUpload', () => {
    const createMockFile = (name: string, type: string, size: number): File => {
      const file = new File([''], name, { type });
      Object.defineProperty(file, 'size', { value: size });
      return file;
    };

    it('should validate allowed file types', () => {
      const validFile = createMockFile('test.jpg', 'image/jpeg', 1000000);
      const result = validateFileUpload(validFile, ['image/jpeg', 'image/png']);
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject disallowed file types', () => {
      const invalidFile = createMockFile('test.txt', 'text/plain', 1000000);
      const result = validateFileUpload(invalidFile, ['image/jpeg', 'image/png']);
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('File type text/plain is not allowed');
    });

    it('should validate file size within limit', () => {
      const validFile = createMockFile('test.jpg', 'image/jpeg', 5000000); // 5MB
      const result = validateFileUpload(validFile, ['image/jpeg'], 10000000); // 10MB limit
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject files exceeding size limit', () => {
      const invalidFile = createMockFile('test.jpg', 'image/jpeg', 20000000); // 20MB
      const result = validateFileUpload(invalidFile, ['image/jpeg'], 10000000); // 10MB limit
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('File size exceeds maximum limit of 9.54 MB');
    });

    it('should use default size limit', () => {
      const invalidFile = createMockFile('test.jpg', 'image/jpeg', 20000000); // 20MB
      const result = validateFileUpload(invalidFile, ['image/jpeg']); // Default 15MB limit
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('File size exceeds maximum limit of 14.31 MB');
    });

    it('should validate filename for suspicious patterns', () => {
      const suspiciousFile = createMockFile('test.php.jpg', 'image/jpeg', 1000000);
      const result = validateFileUpload(suspiciousFile, ['image/jpeg']);
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Suspicious file name detected');
    });

    it('should accept normal filenames', () => {
      const normalFile = createMockFile('vacation-photo.jpg', 'image/jpeg', 1000000);
      const result = validateFileUpload(normalFile, ['image/jpeg']);
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should return multiple errors', () => {
      const invalidFile = createMockFile('malicious.php.jpg', 'text/plain', 20000000);
      const result = validateFileUpload(invalidFile, ['image/jpeg'], 10000000);
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toHaveLength(3);
      expect(result.errors).toContain('File type text/plain is not allowed');
      expect(result.errors).toContain('File size exceeds maximum limit of 9.54 MB');
      expect(result.errors).toContain('Suspicious file name detected');
    });
  });

  describe('rateLimiter', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.clear();
      jest.clearAllTimers();
    });

    afterEach(() => {
      localStorage.clear();
    });

    it('should allow requests under the limit', () => {
      expect(rateLimiter.isAllowed('test-key', 5)).toBe(true);
      expect(rateLimiter.isAllowed('test-key', 5)).toBe(true);
      expect(rateLimiter.isAllowed('test-key', 5)).toBe(true);
    });

    it('should track separate keys independently', () => {
      expect(rateLimiter.isAllowed('key1', 2)).toBe(true);
      expect(rateLimiter.isAllowed('key2', 2)).toBe(true);
      expect(rateLimiter.isAllowed('key1', 2)).toBe(true);
      expect(rateLimiter.isAllowed('key2', 2)).toBe(true);
      
      // Both keys should now be at limit
      expect(rateLimiter.isAllowed('key1', 2)).toBe(false);
      expect(rateLimiter.isAllowed('key2', 2)).toBe(false);
    });

    it('should block requests over the limit', () => {
      const key = 'test-limit';
      const maxAttempts = 3;

      // Make requests up to limit
      for (let i = 0; i < maxAttempts; i++) {
        expect(rateLimiter.isAllowed(key, maxAttempts)).toBe(true);
      }

      // Next request should be blocked
      expect(rateLimiter.isAllowed(key, maxAttempts)).toBe(false);
    });

    it('should reset after time window', () => {
      jest.useFakeTimers();
      
      const key = 'test-reset';
      const maxAttempts = 2;

      // Exhaust attempts
      expect(rateLimiter.isAllowed(key, maxAttempts)).toBe(true);
      expect(rateLimiter.isAllowed(key, maxAttempts)).toBe(true);
      expect(rateLimiter.isAllowed(key, maxAttempts)).toBe(false);

      // Fast forward past the time window (15 minutes)
      jest.advanceTimersByTime(16 * 60 * 1000);

      // Should be allowed again
      expect(rateLimiter.isAllowed(key, maxAttempts)).toBe(true);

      jest.useRealTimers();
    });

    it('should handle localStorage errors gracefully', () => {
      const originalSetItem = localStorage.setItem;
      const originalGetItem = localStorage.getItem;

      // Mock localStorage to throw errors
      localStorage.setItem = jest.fn(() => {
        throw new Error('Storage error');
      });
      localStorage.getItem = jest.fn(() => {
        throw new Error('Storage error');
      });

      // Should still work (fallback to allowing requests)
      expect(rateLimiter.isAllowed('test-key', 5)).toBe(true);

      // Restore localStorage
      localStorage.setItem = originalSetItem;
      localStorage.getItem = originalGetItem;
    });

    it('should get remaining attempts correctly', () => {
      const key = 'test-remaining';
      const maxAttempts = 5;

      expect(rateLimiter.getRemainingAttempts(key, maxAttempts)).toBe(5);

      rateLimiter.isAllowed(key, maxAttempts); // 1st attempt
      expect(rateLimiter.getRemainingAttempts(key, maxAttempts)).toBe(4);

      rateLimiter.isAllowed(key, maxAttempts); // 2nd attempt
      expect(rateLimiter.getRemainingAttempts(key, maxAttempts)).toBe(3);
    });

    it('should get time until reset correctly', () => {
      jest.useFakeTimers();
      const startTime = Date.now();
      
      const key = 'test-reset-time';
      rateLimiter.isAllowed(key, 1);

      // Fast forward 5 minutes
      jest.advanceTimersByTime(5 * 60 * 1000);

      const timeUntilReset = rateLimiter.getTimeUntilReset(key);
      expect(timeUntilReset).toBe(10 * 60 * 1000); // 10 minutes remaining

      jest.useRealTimers();
    });
  });
});