# Phase 3.75: Frontend Completion - Full Feature Implementation

## Overview
**Phase 3.75** completes the frontend implementation by building the remaining essential pages and features identified during Phase 3.5. This phase focuses on completing the user experience with protected routes, conversation interfaces, user dashboard, and production optimization.

**Duration**: 1-2 weeks  
**Goal**: Complete production-ready frontend with all core features and optimization

## Scope
Building on the solid foundation from Phase 3.5, this phase implements:
- Complete authentication pages (login/register)
- Protected dashboard and user management
- Analysis-scoped conversation interface
- PWA capabilities for mobile app-like experience
- Performance optimization and production readiness
- E2E testing and deployment preparation

## Deliverables
- ✅ Complete authentication pages with cultural design
- ✅ Protected user dashboard with analysis history
- ✅ Conversation interface properly scoped to analyses
- ✅ PWA implementation with offline capabilities
- ✅ Performance optimization and bundle analysis
- ✅ Comprehensive E2E testing suite
- ✅ Production deployment configuration

## Tasks & Features

### 1. Core Page Implementation
**Purpose**: Implement all missing essential pages with proper routing and components

**Tasks**:
1. Create landing page `/app/(public)/page.tsx` with cultural design and upload interface
2. Implement login page `/app/(auth)/login/page.tsx` with form validation
3. Build registration page `/app/(auth)/register/page.tsx` with user onboarding
4. Create dashboard page `/app/(dashboard)/dashboard/page.tsx` with analytics
5. Implement analysis history page `/app/(dashboard)/analyses/page.tsx`
6. Build analysis detail page `/app/(dashboard)/analyses/[id]/page.tsx` with conversations
7. Create user profile page `/app/(dashboard)/profile/page.tsx` with settings
8. Add password reset page `/app/(auth)/reset/page.tsx` with email stub

**Acceptance Criteria**:
- All 8 essential pages implemented with proper TypeScript types
- Mobile-first responsive design on all pages
- Cultural design system consistently applied
- Proper Next.js App Router file structure
- Each page has proper error boundaries and loading states
- SEO metadata configured for all public pages
- Authentication guards properly implemented
- Page transitions smooth with loading indicators

**Key Components**:
- `HomePage` - Landing page with cultural header and upload interface
- `LoginPage` - Authentication with return-to functionality
- `RegisterPage` - User registration with validation
- `DashboardPage` - User overview with analytics cards
- `AnalysisHistoryPage` - Paginated analysis list with search
- `AnalysisDetailPage` - Full results with conversation interface
- `ProfilePage` - User settings and preferences
- `PasswordResetPage` - Password recovery flow

### 2. Complete Authentication Pages
**Purpose**: Finish the authentication flow with dedicated pages for login and registration

**Tasks**:
1. Create `/login` page with cultural design and proper form handling
2. Create `/register` page with validation and user onboarding
3. Implement password reset flow (email stub for MVP)
4. Add authentication redirects and return-to functionality
5. Implement social login preparation (Google, Apple for future)
6. Create authentication loading and error states
7. Add form persistence and auto-fill support
8. Implement CSRF token refresh and session validation

**Acceptance Criteria**:
- Dedicated login page with cultural styling and validation
- Registration page with email verification stub
- Password reset flow with email delivery preparation
- Proper redirect handling after successful authentication
- Form state persistence during navigation
- Mobile-optimized form inputs with proper keyboard types
- Error handling with culturally appropriate messaging
- Session validation and auto-refresh capabilities

**Key Components**:
- `LoginForm` - Enhanced form with cultural styling and validation
- `RegisterForm` - Multi-step registration with email verification stub
- `PasswordResetForm` - Password recovery with email delivery preparation
- `AuthGuard` - Route protection with loading states
- `AuthRedirect` - Smart redirect logic after authentication
- `SocialLoginButtons` - Google/Apple login preparation
- `AuthLoadingState` - Cultural loading animations during auth operations
- `CSRFTokenManager` - Automatic CSRF token handling

