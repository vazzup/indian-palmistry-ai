# Phase 3.5: Frontend Development - User Interface & Experience

## Overview
**Phase 3.5** focuses on creating a modern, responsive, mobile-first frontend application that provides an intuitive user interface for the Indian Palmistry AI backend. This phase implements the cultural minimalist design system and correct user flow where analysis is available without login, but full results and conversations require authentication.

**Duration**: 2-3 weeks  
**Goal**: Create a production-ready Next.js frontend application with cultural design system, proper authentication gates, real-time features, and mobile-first experience

## Scope
- Mobile-first Next.js frontend application with cultural minimalist design
- Correct user flow: analysis without login → summary → login gate → full results
- Real-time palm analysis with background job status tracking
- Conversation system scoped to analyses (not standalone)
- User dashboard focused on analysis history and management
- Admin panel for system monitoring (Phase 4 priority)
- Progressive Web App (PWA) capabilities optimized for mobile
- Integration with FastAPI backend including Redis sessions and background jobs

## Deliverables
- ✅ Complete Next.js application with TypeScript and mobile-first design
- ✅ Cultural minimalist UI/UX with saffron-based design system
- ✅ Correct authentication flow: analysis without login → login gate → full access
- ✅ Real-time palm analysis interface with background job tracking
- ✅ Conversation system properly scoped to analyses
- ✅ User dashboard with analysis history and management
- ✅ Session management with Redis integration
- ✅ PWA with offline capabilities optimized for mobile
- ✅ Comprehensive error handling and culturally appropriate loading states

## Features & Tasks

### 1. Foundation & Setup
**Purpose**: Establish mobile-first frontend with cultural design system and correct tech stack

**Tasks**:
1. Set up Next.js 14 with TypeScript and App Router
2. Configure Tailwind CSS with cultural minimalist design system (saffron-based)
3. Implement custom UI components following cultural design principles
4. Configure ESLint, Prettier, and Husky for code quality
5. Set up environment configuration for dev/staging/prod
6. Configure API client with axios for FastAPI backend integration
7. Set up Redis session management and background job status tracking
8. Implement mobile-first responsive layout system with iconographic navigation

**Acceptance Criteria**:
- Next.js application runs with TypeScript support
- Cultural minimalist design system implemented with saffron-based colors
- Mobile-first responsive design with 44px touch targets
- Custom UI components follow cultural design principles
- API client integrates with FastAPI backend and handles Redis sessions
- Background job status tracking works with Redis
- Environment configuration supports dev/staging/prod
- Hot reloading and development tools work properly

### 2. Authentication & User Management
**Purpose**: Implement correct authentication flow with login gate after analysis summary

**Tasks**:
1. Create login and registration forms with cultural design and mobile-first validation
2. Implement Redis-based session management with HTTP-only cookies
3. Build password reset flow (email delivery can be stubbed for MVP)
4. Create login gate component that appears after analysis summary
5. Add user profile management interface (minimal for MVP)
6. Implement CSRF token handling for session-based auth
7. Build logout functionality with Redis session cleanup
8. Add culturally appropriate authentication error handling and feedback

**Acceptance Criteria**:
- Users can upload and analyze without login, see summary, then hit login gate
- Login/registration forms follow cultural design with proper mobile validation
- Redis session management works correctly with FastAPI backend
- Login gate appears after analysis summary, blocks access to full results
- Session management persists across page refreshes
- CSRF protection works with session-based authentication
- Authentication errors display culturally appropriate messaging
- Logout cleans up Redis sessions properly

### 3. Palm Analysis Interface
**Purpose**: Mobile-first palm image upload with background job processing and login gate

**Tasks**:
1. Build mobile-optimized drag-and-drop upload component (up to 2 images: left/right)
2. Create image preview with basic validation (JPEG/PNG, max 15MB, magic bytes)
3. Implement real-time background job progress tracking via Redis
4. Build analysis summary display (visible without login)
5. Create login gate component that appears after summary
6. Build full analysis results display (post-login) with cultural styling
7. Add mobile camera capture with proper constraints
8. Implement proper error states for upload and analysis failures

