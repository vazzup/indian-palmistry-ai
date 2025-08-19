# Indian Palmistry AI 🔮

An AI-powered palmistry reading application that analyzes palm images using OpenAI's vision models to provide personalized palm readings. Built with modern web technologies and designed for scalability.

## ✨ What It Does

- **🖐️ Palm Analysis**: Upload photos of your palms for AI-powered readings
- **🤖 AI Integration**: Uses OpenAI's advanced vision models for detailed analysis
- **💬 Interactive Chat**: Ask follow-up questions about your palm reading
- **🔐 Secure Sessions**: Session-based authentication with Redis storage
- **⚡ Background Processing**: Non-blocking analysis with real-time progress updates
- **📱 Modern UI**: Clean, responsive interface built with Next.js

## 🏗️ Phase 1 Status - Foundation Complete

**Phase 1 Deliverables:**
- ✅ Multi-container architecture with Docker Compose
- ✅ FastAPI backend with health checks
- ✅ Database support (SQLite dev / Supabase prod)
- ✅ Redis for sessions, caching, and job queues
- ✅ Celery background workers
- ✅ Development tools and testing framework
- ✅ Structured logging and monitoring
- ✅ Code quality tools (Black, Ruff, MyPy)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 2GB free RAM
- Ports 3000, 6379, and 8000 available

### 1. Get Started
```bash
# Clone the repository
git clone <repository-url>
cd indian-palmistry-ai

# Start all services
docker compose up -d

# Verify everything is running
curl http://localhost:8000/healthz
```

### 2. Access the Application
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend** (Phase 2): http://localhost:3000
- **Health Check**: http://localhost:8000/healthz

### 3. Development Setup
```bash
# Copy environment template (optional)
cp .env.example .env

# View service logs
docker compose logs -f api
docker compose logs -f worker

# Run tests
docker compose exec api pytest

# Stop services
docker compose down
```

## 🏛️ Architecture

### Services
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Background    │
│   Next.js       │────▶   Backend       │────▶   Workers      │
│   Port 3000     │    │   Port 8000     │    │   Celery        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │    Database     │
                       │ Sessions/Cache/ │    │ SQLite (dev)    │
                       │ Job Queue       │    │ Supabase (prod) │
                       │ Port 6379       │    └─────────────────┘
                       └─────────────────┘
```

### Directory Structure
```
indian-palmistry-ai/
├── app/                          # FastAPI backend
│   ├── api/v1/                   # API endpoints
│   ├── core/                     # Config, database, logging
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic DTOs
│   ├── services/                 # Business logic
│   ├── tasks/                    # Celery background tasks
│   └── main.py                   # FastAPI app factory
├── frontend/                     # Next.js frontend
├── tests/                        # Test suite
├── docs/                         # Project documentation
├── data/images/                  # Local file storage
├── docker-compose.yml            # Multi-service orchestration
├── Dockerfile                    # Multi-stage Docker build
└── pyproject.toml               # Python dependencies
```

## 🛠️ Development

### Make Commands
```bash
make help              # Show all available commands
make dev               # Start development environment
make test              # Run tests
make lint              # Run linting
make format            # Format code
make logs              # Show logs
make shell             # Open shell in API container
make clean             # Clean up containers
```

### Manual Commands
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f redis

# Run tests
docker-compose exec api pytest

# Format code
docker-compose exec api black app/
docker-compose exec api ruff check app/ --fix

# Access containers
docker-compose exec api bash
docker-compose exec redis redis-cli
```

### Background Jobs
```bash
# Test background job processing
docker-compose exec api python -c "
from app.tasks.analysis_tasks import process_palm_analysis
job = process_palm_analysis.delay(123)
print(f'Job ID: {job.id}')
print(f'Result: {job.get()}')
"

# Monitor Celery workers
docker-compose exec api celery -A app.core.celery_app inspect active

# Start Flower monitoring
docker-compose --profile monitoring up -d flower
```

## 🧪 Testing