### 2. Protected User Dashboard
**Purpose**: Create comprehensive user dashboard for managing analyses and account

**Tasks**:
1. Build main dashboard page with analysis overview
2. Create analysis history list with pagination and search
3. Implement analysis detail view with full results access
4. Add user profile management with basic settings
5. Create analysis deletion with confirmation dialogs
6. Implement usage statistics and analytics display
7. Add user preferences (theme, notifications, privacy)
8. Create data export functionality (GDPR compliance)

**Acceptance Criteria**:
- Dashboard shows user statistics and recent analyses
- Analysis history with search, filter, and sort capabilities
- Full analysis detail view accessible post-login
- User profile editing with validation and image upload
- Analysis management (view, delete, export)
- Usage analytics with cultural data visualization
- User preferences management with instant feedback
- GDPR-compliant data export in multiple formats

**Key Components**:
- `DashboardPage` - Main dashboard with overview cards
- `AnalysisHistoryList` - Paginated analysis list with filters
- `AnalysisDetailView` - Full analysis results display
- `UserProfileEdit` - Profile management interface
- `UsageAnalytics` - Cultural charts and statistics
- `DataExportDialog` - GDPR export functionality

### 3. Analysis-Scoped Conversation Interface
**Purpose**: Implement AI conversation system properly scoped to specific analyses

**Tasks**:
1. Create conversation interface within analysis detail view
2. Build message display with cultural chat bubbles
3. Implement real-time message sending with background processing
4. Add conversation management (new, rename, delete)
5. Create message history with infinite scroll pagination
6. Implement conversation templates for common questions
7. Add message export and sharing capabilities
8. Build conversation search within analysis context

**Acceptance Criteria**:
- Conversation interface embedded in analysis pages
- Real-time chat with cultural message styling
- Background AI processing with job polling
- Conversation CRUD operations with proper validation
- Message history with efficient pagination
- Quick templates for common palmistry questions
- Message threading and context preservation
- Search within conversation history

**Key Components**:
- `AnalysisChatInterface` - Main chat component scoped to analysis
- `MessageBubble` - Cultural message display with AI/user differentiation
- `ConversationSidebar` - List of conversations for the analysis
- `ChatInput` - Message input with rich text and emoji support
- `ConversationTemplates` - Quick-start conversation topics
- `MessageSearch` - Search within conversation context

### 4. PWA Implementation
**Purpose**: Transform the web app into a mobile app-like experience

**Tasks**:
1. Configure service worker for offline functionality
2. Implement app manifest with cultural branding
3. Add push notification infrastructure
4. Create offline fallbacks for key features
5. Implement background sync for uploads and messages
6. Add app installation prompts and onboarding
7. Create splash screens and loading states
8. Implement caching strategies for optimal performance

**Acceptance Criteria**:
- App can be installed on mobile and desktop devices
- Core features work offline (view analyses, cached conversations)
- Push notifications for analysis completion
- Background sync ensures data integrity
- Installation prompts appear at appropriate times
- Splash screen with cultural branding
- Caching strategy optimizes load times
- Offline indicator with graceful degradation

**Key Components**:
- `ServiceWorker` - Offline functionality and caching
- `PushNotificationManager` - Notification handling
- `OfflineIndicator` - Connection status display
- `InstallPrompt` - App installation guidance
- `BackgroundSync` - Data synchronization queue
- `PWAManifest` - App metadata and icons

### 5. Performance Optimization
**Purpose**: Optimize the application for production performance and user experience

**Tasks**:
1. Implement code splitting and lazy loading for all heavy components
2. Optimize image loading with Next.js Image component and compression
3. Add bundle analysis and size optimization with webpack-bundle-analyzer
4. Implement React Query for API caching and state management
5. Optimize Tailwind CSS with PurgeCSS and compression
6. Add prefetching for critical user flows and route preloading
7. Implement virtual scrolling for long lists (analysis history, messages)
8. Add performance monitoring with Core Web Vitals and real user metrics