**Acceptance Criteria**:
- Mobile-optimized upload supports up to 2 images (left/right palm)
- File validation enforces JPEG/PNG, max 15MB, proper magic bytes
- Background job progress tracks via Redis with cultural loading animations
- Analysis summary displays without login requirement
- Login gate appears after summary, blocks access to full results
- Full results display with cultural minimalist design (post-login)
- Mobile camera capture works with proper image constraints
- Error states provide clear, culturally appropriate feedback

**Key Components**:
- `MobileImageUpload` - Mobile-first upload with validation (up to 2 images)
- `BackgroundJobProgress` - Redis-based job status tracking
- `AnalysisSummary` - Brief summary visible without login
- `LoginGate` - Authentication gate after summary
- `AnalysisResults` - Full results with cultural design (post-login)
- `AnalysisHistory` - Mobile-first analysis list (page size 5)

### 4. Interactive Conversation System
**Purpose**: Mobile-first conversation system scoped to analyses (post-login only)

**Tasks**:
1. Build mobile-optimized chat interface scoped to specific analysis
2. Implement conversation history tied to analysis context
3. Add background job processing for AI responses to prevent timeouts
4. Create conversation list within analysis detail (most recent first, page size 5)
5. Implement conversation CRUD: start new, continue existing, rename, delete
6. Add proper loading states for background AI processing
7. Build conversation export (basic text format for MVP)
8. Ensure conversations are only accessible through analysis context

**Acceptance Criteria**:
- Conversations are only accessible within analysis context (not standalone)
- Mobile-optimized chat interface with cultural design
- Background processing prevents timeouts for AI responses
- Conversation list shows most recent first with pagination (size 5)
- Users can start new conversations, continue existing ones, rename, and delete
- Proper loading states during background AI processing
- Basic export functionality (text format for MVP)
- Authentication required - conversations not accessible without login

**Key Components**:
- `AnalysisChatInterface` - Chat UI scoped to analysis
- `MessageBubble` - Mobile-optimized message display with cultural styling
- `ConversationList` - Paginated list within analysis (size 5)
- `BackgroundJobMessage` - Loading states for AI processing
- `ConversationExport` - Basic text export for MVP

### 5. User Dashboard & Analysis Management
**Purpose**: Mobile-first dashboard focused on analysis history and management (MVP scope)

**Tasks**:
1. Build mobile-optimized dashboard with cultural design
2. Create analysis history list (most recent first, page size 5)
3. Implement basic user preferences (minimal for MVP)
4. Add analysis detail view with full results and conversation access
5. Build analysis deletion with cascading conversation cleanup
6. Add basic user profile management
7. Implement cultural theme with light mode (dark mode in Phase 4)
8. Create simple data export for user analyses (GDPR compliance)

**Acceptance Criteria**:
- Mobile-optimized dashboard with cultural minimalist design
- Analysis history shows most recent first with pagination (size 5)
- Analysis detail provides full results and conversation access (post-login)
- Analysis deletion cascades to remove associated conversations
- Basic user preferences work with cultural theme
- Simple data export meets GDPR requirements (basic text/JSON format)
- Cultural light theme implemented (dark mode deferred to Phase 4)
- Dashboard navigation follows iconographic principles

**Key Components**:
- `MobileDashboard` - Cultural design dashboard
- `AnalysisHistoryList` - Paginated analysis list (size 5)
- `AnalysisDetailView` - Full results with conversation access
- `BasicPreferences` - Minimal user settings for MVP
- `CulturalTheme` - Saffron-based design system
- `BasicDataExport` - Simple GDPR-compliant export

### 6. Admin Panel & Monitoring (Deferred to Phase 4)
**Purpose**: Basic administrative interface - simplified for MVP, full implementation in Phase 4

**Tasks** (Minimal MVP scope):
1. Create basic admin login and authentication
2. Build simple user list with basic management
3. Add basic system health endpoint consumption
4. Implement Redis job queue monitoring (basic view)
5. Create simple cost tracking display (OpenAI usage)
6. Add basic error log viewing
7. Defer advanced monitoring to Phase 4
8. Focus on essential admin functions only

