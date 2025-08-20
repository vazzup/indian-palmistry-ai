# Indian Palmistry AI

An AI-powered application for traditional Indian palmistry readings using OpenAI's Vision API and natural language processing.

## Overview

This project combines ancient Indian palmistry wisdom (Hast Rekha Shastra) with modern AI technology to provide personalized palm readings. Users can upload images of their palms and receive detailed analyses based on traditional palmistry principles, then engage in conversations about their readings.

## 🚀 Current Status: Phase 2 MVP Complete

The application is now a fully functional AI-powered palmistry service with:
- ✅ Complete user authentication system
- ✅ AI-powered palm analysis using OpenAI GPT-4o-mini
- ✅ Background job processing for scalable analysis
- ✅ Conversation interface for follow-up questions
- ✅ Secure image upload and processing
- ✅ Production-ready infrastructure

## Features

### 🔮 Core Palmistry Features
- **AI Palm Analysis**: Upload palm images for instant AI-powered readings
- **Traditional Indian Palmistry**: Based on authentic Hast Rekha Shastra principles
- **Summary & Full Reports**: Public summaries with detailed reports for registered users
- **Multi-Image Support**: Analyze both left and right palm (up to 2 images)
- **Real-time Processing**: Background job processing with status polling

### 💬 Interactive Experience  
- **Conversation System**: Ask follow-up questions about your palm reading
- **Contextual Responses**: AI responses grounded on your specific analysis
- **Message History**: Complete conversation history with pagination
- **Analysis-Scoped Chats**: Separate conversations for each palm reading

### 👤 User Management
- **User Registration & Login**: Secure email-based authentication
- **Session Management**: Redis-based sessions with CSRF protection
- **Analysis History**: View and manage all your previous palm readings
- **Anonymous Uploads**: Try the service before registering

### 🔒 Security & Performance
- **Secure Authentication**: bcrypt password hashing, HTTP-only cookies
- **File Security**: Image validation, secure storage, thumbnail generation
- **Background Processing**: Non-blocking AI analysis with job queuing
- **Cost Tracking**: Token usage and cost monitoring for OpenAI API

## Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async)
- **AI/ML**: OpenAI GPT-4o-mini Vision API
- **Database**: SQLite (dev), PostgreSQL/Supabase (prod)
- **Caching & Jobs**: Redis, Celery
- **Authentication**: Session-based with Redis, bcrypt
- **Infrastructure**: Docker, Docker Compose, multi-stage builds
- **Image Processing**: Pillow, thumbnail generation
- **API Documentation**: Auto-generated OpenAPI/Swagger

## Project Structure

```
indian-palmistry-ai/
├── app/                    # Main application code
│   ├── api/               # API endpoints
│   │   └── v1/            # API version 1
│   │       ├── auth.py    # Authentication endpoints
│   │       ├── analyses.py # Palm analysis endpoints
│   │       └── conversations.py # Conversation endpoints
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── database.py    # Database setup
│   │   ├── redis.py       # Redis integration
│   │   ├── celery_app.py  # Background jobs
│   │   └── logging.py     # Structured logging
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
│   │   └── password_service.py # Security utilities
│   ├── tasks/             # Background tasks
│   │   └── analysis_tasks.py # AI processing tasks
│   └── dependencies/      # FastAPI dependencies
│       └── auth.py        # Authentication dependencies
├── alembic/               # Database migrations
├── tests/                 # Test suite
├── docs/                  # Documentation
├── data/                  # Local data storage
└── docker-compose.yml     # Multi-service setup
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for AI analysis)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd indian-palmistry-ai
```

2. Set up environment variables:
```bash
cp .env.example .env
# Add your OpenAI API key to .env:
# OPENAI_API_KEY=your_openai_api_key_here
```

3. Start the services:
```bash
docker compose up -d
```

4. Check if services are running:
```bash
curl http://localhost:8000/healthz
```

The application will be available at:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

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

#### Conversations
- `POST /api/v1/analyses/{id}/conversations/` - Create conversation
- `GET /api/v1/analyses/{id}/conversations/` - List conversations
- `POST /api/v1/analyses/{id}/conversations/{id}/talk` - Send message
- `GET /api/v1/analyses/{id}/conversations/{id}/messages` - Get message history

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

### 🔄 Phase 3: Enhancement (Next)
- Frontend React/Next.js application
- Enhanced UI/UX with real-time updates
- Advanced palmistry features
- Performance optimizations
- Comprehensive testing suite

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

## Monitoring and Logging

- **Health Endpoints**: `/healthz` and `/api/v1/health`
- **Structured Logging**: JSON format with correlation IDs
- **Job Monitoring**: Real-time status tracking for background tasks
- **Cost Tracking**: OpenAI token usage and cost monitoring
- **Error Handling**: Comprehensive error tracking and reporting

## Contributing

This project is currently in active development. Contribution guidelines will be added once the core features are stabilized.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This application is for entertainment and educational purposes only. Palmistry readings should not be considered as professional advice for life decisions. The AI-generated content is based on traditional palmistry interpretations but should not replace professional consultation for health, financial, or personal matters.