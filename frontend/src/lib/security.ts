/**
 * Security utilities for input sanitization and validation
 */

// Common XSS attack patterns
const XSS_PATTERNS = [
  /<script[\s\S]*?>[\s\S]*?<\/script>/gi,
  /<iframe[\s\S]*?>[\s\S]*?<\/iframe>/gi,
  /<object[\s\S]*?>[\s\S]*?<\/object>/gi,
  /<embed[\s\S]*?>/gi,
  /<applet[\s\S]*?>[\s\S]*?<\/applet>/gi,
  /<meta[\s\S]*?>/gi,
  /<link[\s\S]*?>/gi,
  /javascript:/gi,
  /vbscript:/gi,
  /data:text\/html/gi,
  /on\w+\s*=/gi, // Event handlers like onclick, onload, etc.
];

// Dangerous HTML attributes
const DANGEROUS_ATTRIBUTES = [
  'onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout',
  'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset',
  'onselect', 'onunload', 'ondblclick', 'onkeydown', 'onkeyup',
  'onkeypress', 'onmousedown', 'onmouseup', 'onmousemove'
];

/**
 * Sanitize user input to prevent XSS attacks
 */
export const sanitizeInput = (input: string): string => {
  if (typeof input !== 'string') {
    return '';
  }

  let sanitized = input;

  // Remove script tags and other dangerous elements
  XSS_PATTERNS.forEach(pattern => {
    sanitized = sanitized.replace(pattern, '');
  });

  // Remove dangerous attributes
  DANGEROUS_ATTRIBUTES.forEach(attr => {
    const attrPattern = new RegExp(`${attr}\\s*=\\s*["'][^"']*["']`, 'gi');
    sanitized = sanitized.replace(attrPattern, '');
  });

  // Encode HTML entities
  sanitized = sanitized
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');

  return sanitized.trim();
};

/**
 * Sanitize an object with string values
 */
export const sanitizeObject = <T extends Record<string, any>>(obj: T): T => {
  const sanitized = { ...obj } as Record<string, any>;

  Object.keys(sanitized).forEach(key => {
    if (typeof sanitized[key] === 'string') {
      sanitized[key] = sanitizeInput(sanitized[key]);
    } else if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
      sanitized[key] = sanitizeObject(sanitized[key]);
    }
  });

  return sanitized as T;
};

/**
 * Validate email format
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
  return emailRegex.test(email);
};

/**
 * Validate password strength
 */
export const validatePasswordStrength = (password: string): {
  isValid: boolean;
  score: number;
  feedback: string[];
} => {
  const feedback: string[] = [];
  let score = 0;

  if (password.length < 8) {
    feedback.push('Password must be at least 8 characters long');
  } else {
    score += 1;
  }

  if (!/[a-z]/.test(password)) {
    feedback.push('Password must contain at least one lowercase letter');
  } else {
    score += 1;
  }

  if (!/[A-Z]/.test(password)) {
    feedback.push('Password must contain at least one uppercase letter');
  } else {
    score += 1;
  }

  if (!/\d/.test(password)) {
    feedback.push('Password must contain at least one number');
  } else {
    score += 1;
  }

  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    feedback.push('Password must contain at least one special character');
  } else {
    score += 1;
  }

  // Check for common weak patterns
  const commonPatterns = [
    /(.)\1{2,}/, // Repeated characters
    /123456|654321|qwerty|password|admin/i, // Common weak passwords
  ];

  commonPatterns.forEach(pattern => {
    if (pattern.test(password)) {
      feedback.push('Password contains common weak patterns');
      score = Math.max(0, score - 1);
    }
  });

  return {
    isValid: score >= 4 && feedback.length === 0,
    score,
    feedback,
  };
};

/**
 * Validate file upload security
 */