**Acceptance Criteria**:
- Bundle size under 500KB gzipped for initial load
- First Contentful Paint under 1.5s on 3G networks
- Largest Contentful Paint under 2.5s on mobile
- Cumulative Layout Shift under 0.1 across all pages
- Time to Interactive under 3s on mobile devices
- 95%+ Lighthouse performance score for all core pages
- API response caching reduces redundant calls by 80%+
- Virtual scrolling handles 1000+ items without performance degradation

**Key Components**:
- `LazyImageUpload` - Lazy-loaded upload component with progressive loading
- `VirtualizedAnalysisList` - Performance list rendering for analysis history
- `VirtualizedMessageList` - Efficient message history rendering
- `CacheManager` - React Query integration for API response caching
- `PerformanceMonitor` - Core Web Vitals tracking with real user metrics
- `BundleAnalyzer` - Webpack bundle analysis and optimization tools
- `ImageOptimizer` - Next.js Image with compression and lazy loading
- `RoutePreloader` - Critical path preloading for better UX

**Implementation Details**:
```typescript
// Code Splitting Implementation
const LazyDashboard = lazy(() => import('@/components/dashboard/Dashboard'));
const LazyAnalysisDetail = lazy(() => import('@/components/analysis/AnalysisDetail'));
const LazyChatInterface = lazy(() => import('@/components/conversation/ChatInterface'));

// React Query Configuration for Caching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});

// Virtual Scrolling for Large Lists
export const VirtualizedAnalysisList = ({ analyses }) => {
  const rowVirtualizer = useVirtualizer({
    count: analyses.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // Estimated row height
    overscan: 5,
  });

  return (
    <div ref={parentRef} className="h-400 overflow-auto">
      <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
        {rowVirtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <AnalysisCard analysis={analyses[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};

// Image Optimization with Next.js
export const OptimizedImage = ({ src, alt, ...props }) => {
  return (
    <Image
      src={src}
      alt={alt}
      quality={85}
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
      loading="lazy"
      {...props}
    />
  );
};
```

### 6. E2E Testing Suite
**Purpose**: Comprehensive end-to-end testing for critical user flows

**Tasks**:
1. Set up Playwright testing environment
2. Create critical path tests (upload → analysis → conversation)
3. Test authentication flows and session management
4. Add mobile-specific testing scenarios
5. Implement visual regression testing
6. Create performance testing benchmarks
7. Add accessibility testing with automated tools
8. Set up CI/CD pipeline integration

**Acceptance Criteria**:
- Complete user journey tests pass consistently
- Authentication flows tested across browsers
- Mobile experience tested on multiple viewport sizes
- Visual regression tests prevent UI breaks
- Performance benchmarks maintain speed requirements
- Accessibility tests ensure WCAG compliance
- CI/CD integration provides continuous validation
- Test coverage above 80% for critical flows

**Test Scenarios**:
- **Happy Path**: Register → Upload → Analysis → Login Gate → Full Results → Chat
- **Error Handling**: Invalid files, network failures, authentication errors
- **Mobile Experience**: Touch interactions, camera upload, responsive layouts
- **Performance**: Large file uploads, long conversations, heavy usage
- **Accessibility**: Screen reader navigation, keyboard-only usage

### Comprehensive Testing Implementation

