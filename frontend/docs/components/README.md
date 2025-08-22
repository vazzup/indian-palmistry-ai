# Frontend Component Documentation

This directory contains comprehensive documentation for all React components in the Indian Palmistry AI frontend application, built with Next.js 14, TypeScript, and a cultural minimalist design system.

## Architecture Overview

The frontend is structured as a modern, mobile-first Progressive Web App with the following key architectural principles:

- **Cultural Minimalist Design**: Saffron-based color palette with Indian cultural elements
- **Mobile-First Responsive**: 44px touch targets, optimized for mobile interactions
- **Type Safety**: 100% TypeScript coverage with strict mode
- **Security-First**: CSRF protection, input sanitization, and secure forms
- **Performance Optimized**: Lazy loading, code splitting, and optimized images
- **PWA Capabilities**: Offline support, installable, background sync

## Component Categories

### Core UI Components (`/components/ui/`)

- **[Button](./ui/Button.md)** - Multi-variant button with cultural styling and loading states
- **[Input](./ui/Input.md)** - Form input with validation, password toggle, and cultural styling
- **[Card](./ui/Card.md)** - Flexible card system for content organization
- **[Spinner](./ui/Spinner.md)** - Cultural loading animations with lotus-inspired design
- **[SecureForm](./ui/SecureForm.md)** - Form with built-in CSRF protection and input sanitization
- **[OptimizedImage](./ui/OptimizedImage.md)** - Next.js Image with loading states and error handling
- **[LazyLoad](./ui/LazyLoad.md)** - Component lazy loading with intersection observer
- **[OfflineIndicator](./ui/OfflineIndicator.md)** - Connection status indicator with sync queue info
- **[InstallPrompt](./ui/InstallPrompt.md)** - PWA installation prompt component

### Authentication Components (`/components/auth/`)

- **[LoginForm](./auth/LoginForm.md)** - Cultural login form with validation and error handling
- **[RegisterForm](./auth/RegisterForm.md)** - User registration with cultural design elements
- **[LoginGate](./auth/LoginGate.md)** - Strategic authentication prompt after analysis summary

### Analysis Components (`/components/analysis/`)

- **[MobileImageUpload](./analysis/MobileImageUpload.md)** - Mobile-optimized upload with drag & drop and camera
- **[BackgroundJobProgress](./analysis/BackgroundJobProgress.md)** - Real-time job status tracking with cultural messaging

### Conversation Components (`/components/conversation/`)

- **[AnalysisConversations](./conversation/AnalysisConversations.md)** - AI chat interface scoped to analyses

### Layout Components (`/components/layout/`)

- **[DashboardLayout](./layout/DashboardLayout.md)** - Protected dashboard layout with navigation

### Dashboard Components (`/components/dashboard/`)

- **[StatsCard](./dashboard/StatsCard.md)** - Analytics display card with cultural styling

### Provider Components (`/components/providers/`)

- **[SecurityProvider](./providers/SecurityProvider.md)** - Global security context and CSRF management
- **[PerformanceProvider](./providers/PerformanceProvider.md)** - Performance monitoring and Core Web Vitals tracking

## Custom Hooks (`/hooks/`)

- **[useCSRF](../hooks/useCSRF.md)** - CSRF token management hook
- **[useOffline](../hooks/useOffline.md)** - Offline detection and background sync management
- **[usePerformanceMonitoring](../hooks/usePerformanceMonitoring.md)** - Core Web Vitals and custom metrics tracking

## Utility Libraries (`/lib/`)

- **[api](../lib/api.md)** - Axios client configuration for FastAPI backend integration
- **[auth](../lib/auth.md)** - Zustand authentication store and utilities
- **[cultural-theme](../lib/cultural-theme.md)** - Design system utilities and theming
- **[redis-jobs](../lib/redis-jobs.md)** - Background job polling utilities
- **[security](../lib/security.md)** - Input sanitization, file validation, and rate limiting

## Design System

### Color Palette

