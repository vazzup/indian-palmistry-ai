# Indian Palmistry AI - Frontend

A modern, mobile-first Next.js frontend for the Indian Palmistry AI application. Built with cultural minimalist design principles and seamless integration with the enterprise-grade FastAPI backend.

## 🌟 Features

- **Cultural Design System**: Saffron-based color palette with Indian cultural elements
- **Mobile-First Experience**: Optimized for mobile devices with 44px touch targets
- **Authentication Flow**: Strategic login gate after analysis summary
- **Real-Time Updates**: Background job polling for AI analysis progress
- **Image Upload**: Mobile-optimized upload with drag & drop and camera support
- **TypeScript**: Full type safety across all components
- **Testing**: Comprehensive test suite with Vitest and React Testing Library

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running FastAPI backend (see main project README)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### Environment Setup

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🏗️ Architecture

### Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4 with cultural design system
- **State Management**: Zustand for auth, React state for local
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios with interceptors
- **Testing**: Vitest + React Testing Library + Playwright

### Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (public)/          # Public routes (no auth)
│   ├── (auth)/            # Authentication routes
│   └── (dashboard)/       # Protected routes
├── components/            # React components
│   ├── ui/               # Base UI components
│   ├── auth/             # Authentication components
│   ├── analysis/         # Analysis-specific components
│   └── layout/           # Layout components
├── lib/                  # Utilities and core logic
│   ├── api.ts           # API client
│   ├── auth.ts          # Auth store
│   ├── cultural-theme.ts # Design system
│   └── redis-jobs.ts    # Job polling
├── types/               # TypeScript definitions
└── __tests__/           # Test suite
```

## 🎨 Design System

### Cultural Color Palette

```css
/* Primary saffron scale */
--saffron-50: #fffaf0;
--saffron-500: #ff8000;  /* Primary brand color */
--saffron-900: #7a2900;

/* Cultural accents */
--turmeric: #f0b429;      /* Warm gold */
--vermillion: #e34234;    /* Sacred red */
--sandalwood: #d4a574;    /* Neutral warm */
--lotus: #e8b4d1;         /* Soft accent */
```

### Component Variants

All components support consistent sizing and variants:

- **Sizes**: `sm`, `md`, `lg`, `xl`
- **Variants**: `default`, `outline`, `ghost`, `destructive`

## 🔧 Development

### Available Scripts

```bash
# Development
npm run dev              # Start development server
npm run build           # Build for production
npm run start           # Start production server

# Code Quality
npm run lint            # Run ESLint
npm run lint:fix        # Fix ESLint errors
npm run type-check      # Run TypeScript checks
npm run format          # Format with Prettier

# Testing
npm test               # Run tests
npm run test:watch     # Run tests in watch mode
npm run test:coverage  # Generate coverage report
npm run test:e2e       # Run Playwright e2e tests
```

### Code Standards

- **TypeScript**: Strict mode enabled with comprehensive typing
- **ESLint**: Extended Next.js and TypeScript configs
- **Prettier**: Consistent code formatting
- **Testing**: Minimum 80% coverage for components

## 🧪 Testing

### Test Structure

```
__tests__/
├── components/
│   ├── ui/              # Base component tests
│   ├── auth/            # Auth component tests
│   └── analysis/        # Analysis component tests
├── lib/                 # Utility function tests
└── pages/               # Page component tests
```

### Running Tests

```bash
# Run all tests
npm test

# Watch mode during development
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

## 📱 Key Components

### UI Components

#### Button
```tsx
<Button variant="default" size="lg" loading={isSubmitting}>
  Submit
</Button>
```

#### Input
```tsx
<Input
  label="Email"
  type="email"
  error={errors.email}
  icon={<Mail />}
  showPasswordToggle
/>
```

### Analysis Components

#### MobileImageUpload
```tsx
<MobileImageUpload
  onUpload={handleFileUpload}
  maxFiles={2}
  maxSize={15}
  isUploading={uploadInProgress}
/>
```

#### BackgroundJobProgress
```tsx
<BackgroundJobProgress
  analysisId={analysis.id}
  onComplete={handleComplete}
  onError={handleError}
/>
```

### Authentication Components

#### LoginForm
```tsx
<LoginForm
  redirectTo="/dashboard"
  onSuccess={handleSuccess}
/>
```

#### LoginGate
```tsx
<LoginGate
  analysisId={analysisId}
  showFullFeatures={true}
/>
```

## 🔗 Backend Integration

### API Client

The frontend uses a configured Axios client with:

- **Base URL**: Configurable via environment variables
- **Session Cookies**: Automatic HTTP-only cookie handling
- **CSRF Protection**: Automatic CSRF token management
- **Error Handling**: Consistent error processing
- **Interceptors**: Request/response transformation

### Authentication Flow

1. **Public Analysis**: Upload and analyze without login
2. **Analysis Summary**: Public summary visible to all
3. **Login Gate**: Strategic prompt after summary
4. **Full Access**: Complete features post-authentication

### Background Jobs

Real-time polling system for long-running AI analysis:

```typescript
const { status, error, isPolling, startPolling } = useAnalysisJobPolling();

useEffect(() => {
  const cleanup = startPolling(analysisId);
  return cleanup;
}, [analysisId]);
```

## 🚢 Deployment

### Build Process

```bash
# Production build
npm run build

# Start production server
npm run start
```

### Environment Variables

```bash
# Required
NEXT_PUBLIC_API_URL=https://api.yourapp.com

# Optional
NEXT_PUBLIC_APP_ENV=production
```

### Vercel Deployment

This app is optimized for deployment on Vercel:

1. Connect your GitHub repository
2. Set environment variables
3. Deploy automatically on push

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Add tests for new components
3. Update documentation for new features
4. Ensure TypeScript strict mode compliance
5. Test on mobile devices

## 📄 License

This project is part of the Indian Palmistry AI application. See the main project LICENSE file for details.

## 🔮 Cultural Context

This frontend honors traditional Indian palmistry (Hast Rekha Shastra) through:

- **Saffron Color Scheme**: Sacred color in Indian culture
- **Minimalist Design**: Reflecting contemplative traditions
- **Respectful Messaging**: Culturally appropriate language
- **Sacred Symbolism**: Lotus-inspired loading animations

The design balances modern UX patterns with cultural authenticity to create an experience that feels both familiar and respectful of the ancient practice of palmistry.