**E2E Testing with Playwright**:
```typescript
// Critical Path Testing
import { test, expect } from '@playwright/test';

test.describe('Critical User Journey', () => {
  test('complete analysis flow with login gate', async ({ page, context }) => {
    // 1. Land on homepage
    await page.goto('/');
    await expect(page.locator('[data-testid="welcome-section"]')).toBeVisible();

    // 2. Upload palm image
    await page.setInputFiles('[data-testid="file-input"]', 'test-assets/palm-test.jpg');
    await page.click('[data-testid="upload-button"]');

    // 3. Wait for analysis completion
    await expect(page.locator('[data-testid="analysis-progress"]')).toBeVisible();
    await page.waitForSelector('[data-testid="analysis-summary"]', { timeout: 60000 });

    // 4. Hit login gate
    await expect(page.locator('[data-testid="login-gate"]')).toBeVisible();
    const analysisId = await page.url().match(/analysis\/(\w+)/)?.[1];
    
    // 5. Login process
    await page.click('[data-testid="login-gate-button"]');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'testpass123');
    await page.click('[data-testid="login-submit"]');

    // 6. Verify redirect to full results
    await expect(page).toHaveURL(`/analysis/${analysisId}`);
    await expect(page.locator('[data-testid="full-analysis-results"]')).toBeVisible();

    // 7. Test conversation functionality
    await page.click('[data-testid="start-conversation"]');
    await page.fill('[data-testid="message-input"]', 'Tell me more about my life line');
    await page.click('[data-testid="send-message"]');
    
    // 8. Verify AI response processing
    await expect(page.locator('[data-testid="ai-thinking-indicator"]')).toBeVisible();
    await page.waitForSelector('[data-testid="ai-message"]', { timeout: 30000 });
  });

  test('mobile experience optimized', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    
    // Test touch targets are at least 44px
    const touchTargets = await page.locator('button, [role="button"], input').all();
    for (const target of touchTargets) {
      const box = await target.boundingBox();
      expect(box.height).toBeGreaterThanOrEqual(44);
    }

    // Test mobile upload with camera
    await page.click('[data-testid="camera-upload"]');
    await expect(page.locator('[data-testid="camera-interface"]')).toBeVisible();
  });

  test('offline functionality', async ({ page, context }) => {
    await page.goto('/dashboard');
    
    // Go offline
    await context.setOffline(true);
    
    // Verify offline indicator
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
    
    // Test offline functionality
    await page.click('[data-testid="cached-analysis"]');
    await expect(page.locator('[data-testid="offline-cached-content"]')).toBeVisible();
  });
});

// Performance Testing
test.describe('Performance Benchmarks', () => {
  test('core web vitals meet targets', async ({ page }) => {
    const client = await page.context().newCDPSession(page);
    await client.send('Performance.enable');
    
    await page.goto('/');
    
    // Measure FCP
    const fcpMetric = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
              resolve(entry.startTime);
            }
          }
        }).observe({ entryTypes: ['paint'] });
      });
    });
    
    expect(fcpMetric).toBeLessThan(1500); // 1.5s target
  });
});

// Accessibility Testing
test.describe('Accessibility Compliance', () => {
  test('keyboard navigation works completely', async ({ page }) => {
    await page.goto('/');
    
    // Test tab navigation
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
    
    // Navigate through all focusable elements
    const focusableElements = await page.locator('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])').count();
    
    for (let i = 0; i < focusableElements; i++) {
      await page.keyboard.press('Tab');
      const focused = page.locator(':focus');
      await expect(focused).toBeVisible();
    }
  });

  test('screen reader compatibility', async ({ page }) => {
    await page.goto('/');
    
    // Check for proper ARIA labels
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const ariaLabel = await button.getAttribute('aria-label');
      const textContent = await button.textContent();
      expect(ariaLabel || textContent).toBeTruthy();
    }
    
    // Check heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
  });
});
```

### 7. Security Implementation
**Purpose**: Implement comprehensive security measures for production readiness

**Tasks**:
1. Implement CSRF token management across all forms
2. Add input sanitization hooks for XSS prevention
3. Create session validation with auto-refresh
4. Implement rate limiting on frontend actions
5. Add Content Security Policy headers
6. Create error boundary with secure error reporting
7. Implement secure file upload validation
8. Add authentication timeout and session management

**Acceptance Criteria**:
- All forms protected with CSRF tokens
- Input sanitization prevents XSS attacks
- Session validation works with auto-refresh
- Rate limiting prevents abuse
- CSP headers block malicious scripts
- Error boundaries don't expose sensitive data
- File uploads validate magic bytes and content
- Sessions timeout securely with proper cleanup

**Key Components**:
- `CSRFTokenProvider` - Global CSRF token management
- `InputSanitizer` - XSS prevention utilities
- `SessionValidator` - Auto-refresh session handling
- `RateLimiter` - Frontend rate limiting component
- `SecureErrorBoundary` - Cultural error boundary with secure reporting
- `FileValidator` - Magic byte and content validation
- `SessionTimeoutManager` - Automatic session cleanup