The application uses a saffron-based color palette with cultural significance:

```css
/* Primary Colors */
--saffron-50: #fffbeb;
--saffron-100: #fef3c7;
--saffron-200: #fde68a;
--saffron-300: #fcd34d;
--saffron-400: #fbbf24;
--saffron-500: #ff8000;  /* Primary brand color */
--saffron-600: #d97706;
--saffron-700: #b45309;
--saffron-800: #92400e;
--saffron-900: #78350f;

/* Cultural Accent Colors */
--turmeric: #f0b429;      /* Warm gold accent */
--vermillion: #e34234;    /* Sacred red for errors */
--sandalwood: #d4a574;    /* Neutral warm tone */
--lotus: #e8b4d1;         /* Soft accent color */
```

### Typography

- **Mobile-first responsive typography** with 16px base size for accessibility
- **Font stack**: System fonts optimized for performance and readability
- **Consistent sizing scale**: sm, md, lg, xl variants across components

### Touch Targets

All interactive elements meet **44px minimum touch target** requirements for mobile accessibility.

## Testing Strategy

### Test Coverage

- **Unit Tests**: All components with user interaction testing
- **Integration Tests**: API client, authentication flow, file upload
- **E2E Tests**: Critical user flows with Playwright
- **Accessibility Tests**: WCAG 2.1 compliance verification

### Testing Tools

```typescript
{
  "testing": "Vitest (Jest alternative)",
  "dom": "jsdom with @testing-library/react",
  "e2e": "Playwright for browser testing",
  "coverage": "Built-in Vitest coverage reporting",
  "mocks": "Comprehensive mocking for Next.js and external APIs"
}
```

## Security Features

### CSRF Protection

All forms are protected with CSRF tokens via the `SecureForm` component and `useCSRF` hook.

### Input Sanitization

User inputs are sanitized to prevent XSS attacks using the security utilities in `/lib/security.ts`.

### Rate Limiting

Client-side rate limiting prevents abuse and enhances security with configurable limits per action.

### File Upload Security

Image uploads include magic byte validation and file type restrictions.

## Performance Optimizations

### Code Splitting

- Route-based code splitting with Next.js App Router
- Component-level lazy loading with React.lazy()
- Dynamic imports for heavy dependencies

### Image Optimization

- Next.js Image component with automatic optimization
- WebP and AVIF format support
- Responsive image loading with proper sizing

### Caching Strategy

- API response caching with React Query (future enhancement)
- Service worker caching for offline capabilities
- Browser caching optimization

## PWA Features

### Offline Support

- Background sync queue for actions performed while offline
- Cached content available offline
- Connection status indication

### Installation

- App installation prompts at appropriate times
- Native app-like experience on mobile devices
- App shortcuts and widget support

### Performance Monitoring

- Core Web Vitals tracking
- Custom metrics collection
- Real user monitoring

## Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Android Chrome 90+
- **Progressive Enhancement**: Basic functionality without JavaScript

## Accessibility

- **WCAG 2.1 AA compliant** with focus states and screen reader support
- **Keyboard navigation** throughout the application
- **High contrast ratios** for visual accessibility
- **Touch target sizing** meets mobile accessibility standards

## Contributing

When creating new components:

1. Follow the cultural design system
2. Include TypeScript definitions
3. Write comprehensive tests
4. Document component props and usage
5. Ensure mobile-first responsive design
6. Include accessibility features
7. Follow security best practices

## File Structure

```
components/
├── ui/                 # Core UI components
├── auth/              # Authentication components
├── analysis/          # Analysis-specific components
├── conversation/      # Chat and messaging components
├── layout/           # Layout and navigation components
├── dashboard/        # Dashboard and analytics components
└── providers/        # Context providers and global state
```

Each component directory includes:
- Component implementation (`.tsx`)
- Type definitions (`.types.ts` if complex)
- Tests (in `__tests__/` directory)
- Documentation (in `docs/` directory)
- Storybook stories (future enhancement)