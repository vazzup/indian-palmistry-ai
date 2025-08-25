# Indian Palmistry AI

An AI-powered application for traditional Indian palmistry readings using OpenAI's Vision API and natural language processing.

## Overview

This project combines ancient Indian palmistry wisdom (Hast Rekha Shastra) with modern AI technology to provide personalized palm readings. Users can upload images of their palms and receive detailed analyses based on traditional palmistry principles, then engage in conversations about their readings.

## 🚀 Current Status: Phase 3.75 Complete - Fully Operational

The application is now a **fully operational, production-ready** Indian Palmistry AI platform with complete backend and frontend integration:

### Backend (Enterprise-Grade)
- ✅ Complete user authentication system
- ✅ AI-powered palm analysis using OpenAI GPT-4o-mini
- ✅ Background job processing for scalable analysis
- ✅ Conversation interface with contextual memory
- ✅ Secure image upload and processing
- ✅ Advanced analytics and monitoring
- ✅ Multi-level rate limiting and security
- ✅ User dashboard with personalized insights
- ✅ Database optimization and performance monitoring
- ✅ Comprehensive caching and queue management
- ✅ GDPR-compliant data export

### Frontend (PWA Complete)
- ✅ **Next.js 14 with TypeScript**: Modern React framework with cultural design system
- ✅ **Mobile-First PWA**: Progressive Web App with offline support and installation
- ✅ **Advanced Security**: CSRF protection, input sanitization, and secure forms
- ✅ **Performance Monitoring**: Real-time Core Web Vitals tracking
- ✅ **Offline Capabilities**: Background sync queue with localStorage persistence
- ✅ **Cultural Design**: Saffron-based minimalist design with Indian cultural elements
- ✅ **Component Architecture**: Comprehensive UI component library with documentation
- ✅ **Testing Suite**: 100+ tests covering all components and functionality

### System Integration
- ✅ **Backend Services**: API (port 8000), Redis, Database all healthy
- ✅ **Frontend Application**: Next.js dev server running on port 3000
- ✅ **Full Workflow**: Image upload → AI analysis → Progress tracking → Results
- ✅ **Production Ready**: Documented, tested, and optimized for deployment

### Deployment & Operations
- ✅ **One-Command Startup**: Complete application stack with `./start.sh`
- ✅ **Management Scripts**: Start, stop, restart, logs, and health check tools
- ✅ **Automated Setup**: Environment configuration and dependency checking
- ✅ **Health Monitoring**: Comprehensive service health validation
- ✅ **Log Management**: Individual and aggregate service log viewing
- ✅ **Error Recovery**: Graceful error handling and recovery procedures

## Features

### 🔮 Advanced Palmistry Features
- **AI Palm Analysis**: Upload palm images for instant AI-powered readings
- **Traditional Indian Palmistry**: Based on authentic Hast Rekha Shastra principles
- **Specialized Line Analysis**: 8 different palm line types (Life, Love, Head, Fate, Health, Career, Marriage, Money)
- **Multi-Analysis Comparison**: Temporal analysis comparing multiple readings
- **Summary & Full Reports**: Public summaries with detailed reports for registered users
- **Multi-Image Support**: Analyze both left and right palm (up to 2 images)
- **Real-time Processing**: Background job processing with status polling

### 💬 Enhanced Interactive Experience  
- **Context-Aware Conversations**: AI responses with conversation memory
- **Conversation Templates**: Pre-built templates for common topics (life insights, relationships, career)
- **Full-Text Search**: Search across all conversations and messages
- **Export Capabilities**: Export conversations in JSON, Markdown, or Text formats
- **Message History**: Complete conversation history with pagination
- **Analysis-Scoped Chats**: Separate conversations for each palm reading

### 👤 Advanced User Management
- **User Dashboard**: Comprehensive analytics and personalized insights
- **User Preferences**: Theme, notifications, privacy settings, and language preferences
- **Achievement System**: Milestone tracking with unlocked achievements
- **Usage Statistics**: Detailed analytics over configurable periods
- **GDPR Data Export**: Complete user data export for compliance
- **Analysis History**: View and manage all your previous palm readings with trends