### 8. Production Configuration
**Purpose**: Prepare the application for production deployment

**Tasks**:
1. Configure Docker multi-stage build for frontend
2. Set up GitHub Actions CI/CD pipeline
3. Implement proper error tracking and monitoring
4. Configure Vercel deployment with environment management
5. Set up security headers and CSP policies
6. Implement performance monitoring with Core Web Vitals
7. Configure analytics and user behavior tracking
8. Set up staging environment and deployment pipeline

**Acceptance Criteria**:
- Docker configuration optimized for production
- CI/CD pipeline runs tests and deploys automatically
- Error tracking captures issues without exposing sensitive data
- Vercel deployment configured with proper environment variables
- Security headers protect against common vulnerabilities
- Performance monitoring tracks Core Web Vitals
- Analytics respect user privacy while providing insights
- Staging environment mirrors production configuration

**Key Components**:
- `Dockerfile` - Multi-stage build configuration
- `docker-compose.yml` - Development and production orchestration
- `/.github/workflows/deploy.yml` - CI/CD pipeline
- `next.config.ts` - Production optimization and security headers
- `ErrorTracker` - Secure error reporting integration
- `PerformanceMonitor` - Core Web Vitals tracking
- `AnalyticsProvider` - Privacy-respecting analytics

## Technical Implementation

### Form Validation & Schemas
```typescript
// Comprehensive Zod schemas with cultural error messages
import { z } from 'zod';

export const LoginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters")
});

export const RegisterSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string()
    .min(8, "Password must be at least 8 characters")
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, "Password must include uppercase, lowercase, and number"),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"]
});

export const AnalysisUploadSchema = z.object({
  leftImage: z.instanceof(File).optional(),
  rightImage: z.instanceof(File).optional(),
}).refine((data) => data.leftImage || data.rightImage, {
  message: "Please upload at least one palm image"
});
```

### Security Implementation
```typescript
// CSRF Token Management
export const useCSRFToken = () => {
  const [csrfToken, setCsrfToken] = useState<string | null>(null);

  useEffect(() => {
    const fetchCSRFToken = async () => {
      try {
        const response = await api.get('/auth/csrf-token');
        setCsrfToken(response.data.csrf_token);
        
        // Set in meta tag for axios interceptor
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
          metaTag.setAttribute('content', response.data.csrf_token);
        }
      } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
      }
    };

    fetchCSRFToken();
  }, []);

  return csrfToken;
};

// Input Sanitization Hook
export const useSanitizedInput = () => {
  const sanitizeInput = useCallback((input: string): string => {
    return input
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+="[^"]*"/gi, '')
      .trim();
  }, []);

  const sanitizeObject = useCallback((obj: Record<string, any>) => {
    const sanitized = {};
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'string') {
        sanitized[key] = sanitizeInput(value);
      } else {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }, [sanitizeInput]);

  return { sanitizeInput, sanitizeObject };
};

// Session Validation with Auto-Refresh
export const useSessionValidation = () => {
  const { user, logout } = useAuthStore();
  
  useEffect(() => {
    const validateSession = async () => {
      if (!user) return;
      
      try {
        await api.get('/auth/validate-session');
      } catch (error) {
        if (error.response?.status === 401) {
          logout();
          router.push('/login');
        }
      }
    };

    // Validate session every 5 minutes
    const interval = setInterval(validateSession, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, logout]);
};
```