**Acceptance Criteria** (MVP scope):
- Basic admin authentication works
- Simple user list with essential management functions
- Basic system health display from backend endpoints
- Redis job queue status visible (simple view)
- OpenAI cost tracking shows usage and spending
- Basic error log viewing for troubleshooting
- Admin functions work with cultural design system
- Advanced monitoring deferred to Phase 4

**Key Components** (MVP scope):
- `BasicAdminDashboard` - Simple system overview
- `BasicUserManagement` - Essential user controls
- `HealthDisplay` - Basic system health metrics
- `JobQueueMonitor` - Simple Redis queue status
- `CostTracker` - OpenAI usage and cost display
- `ErrorLogViewer` - Basic error log interface

### 7. Progressive Web App (PWA) Features
**Purpose**: Native app-like experience with offline capabilities

**Tasks**:
1. Configure PWA manifest and service worker
2. Implement offline functionality for key features
3. Add push notification support
4. Create app installation prompts
5. Implement background sync for uploads
6. Add app shortcuts and widget support
7. Optimize performance with caching strategies
8. Create splash screen and app icons

**Acceptance Criteria**:
- App can be installed on mobile and desktop
- Core features work offline
- Push notifications engage users effectively
- Background sync ensures data reliability
- App performance meets PWA standards
- Installation prompts appear at appropriate times
- Caching strategies optimize load times

### 8. Real-time Features & WebSockets
**Purpose**: Real-time updates and live communication

**Tasks**:
1. Set up WebSocket client for real-time connections
2. Implement real-time analysis progress updates
3. Add live chat functionality with typing indicators
4. Create real-time notification system
5. Build live system status indicators
6. Implement real-time queue monitoring
7. Add collaborative features for shared analyses
8. Create live admin monitoring dashboards

**Acceptance Criteria**:
- WebSocket connections are stable and reliable
- Analysis progress updates in real-time
- Chat feels responsive with immediate feedback
- Notifications appear instantly across devices
- System status reflects current health
- Admin monitoring shows live metrics
- Connection failures are handled gracefully

## Technical Implementation

### Technology Stack (Aligned with tech-stack.md)
```json
{
  "frontend": {
    "framework": "Next.js 14",
    "language": "TypeScript", 
    "styling": "Tailwind CSS with Cultural Design System",
    "components": "Custom components following cultural principles",
    "state": "Built-in React state + custom hooks",
    "forms": "React Hook Form + Zod validation",
    "http": "Axios for FastAPI integration",
    "animations": "CSS transitions with cultural elements"
  },
  "backend_integration": {
    "api": "FastAPI REST endpoints",
    "sessions": "Redis-based HTTP-only cookies",
    "jobs": "Background job status via Redis polling", 
    "files": "Local filesystem storage",
    "auth": "Session-based with CSRF protection"
  },
  "development": {
    "linting": "ESLint + Prettier", 
    "testing": "Vitest + React Testing Library",
    "e2e": "Playwright",
    "validation": "Zod schemas",
    "hooks": "Husky for pre-commit"
  }
}
```

### Project Structure (Corrected for User Flow)
```
frontend/
├── app/                    # Next.js App Router
│   ├── (public)/          # Public routes (no auth required)
│   │   ├── page.tsx       # Landing/upload page
│   │   └── analysis/[id]/summary/  # Analysis summary (pre-login)
│   ├── (auth)/            # Authentication routes  
│   │   ├── login/         # Login page
│   │   ├── register/      # Registration page
│   │   └── reset/         # Password reset (stubbed)
│   ├── (dashboard)/       # Protected routes (post-login)
│   │   ├── dashboard/     # User dashboard
│   │   ├── analyses/      # Analysis history list
│   │   │   └── [id]/      # Analysis detail with conversations
│   │   └── profile/       # Basic user profile
│   ├── admin/             # Admin panel (basic for MVP)
│   │   ├── dashboard/     # Basic admin dashboard
│   │   └── users/         # Basic user management
│   └── api/               # API route handlers (minimal, mostly proxy to FastAPI)
├── components/            # Reusable components with cultural design
│   ├── ui/               # Custom UI components (cultural design system)
│   ├── auth/             # Authentication components
│   ├── analysis/         # Analysis upload, summary, results
│   ├── conversation/     # Conversation components (scoped to analysis)
│   ├── dashboard/        # Dashboard components
│   └── layout/           # Layout components
├── lib/                  # Utilities and configurations
│   ├── api.ts           # Axios client for FastAPI
│   ├── auth.ts          # Session management utilities
│   ├── redis-jobs.ts    # Background job polling utilities
│   ├── cultural-theme.ts # Cultural design system
│   ├── utils.ts         # Helper functions
│   └── validations.ts   # Zod schemas
├── hooks/               # Custom React hooks
├── types/               # TypeScript definitions
├── styles/              # Cultural CSS and Tailwind config
└── public/              # Static assets and PWA manifest
```

