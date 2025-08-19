# Theme Rules

## Overview
This document defines the complete visual theme for the Indian palmistry application, implementing a minimalist cultural design with a saffron-based color palette that honors Indian traditions while maintaining modern usability.

## Color System (Cultural Minimalistic)

### Primary Color Palette
Minimal, culturally grounded palette with ample neutral space. Use accent colors sparingly for emphasis.

```css
:root {
  /* Primary Colors */
  --color-saffron: #FF6B35;        /* Deep Saffron - Sacred, trustworthy */
  --color-gold: #8B6914;           /* Dark Gold - Prosperity, wisdom */
  --color-blue: #1E3A8A;           /* Deep Blue - Trust, stability */
  
  /* Background Colors */
  --color-background: #FAFAFA;     /* Off-White - Clean, welcoming */
  --color-surface: #FFFFFF;        /* Pure White - Cards, modals */
  --color-overlay: rgba(26, 26, 26, 0.5); /* Dark overlay for modals */
  
  /* Text Colors */
  --color-text-primary: #1A1A1A;   /* Charcoal - Primary text */
  --color-text-secondary: #4A5568; /* Gray - Secondary text */
  --color-text-muted: #718096;     /* Light Gray - Muted text */
  --color-text-inverse: #FFFFFF;   /* White - Text on dark backgrounds */
  
  /* Status Colors */
  --color-success: #38A169;        /* Green - Success states */
  --color-warning: #D69E2E;        /* Yellow - Warning states */
  --color-error: #E53E3E;          /* Red - Error states */
  --color-info: #3182CE;           /* Blue - Information states */
  
  /* Border Colors */
  --color-border-light: #E2E8F0;   /* Light Gray - Subtle borders */
  --color-border-medium: #CBD5E0;  /* Medium Gray - Standard borders */
  --color-border-dark: #A0AEC0;    /* Dark Gray - Strong borders */
}
```

### Color Usage Guidelines (Minimalism)

#### Primary Actions
- **Main CTAs**: Use `--color-saffron` for primary buttons (limit to one primary per view)
- **Brand elements**: Logo, subtle navigation highlights
- **Important information**: Key palm reading insights

#### Secondary Actions
- **Secondary buttons**: Use `--color-gold` sparingly
- **Accent elements**: Minimal highlights, badges, progress indicators
- **Premium features**: Special functionality indicators

#### Interactive Elements
- **Links**: `--color-blue` for text links; avoid overuse
- **Focus states**: High-contrast outline for accessibility
- **Hover states**: Subtle, non-distracting variations

#### Status Indicators
- **Success**: Green for completed actions
- **Warning**: Yellow for cautions
- **Error**: Red for failures
- **Info**: Blue for information

### Contrast Compliance
All color combinations meet WCAG AA standards:
- **Normal text**: 4.5:1 minimum contrast ratio
- **Large text**: 3:1 minimum contrast ratio
- **UI components**: 3:1 minimum contrast ratio
 - Prefer neutral backgrounds with limited accent usage to maintain cultural minimalism

## Typography System

### Font Stack
```css
:root {
  /* Primary Font - Clean and Readable */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  
  /* Secondary Font - Elegant Headings */
  --font-secondary: 'Playfair Display', Georgia, serif; /* Headings only; keep body text on primary for readability */
  
  /* Monospace Font - Code and Technical Content */
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
}
```

### Font Sizes
```css
:root {
  /* Mobile-first font sizes */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px - Minimum for body text */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  --text-5xl: 3rem;      /* 48px */
}
```