### Error Boundary Implementation
```typescript
// Cultural Error Boundary with Secure Reporting
export class CulturalErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Cultural Error Boundary:', error, errorInfo);
    // Send to error tracking service (without sensitive data)
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'exception', {
        description: error.message,
        fatal: false
      });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-saffron-50">
          <div className="text-center p-8">
            <div className="cultural-lotus-icon w-16 h-16 mx-auto mb-4 text-saffron-500" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Something went wrong
            </h2>
            <p className="text-gray-600 mb-4">
              We apologize for the inconvenience. Please try refreshing the page.
            </p>
            <Button onClick={() => window.location.reload()}>
              Refresh Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Enhanced Authentication Flow
```typescript
// Complete authentication with return-to functionality
const useAuthFlow = () => {
  const router = useRouter();
  const { login, register, isLoading, error } = useAuth();
  
  const handleLogin = async (credentials: LoginRequest) => {
    await login(credentials);
    const returnTo = sessionStorage.getItem('returnToAnalysis');
    if (returnTo) {
      sessionStorage.removeItem('returnToAnalysis');
      router.push(`/analysis/${returnTo}`);
    } else {
      router.push('/dashboard');
    }
  };
};
```

### Dashboard with Analytics
```typescript
// User dashboard with cultural analytics
export function UserDashboard() {
  const { user } = useAuth();
  const { data: stats } = useAnalyticsQuery();
  const { data: recentAnalyses } = useAnalysesQuery({ limit: 5 });
  
  return (
    <DashboardLayout>
      <WelcomeCard user={user} />
      <StatsOverview stats={stats} />
      <RecentAnalyses analyses={recentAnalyses} />
      <QuickActions />
    </DashboardLayout>
  );
}
```

### Analysis-Scoped Conversations
```typescript
// Conversation interface scoped to specific analysis
export function AnalysisConversations({ analysisId }: { analysisId: number }) {
  const [activeConversation, setActiveConversation] = useState<number>();
  const { conversations } = useConversationsQuery(analysisId);
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <ConversationSidebar 
        conversations={conversations}
        active={activeConversation}
        onSelect={setActiveConversation}
        analysisId={analysisId}
      />
      <div className="md:col-span-2">
        {activeConversation ? (
          <ChatInterface 
            conversationId={activeConversation}
            analysisId={analysisId}
          />
        ) : (
          <ConversationTemplates 
            onStartConversation={setActiveConversation}
            analysisId={analysisId}
          />
        )}
      </div>
    </div>
  );
}
```

### Advanced State Management
```typescript
// Global Loading State Management
export const useGlobalLoading = () => {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  
  const setLoading = useCallback((key: string, loading: boolean) => {
    setLoadingStates(prev => ({ ...prev, [key]: loading }));
  }, []);

  const isLoading = useCallback((key?: string) => {
    if (key) return loadingStates[key] || false;
    return Object.values(loadingStates).some(Boolean);
  }, [loadingStates]);

  return { setLoading, isLoading };
};

// Offline State Management for PWA
export const useOfflineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncQueue, setSyncQueue] = useState<PendingAction[]>([]);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      processSyncQueue();
    };
    
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const addToSyncQueue = useCallback((action: PendingAction) => {
    setSyncQueue(prev => [...prev, action]);
  }, []);

  return { isOnline, addToSyncQueue, syncQueue };
};
```

### PWA Configuration
```typescript
// Progressive Web App setup with advanced caching
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'google-fonts-cache',
        expiration: {
          maxEntries: 10,
          maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
        },
      },
    },
    {
      urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'google-fonts-webfonts',
        expiration: {
          maxEntries: 30,
          maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
        },
      },
    },
    {
      urlPattern: /\.(?:png|jpg|jpeg|svg)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'images',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
        },
      },
    },
    {
      urlPattern: /^\/api\/.*/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        expiration: {
          maxEntries: 200,
          maxAgeSeconds: 60 * 60 * 24, // 24 hours
        },
        networkTimeoutSeconds: 10,
      },
    },
  ],
});