### 🛡️ Enterprise Security & Performance
- **Multi-Level Rate Limiting**: Global, user, IP, and endpoint-specific limits
- **Adaptive Security**: Threat detection with IP reputation and pattern analysis
- **Brute Force Protection**: Automatic blocking with suspicious activity detection
- **File Security Validation**: Magic byte validation and secure upload processing
- **Database Optimization**: Performance indexes and query optimization
- **Advanced Caching**: Redis-based multi-operation caching with intelligent invalidation
- **System Monitoring**: Real-time resource monitoring and health checks

## Technology Stack

### Backend
- **Framework**: Python 3.11, FastAPI, SQLAlchemy (async)
- **AI/ML**: OpenAI GPT-4o-mini Vision API
- **Database**: SQLite (dev), PostgreSQL/Supabase (prod)
- **Caching & Jobs**: Redis, Celery
- **Authentication**: Session-based with Redis, bcrypt
- **Infrastructure**: Docker, Docker Compose, multi-stage builds
- **Image Processing**: Pillow, thumbnail generation
- **Monitoring**: psutil for system metrics, custom analytics
- **Security**: Multi-layer rate limiting, threat detection
- **API Documentation**: Auto-generated OpenAPI/Swagger

### Frontend
- **Framework**: Next.js 14 with App Router, TypeScript
- **Styling**: Tailwind CSS with cultural design system
- **UI Components**: Custom component library with cultural elements
- **State Management**: Zustand for auth, React state for local
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios with interceptors and session management
- **Testing**: Vitest + React Testing Library + Playwright
- **PWA**: Service Worker, offline support, background sync
- **Performance**: Core Web Vitals tracking, optimization
- **Security**: CSRF protection, input sanitization, secure forms

## Project Structure