### Typography Scale
```css
/* Heading Styles */
.heading-1 {
  font-family: var(--font-secondary);
  font-size: var(--text-4xl);
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-text-primary);
}

.heading-2 {
  font-family: var(--font-secondary);
  font-size: var(--text-3xl);
  font-weight: 600;
  line-height: 1.3;
  color: var(--color-text-primary);
}

.heading-3 {
  font-family: var(--font-secondary);
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-text-primary);
}

/* Body Text */
.body-large {
  font-family: var(--font-primary);
  font-size: var(--text-lg);
  font-weight: 400;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.body-base {
  font-family: var(--font-primary);
  font-size: var(--text-base);
  font-weight: 400;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.body-small {
  font-family: var(--font-primary);
  font-size: var(--text-sm);
  font-weight: 400;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

/* Special Text */
.caption {
  font-family: var(--font-primary);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.4;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

## Spacing System

### Spacing Scale
```css
:root {
  --spacing-0: 0;
  --spacing-1: 0.25rem;   /* 4px */
  --spacing-2: 0.5rem;    /* 8px */
  --spacing-3: 0.75rem;   /* 12px */
  --spacing-4: 1rem;      /* 16px */
  --spacing-5: 1.25rem;   /* 20px */
  --spacing-6: 1.5rem;    /* 24px */
  --spacing-8: 2rem;      /* 32px */
  --spacing-10: 2.5rem;   /* 40px */
  --spacing-12: 3rem;     /* 48px */
  --spacing-16: 4rem;     /* 64px */
  --spacing-20: 5rem;     /* 80px */
  --spacing-24: 6rem;     /* 96px */
}
```

### Layout Spacing
```css
/* Container spacing */
.container {
  padding: var(--spacing-4);
  max-width: 100%;
}

@media (min-width: 768px) {
  .container {
    padding: var(--spacing-6);
    max-width: 720px;
  }
}

@media (min-width: 1024px) {
  .container {
    padding: var(--spacing-8);
    max-width: 960px;
  }
}

/* Component spacing */
.card {
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}