module.exports = withPWA({
  // Next.js config
});
```

### Performance Optimization
```typescript
// Environment Configuration with Feature Flags
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  environment: process.env.NODE_ENV,
  isProduction: process.env.NODE_ENV === 'production',
  
  // Feature flags
  features: {
    pushNotifications: process.env.NEXT_PUBLIC_ENABLE_PUSH === 'true',
    analytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
    chatFeature: process.env.NEXT_PUBLIC_ENABLE_CHAT === 'true',
  },
  
  // Performance
  performance: {
    enableCaching: process.env.NEXT_PUBLIC_ENABLE_CACHING !== 'false',
    maxUploadSize: parseInt(process.env.NEXT_PUBLIC_MAX_UPLOAD_SIZE || '15728640'), // 15MB
    pollingInterval: parseInt(process.env.NEXT_PUBLIC_POLLING_INTERVAL || '2000'),
  },

  // Security
  security: {
    csrfEnabled: process.env.NEXT_PUBLIC_CSRF_ENABLED !== 'false',
    maxLoginAttempts: parseInt(process.env.NEXT_PUBLIC_MAX_LOGIN_ATTEMPTS || '5'),
    sessionTimeout: parseInt(process.env.NEXT_PUBLIC_SESSION_TIMEOUT || '3600000'), // 1 hour
  }
};

// Performance Monitoring
export const initializeMonitoring = () => {
  if (typeof window !== 'undefined') {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(sendToAnalytics);
      getFID(sendToAnalytics);
      getFCP(sendToAnalytics);
      getLCP(sendToAnalytics);
      getTTFB(sendToAnalytics);
    });
  }
};

const sendToAnalytics = (metric) => {
  if (config.features.analytics) {
    gtag('event', metric.name, {
      event_category: 'Web Vitals',
      value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
      non_interaction: true,
    });
  }
};
```

### Docker & CI/CD Configuration

**Frontend Dockerfile (Multi-stage Build)**:
```dockerfile
# Multi-stage build for optimal production image
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine AS production
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# Copy built application
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000
ENV PORT 3000
ENV NODE_ENV production

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
```

**CI/CD Pipeline (.github/workflows/frontend-deploy.yml)**:
```yaml
name: Frontend CI/CD Pipeline
on:
  push:
    branches: [main, staging]
    paths: ['frontend/**']
  pull_request:
    branches: [main]
    paths: ['frontend/**']

env:
  NODE_VERSION: '18'
  FRONTEND_DIR: './frontend'

jobs:
  test:
    name: Test Frontend
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: ${{ env.FRONTEND_DIR }}/package-lock.json
      
      - name: Install dependencies
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm ci
      
      - name: Run type checking
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm run type-check
          
      - name: Run linting
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm run lint
          
      - name: Run unit tests
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm run test -- --coverage --watchAll=false
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ${{ env.FRONTEND_DIR }}/coverage/lcov.info
          flags: frontend
          
      - name: Build application
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm run build
          
      - name: Run E2E tests
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm run test:e2e
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Run npm audit
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm audit --audit-level moderate
          
      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
          command: test

  build-and-deploy:
    name: Build and Deploy
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: ${{ env.FRONTEND_DIR }}/package-lock.json
      
      - name: Install dependencies
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm ci
          
      - name: Build for production
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.PRODUCTION_API_URL }}
          NEXT_PUBLIC_ENABLE_ANALYTICS: true
          
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ${{ env.FRONTEND_DIR }}
          vercel-args: '--prod'
          
      - name: Run post-deployment tests
        run: |
          cd ${{ env.FRONTEND_DIR }}
          npm run test:e2e:production
        env:
          E2E_BASE_URL: ${{ secrets.PRODUCTION_URL }}

  performance-audit:
    name: Performance Audit
    runs-on: ubuntu-latest
    needs: build-and-deploy
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v10
        with:
          configPath: './frontend/lighthouserc.js'
          uploadArtifacts: true
          temporaryPublicStorage: true
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

