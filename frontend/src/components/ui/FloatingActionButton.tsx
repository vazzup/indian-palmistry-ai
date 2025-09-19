/**
 * @fileoverview Floating Action Button Component
 * Mobile-friendly button that provides quick access to key actions
 * Positioned in bottom-right corner with proper touch targets
 */

'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';

interface FloatingActionButtonProps {
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  className?: string;
  disabled?: boolean;
}

export function FloatingActionButton({
  onClick,
  icon,
  label,
  className = '',
  disabled = false,
}: FloatingActionButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      className={`
        fixed bottom-6 right-6 z-40
        w-14 h-14 rounded-full shadow-lg
        bg-saffron-600 hover:bg-saffron-700
        border-0 p-0
        transition-all duration-200 ease-in-out
        hover:scale-110 active:scale-95
        focus:ring-4 focus:ring-saffron-200
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
      aria-label={label}
      title={label}
    >
      <div className="flex items-center justify-center">
        {icon}
      </div>
    </Button>
  );
}