### Run Tests
```bash
# All tests
make test

# With coverage
make test-cov

# Watch mode
make test-watch

# Specific test
docker-compose exec api pytest tests/test_api/test_health.py -v
```

### Test Structure
- `tests/test_api/` - API endpoint tests
- `tests/test_services/` - Business logic tests  
- `tests/test_models/` - Database model tests
- `tests/conftest.py` - Shared test fixtures

## 🔧 Configuration

### Environment Variables
Key variables in `.env`:

```bash
# Database (auto-detected)
DATABASE_URL=sqlite+aiosqlite:///./data/dev.db
# DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # Production

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# OpenAI (Phase 2)
OPENAI_API_KEY=sk-your-key-here

# Security
SECRET_KEY=change-in-production
ALLOWED_ORIGINS=http://localhost:3000

# File Storage
FILE_STORAGE_ROOT=./data/images
```

### Database Support
- **Development**: SQLite with WAL mode
- **Production**: Supabase (managed PostgreSQL)
- Automatic detection based on `DATABASE_URL`
- Migrations ready with Alembic

## 📊 Monitoring & Logging

### Health Checks
```bash
# API health
curl http://localhost:8000/healthz

# Service health
make health

# Redis health
docker-compose exec redis redis-cli ping
```

### Logs
- Structured JSON logging to stdout
- Correlation ID tracking across requests
- Request/response logging with duration
- Error tracking with context

### Monitoring Tools
- **Flower**: Celery task monitoring (port 5555)
- **FastAPI Docs**: API documentation (port 8000/docs)
- **Health Endpoints**: `/healthz`, `/api/v1/health`

## 🔄 Background Processing

### Job Flow
1. API receives request → queues background job
2. Celery worker processes job asynchronously  
3. Job status stored in Redis
4. Frontend polls for job completion
5. Results returned to user

### Job Monitoring
```bash
# Queue status
docker-compose exec api celery -A app.core.celery_app inspect reserved

# Test job
docker-compose exec api python -c "
from app.core.celery_app import test_task
result = test_task.delay('Hello World')
print(result.get())
"
```

## 📈 Phase 2 Preparation

The foundation is ready for Phase 2 MVP development:
- ✅ Authentication system (Redis sessions)
- ✅ Background job processing (OpenAI integration)
- ✅ File upload handling infrastructure
- ✅ Database models and migrations
- ✅ API versioning structure
- ✅ Testing framework

## 🐛 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker status
docker --version
docker-compose --version

# Clean start
make clean
make build
make up
```

**Database connection issues:**
```bash
# Check SQLite file
ls -la data/
# Reset database
rm -f data/dev.db
docker-compose exec api python -c "
from app.core.database import create_tables
import asyncio
asyncio.run(create_tables())
"
```

**Redis connection issues:**
```bash
# Check Redis
docker-compose exec redis redis-cli ping
# Expected: PONG

# Check Redis logs
docker-compose logs redis
```

**Worker not processing jobs:**
```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Manual worker start
docker-compose exec api celery -A app.core.celery_app worker --loglevel=debug
```

### Port Conflicts
If ports 3000, 6379, or 8000 are in use:
```bash
# Check what's using ports
lsof -i :8000
lsof -i :3000  
lsof -i :6379

# Kill processes or modify docker-compose.yml ports
```

### Performance Issues
```bash
# Check container resources
docker stats

# Check logs for errors
make logs

# Monitor Redis memory
docker-compose exec redis redis-cli info memory
```

## 📚 Next Steps

1. **Verify Phase 1**: Run `make test` and `make health`
2. **Phase 2 Development**: Add authentication and OpenAI integration
3. **Production Deploy**: Switch to Supabase and managed Redis

## 🤝 Development Workflow

1. Create feature branch
2. Make changes with tests
3. Run `make lint format test`
4. Submit PR with passing CI
5. Deploy to staging/production

---

**Phase 1 Foundation - Complete ✅**  
Ready for Phase 2 MVP development.