# UI Design Rules

## Overview
This document defines the core UI design principles for the Indian palmistry application, emphasizing mobile-first design, responsive layouts, and iconographic communication.

## Core Design Principles

### 1. Mobile-First Design
**Why**: Users primarily upload palm images from mobile devices

#### Rules:
- **Design for mobile first**, then scale up to desktop
- **Touch-friendly targets**: Minimum 44px × 44px for all interactive elements
- **Thumb-friendly zones**: Place primary actions within thumb reach
- **Single-column layouts**: Stack elements vertically on mobile
- **Large, readable text**: Minimum 16px font size for body text
- **Simplified navigation**: Use bottom navigation or hamburger menu
- **Performance budgets**: Optimize for low-bandwidth networks and underpowered devices

#### Implementation:
```css
/* Mobile-first breakpoints */
.container {
  padding: 16px;
  max-width: 100%;
}

/* Tablet and up */
@media (min-width: 768px) {
  .container {
    padding: 24px;
    max-width: 720px;
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .container {
    padding: 32px;
    max-width: 960px;
  }
}
```

### 2. Responsive Design
**Why**: Ensure optimal experience across all devices

#### Rules:
- **Fluid grids**: Use CSS Grid or Flexbox for flexible layouts
- **Responsive images**: Scale images appropriately for different screen sizes
- **Breakpoint strategy**: Mobile (320px), Tablet (768px), Desktop (1024px+)
- **Content priority**: Most important content visible on smallest screens
- **Performance**: Optimize assets for mobile networks

#### Breakpoint System:
```css
/* Mobile: 320px - 767px */
/* Tablet: 768px - 1023px */
/* Desktop: 1024px+ */

.mobile-first {
  /* Base styles for mobile */
}

@media (min-width: 768px) {
  .tablet-enhancements {
    /* Tablet-specific styles */
  }
}

@media (min-width: 1024px) {
  .desktop-enhancements {
    /* Desktop-specific styles */
  }
}
```

### 3. Iconographic Communication
**Why**: Icons transcend language barriers and improve usability

#### Rules:
- **Universal icons**: Use widely recognized symbols
- **Consistent style**: Maintain visual consistency across all icons
- **Meaningful labels**: Always pair icons with text labels
- **Cultural sensitivity**: Choose icons that work across cultures
- **Accessibility**: Ensure icons are screen reader friendly

#### Icon Categories:
- **Navigation**: Home, Profile, Settings, Back, Close
- **Actions**: Upload, Download, Share, Delete, Edit
- **Status**: Loading, Success, Error, Warning, Info
- **Palm Reading**: Hand, Lines, Analysis, Results
- **Communication**: Chat, Send, Receive, History

#### Implementation:
```html
<!-- Icon with accessible label -->
<button aria-label="Upload palm image" class="icon-button">
  <svg class="icon" aria-hidden="true">
    <!-- Icon path -->
  </svg>
  <span class="label">Upload</span>
</button>
```

## Component Design Rules

### 1. Buttons
**Purpose**: Primary interaction elements

#### Rules:
- **Clear hierarchy**: Primary, secondary, and tertiary button styles
- **Consistent sizing**: 44px minimum height for touch targets
- **Visual feedback**: Hover, active, and focus states
- **Loading states**: Show progress for async actions
- **Disabled states**: Clear visual indication when unavailable
- **Minimalist styling**: Avoid heavy shadows/gradients; prefer flat colors from the theme

#### Button Types:
```css
.btn-primary {
  background: var(--color-saffron);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  min-height: 44px;
}

.btn-secondary {
  background: transparent;
  color: var(--color-saffron);
  border: 2px solid var(--color-saffron);
  padding: 12px 24px;
  border-radius: 8px;
  min-height: 44px;
}
```

### 2. Cards
**Purpose**: Content containers for palm readings and results

#### Rules:
- **Consistent spacing**: 16px padding on mobile, 24px on desktop
- **Subtle shadows**: Use elevation to create hierarchy
- **Rounded corners**: 8px border radius for modern feel
- **Responsive images**: Scale palm images appropriately
- **Clear content hierarchy**: Title, subtitle, content, actions
- **Minimalist content**: Prioritize clarity; avoid dense text blocks

#### Card Structure:
```html
<div class="card">
  <div class="card-image">
    <img src="palm-image.jpg" alt="Palm reading image" />
  </div>
  <div class="card-content">
    <h3 class="card-title">Life Line Analysis</h3>
    <p class="card-subtitle">Your life path reveals...</p>
    <div class="card-actions">
      <button class="btn-primary">Learn More</button>
    </div>
  </div>
</div>
```

### 3. Forms
**Purpose**: Image upload and user input

#### Rules:
- **Clear labels**: Always label form fields
- **Error states**: Show validation errors clearly
- **Success feedback**: Confirm successful actions
- **Progressive disclosure**: Show fields as needed
- **Auto-save**: Save progress automatically
- **Upload constraints**: Max 2 images (left/right), JPEG/PNG, enforce size in UI

#### Form Example:
```html
<form class="upload-form">
  <div class="form-group">
    <label for="palm-image">Upload Palm Image</label>
    <div class="upload-area" id="upload-zone">
      <svg class="upload-icon" aria-hidden="true">
        <!-- Upload icon -->
      </svg>
      <p>Drag and drop your palm image here</p>
      <input type="file" id="palm-image" accept="image/jpeg,image/png" multiple />
    </div>
  </div>
</form>
```

### 4. Navigation
**Purpose**: App navigation and user flow