### Key Components Implementation

#### Mobile-First Analysis Upload Component
```typescript
// components/analysis/MobileImageUpload.tsx
export function MobileImageUpload({ onUpload }: { onUpload: (files: File[]) => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [previews, setPreviews] = useState<{left?: string, right?: string}>({});
  const [isValidating, setIsValidating] = useState(false);

  const validateFiles = async (files: File[]) => {
    setIsValidating(true);
    // Validate: JPEG/PNG, max 15MB, check magic bytes
    const validFiles = await Promise.all(
      files.map(async (file) => {
        if (!['image/jpeg', 'image/png'].includes(file.type)) return null;
        if (file.size > 15 * 1024 * 1024) return null; // 15MB limit
        
        // Check magic bytes (basic validation)
        const buffer = await file.arrayBuffer();
        const bytes = new Uint8Array(buffer);
        const isValidImage = 
          (bytes[0] === 0xFF && bytes[1] === 0xD8) || // JPEG
          (bytes[0] === 0x89 && bytes[1] === 0x50); // PNG
        
        return isValidImage ? file : null;
      })
    );
    setIsValidating(false);
    return validFiles.filter(Boolean) as File[];
  };

  const handleUpload = async (files: File[]) => {
    if (files.length > 2) {
      // Show error: Maximum 2 images (cultural error messaging)
      return;
    }
    
    const validFiles = await validateFiles(files);
    if (validFiles.length === 0) {
      // Show error: Invalid file format or size
      return;
    }
    
    onUpload(validFiles);
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Mobile-optimized upload interface with cultural styling */}
      <div 
        className={`
          border-2 border-dashed rounded-lg p-6 transition-all duration-200
          min-h-[200px] flex flex-col items-center justify-center
          ${isDragging 
            ? 'border-saffron bg-saffron/5 scale-[1.02]' 
            : 'border-gray-300 hover:border-saffron/50'
          }
        `}
        style={{ touchAction: 'none' }} // Prevent scroll on mobile drag
      >
        {/* Cultural palm icon and upload messaging */}
        <div className="text-center space-y-4">
          <div className="cultural-palm-icon w-16 h-16 mx-auto text-saffron/60" />
          <h3 className="text-lg font-medium text-gray-900">
            Upload Your Palm Images
          </h3>
          <p className="text-sm text-gray-600">
            Up to 2 images • JPEG or PNG • Max 15MB each
          </p>
        </div>
      </div>
    </div>
  );
}
```

#### Background Job Progress Component
```typescript
// components/analysis/BackgroundJobProgress.tsx
export function BackgroundJobProgress({ analysisId }: { analysisId: string }) {
  const [jobStatus, setJobStatus] = useState<{
    status: 'queued' | 'processing' | 'completed' | 'failed';
    progress?: number;
    error?: string;
  }>({ status: 'queued' });
  
  useEffect(() => {
    // Poll Redis job status via FastAPI endpoint (no WebSocket needed for MVP)
    const pollJobStatus = async () => {
      try {
        const response = await api.get(`/api/v1/analyses/${analysisId}/job-status`);
        setJobStatus(response.data);
        
        // If completed or failed, stop polling
        if (['completed', 'failed'].includes(response.data.status)) {
          return;
        }
        
        // Continue polling every 2 seconds
        setTimeout(pollJobStatus, 2000);
      } catch (error) {
        console.error('Failed to fetch job status:', error);
        setTimeout(pollJobStatus, 5000); // Retry after 5 seconds on error
      }
    };
    
    pollJobStatus();
  }, [analysisId]);

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'queued': return 'Your palm reading is queued...';
      case 'processing': return 'Our AI is analyzing your palm...'; 
      case 'completed': return 'Analysis complete!';
      case 'failed': return 'Analysis failed. Please try again.';
      default: return 'Processing...';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="text-center space-y-4">
        {/* Cultural loading spinner */}
        <div className="cultural-spinner w-12 h-12 mx-auto" />
        
        <h3 className="text-lg font-medium text-gray-900">
          Reading Your Palm
        </h3>
        
        {jobStatus.progress && (
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-saffron h-2 rounded-full transition-all duration-300"
              style={{ width: `${jobStatus.progress}%` }}
            />
          </div>
        )}
        
        <p className="text-sm text-gray-600">
          {getStatusMessage(jobStatus.status)}
        </p>
        
        {jobStatus.error && (
          <p className="text-sm text-red-600">
            {jobStatus.error}
          </p>
        )}
      </div>
    </div>
  );
}
```

