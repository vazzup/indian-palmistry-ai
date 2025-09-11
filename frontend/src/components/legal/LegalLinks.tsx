'use client';

import React from 'react';
import Link from 'next/link';

interface LegalLinksProps {
  variant?: 'footer' | 'inline' | 'vertical';
  className?: string;
  showDividers?: boolean;
}

/**
 * LegalLinks component for displaying legal document links consistently.
 * 
 * Variants:
 * - footer: Horizontal layout with dividers for footer usage
 * - inline: Compact inline layout for forms and small spaces
 * - vertical: Vertical stack for sidebars or mobile layouts
 */
export const LegalLinks: React.FC<LegalLinksProps> = ({ 
  variant = 'footer', 
  className = '',
  showDividers = true 
}) => {
  const links = [
    { href: '/terms', label: 'Terms of Service' },
    { href: '/privacy', label: 'Privacy Policy' },
    { href: '/disclaimer', label: 'Disclaimer' }
  ];

  const linkClassName = "text-saffron-600 hover:text-saffron-700 underline transition-colors";

  if (variant === 'vertical') {
    return (
      <div className={`flex flex-col space-y-2 ${className}`}>
        {links.map((link, index) => (
          <Link 
            key={link.href}
            href={link.href} 
            className={`${linkClassName} text-sm`}
          >
            {link.label}
          </Link>
        ))}
      </div>
    );
  }

  if (variant === 'inline') {
    return (
      <div className={`inline-flex items-center ${className}`}>
        {links.map((link, index) => (
          <React.Fragment key={link.href}>
            <Link 
              href={link.href} 
              className={`${linkClassName} text-xs`}
            >
              {link.label}
            </Link>
            {showDividers && index < links.length - 1 && (
              <span className="mx-1 text-gray-400">•</span>
            )}
          </React.Fragment>
        ))}
      </div>
    );
  }

  // Default 'footer' variant
  return (
    <div className={`flex flex-wrap items-center justify-center gap-x-6 gap-y-2 ${className}`}>
      {links.map((link, index) => (
        <React.Fragment key={link.href}>
          <Link 
            href={link.href} 
            className={`${linkClassName} text-sm font-medium`}
          >
            {link.label}
          </Link>
          {showDividers && index < links.length - 1 && (
            <span className="hidden sm:inline text-gray-400">|</span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};