import React from 'react';
import { Loader2 } from 'lucide-react';
import { getComponentClasses } from '@/lib/cultural-theme';
import type { ComponentSize, ComponentVariant } from '@/types';

/**
 * Props for the Button component
 */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style variant of the button */
  variant?: ComponentVariant;
  /** Size of the button (affects padding, text size, height) */
  size?: ComponentSize;
  /** Show loading spinner and disable interaction */
  loading?: boolean;
  /** Icon to display alongside button text */
  icon?: React.ReactNode;
  /** Button content */
  children: React.ReactNode;
}

/**
 * A customizable button component with cultural design system integration.
 * Supports different variants, sizes, loading states, and icons.
 * 
 * Features:
 * - Multiple visual variants (default, outline, ghost, destructive)
 * - Responsive sizing with mobile-first touch targets
 * - Loading state with spinner
 * - Icon support with proper alignment
 * - Cultural saffron-based color scheme
 * - Accessibility features (focus states, disabled states)
 * 
 * @example
 * ```tsx
 * <Button variant="default" size="lg" loading={isSubmitting}>
 *   Submit Form
 * </Button>
 * 
 * <Button variant="outline" icon={<Icon />}>
 *   With Icon
 * </Button>
 * ```
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    variant = 'default', 
    size = 'md', 
    loading = false, 
    icon, 
    className = '', 
    disabled,
    children, 
    ...props 
  }, ref) => {
    const classes = getComponentClasses('button', variant, size);
    
    const isDisabled = disabled || loading;
    
    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={`${classes} ${className}`}
        {...props}
      >
        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
        {!loading && icon && <span className="cultural-icon">{icon}</span>}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';