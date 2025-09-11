'use client';

import React from 'react';
import Link from 'next/link';

interface LegalNoticeProps {
  variant?: 'upload' | 'footer' | 'card' | 'placeholder';
  className?: string;
}

/**
 * LegalNotice component for displaying legal disclaimers elegantly across the app.
 * 
 * Variants:
 * - upload: Subtle text under upload buttons
 * - footer: Global footer disclaimer for all pages
 * - card: Small footer text for result cards
 * - placeholder: Contextual hint text for inputs
 */
export const LegalNotice: React.FC<LegalNoticeProps> = ({ 
  variant = 'footer', 
  className = '' 
}) => {
  
  if (variant === 'upload') {
    return (
      <p className={`text-xs text-gray-500 text-center ${className}`}>
        By uploading, you agree to our{' '}
        <Link 
          href="/terms" 
          className="text-saffron-600 hover:text-saffron-700 underline"
        >
          Terms
        </Link>
        {' and understand this is '}
        <Link 
          href="/disclaimer" 
          className="text-saffron-600 hover:text-saffron-700 underline"
        >
          entertainment only
        </Link>
      </p>
    );
  }

  if (variant === 'card') {
    return (
      <p className={`text-xs text-gray-400 text-center border-t border-gray-100 pt-2 mt-4 ${className}`}>
        Entertainment only • Not professional advice •{' '}
        <Link 
          href="/disclaimer" 
          className="text-saffron-500 hover:text-saffron-600 underline"
        >
          Learn more
        </Link>
      </p>
    );
  }

  if (variant === 'placeholder') {
    return null; // This will be handled as placeholder text in inputs
  }

  // Default 'footer' variant - Global footer for all pages
  return (
    <div className={`text-center text-xs text-gray-500 ${className}`}>
      <p>
        Entertainment only •{' '}
        <Link 
          href="/terms" 
          className="text-saffron-600 hover:text-saffron-700 underline"
        >
          Terms
        </Link>
        {' • '}
        <Link 
          href="/privacy" 
          className="text-saffron-600 hover:text-saffron-700 underline"
        >
          Privacy
        </Link>
        {' • '}
        <Link 
          href="/disclaimer" 
          className="text-saffron-600 hover:text-saffron-700 underline"
        >
          Disclaimer
        </Link>
      </p>
    </div>
  );
};