export const validateFileUpload = (file: File): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];

  // Check file size (15MB limit)
  const maxSize = 15 * 1024 * 1024; // 15MB
  if (file.size > maxSize) {
    errors.push('File size must be less than 15MB');
  }

  // Check file type
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  if (!allowedTypes.includes(file.type)) {
    errors.push('Only JPEG and PNG files are allowed');
  }

  // Check file extension
  const allowedExtensions = ['.jpg', '.jpeg', '.png'];
  const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
  if (!allowedExtensions.includes(fileExtension)) {
    errors.push('Invalid file extension');
  }

  // Check filename for suspicious content
  const suspiciousPatterns = [
    /<script/i,
    /javascript:/i,
    /\.php$/i,
    /\.exe$/i,
    /\.bat$/i,
    /\.sh$/i,
  ];

  suspiciousPatterns.forEach(pattern => {
    if (pattern.test(file.name)) {
      errors.push('Filename contains suspicious content');
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Generate a secure random string
 */
export const generateSecureRandomString = (length = 32): string => {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  
  if (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues) {
    const randomValues = new Uint8Array(length);
    window.crypto.getRandomValues(randomValues);
    
    for (let i = 0; i < length; i++) {
      result += charset[randomValues[i] % charset.length];
    }
  } else {
    // Fallback for environments without crypto API
    for (let i = 0; i < length; i++) {
      result += charset[Math.floor(Math.random() * charset.length)];
    }
  }
  
  return result;
};

/**
 * Rate limiting for client-side operations
 */
class ClientRateLimiter {
  private attempts: Map<string, number[]> = new Map();

  isAllowed(key: string, maxAttempts = 5, windowMs = 60000): boolean {
    const now = Date.now();
    const attempts = this.attempts.get(key) || [];
    
    // Remove old attempts outside the window
    const validAttempts = attempts.filter(timestamp => now - timestamp < windowMs);
    
    if (validAttempts.length >= maxAttempts) {
      return false;
    }
    
    validAttempts.push(now);
    this.attempts.set(key, validAttempts);
    
    return true;
  }

  reset(key: string): void {
    this.attempts.delete(key);
  }
}

export const rateLimiter = new ClientRateLimiter();

/**
 * Content Security Policy violation reporter
 */
export const setupCSPReporting = (): void => {
  if (typeof window !== 'undefined') {
    document.addEventListener('securitypolicyviolation', (event) => {
      console.warn('CSP Violation:', {
        directive: event.violatedDirective,
        blockedURI: event.blockedURI,
        lineNumber: event.lineNumber,
        originalPolicy: event.originalPolicy,
      });

      // In production, send to monitoring service
      if (process.env.NODE_ENV === 'production') {
        // Send to your monitoring service
        fetch('/api/csp-violation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            directive: event.violatedDirective,
            blockedURI: event.blockedURI,
            lineNumber: event.lineNumber,
            timestamp: new Date().toISOString(),
          }),
        }).catch(() => {
          // Ignore errors in violation reporting
        });
      }
    });
  }
};

/**
 * Session timeout management
 */
export class SessionManager {
  private timeoutId: NodeJS.Timeout | null = null;
  private warningTimeoutId: NodeJS.Timeout | null = null;

  startSession(timeoutMs = 3600000, warningMs = 300000): void { // 1 hour timeout, 5 min warning
    this.clearTimeouts();

    // Set warning timeout
    this.warningTimeoutId = setTimeout(() => {
      this.showSessionWarning();
    }, timeoutMs - warningMs);

    // Set session timeout
    this.timeoutId = setTimeout(() => {
      this.handleSessionTimeout();
    }, timeoutMs);
  }

  extendSession(timeoutMs = 3600000, warningMs = 300000): void {
    this.startSession(timeoutMs, warningMs);
  }

  clearTimeouts(): void {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    if (this.warningTimeoutId) {
      clearTimeout(this.warningTimeoutId);
      this.warningTimeoutId = null;
    }
  }

  private showSessionWarning(): void {
    // Implement session warning UI
    console.warn('Session will expire soon');
    
    // You could dispatch a custom event here for UI components to listen to
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('sessionWarning'));
    }
  }

  private handleSessionTimeout(): void {
    // Clear auth state and redirect
    localStorage.removeItem('auth-store');
    window.location.href = '/login?reason=timeout';
  }
}

export const sessionManager = new SessionManager();