```
indian-palmistry-ai/
├── app/                    # Main application code
│   ├── api/               # API endpoints
│   │   └── v1/            # API version 1
│   │       ├── auth.py    # Authentication endpoints
│   │       ├── analyses.py # Palm analysis endpoints
│   │       ├── conversations.py # Conversation endpoints
│   │       └── enhanced_endpoints.py # Phase 3 enhanced features
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── database.py    # Database setup
│   │   ├── redis.py       # Redis integration
│   │   ├── celery_app.py  # Background jobs
│   │   ├── cache.py       # Advanced Redis caching service
│   │   └── logging.py     # Structured logging
│   ├── middleware/        # Custom middleware
│   │   └── rate_limiting.py # Multi-level rate limiting & security
│   ├── models/            # SQLAlchemy models
│   │   ├── user.py        # User authentication
│   │   ├── analysis.py    # Palm analysis
│   │   ├── conversation.py # Conversations
│   │   └── message.py     # Chat messages
│   ├── schemas/           # Pydantic schemas
│   │   ├── auth.py        # Authentication schemas
│   │   ├── analysis.py    # Analysis schemas
│   │   └── conversation.py # Conversation schemas
│   ├── services/          # Business logic
│   │   ├── user_service.py # User management
│   │   ├── analysis_service.py # Analysis lifecycle
│   │   ├── conversation_service.py # Chat management
│   │   ├── openai_service.py # AI integration
│   │   ├── image_service.py # Image processing
│   │   ├── password_service.py # Security utilities
│   │   ├── advanced_palm_service.py # Specialized palm analysis
│   │   ├── enhanced_conversation_service.py # Context-aware conversations
│   │   ├── monitoring_service.py # System monitoring & analytics
│   │   ├── user_dashboard_service.py # User dashboard & preferences
│   │   └── database_optimization_service.py # DB performance & optimization
│   ├── utils/             # Utilities
│   │   └── pagination.py  # Advanced filtering & pagination
│   ├── tasks/             # Background tasks
│   │   └── analysis_tasks.py # AI processing tasks
│   └── dependencies/      # FastAPI dependencies
│       └── auth.py        # Authentication dependencies
├── alembic/               # Database migrations
│   └── versions/          # Migration files including performance indexes
├── tests/                 # Comprehensive test suite
│   ├── services/          # Service layer tests
│   ├── middleware/        # Middleware tests
│   ├── utils/            # Utility tests
│   └── api/              # API endpoint tests
├── frontend/              # Next.js Progressive Web App
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   │   ├── (public)/  # Public routes (analysis upload)
│   │   │   ├── (auth)/    # Authentication pages
│   │   │   └── (dashboard)/ # Protected dashboard routes
│   │   ├── components/    # React components
│   │   │   ├── ui/        # Core UI components (Button, Input, Card, etc.)
│   │   │   ├── auth/      # Authentication components (LoginForm, RegisterForm)
│   │   │   ├── analysis/  # Analysis components (MobileImageUpload)
│   │   │   ├── conversation/ # Chat components
│   │   │   ├── layout/    # Layout components
│   │   │   ├── dashboard/ # Dashboard components
│   │   │   └── providers/ # Context providers (Security, Performance)
│   │   ├── hooks/         # Custom React hooks
│   │   │   ├── useCSRF.ts # CSRF token management
│   │   │   ├── useOffline.ts # PWA offline functionality
│   │   │   └── usePerformanceMonitoring.ts # Core Web Vitals
│   │   ├── lib/           # Utilities and core logic
│   │   │   ├── api.ts     # API client with session management
│   │   │   ├── auth.ts    # Authentication store (Zustand)
│   │   │   ├── cultural-theme.ts # Design system utilities
│   │   │   ├── redis-jobs.ts # Background job polling
│   │   │   └── security.ts # Security utilities (sanitization)
│   │   └── types/         # TypeScript definitions
│   ├── __tests__/         # Frontend test suite (100+ tests)
│   │   ├── components/    # Component tests
│   │   ├── hooks/         # Hook tests
│   │   └── lib/           # Utility tests
│   ├── docs/              # Component documentation
│   │   ├── components/    # Component API docs
│   │   └── hooks/         # Hook documentation
│   ├── e2e/               # End-to-end tests (Playwright)
│   ├── public/            # Static assets and PWA manifest
│   ├── package.json       # Frontend dependencies
│   ├── next.config.ts     # Next.js configuration
│   ├── tailwind.config.ts # Tailwind CSS with cultural theme
│   ├── playwright.config.ts # E2E testing configuration
│   └── vitest.config.ts   # Unit testing configuration
├── docs/                  # Documentation
│   ├── phases/            # Implementation phase documentation
│   └── phase-3-code-documentation.md # Phase 3 implementation details
├── data/                  # Local data storage
└── docker-compose.yml     # Multi-service setup
```

## 🚀 Quick Start - One Command Setup

### **Easy Startup** (Recommended)

```bash
# Start everything with one command
./start.sh
```

**That's it!** The script will automatically:
- Check prerequisites (Docker, Node.js)
- Start all backend services (API, Redis, Worker)
- Run database migrations
- Start frontend application
- Open the app at http://localhost:3000

### **Management Commands**

```bash
./start.sh     # Start all services
./stop.sh      # Stop all services  
./restart.sh   # Restart all services
./logs.sh      # View all logs
./logs.sh api  # View specific service logs
./health.sh    # Check system health
```

See [QUICK_START.md](./QUICK_START.md) for detailed instructions.

---

## Manual Setup (Alternative)

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend)
- OpenAI API key (for AI analysis)

### Full Application Setup (Backend + Frontend)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd indian-palmistry-ai
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Add your OpenAI API key to .env:
# OPENAI_API_KEY=your_openai_api_key_here
```

3. **Start backend services**:
```bash
docker compose up -d
```

4. **Start frontend application**:
```bash
cd frontend
npm install
npm run dev
```

5. **Verify everything is running**:
```bash
# Check backend health
curl http://localhost:8000/healthz

# Check frontend (should return HTML)
curl http://localhost:3000
```

The application will be available at:
- **Frontend PWA**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

### Using the Application

1. Open http://localhost:3000 in your browser
2. You'll see the Indian Palmistry AI interface with cultural saffron theme
3. Upload palm images using the drag & drop interface
4. Watch real-time analysis progress with traditional messaging
5. Get AI-powered palmistry insights based on Hast Rekha Shastra

### Backend Only (API Development)

If you only need the backend API:

```bash
# Start backend services only
docker compose up -d