#### Rules:
- **Bottom navigation**: Primary navigation on mobile
- **Breadcrumbs**: Show user location in app
- **Back buttons**: Always provide way to go back
- **Skip links**: Accessibility for keyboard users
- **Active states**: Clear indication of current page
- **Information architecture**: Analyses list (most recent first, page size 5) → Analysis detail → Conversations nested under analysis

#### Mobile Navigation:
```html
<nav class="bottom-nav">
  <a href="/" class="nav-item active">
    <svg class="nav-icon" aria-hidden="true">
      <!-- Home icon -->
    </svg>
    <span>Home</span>
  </a>
  <a href="/readings" class="nav-item">
    <svg class="nav-icon" aria-hidden="true">
      <!-- Readings icon -->
    </svg>
    <span>Readings</span>
  </a>
  <a href="/profile" class="nav-item">
    <svg class="nav-icon" aria-hidden="true">
      <!-- Profile icon -->
    </svg>
    <span>Profile</span>
  </a>
</nav>
```

## Interaction Patterns

### 1. Loading States
**Purpose**: Provide feedback during async operations

#### Rules:
- **Immediate feedback**: Show loading state within 100ms
- **Progress indication**: Show progress when possible
- **Skeleton screens**: Use placeholder content
- **Cultural elements**: Incorporate subtle cultural motifs (minimalist, low-contrast)
- **Accessibility**: Screen reader announcements

#### Loading Components:
```html
<div class="loading-state">
  <div class="loading-spinner">
    <!-- Cultural-inspired spinner -->
  </div>
  <p class="loading-text">Analyzing your palm...</p>
  <div class="loading-progress">
    <div class="progress-bar" style="width: 60%"></div>
  </div>
</div>
```

### 2. Error Handling
**Purpose**: Graceful error communication

#### Rules:
- **Clear messaging**: Explain what went wrong
- **Actionable solutions**: Provide next steps
- **Retry options**: Allow users to try again
- **Fallback content**: Show alternative content
- **Cultural sensitivity**: Avoid technical jargon; keep copy concise

#### Error States:
```html
<div class="error-state">
  <svg class="error-icon" aria-hidden="true">
    <!-- Error icon -->
  </svg>
  <h3>Unable to analyze image</h3>
  <p>Please ensure your palm is clearly visible and try again.</p>
  <button class="btn-primary">Try Again</button>
</div>
```

### 3. Success States
**Purpose**: Confirm successful actions

#### Rules:
- **Clear confirmation**: Show what was accomplished
- **Next steps**: Guide users to next action
- **Celebration**: Subtle positive reinforcement
- **Cultural elements**: Use appropriate cultural symbols
- **Auto-dismiss**: Clear success messages after delay

## Accessibility Rules

### 1. Screen Reader Support
- **Semantic HTML**: Use proper heading hierarchy
- **Alt text**: Describe all images meaningfully
- **ARIA labels**: Provide context for interactive elements
- **Focus management**: Logical tab order
- **Skip links**: Jump to main content

### 2. Keyboard Navigation
- **Tab order**: Logical progression through elements
- **Focus indicators**: Clear visual focus states
- **Keyboard shortcuts**: Common shortcuts (Enter, Escape)
- **Modal handling**: Trap focus in modals
- **Form navigation**: Easy form completion

### 3. Color and Contrast
- **WCAG AA compliance**: 4.5:1 contrast ratio for normal text
- **Color independence**: Don't rely solely on color
- **High contrast mode**: Support system preferences
- **Focus indicators**: High contrast focus states
- **Error states**: Clear visual error indication

## Performance Rules

### 1. Mobile Optimization
- **Fast loading**: Under 3 seconds on 3G
- **Image optimization**: WebP format with fallbacks
- **Lazy loading**: Load images as needed
- **Minimal JavaScript**: Reduce bundle size
- **Caching**: Cache static assets

### 2. Progressive Enhancement
- **Core functionality**: Works without JavaScript
- **Enhanced experience**: Add features progressively
- **Graceful degradation**: Fallback for unsupported features
- **Feature detection**: Check capabilities before using
- **Polyfills**: Support older browsers when needed

## Cultural Considerations

### 1. Icon Selection
- **Universal symbols**: Use widely recognized icons
- **Cultural sensitivity**: Avoid culturally specific symbols
- **Meaningful alternatives**: Provide text alternatives
- **Consistent style**: Maintain visual consistency
- **Accessibility**: Ensure icons are understandable

### 2. Layout Patterns
- **Reading direction**: Support RTL languages
- **Cultural spacing**: Respect cultural preferences
- **Color meanings**: Consider cultural color associations
- **Typography**: Choose culturally appropriate fonts
- **Imagery**: Use inclusive, diverse representations

## Implementation Guidelines

### 1. CSS Architecture
```css
/* Use CSS custom properties for theming */
:root {
  --color-primary: #FF6B35;
  --color-secondary: #8B6914;
  --color-accent: #1E3A8A;
  --color-background: #FAFAFA;
  --color-text: #1A1A1A;
  
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  --border-radius: 8px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### 2. Component Structure
```html
<!-- Consistent component structure -->
<div class="component">
  <header class="component-header">
    <h2 class="component-title">Title</h2>
  </header>
  <main class="component-content">
    <!-- Content -->
  </main>
  <footer class="component-footer">
    <!-- Actions -->
  </footer>
</div>
```

### 3. Responsive Images
```html
<picture>
  <source srcset="image-large.webp" media="(min-width: 1024px)">
  <source srcset="image-medium.webp" media="(min-width: 768px)">
  <img src="image-small.webp" alt="Description" loading="lazy">
</picture>
```

These UI rules ensure a consistent, accessible, and culturally sensitive user experience across all devices and user types.
