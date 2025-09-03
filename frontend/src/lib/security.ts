/**
 * @fileoverview Security utilities for the Indian Palmistry AI frontend
 * Provides CSP reporting, session management, and security event handling
 */

'use client';

/**
 * Set up Content Security Policy violation reporting
 * Monitors for CSP violations and reports them for security analysis
 */
export function setupCSPReporting(): void {
  if (typeof window !== 'undefined') {
    // Listen for CSP violations
    document.addEventListener('securitypolicyviolation', (event) => {
      console.warn('CSP Violation:', {
        directive: event.violatedDirective,
        blockedURI: event.blockedURI,
        sourceFile: event.sourceFile,
        lineNumber: event.lineNumber,
        columnNumber: event.columnNumber,
        sample: event.sample
      });

      // In production, you might want to send this to your security monitoring service
      if (process.env.NODE_ENV === 'production') {
        // Example: sendSecurityEvent('csp_violation', event);
      }
    });
  }
}

/**
 * Session management utilities
 * Handles session timeouts, warnings, and automatic logout
 */
export const sessionManager = {
  // Session timeout in milliseconds (30 minutes default)
  sessionTimeout: 30 * 60 * 1000,
  
  // Warning time before session expires (5 minutes default)
  warningTime: 5 * 60 * 1000,
  
  // Timer references
  warningTimer: null as NodeJS.Timeout | null,
  logoutTimer: null as NodeJS.Timeout | null,

  /**
   * Start session management
   * Sets up timers for session warning and automatic logout
   */
  startSession(): void {
    this.clearTimeouts();
    
    const warningTimeout = this.sessionTimeout - this.warningTime;
    
    // Set warning timer
    this.warningTimer = setTimeout(() => {
      this.dispatchSessionWarning();
    }, warningTimeout);
    
    // Set logout timer
    this.logoutTimer = setTimeout(() => {
      this.handleSessionExpired();
    }, this.sessionTimeout);
  },

  /**
   * Extend the current session
   * Resets the session timers based on user activity
   */
  extendSession(): void {
    if (this.warningTimer || this.logoutTimer) {
      this.startSession();
    }
  },

  /**
   * Clear all session timers
   * Used when user logs out or component unmounts
   */
  clearTimeouts(): void {
    if (this.warningTimer) {
      clearTimeout(this.warningTimer);
      this.warningTimer = null;
    }
    
    if (this.logoutTimer) {
      clearTimeout(this.logoutTimer);
      this.logoutTimer = null;
    }
  },

  /**
   * Dispatch session warning event
   * Notifies the application that session will expire soon
   */
  dispatchSessionWarning(): void {
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('sessionWarning', {
        detail: {
          timeRemaining: this.warningTime,
          expiresAt: Date.now() + this.warningTime
        }
      });
      
      window.dispatchEvent(event);
    }
  },

  /**
   * Handle session expiration
   * Automatically logs out the user when session expires
   */
  handleSessionExpired(): void {
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('sessionExpired', {
        detail: {
          expiredAt: Date.now(),
          reason: 'timeout'
        }
      });
      
      window.dispatchEvent(event);
      
      // Clear local storage and redirect to login
      // In a real implementation, you'd call your auth logout function
      console.warn('Session expired - user should be logged out');
    }
  }
};

/**
 * Input sanitization utilities
 * Helps prevent XSS attacks by cleaning user input
 */
export const sanitization = {
  /**
   * Remove potentially dangerous HTML tags and attributes
   * @param input - Raw HTML string to sanitize
   * @returns Sanitized HTML string
   */
  sanitizeHTML(input: string): string {
    if (typeof window === 'undefined') {
      // Server-side: basic sanitization
      return input
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/javascript:/gi, '')
        .replace(/on\w+\s*=/gi, '');
    }

    // Client-side: create temporary element for sanitization
    const temp = document.createElement('div');
    temp.textContent = input;
    return temp.innerHTML;
  },

  /**
   * Sanitize user input for safe display
   * @param input - User input string
   * @returns Sanitized string safe for display
   */
  sanitizeInput(input: string): string {
    return input
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  },

  /**
   * Validate and sanitize URL
   * @param url - URL string to validate
   * @returns Sanitized URL or null if invalid
   */
  sanitizeURL(url: string): string | null {
    try {
      const urlObj = new URL(url);
      
      // Only allow http and https protocols
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return null;
      }
      
      return urlObj.toString();
    } catch {
      return null;
    }
  }
};

/**
 * Rate limiting utilities for client-side protection
 * Helps prevent abuse of API endpoints
 */
export const rateLimiting = {
  // Storage for request counts
  requestCounts: new Map<string, { count: number; resetTime: number }>(),

  /**
   * Check if request is allowed based on rate limit
   * @param key - Unique identifier for the request type
   * @param limit - Maximum requests allowed
   * @param windowMs - Time window in milliseconds
   * @returns true if request is allowed, false if rate limited
   */
  isAllowed(key: string, limit: number, windowMs: number): boolean {
    const now = Date.now();
    const entry = this.requestCounts.get(key);

    // If no entry or window has expired, reset
    if (!entry || now > entry.resetTime) {
      this.requestCounts.set(key, {
        count: 1,
        resetTime: now + windowMs
      });
      return true;
    }

    // Check if under limit
    if (entry.count < limit) {
      entry.count++;
      return true;
    }

    // Rate limited
    return false;
  },

  /**
   * Clear rate limiting data for a specific key
   * @param key - Key to clear
   */
  clear(key: string): void {
    this.requestCounts.delete(key);
  },

  /**
   * Clear all rate limiting data
   */
  clearAll(): void {
    this.requestCounts.clear();
  }
};

/**
 * Security event reporting utilities
 * For monitoring and logging security events
 */
export const securityReporting = {
  /**
   * Report a security event
   * @param eventType - Type of security event
   * @param details - Event details
   */
  reportEvent(eventType: string, details: any): void {
    const event = {
      type: eventType,
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown',
      details
    };

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.warn('Security Event:', event);
    }

    // In production, send to monitoring service
    if (process.env.NODE_ENV === 'production') {
      // Example: fetch('/api/security/events', { method: 'POST', body: JSON.stringify(event) });
    }
  }
};

/**
 * Object sanitization utility
 * Sanitizes all string values in an object
 */
export function sanitizeObject(obj: Record<string, any>): Record<string, any> {
  const sanitized: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string') {
      sanitized[key] = sanitization.sanitizeInput(value);
    } else if (Array.isArray(value)) {
      sanitized[key] = value.map(item => 
        typeof item === 'string' ? sanitization.sanitizeInput(item) : item
      );
    } else if (value && typeof value === 'object') {
      sanitized[key] = sanitizeObject(value);
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
}

/**
 * Rate limiter instance for forms
 * Provides a convenient interface for rate limiting
 */
export const rateLimiter = {
  /**
   * Check if a request is allowed
   */
  isAllowed: (key: string, limit: number = 5, windowMs: number = 60000) => {
    return rateLimiting.isAllowed(key, limit, windowMs);
  },
  
  /**
   * Clear rate limiting for a key
   */
  clear: (key: string) => {
    rateLimiting.clear(key);
  },
  
  /**
   * Clear all rate limiting data
   */
  clearAll: () => {
    rateLimiting.clearAll();
  }
};

const security = {
  setupCSPReporting,
  sessionManager,
  sanitization,
  rateLimiting,
  securityReporting,
  sanitizeObject,
  rateLimiter
};

export default security;