# The API will be available at http://localhost:8000
```

## API Usage Examples

### Register and Login
```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123", "name": "John Doe"}'

# Login and save session cookie
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}' \
  -c cookies.txt
```

### Upload Palm Image for Analysis
```bash
# Upload palm image (creates analysis and queues AI processing)
curl -X POST http://localhost:8000/api/v1/analyses/ \
  -b cookies.txt \
  -F "left_image=@palm_image.jpg"
```

### Check Analysis Status
```bash
# Poll for analysis completion
curl -X GET http://localhost:8000/api/v1/analyses/1/status
```

### Get Analysis Results
```bash
# Get public summary (no auth required)
curl -X GET http://localhost:8000/api/v1/analyses/1/summary

# Get full analysis (requires authentication)
curl -X GET http://localhost:8000/api/v1/analyses/1 -b cookies.txt
```

### Start a Conversation
```bash
# Create a conversation about the analysis
curl -X POST http://localhost:8000/api/v1/analyses/1/conversations/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"title": "Questions about my palm reading"}'

# Ask a follow-up question
curl -X POST http://localhost:8000/api/v1/analyses/1/conversations/1/talk \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your_csrf_token" \
  -d '{"message": "What does my life line indicate about my health?"}'
```

## Local Development

### Setup
```bash
# Install dependencies
pip install -e .[dev]

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
docker compose exec api python -m alembic upgrade head

# Start Redis for local development
docker compose up redis -d
```

### Development Commands
```bash
# Start API server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Run tests
pytest

# Code formatting
black app/ tests/
ruff check app/ tests/