**Docker Compose Configuration**:
```yaml
# docker-compose.yml (Updated with frontend)
services:
  # Existing backend services...
  api:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app/data/dev.db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./app:/app/app
      - ./data:/app/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --save 20 1 --loglevel warning
    volumes:
      - redis_data:/data

  worker:
    build:
      context: .
      target: worker
    environment:
      - DATABASE_URL=sqlite:///app/data/dev.db
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - redis
    volumes:
      - ./app:/app/app
      - ./data:/app/data

  # New frontend service
  frontend:
    build:
      context: ./frontend
      target: development
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_ENABLE_ANALYTICS=false
      - NEXT_PUBLIC_ENABLE_PUSH=false
    depends_on:
      - api
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  redis_data:

# docker-compose.prod.yml (Production overrides)
services:
  api:
    build:
      target: production
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    ports:
      - "8000:8000"

  frontend:
    build:
      target: production
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
      - NEXT_PUBLIC_ENABLE_ANALYTICS=true
    ports:
      - "3000:3000"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - frontend
      - api
    restart: unless-stopped
```

**Next.js Production Configuration (next.config.ts)**:
```typescript
const nextConfig = {
  // Production optimizations
  output: 'standalone',
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', '@headlessui/react'],
  },
  
  // Image optimization
  images: {
    domains: ['localhost', process.env.NEXT_PUBLIC_API_URL?.replace(/https?:\/\//, '')].filter(Boolean),
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 31536000, // 1 year
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "img-src 'self' data: https:",
              "font-src 'self' https://fonts.gstatic.com",
              "connect-src 'self' ws: wss: https://www.google-analytics.com",
              "media-src 'self'",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-ancestors 'none'",
              "upgrade-insecure-requests"
            ].join('; '),
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
          },
        ],
      },
    ];
  },

  // Webpack optimizations
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      // Production optimizations
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...config.optimization.splitChunks.cacheGroups,
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
            enforce: true,
          },
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            enforce: true,
          },
        },
      };
    }
    return config;
  },

  // Environment-specific redirects
  async redirects() {
    return [
      {
        source: '/admin',
        destination: '/admin/dashboard',
        permanent: true,
      },
    ];
  },

  // Rewrites for API proxy (development only)
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

// PWA configuration
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  runtimeCaching: [
    // Cache strategies defined earlier...
  ],
});

module.exports = withPWA(nextConfig);
```

## Success Metrics

### Performance Targets
- **Lighthouse Score**: > 95 for Performance, Accessibility, Best Practices
- **First Contentful Paint**: < 1.5s on 3G networks
- **Time to Interactive**: < 3s on mobile devices
- **Bundle Size**: < 500KB gzipped total bundle size
- **Cache Hit Rate**: > 80% for returning users

### User Experience Metrics
- **Task Completion Rate**: > 95% for core user flows
- **Mobile Usability**: > 90% mobile-friendly score
- **Accessibility**: WCAG 2.1 AA compliance
- **Error Rate**: < 2% for critical user actions
- **User Retention**: > 60% return within 7 days

### Technical Quality
- **Test Coverage**: > 80% for components and critical paths
- **Type Safety**: 100% TypeScript coverage
- **Code Quality**: ESLint/Prettier compliance
- **Security**: No high or critical security vulnerabilities
- **Documentation**: All components documented with examples

## Risk Mitigation

### Technical Risks
- **Performance Issues**: Code splitting, lazy loading, bundle analysis
- **Mobile Compatibility**: Progressive enhancement, feature detection
- **Authentication Security**: Session validation, CSRF protection
- **API Integration**: Error boundaries, retry logic, timeout handling

### User Experience Risks
- **Complex Interfaces**: Progressive disclosure, user testing
- **Mobile Usability**: Touch target sizing, gesture support
- **Loading Times**: Skeleton screens, optimistic updates
- **Cultural Sensitivity**: Community feedback, cultural consulting

## Definition of Done

A Phase 3.75 feature is complete when:
1. ✅ All acceptance criteria are met with evidence
2. ✅ Component tests achieve > 80% coverage
3. ✅ E2E tests cover critical user flows
4. ✅ Performance benchmarks meet targets
5. ✅ Mobile experience tested on multiple devices
6. ✅ Accessibility requirements validated
7. ✅ Security review completed
8. ✅ Documentation updated with examples
9. ✅ Code review approved by team
10. ✅ Production deployment successful

This phase completes the frontend implementation, delivering a production-ready, mobile-first web application that provides an excellent user experience while honoring the cultural context of traditional Indian palmistry.