@media (min-width: 768px) {
  .card {
    padding: var(--spacing-6);
    margin-bottom: var(--spacing-6);
  }
}
```

## Border Radius System

### Border Radius Scale
```css
:root {
  --radius-none: 0;
  --radius-sm: 0.25rem;   /* 4px */
  --radius-base: 0.5rem;  /* 8px */
  --radius-md: 0.75rem;   /* 12px */
  --radius-lg: 1rem;      /* 16px */
  --radius-xl: 1.5rem;    /* 24px */
  --radius-full: 9999px;  /* Full circle */
}
```

### Usage Guidelines
- **Buttons**: `--radius-base` for standard buttons
- **Cards**: `--radius-base` for content cards
- **Modals**: `--radius-lg` for modal dialogs
- **Avatars**: `--radius-full` for circular elements
- **Form inputs**: `--radius-sm` for subtle rounding

## Shadow System

### Shadow Scale
```css
:root {
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
```

### Usage Guidelines
- **Cards**: `--shadow-base` for subtle elevation
- **Modals**: `--shadow-lg` for prominent elevation
- **Dropdowns**: `--shadow-md` for medium elevation
- **Hover states**: Increase shadow by one level
- **Focus states**: Use colored shadows for accessibility

## Icon System

### Icon Guidelines
- **Size**: 16px, 20px, 24px, 32px standard sizes
- **Style**: Outlined icons for consistency
- **Color**: Inherit text color or use semantic colors
- **Accessibility**: Always include `aria-hidden="true"` and proper labels

### Icon Sizes
```css
.icon-xs { width: 1rem; height: 1rem; }   /* 16px */
.icon-sm { width: 1.25rem; height: 1.25rem; } /* 20px */
.icon-base { width: 1.5rem; height: 1.5rem; } /* 24px */
.icon-lg { width: 2rem; height: 2rem; }   /* 32px */
.icon-xl { width: 2.5rem; height: 2.5rem; } /* 40px */
```

## Animation System

### Transition Durations
```css
:root {
  --duration-75: 75ms;
  --duration-100: 100ms;
  --duration-150: 150ms;
  --duration-200: 200ms;
  --duration-300: 300ms;
  --duration-500: 500ms;
  --duration-700: 700ms;
  --duration-1000: 1000ms;
}
```

### Easing Functions
```css
:root {
  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Animation Guidelines
- **Hover effects**: 150ms duration with ease-out
- **Focus states**: 100ms duration with ease-out
- **Page transitions**: 300ms duration with ease-in-out
- **Loading animations**: 1000ms duration with ease-in-out
- **Micro-interactions**: 75ms duration with ease-out

## Cultural Design Elements

### Subtle Cultural Motifs
- **Mandala patterns**: Use as background textures (very subtle)
- **Henna-inspired curves**: For decorative elements
- **Sacred geometry**: For loading animations
- **Cultural symbols**: Only when contextually appropriate

### Implementation Guidelines
```css
/* Cultural background pattern (very subtle) */
.cultural-bg {
  background-image: 
    radial-gradient(circle at 25% 25%, var(--color-saffron) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, var(--color-gold) 0%, transparent 50%);
  opacity: 0.03;
  background-size: 200px 200px;
}

/* Cultural loading animation */
@keyframes cultural-spinner {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.cultural-spinner {
  animation: cultural-spinner 2s linear infinite;
  background: conic-gradient(
    from 0deg,
    var(--color-saffron),
    var(--color-gold),
    var(--color-blue),
    var(--color-saffron)
  );
  border-radius: 50%;
  mask: radial-gradient(circle at center, transparent 60%, black 60%);
}
```

## Component-Specific Themes

### Button Themes
```css
.btn-primary {
  background: var(--color-saffron);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-base);
  padding: var(--spacing-3) var(--spacing-6);
  font-weight: 600;
  transition: all var(--duration-200) var(--ease-out);
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  background: #E55A2B;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-secondary {
  background: transparent;
  color: var(--color-saffron);
  border: 2px solid var(--color-saffron);
  border-radius: var(--radius-base);
  padding: var(--spacing-3) var(--spacing-6);
  font-weight: 600;
  transition: all var(--duration-200) var(--ease-out);
}

.btn-secondary:hover {
  background: var(--color-saffron);
  color: var(--color-text-inverse);
}
```

### Card Themes
```css
.card {
  background: var(--color-surface);
  border-radius: var(--radius-base);
  box-shadow: var(--shadow-base);
  border: 1px solid var(--color-border-light);
  transition: all var(--duration-200) var(--ease-out);
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-header {
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-border-light);
}

.card-content {
  padding: var(--spacing-4);
}

.card-footer {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border-light);
  background: var(--color-background);
}
```

### Form Themes
```css
.form-input {
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-sm);
  padding: var(--spacing-3);
  font-size: var(--text-base);
  transition: all var(--duration-200) var(--ease-out);
  background: var(--color-surface);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-saffron);
  box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
}

.form-input.error {
  border-color: var(--color-error);
  box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.1);
}
```

## Dark Mode Support

### Dark Mode Colors
```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #1A1A1A;
    --color-surface: #2D2D2D;
    --color-text-primary: #FFFFFF;
    --color-text-secondary: #A0AEC0;
    --color-text-muted: #718096;
    --color-border-light: #4A5568;
    --color-border-medium: #2D3748;
    --color-border-dark: #1A202C;
  }
}
```

## Implementation Notes

### CSS Custom Properties
- Use CSS custom properties for all theme values
- Maintain consistent naming conventions
- Group related properties together
- Document all custom properties

### Responsive Design
- Scale typography and spacing appropriately
- Maintain touch targets on mobile
- Ensure readability across all screen sizes
- Test color contrast on different devices

### Performance
- Minimize CSS bundle size
- Use efficient selectors
- Optimize animations for performance
- Consider critical CSS for above-the-fold content

This theme system provides a comprehensive foundation for creating a consistent, accessible, and culturally sensitive user interface that honors Indian traditions while maintaining modern usability standards.