# Type checking
mypy app/
```

## API Documentation

Interactive API documentation is automatically generated:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Current user info

#### Palm Analysis
- `POST /api/v1/analyses/` - Upload images for analysis
- `GET /api/v1/analyses/{id}/status` - Check analysis job status
- `GET /api/v1/analyses/{id}/summary` - Get public summary
- `GET /api/v1/analyses/{id}` - Get full analysis (auth required)
- `GET /api/v1/analyses/` - List user's analyses
- `POST /api/v1/enhanced/analyses/{id}/advanced-analysis` - Specialized line analysis
- `POST /api/v1/enhanced/analyses/compare` - Multi-analysis comparison
- `GET /api/v1/enhanced/analyses/history` - Analysis history with trends

#### Enhanced Conversations
- `POST /api/v1/analyses/{id}/conversations/` - Create conversation
- `GET /api/v1/analyses/{id}/conversations/` - List conversations
- `POST /api/v1/analyses/{id}/conversations/{id}/talk` - Send message
- `GET /api/v1/analyses/{id}/conversations/{id}/messages` - Get message history
- `GET /api/v1/enhanced/conversations/templates` - Conversation templates
- `POST /api/v1/enhanced/conversations/{id}/enhanced-talk` - Context-aware chat
- `GET /api/v1/enhanced/conversations/search` - Full-text search
- `GET /api/v1/enhanced/conversations/{id}/export` - Export conversations
- `GET /api/v1/enhanced/conversations/analytics` - Usage analytics

#### User Dashboard
- `GET /api/v1/enhanced/dashboard` - Comprehensive dashboard
- `GET /api/v1/enhanced/dashboard/preferences` - User preferences
- `PUT /api/v1/enhanced/dashboard/preferences` - Update preferences
- `GET /api/v1/enhanced/dashboard/statistics` - Usage statistics
- `GET /api/v1/enhanced/dashboard/achievements` - Achievements
- `GET /api/v1/enhanced/dashboard/export-data` - GDPR export

#### Monitoring & Analytics
- `GET /api/v1/enhanced/monitoring/dashboard` - System monitoring
- `GET /api/v1/enhanced/monitoring/health` - Detailed health status
- `GET /api/v1/enhanced/monitoring/cost-analytics` - Cost tracking
- `GET /api/v1/enhanced/monitoring/usage-analytics` - Usage patterns

## Architecture

### Multi-Container Architecture
- **API Service**: FastAPI application with health monitoring
- **Redis Service**: Session storage, caching, and job queuing
- **Worker Service**: Celery workers for background AI processing
- **Database**: SQLite (dev) / PostgreSQL (prod)

### Key Design Patterns
- **Background Job Processing**: Non-blocking AI analysis with real-time status
- **Session-based Authentication**: Secure Redis sessions with CSRF protection  
- **Service Layer Architecture**: Clean separation of concerns
- **Async/Await**: Full async support for database and external API calls
- **Structured Logging**: JSON logs with correlation ID tracking

## Development Roadmap

### ✅ Phase 1: Foundation (Complete)
- Multi-container Docker setup
- FastAPI backend with async SQLAlchemy
- Redis integration for sessions and jobs
- Celery background task processing
- Database migrations with Alembic
- Structured logging and health monitoring

### ✅ Phase 2: MVP (Complete)
- User authentication and session management
- Palm image upload and validation
- OpenAI GPT-4o-mini integration for AI analysis
- Background job processing for AI requests
- Conversation system for follow-up questions
- Complete API with documentation

### ✅ Phase 3: Enterprise Enhancement (Complete)
- Advanced Redis caching with connection pooling
- Multi-level rate limiting and adaptive security
- Specialized palm line analysis (8 line types)
- Context-aware conversations with memory
- Comprehensive user dashboard and analytics
- Database optimization with performance indexes
- System monitoring and cost tracking
- GDPR-compliant data export
- Advanced filtering and pagination utilities
- Comprehensive test suite (100+ tests)

### ✅ Phase 3.5: Frontend Foundation (Complete)
- Next.js 14 with TypeScript and App Router
- Cultural minimalist design system with saffron palette
- Mobile-first responsive design with 44px touch targets
- Core UI component library (Button, Input, Card, Spinner)
- Authentication system integration with backend
- Background job polling for real-time analysis status
- Image upload with validation and camera support

### ✅ Phase 3.75: Frontend Completion (Complete)
- **Advanced Security**: CSRF protection, input sanitization, secure forms
- **Progressive Web App**: Offline support, background sync, installation prompts
- **Performance Monitoring**: Core Web Vitals tracking with web-vitals library
- **Optimized Components**: OptimizedImage, LazyLoad, OfflineIndicator, InstallPrompt
- **Context Providers**: SecurityProvider, PerformanceProvider for global state
- **Custom Hooks**: useCSRF, useOffline, usePerformanceMonitoring
- **Comprehensive Testing**: 100+ tests covering all components and functionality
- **Component Documentation**: Complete API documentation for all components

### 🔄 Phase 4: Full Integration & Scaling (Next)
- Complete dashboard implementation with analytics
- Real-time conversation interface with AI chat
- Advanced PWA features (push notifications, background sync)
- Performance optimization and bundle analysis
- Production deployment and CI/CD pipeline

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# OpenAI Integration
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/dev.db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Security  
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# File Storage
FILE_STORAGE_ROOT=./data/images
```

## Enterprise Monitoring and Analytics

- **Health Endpoints**: `/healthz` and `/api/v1/enhanced/monitoring/health`
- **System Monitoring**: Real-time CPU, memory, and disk usage tracking
- **Queue Dashboard**: Celery job monitoring with worker health status
- **Cost Analytics**: Comprehensive OpenAI usage and cost tracking
- **Usage Analytics**: User behavior patterns and feature adoption
- **Performance Monitoring**: Database query optimization and slow query detection
- **Security Monitoring**: Rate limiting, threat detection, and IP reputation
- **Structured Logging**: JSON format with correlation IDs
- **Error Handling**: Comprehensive error tracking and reporting

## Contributing

This project is currently in active development. Contribution guidelines will be added once the core features are stabilized.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This application is for entertainment and educational purposes only. Palmistry readings should not be considered as professional advice for life decisions. The AI-generated content is based on traditional palmistry interpretations but should not replace professional consultation for health, financial, or personal matters.