#### Analysis-Scoped Chat Interface Component
```typescript
// components/conversation/AnalysisChatInterface.tsx
export function AnalysisChatInterface({ 
  analysisId, 
  conversationId 
}: { 
  analysisId: string; 
  conversationId?: string; 
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [backgroundJobId, setBackgroundJobId] = useState<string | null>(null);
  
  // Load conversation history on mount
  useEffect(() => {
    if (conversationId) {
      loadConversationHistory();
    }
  }, [conversationId]);
  
  const loadConversationHistory = async () => {
    try {
      const response = await api.get(`/api/v1/analyses/${analysisId}/conversations/${conversationId}`);
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };
  
  const sendMessage = async () => {
    if (!newMessage.trim()) return;
    
    setIsSending(true);
    const userMessage = {
      content: newMessage,
      is_ai: false,
      created_at: new Date().toISOString()
    };
    
    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    const messageContent = newMessage;
    setNewMessage('');
    
    try {
      // Send message - this triggers background job processing
      const response = await api.post(
        `/api/v1/analyses/${analysisId}/conversations/${conversationId}/talk`,
        { message: messageContent }
      );
      
      // Get background job ID to track AI response
      setBackgroundJobId(response.data.job_id);
      
      // Poll for AI response completion
      pollForAIResponse(response.data.job_id);
      
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsSending(false);
    }
  };
  
  const pollForAIResponse = async (jobId: string) => {
    try {
      const response = await api.get(`/api/v1/background-jobs/${jobId}/status`);
      
      if (response.data.status === 'completed') {
        // Job complete, fetch the AI response
        const aiResponse = response.data.result;
        setMessages(prev => [...prev, aiResponse]);
        setBackgroundJobId(null);
      } else if (response.data.status === 'failed') {
        // Handle job failure
        setBackgroundJobId(null);
        // Show error message
      } else {
        // Continue polling
        setTimeout(() => pollForAIResponse(jobId), 2000);
      }
    } catch (error) {
      console.error('Failed to check job status:', error);
      setTimeout(() => pollForAIResponse(jobId), 5000);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border">
      {/* Header showing analysis context */}
      <div className="border-b border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-900">
          Palm Reading Conversation
        </h3>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.is_ai ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.is_ai
                  ? 'bg-gray-100 text-gray-900'
                  : 'bg-saffron text-white'
              }`}
            >
              <p className="text-sm">{message.content}</p>
            </div>
          </div>
        ))}
        
        {/* Show loading state when AI is processing */}
        {backgroundJobId && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <div className="cultural-spinner w-4 h-4" />
                <span className="text-sm text-gray-600">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about your palm reading..."
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-saffron focus:border-saffron"
            disabled={isSending || !!backgroundJobId}
          />
          <button
            onClick={sendMessage}
            disabled={isSending || !!backgroundJobId || !newMessage.trim()}
            className="bg-saffron text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-saffron/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

### API Integration Layer
```typescript
// lib/api.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // Include cookies
});

// Request interceptor for CSRF tokens
api.interceptors.request.use((config) => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

// Response interceptor for auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### State Management
```typescript
// stores/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      
      login: async (email, password) => {
        const response = await api.post('/auth/login', { email, password });
        set({ user: response.data.user, isAuthenticated: true });
      },
      
      logout: async () => {
        await api.post('/auth/logout');
        set({ user: null, isAuthenticated: false });
      },
      
      checkAuth: async () => {
        try {
          const response = await api.get('/auth/me');
          set({ user: response.data, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false });
        }
      }
    }),
    { name: 'auth-store' }
  )
);
```

## Testing Strategy

### Component Testing
```typescript
// __tests__/components/ImageUpload.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ImageUpload } from '@/components/analysis/ImageUpload';

describe('ImageUpload', () => {
  it('accepts image files via drag and drop', async () => {
    const onUpload = jest.fn();
    render(<ImageUpload onUpload={onUpload} />);
    
    const dropzone = screen.getByRole('button');
    const file = new File(['dummy'], 'palm.jpg', { type: 'image/jpeg' });
    
    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } });
    
    expect(onUpload).toHaveBeenCalledWith([file]);
  });
});
```

### E2E Testing
```typescript
// e2e/analysis-flow.spec.ts
import { test, expect } from '@playwright/test';

test('complete analysis flow', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password123');
  await page.click('[data-testid="login-button"]');
  
  await page.goto('/analysis/upload');
  await page.setInputFiles('[data-testid="file-input"]', 'test-images/palm.jpg');
  await page.click('[data-testid="upload-button"]');
  
  await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
  await page.waitForSelector('[data-testid="analysis-results"]', { timeout: 60000 });
  
  expect(await page.textContent('[data-testid="analysis-summary"]')).toContain('palm');
});
```

## Performance Optimization

### Code Splitting
```typescript
// Lazy load heavy components
const AdminDashboard = lazy(() => import('@/components/admin/AdminDashboard'));
const AnalysisComparison = lazy(() => import('@/components/analysis/AnalysisComparison'));

// Route-based splitting
const ChatPage = lazy(() => import('@/app/chat/[id]/page'));
```

### Image Optimization
```typescript
// Next.js Image component with optimization
import Image from 'next/image';

export function OptimizedImage({ src, alt, ...props }) {
  return (
    <Image
      src={src}
      alt={alt}
      quality={85}
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
      {...props}
    />
  );
}
```

### Caching Strategy
```typescript
// React Query configuration
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
```

## Success Metrics

### User Experience Metrics
- ✅ First Contentful Paint < 1.5s
- ✅ Largest Contentful Paint < 2.5s
- ✅ Cumulative Layout Shift < 0.1
- ✅ Time to Interactive < 3s
- ✅ 95% user tasks completed successfully

### Technical Metrics
- ✅ 100% TypeScript coverage
- ✅ 90%+ component test coverage
- ✅ Lighthouse score > 90
- ✅ Bundle size < 500KB gzipped
- ✅ Error rate < 1%

### Feature Adoption
- ✅ 80%+ users complete palm analysis
- ✅ 60%+ users engage with chat feature
- ✅ 40%+ users customize preferences
- ✅ 90%+ mobile compatibility score

## Risk Mitigation

### Technical Risks
- **API Integration Issues**: Comprehensive API mocking and error handling
- **Performance Problems**: Code splitting, lazy loading, optimization
- **Browser Compatibility**: Progressive enhancement, polyfills
- **Real-time Connection Issues**: Reconnection logic, fallback mechanisms

### User Experience Risks
- **Complex Interface**: User testing, progressive disclosure
- **Mobile Usability**: Responsive design, touch-friendly interactions
- **Accessibility Issues**: WCAG compliance, screen reader testing
- **Loading Times**: Skeleton screens, optimistic updates

## Definition of Done

A frontend feature is considered complete when:
1. ✅ Component is built with TypeScript and proper typing
2. ✅ Responsive design works on all device sizes
3. ✅ Component tests are written and passing
4. ✅ Accessibility standards are met (WCAG 2.1)
5. ✅ Integration with backend APIs is tested
6. ✅ Error states and loading states are handled
7. ✅ Performance benchmarks are met
8. ✅ Code review is completed
9. ✅ E2E tests cover critical user flows
10. ✅ Feature works in all supported browsers
11. ✅ Documentation is updated
12. ✅ Design system consistency maintained

This frontend phase creates a modern, accessible, and performant user interface that fully leverages the enterprise-grade backend system built in Phases 1-3.